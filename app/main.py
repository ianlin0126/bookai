from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.db.database import engine, Base
from app.api import books, analytics, admin, search, llm
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

app = FastAPI(title="BookDigest.ai")

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

# Ensure static directories exist and mount them
base_dir = Path(__file__).resolve().parent.parent
static_dir = base_dir / "static"
assets_dir = base_dir / "assets"

# Create directories if they don't exist
if not static_dir.exists():
    static_dir.mkdir(parents=True)
    logger.info(f"Created static directory at {static_dir}")

if not assets_dir.exists():
    assets_dir.mkdir(parents=True)
    logger.info(f"Created assets directory at {assets_dir}")

# Ensure js directory exists
js_dir = static_dir / "js"
if not js_dir.exists():
    js_dir.mkdir(parents=True)
    logger.info(f"Created js directory at {js_dir}")

# Mount static directories with correct paths
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Mount routers
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def read_root(request: Request):
    try:
        return templates.TemplateResponse("base.html", {"request": request})
    except Exception as e:
        logger.error(f"Template rendering failed: {str(e)}")
        return HTMLResponse(content="<html><body><h1>BookAI</h1><p>Service is starting up...</p></body></html>")

@app.get("/book", response_class=HTMLResponse)
async def book_detail(request: Request, id: str = None, key: str = None):
    """
    Render book detail page. Can be accessed by either:
    - /book?id=<book_id> for books in our database
    - /book?key=<open_library_key> for books from Open Library
    """
    return templates.TemplateResponse("book_detail.html", {
        "request": request,
        "book_id": id,
        "open_library_key": key
    })

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
