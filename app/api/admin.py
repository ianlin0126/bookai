from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from scripts.bootstrap_books import bootstrap_books

router = APIRouter()

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
