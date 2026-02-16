"""
Semantic Search router - Weaviate-powered semantic search
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")

try:
    import weaviate
    HAS_WEAVIATE = True
except ImportError:
    HAS_WEAVIATE = False
    logger.warning("weaviate-client not installed. Semantic search endpoints will return 503.")


def get_weaviate_client():
    """Get Weaviate client."""
    if not HAS_WEAVIATE:
        raise HTTPException(status_code=503, detail="Vector search service not available (weaviate-client not installed)")
    try:
        return weaviate.Client(WEAVIATE_URL)
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        raise HTTPException(status_code=503, detail="Vector search service unavailable")


@router.get("/search")
async def semantic_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    min_certainty: float = Query(0.7, ge=0, le=1)
):
    """
    Perform semantic search on candidates using natural language.

    Uses Weaviate vector embeddings to find candidates matching a natural
    language query (e.g., "senior Python developer with cloud experience").
    Results are filtered by minimum certainty threshold and ranked by similarity.
    """
    try:
        client = get_weaviate_client()

        result = (
            client.query
            .get("Candidate", [
                "candidateId", "fullName", "email", "skills",
                "yearsExperience", "educationLevel", "githubUsername",
                "totalScore"
            ])
            .with_near_text({"concepts": [query]})
            .with_additional(["certainty", "distance"])
            .with_limit(limit)
            .do()
        )

        candidates = result.get('data', {}).get('Get', {}).get('Candidate', [])

        filtered = [
            {
                **c,
                "similarity_score": c.get('_additional', {}).get('certainty', 0)
            }
            for c in candidates
            if c.get('_additional', {}).get('certainty', 0) >= min_certainty
        ]

        return {
            "query": query,
            "results_count": len(filtered),
            "candidates": filtered
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_vector_stats():
    """
    Get Weaviate vector database statistics.

    Returns the health status and number of candidate profiles
    currently indexed in the vector store. Returns 503 if the
    Weaviate service is unavailable.
    """
    try:
        client = get_weaviate_client()

        candidate_count = (
            client.query
            .aggregate("Candidate")
            .with_meta_count()
            .do()
        )

        return {
            "status": "healthy",
            "candidates_indexed": candidate_count.get('data', {}).get('Aggregate', {}).get('Candidate', [{}])[0].get('meta', {}).get('count', 0),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
