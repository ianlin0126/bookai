import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Mock data for tests
MOCK_TYPEAHEAD_RESULTS = [
    {
        "id": 1,
        "title": "Test Book",
        "author": "Test Author",
        "open_library_key": "OL123456W",
        "cover_image_url": "https://covers.openlibrary.org/b/id/12345-M.jpg"
    },
    {
        "id": 2,
        "title": "Another Test Book",
        "author": "Another Author",
        "open_library_key": "OL789012W",
        "cover_image_url": "https://covers.openlibrary.org/b/id/67890-M.jpg"
    }
]

MOCK_SEARCH_RESULTS = [
    {
        "title": "Test Book",
        "author": "Test Author",
        "open_library_key": "/works/OL123456W",
        "cover_image_url": "https://covers.openlibrary.org/b/id/12345-M.jpg",
        "first_publish_year": 2020
    }
]

@pytest.mark.asyncio
async def test_typeahead_search(client):
    """Test typeahead search with valid query."""
    with patch('app.services.search_service.typeahead_search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_TYPEAHEAD_RESULTS
        response = await client.get("/search/typeahead?query=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(MOCK_TYPEAHEAD_RESULTS)
        assert data[0]["title"] == MOCK_TYPEAHEAD_RESULTS[0]["title"]

@pytest.mark.asyncio
async def test_typeahead_search_empty_query(client):
    """Test typeahead search with empty query."""
    response = await client.get("/search/typeahead?query=")
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_typeahead_search_limit(client):
    """Test typeahead search with custom limit."""
    with patch('app.services.search_service.typeahead_search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_TYPEAHEAD_RESULTS[:1]
        response = await client.get("/search/typeahead?query=test&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

@pytest.mark.asyncio
async def test_search_books(client):
    """Test book search with valid query."""
    with patch('app.services.search_service.search_books', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_SEARCH_RESULTS
        response = await client.get("/search/books?q=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(MOCK_SEARCH_RESULTS)
        assert data[0]["title"] == MOCK_SEARCH_RESULTS[0]["title"]

@pytest.mark.asyncio
async def test_search_books_pagination(client):
    """Test book search with pagination."""
    with patch('app.services.search_service.search_books', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_SEARCH_RESULTS
        response = await client.get("/search/books?q=test&page=2&per_page=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1  # Should respect per_page limit

@pytest.mark.asyncio
async def test_search_books_empty_query(client):
    """Test book search with empty query."""
    response = await client.get("/search/books?q=")
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_search_books_invalid_pagination(client):
    """Test book search with invalid pagination parameters."""
    response = await client.get("/search/books?q=test&page=0")  # Invalid page
    assert response.status_code == 422
    
    response = await client.get("/search/books?q=test&per_page=0")  # Invalid per_page
    assert response.status_code == 422
    
    response = await client.get("/search/books?q=test&per_page=51")  # Exceeds max per_page
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_special_characters(client):
    """Test search with special characters."""
    with patch('app.services.search_service.typeahead_search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = MOCK_TYPEAHEAD_RESULTS
        response = await client.get("/search/typeahead?query=test%20%26%20book")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(MOCK_TYPEAHEAD_RESULTS)

@pytest.mark.asyncio
async def test_search_no_results(client):
    """Test search with no results."""
    with patch('app.services.search_service.typeahead_search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        response = await client.get("/search/typeahead?query=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
