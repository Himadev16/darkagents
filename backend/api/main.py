"""
DARKAGENTS FastAPI Application
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import settings
from backend.database import init_db
from backend.api.routes import auth, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Runs on startup and shutdown
    """
    # Startup
    print("🚀 DARKAGENTS Backend starting...")
    print(f"📊 Database: {settings.DATABASE_URL}")

    # Initialize database
    init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 DARKAGENTS Backend shutting down...")


# Create FastAPI app
app = FastAPI(
    title="DARKAGENTS API",
    description="AI Agent Orchestration Platform for Building SaaS Applications",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "DARKAGENTS API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
