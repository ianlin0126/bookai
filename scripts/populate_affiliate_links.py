#!/usr/bin/env python3

import sys
import os
import json
import sqlite3

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.core.utils import create_amazon_affiliate_link
from app.core.config import settings

def populate_affiliate_links():
    """Populate affiliate_links for all books that don't have them."""
    # Extract SQLite database path from URL
    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all books without affiliate links
        cursor.execute("""
            SELECT b.id, b.title, a.name as author_name 
            FROM books b 
            LEFT JOIN authors a ON b.author_id = a.id 
            WHERE b.affiliate_links IS NULL
        """)
        books = cursor.fetchall()
        
        print("Found {} books without affiliate links".format(len(books)))
        
        # Update each book
        for book_id, title, author_name in books:
            affiliate_links = {
                "amazon": create_amazon_affiliate_link(
                    book_title=title,
                    author=author_name
                )
            }
            
            cursor.execute(
                "UPDATE books SET affiliate_links = ? WHERE id = ?",
                (json.dumps(affiliate_links), book_id)
            )
            print("Updated affiliate links for '{}' by {}".format(
                title, 
                author_name or 'Unknown'
            ))
        
        # Commit all changes
        conn.commit()
        print("All affiliate links have been updated!")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_affiliate_links()
