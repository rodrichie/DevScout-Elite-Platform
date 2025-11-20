"""
Semantic Search router - Weaviate-powered semantic search
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import weaviate
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# Weaviate client
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")


def get_weaviate_client():
    """Get Weaviate client."""
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
    
    - **query**: Natural language search query
    - **limit**: Maximum number of results
    - **min_certainty**: Minimum similarity score (0-1)
    """
    try:
        client = get_weaviate_client()
        
        result = (
            client.query
            .get("Candidate", [
                "candidateId", "candidateName", "email", "skills",
                "yearsExperience", "educationLevel", "githubUsername",
                "overallScore"
            ])
            .with_near_text({"concepts": [query]})
            .with_additional(["certainty", "distance"])
            .with_limit(limit)
            .do()
        )
        
        candidates = result.get('data', {}).get('Get', {}).get('Candidate', [])
        
        # Filter by certainty
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


@router.get("/similar/{candidate_id}")
async def find_similar_candidates(
    candidate_id: int,
    limit: int = Query(5, ge=1, le=20)
):
    """Find candidates similar to a given candidate."""
    try:
        client = get_weaviate_client()
        
        # Get reference candidate
        result = (
            client.query
            .get("Candidate", ["candidateId", "resumeText"])
            .with_where({
                "path": ["candidateId"],
                "operator": "Equal",
                "valueInt": candidate_id
            })
            .do()
        )
        
        candidates = result.get('data', {}).get('Get', {}).get('Candidate', [])
        if not candidates:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        reference_text = candidates[0]['resumeText']
        
        # Find similar
        result = (
            client.query
            .get("Candidate", [
                "candidateId", "candidateName", "email", "skills",
                "yearsExperience", "educationLevel", "overallScore"
            ])
            .with_near_text({"concepts": [reference_text]})
            .with_additional(["certainty"])
            .with_limit(limit + 1)
            .do()
        )
        
        similar = result.get('data', {}).get('Get', {}).get('Candidate', [])
        
        # Exclude reference candidate
        similar = [
            {**c, "similarity_score": c.get('_additional', {}).get('certainty', 0)}
            for c in similar
            if c['candidateId'] != candidate_id
        ][:limit]
        
        return {
            "reference_candidate_id": candidate_id,
            "similar_count": len(similar),
            "similar_candidates": similar
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/semantic")
async def semantic_skill_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=30)
):
    """Search for skills using semantic understanding."""
    try:
        client = get_weaviate_client()
        
        result = (
            client.query
            .get("Skill", [
                "skillName", "skillCategory", "description", "candidateCount"
            ])
            .with_near_text({"concepts": [query]})
            .with_additional(["certainty"])
            .with_limit(limit)
            .do()
        )
        
        skills = result.get('data', {}).get('Get', {}).get('Skill', [])
        
        return {
            "query": query,
            "results_count": len(skills),
            "skills": [
                {
                    **s,
                    "relevance_score": s.get('_additional', {}).get('certainty', 0)
                }
                for s in skills
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in semantic skill search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_vector_stats():
    """Get Weaviate vector database statistics."""
    try:
        client = get_weaviate_client()
        
        candidate_count = (
            client.query
            .aggregate("Candidate")
            .with_meta_count()
            .do()
        )
        
        skill_count = (
            client.query
            .aggregate("Skill")
            .with_meta_count()
            .do()
        )
        
        return {
            "status": "healthy",
            "candidates_indexed": candidate_count['data']['Aggregate']['Candidate'][0]['meta']['count'],
            "skills_indexed": skill_count['data']['Aggregate']['Skill'][0]['meta']['count']
        }
        
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
