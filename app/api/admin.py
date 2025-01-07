from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.database import get_db
from app.db.models import Book, Author
from scripts.bootstrap_books import bootstrap_books
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class BookUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    questions_and_answers: Optional[str] = None
    affiliate_links: Optional[str] = None
    cover_image_url: Optional[str] = None
    author: Optional[str] = None  # To update author's name
    author_key: Optional[str] = None  # To link to different author

@router.post("/bootstrap")
async def run_bootstrap(
    start: int = Query(0, description="Starting index for book titles"),
    limit: int = Query(None, description="Maximum number of books to process"),
    db: AsyncSession = Depends(get_db)
):
    """Run the bootstrap script to populate the database with initial books.
    
    Args:
        start (int): Starting index for book titles (default: 0)
        limit (int): Maximum number of books to process (default: None, process all)
        db (AsyncSession): Database session
    """
    try:
        await bootstrap_books(start=start, limit=limit)
        return {
            "message": "Successfully bootstrapped the database",
            "start": start,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/books/{book_id}")
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a book record and optionally its author in the database.
    
    Args:
        book_id (int): ID of the book to update
        book_update (BookUpdate): Fields to update, including author fields
        db (AsyncSession): Database session
    
    Returns:
        dict: Updated book and author data
    
    Raises:
        HTTPException: If book not found, author key invalid, or update fails
    """
    try:
        # Check if book exists
        result = await db.execute(
            select(Book).where(Book.id == book_id)
        )
        book = result.scalars().first()
        if not book:
            raise HTTPException(status_code=404, detail=f"Book {book_id} not found")

        # Handle author updates first
        if book_update.author_key is not None:
            # Try to find author by open_library_key
            result = await db.execute(
                select(Author).where(Author.open_library_key == book_update.author_key)
            )
            new_author = result.scalars().first()
            if not new_author:
                raise HTTPException(
                    status_code=404,
                    detail=f"Author with key {book_update.author_key} not found"
                )
            # Update book's author_id
            book.author_id = new_author.id
        elif book_update.author is not None:
            # Update existing author's name
            await db.execute(
                update(Author)
                .where(Author.id == book.author_id)
                .values(name=book_update.author)
            )

        # Build update dict for book fields
        update_data = book_update.dict(
            exclude={'author', 'author_key'},  # Exclude author fields
            exclude_unset=True
        )

        if update_data:
            # Update the book
            await db.execute(
                update(Book)
                .where(Book.id == book_id)
                .values(**update_data)
            )

        await db.commit()

        # Get updated book with author
        result = await db.execute(
            select(Book).where(Book.id == book_id)
        )
        updated_book = result.scalars().first()
        
        return {
            "message": "Book updated successfully",
            "book": {
                "id": updated_book.id,
                "title": updated_book.title,
                "author": updated_book.author_str,
                "author_key": updated_book.author.open_library_key,
                "summary": updated_book.summary,
                "questions_and_answers": updated_book.questions_and_answers,
                "affiliate_links": updated_book.affiliate_links,
                "cover_image_url": updated_book.cover_image_url
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
