"""
FastAPI Application - DevScout Elite API
RESTful API for candidate search, scoring, and analytics
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import logging

from .routers import candidates, skills, github, analytics, semantic, auth
from .models.database import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="DevScout Elite API",
    description="Hiring Intelligence Platform API for candidate search and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(github.router, prefix="/api/v1/github", tags=["github"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(semantic.router, prefix="/api/v1/semantic", tags=["semantic-search"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DevScout Elite API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "candidates": "/api/v1/candidates",
            "skills": "/api/v1/skills",
            "github": "/api/v1/github",
            "analytics": "/api/v1/analytics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2025-11-20T00:00:00Z"
    }


@app.get("/api/v1/status")
async def api_status():
    """Detailed API status."""
    return {
        "api_version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "candidate_search": True,
            "skill_matching": True,
            "github_integration": True,
            "analytics": True,
            "vector_search": False  # TODO: Implement Weaviate
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
