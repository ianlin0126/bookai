import asyncio
import sys
import os
from datetime import datetime, date
from sqlalchemy import select

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Book, Visit

async def add_test_visits():
    """Add test visit data for books."""
    async with SessionLocal() as db:
        # Get all books
        result = await db.execute(select(Book))
        books = result.scalars().all()
        
        if not books:
            print("No books found in database")
            return
        
        today = date.today()
        
        # Add visits with different counts to create a ranking
        for i, book in enumerate(books):
            visit = Visit(
                book_id=book.id,
                visit_date=today,
                visit_count=10 - i  # First book gets most visits, decreasing thereafter
            )
            db.add(visit)
            print(f"Added {10-i} visits for book: {book.title}")
        
        await db.commit()
        print("\nTest visit data added successfully!")

if __name__ == "__main__":
    asyncio.run(add_test_visits())
