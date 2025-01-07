from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import httpx

from app.db import models, schemas
from app.services import llm_service
from app.core.utils import clean_json_string, validate_book_metadata, create_amazon_affiliate_link
from app.api.llm import generate_book_digest_prompt

async def get_book(db: AsyncSession, book_id: int) -> models.Book:
    """Get a book by ID."""
    result = await db.execute(
        select(models.Book)
        .join(models.Author)
        .options(selectinload(models.Book.author))
        .where(models.Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise ValueError(f"Book with id {book_id} not found")
    return book

async def create_book_with_author(
    db: AsyncSession,
    title: str,
    author_name: str,
    author_key: str = None,
    publication_year: int = None,
    open_library_key: str = None,
    cover_image_url: str = None
) -> models.Book:
    """Create a new book with its author."""
    # Only proceed if we have an author key
    if not author_key:
        raise ValueError("Cannot create author without OpenLibrary key")

    # Try to find existing author by key
    result = await db.execute(
        select(models.Author).where(models.Author.open_library_key == author_key)
    )
    author = result.scalar_one_or_none()
    
    # If author doesn't exist, create new one with the key
    if not author:
        author = models.Author(
            name=author_name,
            open_library_key=author_key,
            created_at=datetime.now()  # Explicitly set created_at
        )
        db.add(author)
        await db.commit()  # Commit to ensure author is created
        await db.refresh(author)  # Refresh to get all fields
    
    # Generate affiliate link
    affiliate_link = create_amazon_affiliate_link(title, author_name)
    
    # Create new book
    book = models.Book(
        title=title,
        author=author,
        publication_year=publication_year,
        open_library_key=open_library_key,
        cover_image_url=cover_image_url,
        affiliate_links=affiliate_link
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)
    
    return book

async def refresh_book_digest(db: AsyncSession, book_id: int, provider: str = "gemini") -> models.Book:
    """Update a book's AI-generated content using the specified LLM provider."""
    book = await get_book(db, book_id)
    
    # Generate prompt and get LLM response
    prompt = generate_book_digest_prompt(book.title, book.author.name)
    print(f"Generated prompt: {prompt}")  # Debug log
    
    try:
        if provider == "gemini":
            response = await llm_service.query_gemini(prompt)
        else:  # ChatGPT
            response = await llm_service.query_chatgpt(prompt)
        print(f"Raw LLM response: {response}")  # Debug log
    except Exception as e:
        print(f"LLM service error: {str(e)}")  # Debug log
        raise ValueError(f"Error getting response from LLM service: {str(e)}")
    
    # Clean and parse the response
    cleaned_response = clean_json_string(response)
    print(f"Cleaned response: {cleaned_response}")  # Debug log
    
    try:
        digest = json.loads(cleaned_response)
        print(f"Parsed digest: {json.dumps(digest, indent=2)}")  # Debug log
        
        # Validate book metadata to prevent hallucination
        is_valid, error_message = validate_book_metadata(
            digest,
            book.title,
            book.author.name
        )
        print(f"Validation result: valid={is_valid}, message={error_message}")  # Debug log
        
        if not is_valid:
            raise ValueError(f"LLM response validation failed: {error_message}")
        
        # Refresh the book object
        await db.refresh(book)
        
        # Update book with the parsed response
        book.summary = digest.get("summary")
        book.questions_and_answers = json.dumps(digest.get("questions_and_answers"))
        book.updated_at = datetime.utcnow()
        
        # Explicitly add the book to the session
        db.add(book)
        await db.flush()
        await db.commit()
        
        # Refresh one final time to ensure we have the latest data
        await db.refresh(book)
        return book
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}, Response: {cleaned_response}")  # Debug log
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")

async def get_book_summary(db: AsyncSession, book_id: int) -> Dict[str, str]:
    """Get a book's summary."""
    try:
        book = await get_book(db, book_id)
        return {"summary": book.summary if book.summary else ""}
    except ValueError:
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

async def get_book_by_open_library_key(
    db: AsyncSession,
    open_library_key: str,
) -> Optional[models.Book]:
    """
    Get a book by Open Library key from the database.
    Returns None if no book is found.
    """
    print(f"[DEBUG] get_book_by_open_library_key called with key: {open_library_key}")
    
    # Try to find existing book
    result = await db.execute(
        select(models.Book)
        .join(models.Author, isouter=True)
        .options(selectinload(models.Book.author))
        .where(models.Book.open_library_key == open_library_key)
    )
    book = result.scalar_one_or_none()
    
    if book:
        print(f"[DEBUG] Found existing book: {book.title}")
        return book
    else:
        print(f"[DEBUG] No book found with key: {open_library_key}")
        return None

async def post_book_by_open_library_key(
    db: AsyncSession,
    open_library_key: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    cover_image_url: Optional[str] = None
) -> models.Book:
    """
    Create a new book from Open Library key.
    If title/author provided, creates book with those details.
    Otherwise, fetches details from Open Library API.
    """
    if title and author:
        print(f"[DEBUG] Creating new book with provided title/author: {title} by {author}")
        return await create_book_with_author(db, title, author, open_library_key, cover_image_url)
    
    print(f"[DEBUG] Fetching from Open Library API for key: {open_library_key}")
    # Fetch from Open Library Works API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://openlibrary.org/works/{open_library_key}.json',
            timeout=60.0
        )
        
        if response.status_code != 200:
            print(f"[DEBUG] Request error fetching from Open Library: {response.text}")
            raise ValueError(f"Book with Open Library key {open_library_key} not found")
            
        data = response.json()
        
        # Get author information
        author_name = "Unknown"
        author_key = None
        if data.get('authors'):
            author_data = data['authors'][0].get('author', {})
            if isinstance(author_data, dict):
                author_key = author_data.get('key', '').replace('/authors/', '')
                # Fetch author details
                author_response = await client.get(
                    f'https://openlibrary.org/authors/{author_key}.json',
                    timeout=60.0
                )
                if author_response.status_code == 200:
                    author_info = author_response.json()
                    author_name = author_info.get('name', 'Unknown')
        
        # Get cover image URL
        cover_id = None
        if data.get('covers'):
            cover_id = data['covers'][0]
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id and cover_id > 0 else None
        
        # Create book with data from Open Library
        try:
            book = await create_book_with_author(
                db,
                data.get('title'),
                author_name,
                author_key=author_key,
                open_library_key=open_library_key,
                cover_image_url=cover_url
            )
            print(f"[DEBUG] Successfully created book: {book.title}")
            return book
        except Exception as e:
            print(f"[DEBUG] Error creating book: {str(e)}")
            raise