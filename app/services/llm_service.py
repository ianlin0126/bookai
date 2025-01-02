import google.generativeai as genai
from openai import AsyncOpenAI
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configure OpenAI
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_system_prompt() -> str:
    return """You are a book analysis assistant. Always respond in valid JSON format.
Your responses must be structured exactly as shown in the user's prompt.
Do not include any explanatory text, markdown formatting, or code block indicators.
If you cannot provide information about a book, return null."""

async def query_gemini(prompt: str) -> str:
    """Query Google's Gemini model with enforced JSON response."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # Add JSON formatting instruction
    formatted_prompt = f"""IMPORTANT: Respond ONLY with a JSON object.
Do not include any explanatory text, markdown formatting, or code block indicators.
If you cannot provide information about the book, return null.

{prompt}"""
    
    try:
        response = await model.generate_content_async(formatted_prompt)
        if not response or not response.text:
            raise ValueError("Empty response from Gemini API")
        return response.text
    except Exception as e:
        print(f"Error in query_gemini: {str(e)}")  # Debug log
        raise Exception(f"Error querying Gemini: {str(e)}")

async def query_chatgpt(prompt: str) -> str:
    """Query OpenAI's GPT model with enforced JSON response."""
    system_prompt = format_system_prompt()
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # Using JSON mode capable model
            response_format={ "type": "json_object" },  # Enforce JSON response
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error querying ChatGPT: {str(e)}")

def generate_book_prompts(book: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate prompts for book summary and Q&A.
    """
    summary_prompt = f"""Please provide a comprehensive summary of the book '{book['title']}' by {book.get('author_name', 'unknown author')}.
    Focus on the main themes, key arguments, and important takeaways. Keep the summary clear and engaging."""

    qa_prompt = f"""For the book '{book['title']}' by {book.get('author_name', 'unknown author')}, please generate 5 insightful question-answer pairs.
    Focus on key concepts, important themes, and practical applications. Format as a JSON array with 'question' and 'answer' fields."""

    return {
        "summary": summary_prompt,
        "qa": qa_prompt
    }
