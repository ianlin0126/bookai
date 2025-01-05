from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(app_dir))

from app.db.models import Visit, Book
from app.core.config import get_settings

settings = get_settings()

def show_all_visits():
    # Create engine and session
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query all visits with book information
        query = select(Visit, Book).join(Book)
        results = session.execute(query).all()

        if not results:
            print("No visits found in the database.")
            return

        print("\nAll visits in the database:")
        print("-" * 80)
        print(f"{'Book ID':<8} {'Book Title':<30} {'Visit Date':<12} {'Visit Count':<11} {'Created At':<20}")
        print("-" * 80)

        for visit, book in results:
            print(f"{visit.book_id:<8} {book.title[:28]:<30} {visit.visit_date} {visit.visit_count:<11} {visit.created_at}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    show_all_visits()
