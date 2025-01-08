from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.services.image_cache_service import image_cache
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
