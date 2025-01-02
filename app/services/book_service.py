from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple, Dict, Any
from app.db import models, schemas
from app.core.exceptions import BookNotFoundError
from app.services import llm_service, search_service
from app.api.llm import generate_book_digest_prompt
import json
import re

def validate_book_metadata(digest: dict, book_title: str, book_author: str, threshold: int = 80) -> Tuple[bool, str]:
    """
    Validate that the book metadata in the LLM response matches the database record.
    Uses fuzzy matching to handle slight variations in text.
    
    Args:
        digest: The parsed LLM response
        book_title: The title from the database
        book_author: The author from the database
        threshold: Minimum fuzzy match score (0-100) to consider a match
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract title and author from LLM response
    digest_title = digest.get("title", "")
    digest_author = digest.get("author", "")
    
    # Skip validation if LLM response doesn't include title/author
    if not digest_title and not digest_author:
        return True, ""
        
    # Check title match if present
    if digest_title:
        title_ratio = fuzz.ratio(digest_title.lower(), book_title.lower())
        if title_ratio < threshold:
            return False, f"Title mismatch: LLM response '{digest_title}' doesn't match book title '{book_title}' (match score: {title_ratio})"
    
    # Check author match if present
    if digest_author and book_author:
        author_ratio = fuzz.ratio(digest_author.lower(), book_author.lower())
        if author_ratio < threshold:
            return False, f"Author mismatch: LLM response '{digest_author}' doesn't match book author '{book_author}' (match score: {author_ratio})"
    
    return True, ""

async def get_book(db: AsyncSession, book_id: int) -> models.Book:
    """Get a book by ID."""
    result = await db.execute(
        select(models.Book).where(models.Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise BookNotFoundError(f"Book with id {book_id} not found")
    return book

async def get_book_summary(db: AsyncSession, book_id: int) -> Dict[str, str]:
    """Get a book's summary."""
    try:
        book = await get_book(db, book_id)
        return {"summary": book.summary if book.summary else ""}
    except BookNotFoundError:
        raise

async def get_book_questions_and_answers(db: AsyncSession, book_id: int) -> Dict[str, Any]:
    """Get a book's questions and answers."""
    book = await get_book(db, book_id)
    qa = book.questions_and_answers
    if isinstance(qa, str):
        try:
            qa = json.loads(qa)
        except json.JSONDecodeError:
            qa = []
    elif qa is None:
        qa = []
    return {"questions_and_answers": qa}

async def refresh_book_digest(db: AsyncSession, book_id: int, provider: str = "gemini") -> models.Book:
    """Update a book's AI-generated content using the specified LLM provider."""
    try:
        book = await get_book(db, book_id)
        
        # Generate prompt and get LLM response
        prompt = generate_book_digest_prompt(book.title, book.author_name if book.author_name else "Unknown")
        
        try:
            if provider == "gemini":
                response = await llm_service.query_gemini(prompt)
            else:  # ChatGPT
                response = await llm_service.query_chatgpt(prompt)
        except Exception as e:
            print(f"LLM service error: {str(e)}")  # Debug log
            raise ValueError(f"Error getting response from LLM service: {str(e)}")
        
        # Clean and parse the response
        cleaned_response = clean_json_string(response)
        try:
            digest = json.loads(cleaned_response)
            
            # Validate book metadata to prevent hallucination
            is_valid, error_message = validate_book_metadata(
                digest,
                book.title,
                book.author_name if book.author_name else "Unknown"
            )
            
            if not is_valid:
                raise ValueError(f"LLM response validation failed: {error_message}")
            
            # Update book with the parsed response
            book.summary = digest.get("summary")
            book.questions_and_answers = json.dumps(digest.get("questions_and_answers"))
            book.updated_at = datetime.utcnow()
            
            await db.commit()
            return book
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}, Response: {cleaned_response}")  # Debug log
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        print(f"Error in refresh_book_digest: {str(e)}")  # Debug log
        raise

async def create_book(db: AsyncSession, book: schemas.BookCreate) -> models.Book:
    """Create a new book."""
    db_book = models.Book(**book.dict())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book

async def update_book(db: AsyncSession, book_id: int, book_update: schemas.BookCreate) -> models.Book:
    """Update a book's details."""
    db_book = await get_book(db, book_id)
    for key, value in book_update.dict().items():
        setattr(db_book, key, value)
    await db.commit()
    await db.refresh(db_book)
    return db_book

