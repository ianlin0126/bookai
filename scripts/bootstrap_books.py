import asyncio
import sys
import os
import json
import time
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Book, Author
from app.services.search_service import search_books
from app.services.book_service import create_book_with_author

async def process_book(db, title: str) -> Optional[Book]:
    """Process a single book: search and add to database."""
    try:
        print(f"Searching for book: {title}")
        
        # Search for book in OpenLibrary
        results = await search_books(db, title, 1, 1)
        
        if not results:
            print(f"No results found for: {title}")
            return None

        book_data = results[0]
        print(f"[DEBUG] Book data from search: {book_data}")
        
        # Check for required fields
        if not book_data.get('open_library_key') or not book_data.get('author_key'):
            print(f"Missing required OpenLibrary keys for: {title}")
            return None

        print(f"Found Open Library key: {book_data['open_library_key']}")
        
        # Create book with author using book service
        try:
            book = await create_book_with_author(
                db=db,
                title=book_data['title'],
                author_name=book_data['author'],
                author_key=book_data['author_key'],
                open_library_key=book_data['open_library_key'],
                cover_image_url=book_data.get('cover_image_url'),
                publication_year=book_data.get('publication_year')
            )
            print(f"Added book: {book.title} by {book.author.name}")
            return book
            
        except ValueError as e:
            print(f"Error creating book: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error processing book {title}: {str(e)}")
        return None

async def bootstrap_books():
    """Add initial set of books to the database."""
    books_to_add = [
        "To Kill a Mockingbird",
        "1984",
        "The Great Gatsby",
        "Pride and Prejudice",
        "The Catcher in the Rye",
        "The Hobbit",
        "Harry Potter and the Sorcerer's Stone",
        "The Lord of the Rings: The Fellowship of the Ring",
        "The Diary of a Young Girl",
        "Moby-Dick",
        "The Hunger Games",
        "The Alchemist",
        "The Da Vinci Code",
        "The Road",
        "Brave New World",
        "The Grapes of Wrath",
        "The Little Prince",
        "One Hundred Years of Solitude",
        "Animal Farm",
        "The Book Thief",
        "Lord of the Flies",
        "The Chronicles of Narnia",
        "Gone with the Wind",
        "The Shining",
        "The Outsiders",
        "The Odyssey",
        "Fahrenheit 451",
        "The Handmaid's Tale"
    ]

    async with SessionLocal() as db:
        start_time = time.time()
        success_count = 0
        fail_count = 0

        for i, title in enumerate(books_to_add, 1):
            print(f"\nProcessing book {i}/{len(books_to_add)}: {title}")
            try:
                if await process_book(db, title):
                    success_count += 1
                    await db.commit()
                else:
                    fail_count += 1
            except Exception as e:
                print(f"Error processing book {title}: {str(e)}")
                await db.rollback()
                fail_count += 1

        total_time = time.time() - start_time
        print("\nBootstrap complete!")
        print(f"Total books processed: {len(books_to_add)}")
        print(f"Successfully added: {success_count}")
        print(f"Failed to add: {fail_count}")
        print(f"\nTotal time: {total_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(bootstrap_books())
