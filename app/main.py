from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api import books, analytics, search, llm
from app.db.database import engine, Base
import time
import asyncio

# Create database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI(title="BookDigest.ai")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"[DEBUG] Request path: {request.url.path}")
    print(f"[DEBUG] Request method: {request.method}")
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"[DEBUG] Response status: {response.status_code}")
    print(f"[DEBUG] Process time: {process_time:.2f}s")
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()

# Mount routers with /api prefix
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/book", response_class=HTMLResponse)
async def book_detail(request: Request):
    return templates.TemplateResponse("book_detail.html", {"request": request})

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