async def get_popular_books(db: AsyncSession, limit: int = 10) -> List[models.Book]:
    # Get books with most visits in the last 30 days
    today = datetime.today()
    result = await db.execute(
        select(models.Visit.book_id, func.sum(models.Visit.visit_count).label('total_visits'))
        .group_by(models.Visit.book_id)
        .order_by(func.sum(models.Visit.visit_count).desc())
        .limit(limit)
    )
    visits = result.all()
    
    # Get the actual book objects
    book_ids = [v.book_id for v in visits]
    if not book_ids:
        return []
    
    result = await db.execute(
        select(models.Book)
        .join(models.Author)
        .where(models.Book.id.in_(book_ids))
    )
    books = result.all()
    
    # Sort books by visit count
    visit_counts = {v.book_id: v.total_visits for v in visits}
    books.sort(key=lambda b: visit_counts.get(b.id, 0), reverse=True)
    
    return books

async def get_book_by_open_library_key(
    db: AsyncSession,
    open_library_key: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    cover_image_url: Optional[str] = None
) -> models.Book:
    """
    Get or create a book by Open Library key.
    If book doesn't exist and title/author provided, creates new book.
    If book doesn't exist and no title/author, fetches from Open Library API.
    """
    print(f"[DEBUG] get_book_by_open_library_key called with key: {open_library_key}")
    print(f"[DEBUG] Title: {title}, Author: {author}")
    
    # Try to find existing book
    result = await db.execute(
        select(models.Book)
        .join(models.Author, isouter=True)
        .where(models.Book.open_library_key == open_library_key)
    )
    book = result.scalar_one_or_none()
    
    if book:
        print(f"[DEBUG] Found existing book: {book.title}")
        return book
        
    # If no existing book, we need to create one
    if title and author:
        print(f"[DEBUG] Creating new book with provided title/author: {title} by {author}")
        return await create_book_with_author(db, title, author, open_library_key, cover_image_url)
    else:
        print(f"[DEBUG] Searching Open Library API for key: {open_library_key}")
        # Search Open Library API
        search_results = await search_service.search_books(db, open_library_key, 1, 1)
        print(f"[DEBUG] Search results: {search_results}")
        
        if not search_results:
            print(f"[DEBUG] No search results found")
            raise BookNotFoundError(f"Book with Open Library key {open_library_key} not found")
            
        book_data = search_results[0]
        print(f"[DEBUG] Found book data: {book_data}")
        
        # Create book with data from Open Library
        try:
            book = await create_book_with_author(
                db,
                book_data.get("title"),
                book_data.get("author"),
                open_library_key,
                book_data.get("cover_image_url")
            )
            print(f"[DEBUG] Successfully created book: {book.title}")
            return book
        except Exception as e:
            print(f"[DEBUG] Error creating book: {str(e)}")
            raise

async def create_book_with_author(
    db: AsyncSession,
    title: str,
    author_name: str,
    open_library_key: str,
    cover_image_url: Optional[str] = None,
    publication_year: Optional[int] = None
) -> models.Book:
    """Helper function to create a book with its author."""
    print(f"[DEBUG] Creating book with author: {title} by {author_name}")
    
    if not title or not author_name:
        raise ValueError("Title and author are required")
    
    # Create author if not exists
    result = await db.execute(
        select(models.Author).where(models.Author.name == author_name)
    )
    author = result.scalar_one_or_none()
    
    if not author:
        print(f"[DEBUG] Creating new author: {author_name}")
        author = models.Author(name=author_name)
        db.add(author)
        await db.commit()
        await db.refresh(author)
        print(f"[DEBUG] Author created: {author_name}")
    
    # Create book
    print(f"[DEBUG] Creating new book: {title}")
    book = models.Book(
        title=title,
        author_id=author.id,
        open_library_key=open_library_key,
        cover_image_url=cover_image_url,
        publication_year=publication_year
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    print(f"[DEBUG] Book created: {title}")
    return book

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
        raise ValueError("No closing brace found in JSON string")
    json_str = json_str[:end_idx + 1]
    
    # Replace invalid control characters
    json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')
    
    # Fix common JSON formatting issues
    json_str = json_str.replace('\n', ' ')
    json_str = json_str.replace('\r', ' ')
    json_str = json_str.replace('\t', ' ')
    json_str = json_str.replace('\\n', ' ')
    json_str = json_str.replace('\\r', ' ')
    json_str = json_str.replace('\\t', ' ')
    
    # Remove multiple spaces
    json_str = ' '.join(json_str.split())
    
    try:
        # Try to parse and re-stringify to ensure valid JSON
        parsed = json.loads(json_str)
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"Failed to clean JSON: {str(e)}, Original string: {json_str}")
        raise
