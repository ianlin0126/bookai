from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from datetime import datetime, timedelta
from typing import List, Optional
from app.db import models
from app.core.exceptions import BookNotFoundError

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

async def get_popular_books(db: Session, days: int = 7, limit: int = 10) -> List[models.Book]:
    """Get the most visited books in the last N days."""
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
    
    # Main query joining books with visit counts
    query = (
        select(models.Book)
        .join(visit_counts, models.Book.id == visit_counts.c.book_id)
        .order_by(desc(visit_counts.c.total_visits))
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()
