import pytest
from sqlalchemy.orm import Session
from app.services import book_service
from app.db.models import Book, Author, Visit
from app.core.exceptions import BookNotFoundError
from datetime import datetime

@pytest.mark.asyncio
async def test_get_book(test_db: Session, sample_data):
    book = sample_data["books"][0]
    result = await book_service.get_book(test_db, book.id)
    assert result.title == book.title
    assert result.author.name == sample_data["author"].name

@pytest.mark.asyncio
async def test_get_nonexistent_book(test_db: Session):
    with pytest.raises(BookNotFoundError):
        await book_service.get_book(test_db, 999)

@pytest.mark.asyncio
async def test_get_book_summary(test_db: Session, sample_data):
    book = sample_data["books"][0]
    summary = await book_service.get_book_summary(test_db, book.id)
    assert summary == "This is a test summary for book 1"

@pytest.mark.asyncio
async def test_get_popular_books(test_db: Session, sample_data):
    # Create visits for the test books
    book1, book2 = sample_data["books"]
    today = datetime.now().date()
    
    visit1 = Visit(book_id=book1.id, visit_date=today, visit_count=3)
    visit2 = Visit(book_id=book2.id, visit_date=today, visit_count=1)
    
    test_db.add(visit1)
    test_db.add(visit2)
    test_db.commit()

    # Get popular books
    popular_books = await book_service.get_popular_books(test_db, limit=5)
    assert len(popular_books) == 2
    assert popular_books[0].id == book1.id  # Most visited book should be first
