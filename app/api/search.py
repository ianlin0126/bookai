from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.db.database import get_db
from app.services import search_service
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/typeahead")
async def typeahead(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """Get typeahead suggestions for search."""
    return await search_service.get_typeahead_suggestions(db, q)

@router.get("/books", response_class=HTMLResponse)
async def search_books(
    request: Request,
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    """Search for books and return HTML results."""
    try:
        books = await search_service.search_books(db, q)
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "books": books, "query": q}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "books": [],
                "query": q,
                "error": "An error occurred while searching. Please try again."
            }
        )
