import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Book, Author

async def cleanup_db():
    """Delete all records from the database."""
    async with SessionLocal() as db:
        try:
            # Delete all books first (due to foreign key constraint)
            await db.execute('DELETE FROM books')
            print("Deleted all books")
            
            # Delete all authors
            await db.execute('DELETE FROM authors')
            print("Deleted all authors")
            
            await db.commit()
            print("\nDatabase cleanup complete!")
            
        except Exception as e:
            print(f"Error cleaning database: {str(e)}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(cleanup_db())
