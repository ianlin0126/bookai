from typing import Tuple
from thefuzz import fuzz

def clean_json_string(json_str: str) -> str:
    """Clean a string to ensure it's valid JSON."""
    # Remove any text before the first {
    start = json_str.find('{')
    if start == -1:
        return json_str
    json_str = json_str[start:]
    
    # Remove any text after the last }
    end = json_str.rfind('}')
    if end == -1:
        return json_str
    json_str = json_str[:end+1]
    
    return json_str

def validate_book_metadata(digest: dict, book_title: str, book_author: str, threshold: int = 80) -> Tuple[bool, str]:
    """
    Validate that the book metadata in the LLM response matches the database record.
    Uses fuzzy matching to handle slight variations in text.
    
    Args:
        digest: The parsed LLM response
        book_title: The title from the database
        book_author: The author from the database
        threshold: Minimum fuzzy match score (0-100) to consider a match
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract title and author from LLM response
    digest_title = digest.get("title", "")
    digest_author = digest.get("author", "")
    
    # Skip validation if LLM response doesn't include title/author
    if not digest_title and not digest_author:
        return True, ""
        
    # Check title match if present
    if digest_title:
        title_ratio = fuzz.ratio(digest_title.lower(), book_title.lower())
        if title_ratio < threshold:
            return False, f"Title mismatch: LLM response '{digest_title}' doesn't match book title '{book_title}' (match score: {title_ratio})"
    
    # Check author match if present
    if digest_author and book_author:
        author_ratio = fuzz.ratio(digest_author.lower(), book_author.lower())
        if author_ratio < threshold:
            return False, f"Author mismatch: LLM response '{digest_author}' doesn't match book author '{book_author}' (match score: {author_ratio})"
    
    return True, ""

def generate_book_digest_prompt(title: str, author: str) -> str:
    """Generate a prompt for the LLM to create a book digest."""
    return f"""Please provide information about the book "{title}" by {author} in the following JSON format:
{{
    "title": "The exact book title",
    "author": "The author's name",
    "summary": "A concise 2-3 paragraph summary of the book's plot, themes, and significance",
    "questions_and_answers": [
        {{
            "question": "An insightful question about the book",
            "answer": "A detailed answer to the question"
        }},
        // 2-3 more question/answer pairs
    ]
}}"""
