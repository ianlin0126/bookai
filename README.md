# BookAI - AI-Powered Book Discovery Platform

## Project Overview

BookAI is a modern web application that helps users discover and evaluate books through AI-powered insights. The platform combines traditional book search with AI capabilities to provide summaries, insights, and recommendations, while monetizing through Amazon affiliate links.

## Technical Architecture

### Backend Architecture

#### Core Components
- **Framework**: FastAPI (async)
- **Database**: SQLite with SQLAlchemy ORM (async)
- **AI Integration**: 
  - Google PaLM API for content generation
  - OpenAI for recommendations
- **Template Engine**: Jinja2
- **Migration Tool**: Alembic

#### API Structure
```
/api/
├── books/
│   ├── GET /{book_id}         # Get book details
│   ├── GET /popular           # Get popular books
│   └── POST /                 # Create new book
├── search/
│   ├── GET /                  # Search books
│   └── GET /typeahead        # Get search suggestions
├── analytics/
│   ├── POST /track           # Track user interactions
│   └── GET /popular          # Get trending books
└── llm/
    ├── POST /summarize       # Generate book summary
    └── POST /insights        # Generate book insights
```

### Frontend Architecture

#### Core Technologies
- **JavaScript**: Vanilla ES6+ (no framework)
- **CSS**: Tailwind CSS
- **HTML**: Jinja2 templates
- **Icons**: Heroicons

#### Template Structure
```
templates/
├── base.html          # Base template with common elements
├── index.html         # Homepage with search and popular books
└── book_detail.html   # Book details page
```

### Database Schema

```sql
Book
  - id: Integer (Primary Key)
  - title: String
  - author: String
  - open_library_key: String (Optional)
  - cover_image_url: String (Optional)
  - summary: Text (Optional)
  - questions_and_answers: Text (Optional)
  - affiliate_links: JSON
  - created_at: DateTime
  - updated_at: DateTime

Analytics
  - id: Integer (Primary Key)
  - book_id: Integer (Foreign Key)
  - event_type: String
  - timestamp: DateTime
  - metadata: JSON

SearchHistory
  - id: Integer (Primary Key)
  - query: String
  - timestamp: DateTime
  - results_count: Integer
```

## Implementation Details

### 1. Search Functionality

#### Frontend Implementation
- Real-time search with debouncing (300ms)
- Typeahead suggestions
- Mobile-responsive search UI
- Search history tracking

```javascript
// Debounced search implementation
const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
};

// Search input handler
const handleSearchInput = debounce(async (event) => {
    const query = event.target.value.trim();
    if (query.length < 2) return;
    
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const results = await response.json();
    updateSearchResults(results);
}, 300);
```

### 2. Book Detail Page

#### Components
- Dynamic content loading
- AI-generated insights
- Amazon affiliate integration
- Mobile-responsive layout

#### Key Features
- Back navigation to previous page
- Loading states with skeleton UI
- Error handling
- Analytics tracking

```javascript
async function showBookDetails(bookId) {
    try {
        // Show loading state
        showLoadingState();
        
        // Fetch book data
        const response = await fetch(`/api/books/${bookId}`);
        const book = await response.json();
        
        // Update UI
        updateBookUI(book);
        
        // Track visit
        await recordVisit(bookId);
    } catch (error) {
        showError(error);
    }
}
```

### 3. AI Integration

#### Summary Generation
- Uses Google PaLM API
- Caches results in database
- Handles rate limiting
- Error recovery

#### Insights Generation
- Uses OpenAI API
- Generates Q&A format
- Contextual understanding
- Content moderation

### 4. Performance Optimizations

#### Frontend
- Lazy loading of images
- Debounced search
- Skeleton loading states
- Client-side caching

#### Backend
- Async database operations
- Connection pooling
- Query optimization
- Response caching

### 5. Security Measures

#### API Security
- CORS configuration
- Rate limiting
- Input validation
- Error handling

#### Data Protection
- SQL injection prevention
- XSS protection
- Secure headers
- Environment variables

## Setup Instructions

1. Clone and Environment Setup:
```bash
git clone <repository-url>
cd bookai
python -m venv myenv
source myenv/bin/activate  # Windows: myenv\Scripts\activate
```

2. Install Dependencies:
```bash
pip install -r requirements.txt
```

3. Environment Configuration:
Create `.env` file:
```
DATABASE_URL=sqlite:///bookai.db
GOOGLE_API_KEY=your_palm_api_key
OPENAI_API_KEY=your_openai_api_key
```

4. Database Setup:
```bash
alembic upgrade head
```

5. Run Development Server:
```bash
uvicorn app.main:app --reload
```

## Development Workflow

### Adding New Features
1. Create database migrations
2. Implement API endpoints
3. Add service layer logic
4. Create/update templates
5. Implement frontend JS
6. Add tests

### Testing
```bash
# Run tests
pytest

# With coverage
pytest --cov

# Specific test file
pytest tests/test_books.py
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment Considerations

### Environment Variables
- `DATABASE_URL`
- `GOOGLE_API_KEY`
- `OPENAI_API_KEY`
- `ENVIRONMENT` (development/production)

### Production Setup
- Use production ASGI server (e.g., Gunicorn)
- Configure CORS appropriately
- Set up monitoring
- Configure logging

### Scaling Strategies
- Database indexing
- Caching layer
- Load balancing
- CDN for static assets

## Contributing

1. Fork repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## License

[Specify License]