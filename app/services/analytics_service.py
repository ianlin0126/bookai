from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload, Session
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union, Dict, Any
import asyncio

from app.db import models, schemas
from app.core.exceptions import BookNotFoundError
from app.services.image_cache_service import image_cache
import logging

logger = logging.getLogger(__name__)

async def _process_book_for_response(book: models.Book) -> Dict[str, Any]:
    """Process a book for API response, including cached image URL."""
    original_url = book.cover_image_url
    if original_url:
        cached_url = await image_cache.get_cached_url(original_url)
        book.cover_image_url = cached_url
    return book

async def _cache_book_cover(book: models.Book) -> None:
    """Cache a book's cover image in the background."""
    if book and book.cover_image_url:
        try:
            await image_cache.ensure_cached(book.cover_image_url)
        except Exception as e:
            logger.error(f"Error caching cover for book {book.id}: {str(e)}")

async def record_visit(db: Session, book_id: int) -> models.Visit:
    # Check if book exists
    result = await db.execute(
        select(models.Book).where(models.Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise BookNotFoundError(f"Book with id {book_id} not found")

    today = datetime.now().date()
    result = await db.execute(
        select(models.Visit).where(
            models.Visit.book_id == book_id,
            models.Visit.visit_date == today
        )
    )
    visit = result.scalar_one_or_none()
    
    if visit:
        visit.visit_count += 1
        visit.updated_at = datetime.utcnow()
    else:
        visit = models.Visit(
            book_id=book_id,
            visit_date=today,
            visit_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(visit)
    
    await db.commit()
    return visit

async def get_popular_books(
    db: AsyncSession, 
    days: int = 7, 
    limit: int = 12,
    offset: int = 0,
    get_total: bool = False
) -> Union[List[Tuple[models.Book, int]], Tuple[List[Tuple[models.Book, int]], int]]:
    """Get the most visited books in the last N days with their visit counts."""
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    # Build subquery to get visit counts
    visit_counts = (
        select(
            models.Visit.book_id,
            func.sum(models.Visit.visit_count).label('total_visits')
        )
        .where(models.Visit.visit_date >= cutoff_date)
        .group_by(models.Visit.book_id)
        .subquery()
    )
    
    # Main query joining books with visit counts and authors
    query = (
        select(models.Book, visit_counts.c.total_visits)
        .join(visit_counts, models.Book.id == visit_counts.c.book_id)
        .join(models.Author)
        .options(selectinload(models.Book.author))
        .order_by(desc(visit_counts.c.total_visits))
    )
    
    if get_total:
        # Get total count
        count_query = select(func.count()).select_from(query)
        total = await db.scalar(count_query) or 0
        
        # Get paginated results
        results = await db.execute(query.offset(offset).limit(limit))
        books_with_visits = results.all()
    else:
        # Get results with limit only (original behavior)
        results = await db.execute(query.limit(limit))
        books_with_visits = results.all()
    
    # Process books to use cached URLs
    processed_books_with_visits = []
    for book, visits in books_with_visits:
        processed_book = await _process_book_for_response(book)
        processed_books_with_visits.append((processed_book, visits))
    
    return (processed_books_with_visits, total) if get_total else processed_books_with_visits
