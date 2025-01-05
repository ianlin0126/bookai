#!/usr/bin/env python3

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from sqlalchemy import select
from app.db.database import SessionLocal
from app.db.models import Book
from app.core.utils import create_amazon_affiliate_link

async def populate_affiliate_links():
    """Populate affiliate_links field for all books that don't have it."""
    async with SessionLocal() as db:
        try:
            # Get all books that don't have affiliate links
            query = select(Book).where(
                (Book.affiliate_links.is_(None)) | 
                (Book.affiliate_links == '{}') |
                (Book.affiliate_links == '')
            )
            result = await db.execute(query)
            books = result.scalars().all()
            
            print(f"\nFound {len(books)} books without affiliate links")
            
            # Update each book
            for book in books:
                try:
                    # Generate Amazon affiliate link
                    amazon_link = create_amazon_affiliate_link(book.title, book.author_str)
                    
                    book.affiliate_links = amazon_link
                    
                    print(f"\nUpdated book ID:'{book.id}' {book.title}")
                    print(f"Amazon link: {amazon_link}")
                    
                except Exception as e:
                    print(f"Error updating book {book.id}: {str(e)}")
                    continue
            
            # Commit all changes
            await db.commit()
            print("\nFinished updating affiliate links!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            await db.rollback()
            return

if __name__ == "__main__":
    # Set affiliate ID if not in environment
    if "AMAZON_AFFILIATE_ID" not in os.environ:
        os.environ["AMAZON_AFFILIATE_ID"] = "httppinteco01-20"
    
    # Run the script
    asyncio.run(populate_affiliate_links())
