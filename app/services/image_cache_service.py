import os
import hashlib
import aiofiles
import aiohttp
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import Optional
import logging
import ssl
import asyncio

logger = logging.getLogger(__name__)

def get_cache_dir() -> Path:
    """Get the cache directory path, ensuring it exists."""
    # Get the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    # Always use static/cache/images relative to project root
    cache_dir = base_dir / "static" / "cache" / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir

class ImageCache:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or get_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        logger.info(f"Initialized image cache at {self.cache_dir}")

    def _get_cache_path(self, url: str) -> Path:
        """Generate a cache file path from URL using MD5 hash"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.jpg"

    async def get_cached_image_path(self, url: str) -> Optional[str]:
        """
        Get the path to a cached image. If the image isn't cached, return None.
        This doesn't download the image - use ensure_cached() for that.
        """
        cache_path = self._get_cache_path(url)
        if cache_path.exists():
            return str(cache_path)
        return None

    async def ensure_cached(self, url: str) -> Optional[str]:
        """
        Ensure an image is in the cache, downloading it if necessary.
        Returns the path to the cached image, or None if caching failed.
        """
        cache_path = self._get_cache_path(url)
        
        # Return cached path if exists
        if cache_path.exists():
            return str(cache_path)
            
        try:
            # Download and cache the image
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image from {url}: {response.status}")
                        return None
                        
                    data = await response.read()
                    
                    # Verify it's a valid image
                    try:
                        img = Image.open(BytesIO(data))
                        
                        # Save the image
                        async with aiofiles.open(cache_path, 'wb') as f:
                            await f.write(data)
                            
                        logger.info(f"Successfully cached image from {url} to {cache_path}")
                        return str(cache_path)
                        
                    except Exception as e:
                        logger.error(f"Invalid image data from {url}: {str(e)}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error caching image from {url}: {str(e)}")
            return None

    async def get_or_download(self, url: str) -> Optional[str]:
        """
        Get a cached image path, downloading it if necessary.
        Returns the path to the cached image, or None if unavailable.
        """
        return await self.ensure_cached(url)

    async def get_cached_url(self, original_url: str, cache_if_missing: bool = True) -> str:
        """
        Get the URL for a cached image. If the image isn't cached and cache_if_missing is True,
        it will be cached in the background. Returns the cached URL if available, otherwise
        returns the original URL.
        """
        if not original_url:
            return ""
            
        # If URL is already in cached format, return as is
        if original_url.startswith('/cache/images/'):
            return original_url
            
        try:
            # Try to get cached path
            cached_path = await self.get_cached_image_path(original_url)
            
            if cached_path:
                # Convert to URL path - always use /cache/images/
                filename = Path(cached_path).name
                return f"/cache/images/{filename}"
            
            # If not cached and we should cache it
            if cache_if_missing and not original_url.startswith('/cache/'):
                # Start caching in background
                asyncio.create_task(self.ensure_cached(original_url))
            
            # Return original URL while caching happens
            return original_url
            
        except Exception as e:
            logger.error(f"Error getting cached URL for {original_url}: {str(e)}")
            return original_url

# Create a global instance
image_cache = ImageCache()
