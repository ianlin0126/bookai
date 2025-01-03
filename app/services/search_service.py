import httpx
import json
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func
from sqlalchemy import select
from app.db import models, schemas

async def get_typeahead_suggestions(db: AsyncSession, query: str, limit: int = 10) -> List[schemas.TypeaheadSuggestion]:
    """Get typeahead suggestions for search by matching book titles and author names.
    
    Args:
        db: Database session
        query: Search query string
        limit: Maximum number of suggestions to return
        
    Returns:
        List of TypeaheadSuggestion objects containing book title and author name
    """
    if not query or len(query.strip()) == 0:
        return []
        
    # Clean the query and add wildcard for LIKE
    clean_query = query.strip().lower() + '%'
    
    # Query books and join with authors to search across both
    result = await db.execute(
        select(models.Book, models.Author)
        .join(models.Author)
        .where(
            or_(
                func.lower(models.Book.title).like(clean_query),
                func.lower(models.Author.name).like(clean_query)
            )
        )
        .limit(limit)
    )
    
    matches = result.all()
    suggestions = []
    
    # Format results
    for book, author in matches:
        suggestions.append(schemas.TypeaheadSuggestion(
            title=book.title,
            author=author.name if author else None,
            cover_image_url=book.cover_image_url
        ))
    
    return suggestions

async def search_books(db: AsyncSession, query: str, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
    """Search for books using Open Library API."""
    try:
        print("[DEBUG] Searching Open Library with query:", query)
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Prepare search parameters
        params = {
            'q': query,
            'limit': per_page,
            'offset': offset,
            'fields': 'key,title,author_name,author_key,cover_i,first_publish_year'
        }
        
        print("[DEBUG] Search parameters:", params)
        print("[DEBUG] Making request to: https://openlibrary.org/search.json")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            response = await client.get(
                'https://openlibrary.org/search.json',
                params=params,
                timeout=10.0  # 10 second timeout
            )
            
            if response.status_code != 200:
                print(f"[DEBUG] Request error searching Open Library: {response.text}")
                print("[DEBUG] Response status:", response.status_code)
                return []
            
            data = response.json()
            process_time = time.time() - start_time
            print(f"[DEBUG] Process time: {process_time:.2f}s")
            
            # Transform the results
            results = []
            for doc in data.get('docs', []):
                # Get author info
                author_names = doc.get('author_name', [])
                author_keys = doc.get('author_key', [])
                author = {
                    'name': author_names[0] if author_names else "Unknown Author",
                    'key': author_keys[0] if author_keys else None
                }
                
                book = {
                    'open_library_key': doc.get('key', '').split('/')[-1],
                    'title': doc.get('title', 'Unknown Title'),
                    'author': author['name'],
                    'author_key': author['key'],
                    'publication_year': doc.get('first_publish_year'),
                    'cover_image_url': f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-M.jpg" if doc.get('cover_i') else None
                }
                print(f"[DEBUG] Transformed book: {book}")
                results.append(book)
            
            return results
            
    except httpx.RequestError as e:
        print(f"[DEBUG] HTTP Request error: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON Decode error: {str(e)}")
        return []
    except Exception as e:
        print(f"[DEBUG] Unexpected error: {str(e)}")
        return []
