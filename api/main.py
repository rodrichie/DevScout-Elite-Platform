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

from routers import candidates, skills, github, analytics, semantic, auth
from models.database import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

# OpenAPI tag metadata
tags_metadata = [
    {
        "name": "authentication",
        "description": "OAuth2 token-based authentication. Obtain a JWT token via the `/token` endpoint using username and password credentials. Default accounts: `admin` / `secret`, `recruiter` / `secret`.",
    },
    {
        "name": "candidates",
        "description": "Browse, search, and retrieve candidate profiles. Candidates are scored across resume matching, GitHub contributions, and coding challenges. Results are ranked using a composite score from the gold layer data warehouse.",
    },
    {
        "name": "skills",
        "description": "Query the skills taxonomy extracted from candidate resumes. View skill categories, candidate counts per skill, and trending skills identified by the analytics pipeline.",
    },
    {
        "name": "github",
        "description": "Access GitHub profile analytics for candidates. View contribution scores, language distributions, and top contributors ranked by stars, repos, or commit activity.",
    },
    {
        "name": "analytics",
        "description": "Platform-wide analytics and insights. Includes summary statistics, data pipeline health monitoring, and hiring trend analysis across experience levels and education.",
    },
    {
        "name": "semantic-search",
        "description": "Natural language candidate search powered by Weaviate vector database. Requires the Weaviate service to be running and indexed.",
    },
]

# Initialize FastAPI app
app = FastAPI(
    title="DevScout Elite API",
    description=(
        "## Hiring Intelligence Platform\n\n"
        "DevScout Elite is a data-driven hiring intelligence platform that aggregates "
        "candidate data from resumes, GitHub profiles, and coding challenges into a "
        "unified scoring and ranking system.\n\n"
        "### Architecture\n\n"
        "The platform uses a **medallion data warehouse** architecture:\n\n"
        "- **Bronze layer** -- Raw ingested data (resumes, GitHub API responses)\n"
        "- **Silver layer** -- Cleaned and normalized candidate profiles, skills, and GitHub metrics\n"
        "- **Gold layer** -- Aggregated rankings, scores, and analytics-ready dimensions\n\n"
        "### Data Pipeline\n\n"
        "- **Apache Airflow** orchestrates ETL workflows\n"
        "- **Apache Spark** handles large-scale data transformations\n"
        "- **Apache Kafka** streams real-time events (resume uploads, coding challenges)\n"
        "- **MLflow** tracks ML model experiments and scoring models\n"
        "- **Weaviate** provides vector-based semantic search\n\n"
        "### Scoring System\n\n"
        "Each candidate receives a composite score (0-300) based on:\n\n"
        "| Component | Max Score |\n"
        "|---|---|\n"
        "| Resume Match | 100 |\n"
        "| GitHub Contribution | 100 |\n"
        "| Coding Challenge | 100 |\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "DevScout Engineering",
        "url": "https://github.com/rodrichie/DevScout-Elite-Platform",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware - Restricted by environment
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
