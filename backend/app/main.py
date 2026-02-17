"""
TG Business Suite - Main FastAPI Application
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.core.database import async_engine, Base
from app.modules.auth.router import router as auth_router
from app.modules.telegram.router import router as telegram_router
from app.modules.automation.router import router as automation_router
from app.modules.proxies.router import router as proxies_router
from app.modules.billing.router import router as billing_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    async with async_engine.begin() as conn:
        # Create tables (use migrations in production)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await async_engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Telegram Business Account Management Platform",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(telegram_router, prefix="/api")
app.include_router(automation_router, prefix="/api")
app.include_router(proxies_router, prefix="/api")
app.include_router(billing_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
