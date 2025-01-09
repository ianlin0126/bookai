from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.db.database import engine, Base
from app.api import books, analytics, admin, search, llm, images
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

app = FastAPI(title="BookDigest.ai")

# Add security middlewares in production
if os.getenv('ENVIRONMENT') == 'production':
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "bookai-production.up.railway.app",
            "*.railway.app",
            "booksai.xyz",
            "www.booksai.xyz"
        ]
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def init_db():
    """Initialize database tables on startup"""
    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise  # Raise the error to prevent app from starting with broken DB

# Custom middleware to handle static file URLs
@app.middleware("http")
async def rewrite_static_urls(request: Request, call_next):
    """Ensure static file URLs use HTTPS when in production"""
    response = await call_next(request)
    
    # Only process HTML responses
    if response.headers.get("content-type") == "text/html; charset=utf-8":
        # Get the response content
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Convert to string and replace http:// with https:// for static files
        content = body.decode()
        if os.getenv('ENVIRONMENT') == 'production':
            content = content.replace(
                'http://bookai-production.up.railway.app/static/',
                'https://bookai-production.up.railway.app/static/'
            )
        
        # Create new response with modified content
        return HTMLResponse(
            content=content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    
    return response

# Ensure static directories exist and mount them
base_dir = Path(__file__).resolve().parent.parent
static_dir = base_dir / "static"
js_dir = static_dir / "js"
css_dir = static_dir / "css"
cache_dir = static_dir / "cache"
cache_images_dir = cache_dir / "images"

# Create directories if they don't exist
for directory in [static_dir, js_dir, css_dir, cache_dir, cache_images_dir]:
    directory.mkdir(parents=True, exist_ok=True)

try:
    # Mount static directories
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/js", StaticFiles(directory=js_dir), name="js")
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
    app.mount("/cache/images", StaticFiles(directory=cache_images_dir), name="cache_images")
    
    # Configure templates
    templates = Jinja2Templates(directory=str(base_dir / "app" / "templates"))
except Exception as e:
    logger.error(f"Error mounting static directories: {str(e)}")
    raise

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template rendering failed: {str(e)}")
        return HTMLResponse(
            content="""
            <html>
                <head>
                    <title>BookAI</title>
                    <style>
                        body { font-family: system-ui, -apple-system, sans-serif; padding: 2rem; }
                        h1 { color: #2563eb; }
                    </style>
                </head>
                <body>
                    <h1>BookAI</h1>
                    <p>Service is starting up...</p>
                </body>
            </html>
            """,
            status_code=200
        )

@app.get("/book", response_class=HTMLResponse)
async def book_detail(request: Request, id: str = None, key: str = None):
    """
    Render book detail page. Can be accessed by either:
    - /book?id=<book_id> for books in our database
    - /book?key=<open_library_key> for books from Open Library
    """
    try:
        return templates.TemplateResponse("book_detail.html", {
            "request": request,
            "book_id": id,
            "open_library_key": key
        })
    except Exception as e:
        logger.error(f"Template rendering failed: {str(e)}")
        return HTMLResponse(content="<html><body><h1>Error</h1><p>Failed to load book details.</p></body></html>")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount routers
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
