# BookDigest.ai

A modern web application for discovering, analyzing, and managing book recommendations with AI-powered insights.

## Project Overview

BookDigest.ai is a FastAPI-based web application that combines traditional book management with AI capabilities to provide intelligent book recommendations and insights. The application features a responsive frontend built with HTML, JavaScript, and Tailwind CSS.

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI
- **Database**: SQLAlchemy with SQLite
- **AI Integration**: Google PaLM API and OpenAI
- **Template Engine**: Jinja2
- **Migration Tool**: Alembic

### Frontend Stack
- **Styling**: Tailwind CSS
- **JavaScript**: Vanilla JS with modern ES6+ features
- **Templates**: HTML with Jinja2 templating

### Directory Structure
```
bookai/
├── alembic/              # Database migrations
├── app/                  # Main application code
│   ├── api/             # API endpoints
│   ├── db/              # Database models and config
│   ├── templates/       # Jinja2 HTML templates
│   └── main.py         # FastAPI application entry
├── assets/              # Static assets (images)
├── static/              # Static files (JS, CSS)
│   ├── js/             # JavaScript files
│   └── css/            # CSS files
├── scripts/             # Utility scripts
└── tests/              # Test files
```

## Key Features

### 1. Book Management
- Book details page with cover image, title, author, and description
- Amazon affiliate integration for book purchases
- Responsive design for mobile and desktop

### 2. Search and Discovery
- Full-text search functionality
- AI-powered book recommendations
- Search result filtering and sorting

### 3. User Interface
- Modern, responsive design using Tailwind CSS
- Dynamic content loading with JavaScript
- Loading states and animations for better UX

### 4. API Endpoints
- `/api/books`: Book management endpoints
- `/api/search`: Search functionality
- `/api/analytics`: Analytics and insights
- `/api/llm`: AI integration endpoints

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd bookai
```

2. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with:
```
DATABASE_URL=sqlite:///bookai.db
GOOGLE_API_KEY=your_palm_api_key
OPENAI_API_KEY=your_openai_api_key
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Development Guidelines

### Database Changes
- Use Alembic for all database migrations
- Create new migrations: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`

### Frontend Development
- JavaScript files are in `static/js/`
- Main application logic is in `main.js`
- Use Tailwind CSS classes for styling
- Follow BEM naming convention for custom CSS

### Testing
- Write tests in the `tests/` directory
- Run tests with: `pytest`
- Maintain test coverage with: `pytest --cov`

### API Development
- Follow RESTful principles
- Document all endpoints with FastAPI's automatic documentation
- Include type hints and docstrings
- Handle errors consistently using FastAPI's exception handlers

## Key Components

### Book Detail Page (`book_detail.html`)
- Displays comprehensive book information
- Features:
  - Dynamic content loading
  - Amazon affiliate integration
  - Responsive design
  - Navigation history support

### Search Implementation (`search.py`)
- Full-text search capability
- AI-enhanced search results
- Filtering and sorting options

### Database Models
- Book model with relationships
- Analytics tracking
- Search history

## Security Considerations

- CORS middleware configured for API security
- Environment variables for sensitive data
- Input validation using Pydantic models
- SQL injection prevention with SQLAlchemy

## Performance Optimizations

- Async database operations
- Efficient SQL queries with proper indexing
- Frontend optimizations:
  - Lazy loading of images
  - Debounced search
  - Efficient DOM updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

[Specify License]
