from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.db.database import get_db
from app.db import schemas
from app.services import search_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/typeahead", response_model=List[schemas.TypeaheadSuggestion])
async def typeahead(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Get typeahead suggestions for search."""
    return await search_service.get_typeahead_suggestions(db, q)

@router.get("/books")
async def search_books(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search for books and return json response."""
    try:
        return await search_service.search_books(db, q, page, per_page)
    except Exception as e:
        return "An error occurred while searching. Please try again."

@router.get("/books/view")
async def view_search_books(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Search for books and return HTML page."""
    try:
        books = await search_service.search_books(db, q, page, per_page)
        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "query": q,
                "books": books,
                "error": None
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "query": q,
                "books": [],
                "error": str(e)
            }
        )
