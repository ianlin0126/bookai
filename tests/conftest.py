import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.db.models import Book, Author, Visit

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session for the test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

@pytest.fixture
def sample_data(test_db):
    # Create sample author
    author = Author(
        name="Test Author",
        open_library_key="OL123456A"
    )
    test_db.add(author)
    test_db.commit()

    # Create sample books
    books = [
        Book(
            title="Test Book 1",
            open_library_key="OL123456B",
            author_id=author.id,
            cover_image_url="http://example.com/cover1.jpg",
            ai_summary="This is a test summary for book 1",
            ai_qa='[{"question": "Test Q1?", "answer": "Test A1"}]',
            affiliate_links='{"amazon": "http://amazon.com/book1"}'
        ),
        Book(
            title="Test Book 2",
            open_library_key="OL789012B",
            author_id=author.id,
            cover_image_url="http://example.com/cover2.jpg",
            ai_summary="This is a test summary for book 2",
            ai_qa='[{"question": "Test Q2?", "answer": "Test A2"}]',
            affiliate_links='{"amazon": "http://amazon.com/book2"}'
        )
    ]
    
    for book in books:
        test_db.add(book)
    test_db.commit()

    return {"author": author, "books": books}
