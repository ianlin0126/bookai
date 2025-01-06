from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Dict, Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from datetime import datetime

from app.db.database import get_db
from app.db import schemas, models
from app.services import book_service, analytics_service
from app.core.exceptions import BookNotFoundError
import httpx

router = APIRouter()

@router.post("/", response_model=schemas.BookResponse)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new book.
    """
    return await book_service.create_book(db, book)

@router.get("/{book_id}", response_model=schemas.BookResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a book by its ID."""
    try:
        book = await book_service.get_book(db, book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return schemas.BookResponse(
            id=book.id,
            title=book.title,
            author_id=book.author_id,
            author=book.author_str,
            open_library_key=book.open_library_key,
            cover_image_url=book.cover_image_url,
            summary=book.summary,
            questions_and_answers=book.questions_and_answers,
            affiliate_links=book.affiliate_links,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open_library/{open_library_key}")
async def search_book_by_open_library_key(open_library_key: str):
    """Search for a book by its Open Library key directly from Open Library API."""
    try:
        async with httpx.AsyncClient() as client:
            # Fetch book data
            response = await client.get(
                f'https://openlibrary.org/works/{open_library_key}.json',
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=404,
                    detail=f"Book with key {open_library_key} not found on Open Library"
                )
                
            book_data = response.json()
            
            # Get author information
            author_name = "Unknown"
            if book_data.get('authors'):
                author_data = book_data['authors'][0].get('author', {})
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
            if book_data.get('covers'):
                cover_id = book_data['covers'][0]
            cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
            
            # Return book data
            return {
                "title": book_data.get('title'),
                "author": author_name,
                "open_library_key": open_library_key,
                "cover_image_url": cover_url,
                "description": book_data.get('description', {}).get('value') if isinstance(book_data.get('description'), dict) else book_data.get('description'),
                "first_publish_year": book_data.get('first_publish_year')
            }
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error fetching data from Open Library: {str(e)}"
        )

@router.post("/open_library/{open_library_key}", response_model=schemas.BookResponse)
async def create_book_from_open_library(
    open_library_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a new book from Open Library data. If book already exists in DB, return it."""
    try:
        # First check if book exists in our DB
        try:
            existing_book = await book_service.get_book_by_open_library_key(db, open_library_key)
            if existing_book:
                return schemas.BookResponse(
                    id=existing_book.id,
                    title=existing_book.title,
                    author_id=existing_book.author_id,
                    author=existing_book.author_str,
                    open_library_key=existing_book.open_library_key,
                    cover_image_url=existing_book.cover_image_url,
                    summary=existing_book.summary,
                    questions_and_answers=existing_book.questions_and_answers,
                    affiliate_links=existing_book.affiliate_links,
                    created_at=existing_book.created_at,
                    updated_at=existing_book.updated_at
                )
        except ValueError:
            # Book not found in DB, continue with creation
            pass
            
        # Create new book from Open Library
        book = await book_service.post_book_by_open_library_key(db, open_library_key)
        return schemas.BookResponse(
            id=book.id,
            title=book.title,
            author_id=book.author_id,
            author=book.author_str,
            open_library_key=book.open_library_key,
            cover_image_url=book.cover_image_url,
            summary=book.summary,
            questions_and_answers=book.questions_and_answers,
            affiliate_links=book.affiliate_links,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
    except Exception as e:
        print(f"[DEBUG] Error creating book: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db/open_library/{open_library_key}", response_model=Optional[schemas.BookResponse])
async def get_book_by_open_library_key(
    open_library_key: str,
    db: AsyncSession = Depends(get_db)
) -> Optional[schemas.BookResponse]:
    """Get a book from our database by its Open Library key."""
    try:
        book = await book_service.get_book_by_open_library_key(db, open_library_key)
        if not book:
            return None
            
        # Record the visit
        await analytics_service.record_visit(db, book.id)
            
        return schemas.BookResponse(
            id=book.id,
            title=book.title,
            author_id=book.author_id,
            author=book.author_str,
            open_library_key=book.open_library_key,
            cover_image_url=book.cover_image_url,
            summary=book.summary,
            questions_and_answers=book.questions_and_answers,
            affiliate_links=book.affiliate_links,
            created_at=book.created_at,
            updated_at=book.updated_at
        )
    except Exception as e:
        # Log unexpected errors but don't expose them to client
        print(f"[ERROR] Unexpected error in get_book_by_open_library_key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{book_id}/summary")
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a summary for a book."""
    query = select(models.Book).where(models.Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"summary": book.summary}

@router.get("/{book_id}/questions_and_answers")
async def get_book_questions_and_answers(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get a book's questions and answers."""
    try:
        query = select(models.Book).where(models.Book.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return {"questions_and_answers": book.questions_and_answers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/list", response_model=List[schemas.BookResponse])
async def list_books(
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """List books for debugging."""
    try:
        query = select(models.Book).join(models.Author, isouter=True).limit(limit)
        result = await db.execute(query)
        books = result.scalars().all()
        
        return [
            schemas.BookResponse(
                id=book.id,
                title=book.title,
                author_id=book.author_id,
                author=book.author_str,
                open_library_key=book.open_library_key,
                cover_image_url=book.cover_image_url,
                summary=book.summary,
                questions_and_answers=book.questions_and_answers,
                affiliate_links=book.affiliate_links,
                created_at=book.created_at,
                updated_at=book.updated_at
            ) 
            for book in books
        ]
    except Exception as e:
        print(f"[DEBUG] Error listing books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/authors", response_model=List[Dict[str, Any]])
async def list_authors(
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """List authors for debugging."""
    try:
        query = select(models.Author).limit(limit)
        result = await db.execute(query)
        authors = result.scalars().all()
        return [
            {
                "id": author.id,
                "name": author.name,
                "open_library_key": author.open_library_key,
                "created_at": author.created_at.isoformat() if author.created_at else None
            }
            for author in authors
        ]
    except Exception as e:
        print(f"[DEBUG] Error listing authors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
