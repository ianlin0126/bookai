from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.services import analytics_service
from app.db import schemas
from app.core.exceptions import BookNotFoundError

router = APIRouter()

@router.post("/visit/{book_id}", response_model=schemas.Visit)
async def record_visit(book_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await analytics_service.record_visit(db, book_id)
    except BookNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/popular", response_model=List[Dict[str, Any]])
async def get_popular_books(
    days: int = Query(365, ge=1, description="Number of days to look back"),
    limit: int = Query(12, ge=1, le=50, description="Maximum number of books to return"),
    page: Optional[int] = Query(None, ge=1, description="Page number (enables pagination if provided)"),
    per_page: Optional[int] = Query(None, ge=1, le=50, description="Items per page (required if page is provided)"),
    db: AsyncSession = Depends(get_db)
):
    """Get the most popular books based on visit count."""
    # If page is provided, use pagination
    if page is not None:
        items_per_page = per_page or limit
        offset = (page - 1) * items_per_page
        books_with_visits, total = await analytics_service.get_popular_books(
            db=db, 
            days=days,
            limit=items_per_page,
            offset=offset,
            get_total=True
        )
        
        # Return paginated response in the same format as before
        return [
            {
                "id": book.id,
                "title": book.title,
                "author_id": book.author_id,
                "author": book.author_str,
                "open_library_key": book.open_library_key,
                "cover_image_url": book.cover_image_url,
                "summary": book.summary,
                "questions_and_answers": book.questions_and_answers,
                "affiliate_links": book.affiliate_links,
                "created_at": book.created_at,
                "updated_at": book.updated_at,
                "visit_count": visit_count,
                # Add pagination metadata as regular fields
                "_total": total,
                "_page": page,
                "_per_page": items_per_page,
                "_total_pages": (total + items_per_page - 1) // items_per_page,
                "_has_more": page * items_per_page < total
            }
            for book, visit_count in books_with_visits
        ]
    else:
        # Original behavior without pagination
        books_with_visits = await analytics_service.get_popular_books(
            db=db, 
            days=days,
            limit=limit
        )
        return [
            {
                "id": book.id,
                "title": book.title,
                "author_id": book.author_id,
                "author": book.author_str,
                "open_library_key": book.open_library_key,
                "cover_image_url": book.cover_image_url,
                "summary": book.summary,
                "questions_and_answers": book.questions_and_answers,
                "affiliate_links": book.affiliate_links,
                "created_at": book.created_at,
                "updated_at": book.updated_at,
                "visit_count": visit_count
            }
            for book, visit_count in books_with_visits
        ]
