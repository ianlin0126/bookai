import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db.models import Book, Visit

@pytest.mark.asyncio
async def test_record_visit(client: TestClient, sample_data):
    book = sample_data["books"][0]
    response = client.post(f"/analytics/visit/{book.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["book_id"] == book.id
    assert data["visit_count"] == 1
    assert "visit_date" in data

    # Verify visit was recorded
    visit = client.app.state.db.query(Visit).filter(Visit.book_id == book.id).first()
    assert visit is not None
    assert visit.visit_count == 1

@pytest.mark.asyncio
async def test_record_visit_nonexistent_book(client: TestClient):
    response = client.post("/analytics/visit/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_popular_books(client: TestClient, sample_data):
    # Create visits for books
    book1, book2 = sample_data["books"]
    today = datetime.now().date()
    
    # Book 1 has 3 visits
    for _ in range(3):
        response = client.post(f"/analytics/visit/{book1.id}")
        assert response.status_code == 200
    
    # Book 2 has 1 visit
    response = client.post(f"/analytics/visit/{book2.id}")
    assert response.status_code == 200
    
    # Get popular books
    response = client.get("/analytics/popular")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["id"] == book1.id  # Most visited book should be first

@pytest.mark.asyncio
async def test_get_popular_books_custom_days(client: TestClient, sample_data):
    # Create some visits
    book = sample_data["books"][0]
    response = client.post(f"/analytics/visit/{book.id}")
    assert response.status_code == 200
    
    # Get popular books with custom days
    response = client.get("/analytics/popular?days=30")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0

@pytest.mark.asyncio
async def test_get_popular_books_custom_limit(client: TestClient, sample_data):
    # Create some visits
    for book in sample_data["books"]:
        response = client.post(f"/analytics/visit/{book.id}")
        assert response.status_code == 200
    
    # Get popular books with custom limit
    limit = 1
    response = client.get(f"/analytics/popular?limit={limit}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == limit

@pytest.mark.asyncio
async def test_get_popular_books_no_visits(client: TestClient):
    response = client.get("/analytics/popular")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
