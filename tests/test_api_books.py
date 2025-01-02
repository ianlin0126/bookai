import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from datetime import datetime

# Mock data for tests
MOCK_BOOK = {
    "id": 1,
    "title": "Test Book",
    "author_name": "Test Author",
    "open_library_key": "OL123456W",
    "cover_image_url": "https://covers.openlibrary.org/b/id/12345-M.jpg",
    "summary": "Test summary",
    "questions_and_answers": "Test Q&A",
    "affiliate_links": None,
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

@pytest.mark.asyncio
async def test_create_book(client):
    """Test creating a new book."""
    book_data = {
        "title": "New Book",
        "author_name": "New Author",
        "open_library_key": "OL789012W"
    }
    
    with patch('app.services.book_service.create_book', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {**MOCK_BOOK, **book_data}
        response = await client.post("/books/", json=book_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author_name"] == book_data["author_name"]

@pytest.mark.asyncio
async def test_get_book(client):
    """Test getting a book by ID."""
    with patch('app.services.book_service.get_book', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_BOOK
        response = await client.get(f"/books/{MOCK_BOOK['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == MOCK_BOOK["title"]
        assert data["author_name"] == MOCK_BOOK["author_name"]

@pytest.mark.asyncio
async def test_get_nonexistent_book(client):
    """Test getting a book that doesn't exist."""
    with patch('app.services.book_service.get_book', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Book not found")
        response = await client.get("/books/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_book_by_key(client):
    """Test getting a book by Open Library key."""
    with patch('app.services.book_service.get_book_by_open_library_key', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_BOOK
        response = await client.get(f"/books/by_key/{MOCK_BOOK['open_library_key']}")
        assert response.status_code == 200
        data = response.json()
        assert data["open_library_key"] == MOCK_BOOK["open_library_key"]

@pytest.mark.asyncio
async def test_get_book_by_key_with_creation(client):
    """Test getting/creating a book by Open Library key."""
    book_data = {
        "title": "New Book",
        "author": "New Author",
        "cover_image_url": "https://example.com/cover.jpg"
    }
    with patch('app.services.book_service.get_book_by_open_library_key', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {**MOCK_BOOK, **book_data}
        response = await client.get(
            f"/books/by_key/OL999999W",
            params=book_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == book_data["title"]

@pytest.mark.asyncio
async def test_get_book_summary(client):
    """Test getting a book's summary."""
    with patch('app.services.book_service.get_book_summary', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"summary": MOCK_BOOK["summary"]}
        response = await client.get(f"/books/{MOCK_BOOK['id']}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == MOCK_BOOK["summary"]

@pytest.mark.asyncio
async def test_get_book_qa(client):
    """Test getting a book's Q&A."""
    with patch('app.services.book_service.get_book_questions_and_answers', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"questions_and_answers": MOCK_BOOK["questions_and_answers"]}
        response = await client.get(f"/books/{MOCK_BOOK['id']}/qa")
        assert response.status_code == 200
        data = response.json()
        assert data["questions_and_answers"] == MOCK_BOOK["questions_and_answers"]

@pytest.mark.asyncio
async def test_get_popular_books(client):
    """Test getting popular books."""
    mock_books = [MOCK_BOOK, {**MOCK_BOOK, "id": 2, "title": "Popular Book 2"}]
    with patch('app.services.book_service.get_popular_books', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_books
        response = await client.get("/books/popular")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(mock_books)
        assert data[0]["title"] == mock_books[0]["title"]

# Error cases
@pytest.mark.asyncio
async def test_create_book_invalid_data(client):
    """Test creating a book with invalid data."""
    response = await client.post("/books/", json={})
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_get_book_by_key_not_found(client):
    """Test getting a non-existent book by key."""
    with patch('app.services.book_service.get_book_by_open_library_key', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Book not found")
        response = await client.get("/books/by_key/INVALID_KEY")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_book_summary_not_found(client):
    """Test getting summary for non-existent book."""
    with patch('app.services.book_service.get_book_summary', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Book not found")
        response = await client.get("/books/999/summary")
        assert response.status_code == 404
