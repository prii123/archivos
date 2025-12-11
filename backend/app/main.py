from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db import init_db
from app.routers import auth, users, files, admin, drive


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    await init_db()
    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(
    title="DocManager Drive",
    description="Document Management System with Google Drive Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(drive.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DocManager Drive API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
