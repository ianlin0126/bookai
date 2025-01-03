from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import json
import logging

from app.db.database import get_db
from app.db import schemas
from app.services import book_service, llm_service
from app.core.utils import clean_json_string

router = APIRouter()
logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    GEMINI = "gemini"
    CHATGPT = "chatgpt"

class BookRequest(BaseModel):
    title: str
    author: str

def generate_book_digest_prompt(title: str, author: str) -> str:
    """Generate a prompt for the LLM to create a book digest."""
    return f"""Please analyze the book '{title}' by {author} and provide a comprehensive digest in the following JSON format:
{{
    "summary": "A detailed summary of the book's content, themes, and key takeaways",
    "questions_and_answers": [
        {{
            "question": "An insightful question about the book",
            "answer": "A detailed answer based on the book's content"
        }}
    ]
}}

Please ensure:
1. The summary is detailed and captures the main themes
2. Include at least 3-5 question-answer pairs
3. Questions should cover different aspects of the book
4. Answers should be thorough and informative
5. IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no explanatory text.
6. Do not use newlines or special characters in text fields.
7. Use simple quotes for strings to avoid escaping issues."""

def clean_json_string(json_str: str) -> str:
    """Clean a string to ensure it's valid JSON."""
    # Remove any text before the first {
    start_idx = json_str.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in string")
    json_str = json_str[start_idx:]
    
    # Remove any text after the last }
    end_idx = json_str.rfind('}')
    if end_idx == -1:
        raise ValueError("Invalid JSON format: missing closing brace")
    json_str = json_str[:end_idx + 1]
    
    return json_str

@router.post("/query")
async def query_llm(
    request: BookRequest,
    provider: LLMProvider = Query(LLMProvider.GEMINI, description="LLM provider to use"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get an AI-generated book digest using either Gemini (default) or ChatGPT.
    Returns a JSON object with book information or NULL if book is not known.
    """
    try:
        prompt = generate_book_digest_prompt(request.title, request.author)
        
        if provider == LLMProvider.GEMINI:
            response = await llm_service.query_gemini(prompt)
        else:  # ChatGPT
            response = await llm_service.query_chatgpt(prompt)
        
        # Clean and parse the response
        cleaned_response = clean_json_string(response)
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {cleaned_response}")
            logger.error(f"Error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to parse LLM response as JSON"
            )
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/books/{book_id}/refresh", response_model=schemas.BookResponse)
async def refresh_book_digest(
    book_id: int,
    provider: Optional[str] = "gemini",
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh a book's AI-generated content using the specified LLM provider.
    """
    try:
        book = await book_service.refresh_book_digest(db, book_id, provider)
        return book
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
