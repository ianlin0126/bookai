import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.services import book_service
from app.core.utils import create_amazon_affiliate_link

async def test_affiliate_link():
    """Test generating affiliate link for book ID 1"""
    async with async_session() as db:
        try:
            # Get book with ID 1
            book = await book_service.get_book(db, 1)
            print(f"\nFound book: {book.title} by {book.author_str}")
            
            # Generate affiliate link
            link = create_amazon_affiliate_link(book.title, book.author_str)
            print(f"\nGenerated affiliate link: {link}")
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Set test affiliate ID
    os.environ["AMAZON_AFFILIATE_ID"] = "test-20"
    
    # Run the test
    asyncio.run(test_affiliate_link())
