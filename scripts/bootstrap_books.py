from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.services import search_service, book_service
from app.core.utils import clean_json_string
from thefuzz import fuzz
import asyncio
import time

async def bootstrap_books():
    """Bootstrap the database with initial books."""
    book_titles = [
        "To Kill a Mockingbird",
        "1984",
        "The Great Gatsby",
        "The Catcher in the Rye",
        "Pride and Prejudice",
        "The Hobbit",
        "Fahrenheit 451",
        "The Lord of the Rings",        
        "Moby-Dick",
        "War and Peace",
        "Crime and Punishment",
        "Brave New World",
        "The Odyssey",
        "The Brothers Karamazov",
        "Catch-22",
        "Jane Eyre",
        "Wuthering Heights",
        "The Grapes of Wrath",
        "One Hundred Years of Solitude",
        "The Picture of Dorian Gray",
        "The Diary of a Young Girl",
        "The Alchemist",
        "The Kite Runner",
        "Sapiens: A Brief History of Humankind",
        "The Book Thief",
        "The Hunger Games",
        "The Fault in Our Stars",
        "The Shining",
        "The Chronicles of Narnia",
        "The Secret Garden",
        "Little Women",
        "The Help",
        "The Godfather",
        "The Outsiders",
        "The Lord of the Flies",
        "The Silmarillion",
        "Beloved",
        "Slaughterhouse-Five",
        "Gone with the Wind",
        "A Game of Thrones",
        "The Handmaid's Tale",
        "The Catcher in the Rye",
        "The Secret Life of Bees",
        "The Night Circus",
        "The Road",
        "The Hobbit",
        "The Black Prism",
        "The Dark Tower",
        "The Outsider",
        "The Martian",
        "Dune",
        "Ender's Game",
        "The Wind-Up Bird Chronicle",
        "The Road",
        "The Girl on the Train",
        "All the Light We Cannot See",
        "The Hunger Games",
        "The Girl with the Dragon Tattoo",
        "The Time Traveler's Wife",
        "The Shadow of the Wind",
        "Shogun",
        "The Water Dancer",
        "The Goldfinch",
        "The Underground Railroad",
        "The Night Manager",
        "The Girl Who Lived",
        "Sharp Objects",
        "Big Little Lies",
        "Where the Crawdads Sing",
        "The Silent Patient",
        "Educated",
        "Circe",
        "The Nightingale",
        "A Little Life",
        "The Seven Husbands of Evelyn Hugo",
        "Before We Were Strangers",
        "Anxious People",
        "The 5th Wave",
        "The One and Only Ivan",
        "The Rosie Project",
        "Normal People",
        "Eleanor Oliphant Is Completely Fine",
        "The Lovely Bones",
        "The Giver",
        "The Phantom of the Opera",
        "The Hunger Games",
        "The Maze Runner",
        "Harry Potter and the Chamber of Secrets",
        "Harry Potter and the Prisoner of Azkaban",
        "Harry Potter and the Goblet of Fire",
        "Harry Potter and the Order of the Phoenix",
        "Harry Potter and the Half-Blood Prince",
        "Harry Potter and the Deathly Hallows",
        "The Giver",
        "The Hitchhiker's Guide to the Galaxy",
        "Percy Jackson and the Olympians: The Lightning Thief",
        "The Percy Jackson Series",
        "The House on Mango Street",
        "The Shadow of the Wind",
        "Room",
        "The Night Circus",
        "The Ocean at the End of the Lane",
        "Good Omens",
        "American Gods",
        "The Song of Achilles",
        "The Lovely Bones",
        "The Great Alone",
        "The Girl in the Spider's Web",
        "The Girl Who Played with Fire",
        "The Girl Who Kicked the Hornet's Nest",
        "Dracula",
        "Frankenstein",
        "The War of the Worlds",
        "The Call of the Wild",
        "The Old Man and the Sea",
        "A Tale of Two Cities",
        "The Three Musketeers",
        "Les Misérables",
        "Don Quixote",
        "Brave New World",
        "The Grapes of Wrath",
        "The Kite Runner",
        "The Book Thief",
        "The Handmaid's Tale",
        "Animal Farm",
        "The Night Circus",
        "Cloud Atlas",
        "The Goldfinch",
        "The Secret Garden",
        "The Outsiders",
        "The Picture of Dorian Gray",
        "The Girl on the Train",
        "The Help",
        "The Sun Down Motel",
        "The Little Prince",
        "The Secret History",
        "The Night Watch",
        "The Ocean at the End of the Lane",
        "The Alice Network",
        "Atonement",
        "The Silent Patient",
        "The Wife Between Us",
        "The Couple Next Door",
        "The Woman in the Window",
        "The Death of Mrs. Westaway",
        "Before I Go to Sleep",
        "The 5th Wave",
        "The Girl with All the Gifts",
        "The Murder of Roger Ackroyd",
        "The Girl on the Train",
        "Gone Girl",
        "Big Little Lies",
        "The Silent Corner",
        "The Woman in Cabin 10",
        "The Girl Who Lived",
        "Sharp Objects",
        "The Secret Life of Bees",
        "The Help",
        "The Secret Garden",
        "The Nightingale",
        "Circe",
        "The House in the Cerulean Sea",
        "A Little Life",
        "The Seven Husbands of Evelyn Hugo",
        "The Goldfinch",
        "The Night Circus"
    ]

    async with SessionLocal() as db:
        for title in book_titles:
            try:
                # Step 1: Search Open Library
                print(f"\nSearching for book: {title}")
                search_results = await search_service.search_books(db, title, page=1, per_page=1)
                
                if not search_results:
                    print(f"No results found for: {title}")
                    continue
                
                book_data = search_results[0]
                open_library_key = book_data['open_library_key']
                found_title = book_data['title']
                
                # Check if the found title matches the input title using fuzzy matching
                similarity_ratio = fuzz.ratio(title.lower(), found_title.lower())
                if similarity_ratio < 80:  # Threshold of 80% similarity
                    print(f"Skipping book: Found title '{found_title}' doesn't match input title '{title}' (similarity: {similarity_ratio}%)")
                    continue
                
                print(f"Found matching book: {found_title} (similarity: {similarity_ratio}%)")
                
                # Step 2: Check if book exists
                try:
                    existing_book = await book_service.get_book_by_open_library_key(db, open_library_key)
                    if existing_book:
                        print(f"Book already exists: {title}")
                        continue
                except ValueError:
                    pass  # Book doesn't exist, continue with creation
                
                # Step 3: Create book using Open Library data
                book = await book_service.post_book_by_open_library_key(db, open_library_key)
                print(f"Added book: {title} (OpenLibrary key: {open_library_key})")
                
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing book {title}: {str(e)}")
                continue

if __name__ == "__main__":
    asyncio.run(bootstrap_books())
