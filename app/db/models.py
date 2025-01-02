from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=True)
    open_library_key = Column(String, unique=True, nullable=False, index=True)
    cover_image_url = Column(String, nullable=True)
    publication_year = Column(Integer)
    summary = Column(Text, nullable=True)
    questions_and_answers = Column(Text, nullable=True)
    affiliate_links = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("Author", back_populates="books", lazy="joined")
    visits = relationship("Visit", back_populates="book")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._author_name = None

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    open_library_key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
