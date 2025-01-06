from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from scripts.bootstrap_books import bootstrap_books

router = APIRouter()

@router.post("/bootstrap")
async def run_bootstrap(db: AsyncSession = Depends(get_db)):
    """Run the bootstrap script to populate the database with initial books."""
    try:
        await bootstrap_books()
        return {"message": "Successfully bootstrapped the database"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
