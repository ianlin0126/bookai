# BookDigest.ai

An AI-powered book summary and discovery platform that helps users get quick insights into books and decide if they're worth reading.

## Features

- Book search with typeahead suggestions
- AI-generated book summaries using Google Gemini and ChatGPT
- Chapter-by-chapter breakdowns
- Curated questions and answers about each book
- Popular books discovery
- Amazon affiliate integration for book purchases

## Setup

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
bookai/
├── alembic/              # Database migrations
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core functionality
│   ├── db/              # Database models and schemas
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test files
├── static/              # Static files (CSS, JS)
└── templates/           # HTML templates
```

## Testing

Run tests with:
```bash
pytest
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
