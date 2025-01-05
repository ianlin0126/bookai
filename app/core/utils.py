from typing import Tuple, Optional
import json
from thefuzz import fuzz
from urllib.parse import quote
import os

def clean_json_string(json_str: str) -> str:
    """Clean a string to ensure it's valid JSON."""
    # Remove any text before the first {
    start_idx = json_str.find('{')
    if start_idx == -1:
        raise ValueError("No JSON object found in string")
    json_str = json_str[start_idx:]
    
    # Remove any text after the last }
    end_idx = json_str.rfind('}')
    if end_idx == -1:
        raise ValueError("No closing brace found in JSON string")
    json_str = json_str[:end_idx + 1]
    
    # Replace invalid control characters
    json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')
    
    # Fix common JSON formatting issues
    json_str = json_str.replace('\n', ' ')
    json_str = json_str.replace('\r', ' ')
    json_str = json_str.replace('\t', ' ')
    json_str = json_str.replace('\\n', ' ')
    json_str = json_str.replace('\\r', ' ')
    json_str = json_str.replace('\\t', ' ')
    
    # Remove multiple spaces
    json_str = ' '.join(json_str.split())
    
    try:
        # Try to parse and re-stringify to ensure valid JSON
        parsed = json.loads(json_str)
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"Failed to clean JSON: {str(e)}, Original string: {json_str}")
        raise

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

def create_amazon_affiliate_link(book_title: str, author: Optional[str] = None) -> str:
    """
    Create an Amazon affiliate link for a book search.
    
    Args:
        book_title: The title of the book
        author: Optional author name
        
    Returns:
        str: Amazon affiliate link with search query and affiliate tag
        
    Example:
        >>> create_amazon_affiliate_link("The Great Gatsby", "F. Scott Fitzgerald")
        'https://www.amazon.com/s?k=The+Great+Gatsby+F.+Scott+Fitzgerald&tag=your-tag-20'
    """
    # Get affiliate ID from environment
    affiliate_id = os.getenv('AMAZON_AFFILIATE_ID', 'httppinteco01-20')
    
    # Clean and encode search terms
    search_terms = [book_title]
    if author:
        search_terms.append(author)
    
    # Join with space and encode for URL
    search_query = quote(' '.join(search_terms))
    
    # Create affiliate link
    return f"https://www.amazon.com/s?k={search_query}&tag={affiliate_id}"
