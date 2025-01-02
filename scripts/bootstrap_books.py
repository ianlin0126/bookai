import asyncio
import sys
import os
import time
from typing import Optional, Dict, Any
from sqlalchemy import select, or_

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import app modules
from app.db.database import SessionLocal
from app.services import search_service, book_service
from app.db.models import Author
from popular_books import POPULAR_BOOKS

async def process_book(db, title: str) -> Optional[Dict[str, Any]]:
    """Process a single book."""
    try:
        print(f"\nSearching for book: {title}")
        # Search Open Library API
        results = await search_service.search_books(db, title, 1, 1)
        
        if not results:
            print(f"No results found for: {title}")
            return None
        
        book_data = results[0]
        print(f"[DEBUG] Book data from search: {book_data}")
        
        open_library_key = book_data.get("open_library_key")
        if not open_library_key:
            print(f"No Open Library key found for: {title}")
            return None
        
        print(f"Found Open Library key: {open_library_key}")
        
        # Add book to database
        try:
            # Create author with Open Library key if available
            author_name = book_data.get("author")
            author_key = book_data.get("author_key")
            
            # Find or create author
            result = await db.execute(
                select(Author).where(
                    or_(
                        Author.open_library_key == author_key,
                        Author.name == author_name
                    )
                )
            )
            author = result.scalar_one_or_none()
            
            if not author:
                print(f"[DEBUG] Creating new author: {author_name}")
                author = Author(
                    name=author_name,
                    open_library_key=author_key
                )
                db.add(author)
                await db.commit()
                await db.refresh(author)
            
            # Create book with author
            book = await book_service.create_book_with_author(
                db,
                title=book_data.get("title"),
                author_name=author_name,
                open_library_key=open_library_key,
                cover_image_url=book_data.get("cover_image_url"),
                publication_year=book_data.get("publication_year")
            )
            print(f"Added book: {book.title} by {book.author.name if book.author else 'Unknown Author'}")
            return book_data
        except Exception as e:
            print(f"Error adding book {title}: {str(e)}")
            return None
        
    except Exception as e:
        print(f"Error processing {title}: {str(e)}")
        return None

async def bootstrap_books():
    """Add popular books to the database."""
    async with SessionLocal() as db:
        total_books = len(POPULAR_BOOKS)
        successful = 0
        failed = 0
        
        for i, title in enumerate(POPULAR_BOOKS, 1):
            print(f"\nProcessing book {i}/{total_books}: {title}")
            
            result = await process_book(db, title)
            if result:
                successful += 1
            else:
                failed += 1
            
            # Add a small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        print(f"\nBootstrap complete!")
        print(f"Total books processed: {total_books}")
        print(f"Successfully added: {successful}")
        print(f"Failed to add: {failed}")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(bootstrap_books())
    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f} seconds")
