from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from app.services.image_cache_service import image_cache
from app.services import book_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/images/proxy")
async def get_proxied_image(url: str):
    """
    Proxy and cache images from external sources.
    Images are cached on first request and served from cache thereafter.
    """
    try:
        cached_path = await image_cache.get_or_download(url)
        if cached_path:
            return FileResponse(cached_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found or failed to cache")
    except Exception as e:
        logger.error(f"Error serving proxied image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/images/refresh/{book_id}")
async def refresh_book_cover(book_id: int, db: AsyncSession = Depends(get_db)):
    """Refresh a book's cover image by re-fetching from OpenLibrary"""
    try:
        book = await book_service.refresh_book_cover(db, book_id)
        return {"message": "Successfully refreshed book cover", "book": book}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing book cover: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/images/refresh-all")
async def refresh_all_covers(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Refresh cover images for all books in the background"""
    try:
        # Start the refresh in the background
        background_tasks.add_task(book_service.refresh_all_book_covers, db)
        return {"message": "Started refreshing all book covers in the background"}
    except Exception as e:
        logger.error(f"Error starting cover refresh: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start cover refresh")
