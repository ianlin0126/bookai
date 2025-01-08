from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import asyncio
from app.services.image_cache_service import image_cache

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    open_library_key = Column(String, nullable=False, unique=True, index=True)
    _image_url = Column("cover_image_url", String, nullable=True)  # Actual database column
    publication_year = Column(Integer)
    summary = Column(Text, nullable=True)
    questions_and_answers = Column(Text, nullable=True)
    affiliate_links = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("Author", back_populates="books", lazy="joined")
    visits = relationship("Visit", back_populates="book")

    def __init__(self, **kwargs):
        # Handle the cover_image_url -> _image_url mapping
        if 'cover_image_url' in kwargs:
            kwargs['_image_url'] = kwargs.pop('cover_image_url')
        super().__init__(**kwargs)
        self._author = None

    @property
    def cover_image_url(self) -> str:
        """Get the cover image URL."""
        return self._image_url

    @cover_image_url.setter
    def cover_image_url(self, value: str):
        """Set the cover image URL."""
        self._image_url = value

    @property
    def author_str(self) -> str:
        """Get the author's name."""
        return self.author.name if self.author else None

    @property
    def cached_cover_image_url(self) -> str:
        """Get the cover image URL, using cached version if available."""
        if self.cover_image_url:
            # Start background task to cache the image and get URL
            event_loop = asyncio.get_event_loop()
            return event_loop.run_until_complete(
                image_cache.get_cached_url(self.cover_image_url)
            )
        return self.cover_image_url

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    open_library_key = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    books = relationship("Book", back_populates="author")

class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    visit_date = Column(Date, index=True)
    visit_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    book = relationship("Book", back_populates="visits")
