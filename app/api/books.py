from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Dict, Any
from app.db.database import get_db
from app.services import book_service
from app.db import schemas, models
from app.core.exceptions import BookNotFoundError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import httpx

router = APIRouter()

@router.post("/", response_model=schemas.BookResponse)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new book.
    """
    return await book_service.create_book(db, book)

@router.get("/popular", response_model=List[schemas.BookResponse])
async def get_popular_books(limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await book_service.get_popular_books(db, limit=limit)

@router.get("/by_key/{open_library_key:path}", response_model=schemas.BookResponse)
async def get_book_by_key(
    open_library_key: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get or create a book by Open Library key.
    If book doesn't exist and title/author provided, creates new book.
    If book doesn't exist and no title/author, fetches from Open Library API.
    """
    # Remove any leading slashes
    open_library_key = open_library_key.lstrip('/')
    
    print(f"[DEBUG] API endpoint called with key: {open_library_key}")
    try:
        result = await book_service.get_book_by_open_library_key(
            db,
            open_library_key,
            title=title,
            author=author,
            cover_image_url=cover_image_url
        )
        print(f"[DEBUG] Successfully got/created book: {result.title if result else None}")
        return JSONResponse(content=jsonable_encoder(result))
    except BookNotFoundError as e:
        print(f"[DEBUG] BookNotFoundError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[DEBUG] Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{book_id}")
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a book by ID."""
    try:
        query = select(models.Book).join(models.Author, isouter=True).where(models.Book.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book
    except Exception as e:
        print(f"[DEBUG] Error getting book: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open_library/{open_library_key}")
async def get_book_by_open_library_key(
    open_library_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a book by its Open Library key."""
    try:
        query = select(models.Book).where(models.Book.open_library_key == open_library_key)
        result = await db.execute(query)
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book
    except Exception as e:
        print(f"[DEBUG] Error getting book: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open_library/{open_library_key}")
async def create_book_from_open_library(
    open_library_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a book from Open Library data."""
    try:
        # Check if book already exists
        query = select(models.Book).where(models.Book.open_library_key == open_library_key)
        result = await db.execute(query)
        existing_book = result.scalar_one_or_none()
        
        if existing_book:
            return existing_book
        
        # Fetch book data from Open Library
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://openlibrary.org/works/{open_library_key}.json")
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch book data from Open Library")
            
            data = response.json()
            
            # Get author name and key
            author_name = "Unknown Author"
            author_key = None
            if data.get('authors'):
                author_data = data['authors'][0].get('author', {})
                author_key = author_data.get('key', '').split('/')[-1] if author_data.get('key') else None
                if author_key:
                    author_response = await client.get(f"https://openlibrary.org{author_data.get('key')}.json")
                    if author_response.status_code == 200:
                        author_data = author_response.json()
                        author_name = author_data.get('name', "Unknown Author")
            
            # Get or create author
            author = None
            if author_key:
                # Check if author exists
                author_query = select(models.Author).where(models.Author.open_library_key == author_key)
                author_result = await db.execute(author_query)
                author = author_result.scalar_one_or_none()
                
                if not author:
                    # Create new author
                    author = models.Author(
                        name=author_name,
                        open_library_key=author_key
                    )
                    db.add(author)
                    await db.flush()  # Get author ID without committing
            
            # Get cover image
            cover_id = None
            if data.get('covers'):
                cover_id = data['covers'][0]
            
            # Create book
            book = models.Book(
                title=data.get('title', "Unknown Title"),
                author_id=author.id if author else None,
                open_library_key=open_library_key,
                cover_image_url=f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
            )
            
            db.add(book)
            await db.commit()
            await db.refresh(book)
            
            return book
            
    except Exception as e:
        print(f"[DEBUG] Error creating book: {str(e)}")
        await db.rollback()  # Rollback on error
        raise HTTPException(status_code=500, detail=str(e))

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
    
    return {"summary": book.summary or "No summary available yet."}

@router.get("/{book_id}/qa")
async def get_book_qa(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get Q&A for a book."""
    query = select(models.Book).where(models.Book.id == book_id)
    result = await db.execute(query)
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"qa": book.qa or []}

@router.get("/{book_id}/questions_and_answers")
async def get_book_questions_and_answers(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get a book's questions and answers."""
    try:
        query = select(models.Book).where(models.Book.id == book_id)
        result = await db.execute(query)
        book = result.scalar_one_or_none()
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return {"questions_and_answers": book.questions_and_answers or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{book_id}/refresh")
async def refresh_book_content(
    book_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Refresh a book's AI-generated content."""
    try:
        # Start the refresh in the background
        background_tasks.add_task(book_service.refresh_book_digest, db, book_id)
        return JSONResponse(content={"status": "refresh_started"})
    except Exception as e:
        print(f"Error starting refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/list")
async def list_books(
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """List books for debugging."""
    try:
        query = select(models.Book).join(models.Author, isouter=True).limit(limit)
        result = await db.execute(query)
        books = result.scalars().all()
        
        return [{
            "id": book.id,
            "title": book.title,
            "author_name": book.author.name if book.author else None,
            "open_library_key": book.open_library_key,
            "cover_image_url": book.cover_image_url,
            "created_at": book.created_at,
            "publication_year": book.publication_year
        } for book in books]
    except Exception as e:
        print(f"[DEBUG] Error listing books: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
