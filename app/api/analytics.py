from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
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

@router.get("/popular", response_model=List[schemas.BookResponse])
async def get_popular_books(
    days: int = Query(7, ge=1, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of books to return"),
    db: AsyncSession = Depends(get_db)
):
    return await analytics_service.get_popular_books(db, days=days, limit=limit)
