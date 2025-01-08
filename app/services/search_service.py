import httpx
import json
import time
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, case
from sqlalchemy import select
from app.db import models, schemas
import asyncio
from app.services.image_cache_service import image_cache
import logging

logger = logging.getLogger(__name__)

async def get_typeahead_suggestions(db: AsyncSession, query: str, limit: int = 10) -> List[schemas.TypeaheadSuggestion]:
    """Get typeahead suggestions for search by matching book titles and author names.
    
    Args:
        db: Database session
        query: Search query string
        limit: Maximum number of suggestions to return
        
    Returns:
        List of TypeaheadSuggestion objects containing book title, author name, and book ID
    """
    if not query or len(query.strip()) == 0:
        return []
        
    # Clean the query and prepare patterns
    clean_query = query.strip().lower()
    strict_pattern = clean_query + '%'  # For exact prefix match
    word_pattern = '% ' + clean_query + '%'  # For matching word prefixes
    
    # Query books and join with authors to search across both
    # Use CASE to prioritize strict prefix matches over word prefix matches
    result = await db.execute(
        select(models.Book, models.Author)
        .join(models.Author)
        .where(
            or_(
                # Title matches
                func.lower(models.Book.title).like(strict_pattern),
                func.lower(models.Book.title).like(word_pattern),
                # Author matches
                func.lower(models.Author.name).like(strict_pattern),
                func.lower(models.Author.name).like(word_pattern)
            )
        )
        .order_by(
            # Order by match type (strict prefix first, then word prefix)
            case(
                (func.lower(models.Book.title).like(strict_pattern), 1),
                (func.lower(models.Author.name).like(strict_pattern), 1),
                (func.lower(models.Book.title).like(word_pattern), 2),
                (func.lower(models.Author.name).like(word_pattern), 2),
                else_=3
            ),
            models.Book.title
        )
        .limit(limit)
    )
    
    matches = result.all()
    suggestions = []
    
    # Format results
    for book, author in matches:
        suggestions.append(schemas.TypeaheadSuggestion(
            id=book.id,
            title=book.title,
            author=author.name if author else None,
            cover_image_url=await convert_to_small_cover(book.cover_image_url)
        ))
    
    return suggestions

async def convert_to_small_cover(url: Optional[str]) -> Optional[str]:
    """Convert an OpenLibrary cover URL to use the small (-S) size."""
    if not url:
        return None
    return re.sub(r'-[LM]\.jpg$', '-S.jpg', url)

async def _cache_cover_image(cover_url: str) -> None:
    """Cache a cover image in the background without blocking."""
    try:
        await image_cache.ensure_cached(cover_url)
    except Exception as e:
        logger.error(f"Error caching cover image {cover_url}: {str(e)}")

async def search_books(db: AsyncSession, query: str, page: int = 1, per_page: int = 12) -> List[Dict[str, Any]]:
    """Search for books using Open Library API."""
    try:
        logger.info(f"[DEBUG] Searching Open Library with query: {query}")
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Prepare search parameters
        params = {
            'q': query,
            'limit': per_page,
            'offset': offset,
            'fields': 'key,title,author_name,author_key,cover_i,first_publish_year'
        }
        
        logger.info(f"[DEBUG] Search parameters: {params}")
        logger.info("[DEBUG] Making request to: https://openlibrary.org/search.json")
        
        client = httpx.AsyncClient()
        try:
            start_time = time.time()
            response = await client.get(
                'https://openlibrary.org/search.json',
                params=params,
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"[DEBUG] Request error searching Open Library: {response.text}")
                logger.error(f"[DEBUG] Response status: {response.status_code}")
                return []
                
            data = response.json()
            end_time = time.time()
            logger.info(f"[DEBUG] Open Library API response time: {end_time - start_time:.2f} seconds")
            
            if not data.get('docs'):
                logger.info("[DEBUG] No results found")
                return []
            
            # Process results
            results = []
            
            for doc in data['docs']:
                # Skip if missing required fields
                if not doc.get('key') or not doc.get('title'):
                    continue
                    
                # Get first author if available
                author_name = doc.get('author_name', ['Unknown'])[0] if doc.get('author_name') else 'Unknown'
                author_key = doc.get('author_key', [None])[0] if doc.get('author_key') else None
                
                # Get cover image URL if available
                cover_id = doc.get('cover_i')
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id and cover_id > 0 else None
                
                # Get cached URL if available
                if cover_url:
                    cover_url = await image_cache.get_cached_url(cover_url)
                
                result = {
                    'title': doc['title'],
                    'author': author_name,
                    'author_key': author_key,
                    'open_library_key': doc['key'].replace('/works/', ''),
                    'cover_image_url': cover_url,
                    'publication_year': doc.get('first_publish_year')
                }
                results.append(result)
            
            return results
            
        finally:
            await client.aclose()
            
    except Exception as e:
        logger.error(f"[DEBUG] Error searching Open Library: {str(e)}")
        return []
