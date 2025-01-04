from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import Field

class AuthorBase(BaseModel):
    name: str
    open_library_key: Optional[str] = None

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BookBase(BaseModel):
    title: str
    open_library_key: Optional[str] = None
    cover_image_url: Optional[str] = None
    summary: Optional[str] = None
    questions_and_answers: Optional[str] = None
    affiliate_links: Optional[str] = None

class BookCreate(BookBase):
    author_id: Optional[int] = None

class Book(BookBase):
    id: int
    author_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: Optional[str] = None  # Use the property from the model

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BookResponse(Book):
    """Response model for book endpoints that includes all fields."""
    pass

class BookQAResponse(BaseModel):
    """Response model for book Q&A."""
    questions_and_answers: Union[List[Dict[str, str]], str, None] = Field(default=None, description="List of Q&A pairs or raw Q&A text")

class BookSearchResult(BaseModel):
    title: str
    author: Optional[str] = None
    open_library_key: str
    cover_image_url: Optional[str] = None
    publication_year: Optional[int] = None

    class Config:
        from_attributes = True

class TypeaheadSuggestion(BaseModel):
    """Schema for typeahead suggestions."""
    id: int
    title: str
    author: Optional[str] = None
    cover_image_url: Optional[str] = None

class VisitBase(BaseModel):
    book_id: int
    visit_date: date
    visit_count: int = 1

class VisitCreate(VisitBase):
    pass

class Visit(VisitBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
