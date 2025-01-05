import os
from app.core.utils import create_amazon_affiliate_link

def test_affiliate_link():
    """Test generating affiliate link"""
    # Test data
    title = "The Great Gatsby"
    author = "F. Scott Fitzgerald"
    
    # Set test affiliate ID
    os.environ["AMAZON_AFFILIATE_ID"] = "httppinteco01-20"
    
    # Generate affiliate link
    link = create_amazon_affiliate_link(title, author)
    print(f"\nTest case: '{title}' by {author}")
    print(f"Generated affiliate link: {link}")
    
    # Test with special characters
    title2 = "Harry Potter & the Philosopher's Stone"
    author2 = "J.K. Rowling"
    link2 = create_amazon_affiliate_link(title2, author2)
    print(f"\nTest case: '{title2}' by {author2}")
    print(f"Generated affiliate link: {link2}")

if __name__ == "__main__":
    test_affiliate_link()
