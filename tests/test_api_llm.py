import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.services import llm_service
from datetime import datetime

@pytest.fixture
def mock_llm_responses():
    return {
        "gemini": "This is a test response from Gemini",
        "chatgpt": "This is a test response from ChatGPT"
    }

@pytest.mark.asyncio
async def test_query_llm_gemini(client, mock_llm_responses):
    with patch('app.services.llm_service.query_gemini', new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = mock_llm_responses["gemini"]
        response = await client.post(
            "/llm/query?provider=gemini",
            json={"prompt": "Test prompt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "gemini" in data
        assert data["gemini"] == mock_llm_responses["gemini"]

@pytest.mark.asyncio
async def test_query_llm_chatgpt(client, mock_llm_responses):
    with patch('app.services.llm_service.query_chatgpt', new_callable=AsyncMock) as mock_chatgpt:
        mock_chatgpt.return_value = mock_llm_responses["chatgpt"]
        response = await client.post(
            "/llm/query?provider=chatgpt",
            json={"prompt": "Test prompt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "chatgpt" in data
        assert data["chatgpt"] == mock_llm_responses["chatgpt"]

@pytest.mark.asyncio
async def test_query_llm_both(client, mock_llm_responses):
    with patch('app.services.llm_service.query_gemini', new_callable=AsyncMock) as mock_gemini, \
         patch('app.services.llm_service.query_chatgpt', new_callable=AsyncMock) as mock_chatgpt:
        mock_gemini.return_value = mock_llm_responses["gemini"]
        mock_chatgpt.return_value = mock_llm_responses["chatgpt"]
        response = await client.post(
            "/llm/query?provider=both",
            json={"prompt": "Test prompt"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "gemini" in data and "chatgpt" in data
        assert data["gemini"] == mock_llm_responses["gemini"]
        assert data["chatgpt"] == mock_llm_responses["chatgpt"]

@pytest.mark.asyncio
async def test_query_llm_missing_prompt(client):
    response = await client.post("/llm/query?provider=gemini", json={})
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_refresh_book_digest_gemini(client, sample_data, mock_llm_responses):
    book = sample_data["books"][0]
    with patch('app.services.book_service.refresh_book_digest', new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = book
        response = await client.post(f"/llm/books/{book.id}/refresh?provider=gemini")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book.id
        assert data["title"] == book.title
        assert data["author"]["name"] == sample_data["author"].name

@pytest.mark.asyncio
async def test_refresh_book_digest_chatgpt(client, sample_data, mock_llm_responses):
    book = sample_data["books"][0]
    with patch('app.services.book_service.refresh_book_digest', new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = book
        response = await client.post(f"/llm/books/{book.id}/refresh?provider=chatgpt")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book.id
        assert data["title"] == book.title
        assert data["author"]["name"] == sample_data["author"].name

@pytest.mark.asyncio
async def test_refresh_nonexistent_book(client):
    with patch('app.services.book_service.refresh_book_digest', new_callable=AsyncMock) as mock_refresh:
        mock_refresh.side_effect = Exception("Book not found")
        response = await client.post("/llm/books/999/refresh?provider=gemini")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
