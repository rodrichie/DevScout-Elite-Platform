"""
Candidates router - CRUD operations for candidates
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..models.database import get_db
from ..models.schemas import CandidateResponse, CandidateCreate, SearchQuery

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[CandidateResponse])
async def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of candidates with pagination.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **min_score**: Minimum overall score filter
    """
    try:
        query = """
            SELECT 
                c.candidate_id,
                c.candidate_name,
                c.email,
                c.phone,
                c.years_experience,
                c.education_level,
                c.skill_count,
                c.github_username,
                c.github_score,
                r.overall_score,
                r.rank,
                c.created_at
            FROM gold.dim_candidates c
            LEFT JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
            WHERE 1=1
        """
        
        params = {}
        
        if min_score is not None:
            query += " AND r.overall_score >= :min_score"
            params['min_score'] = min_score
        
        query += " ORDER BY r.rank NULLS LAST LIMIT :limit OFFSET :skip"
        params['limit'] = limit
        params['skip'] = skip
        
        result = db.execute(query, params)
        candidates = result.fetchall()
        
        return [
            {
                "candidate_id": row[0],
                "candidate_name": row[1],
                "email": row[2],
                "phone": row[3],
                "years_experience": row[4],
                "education_level": row[5],
                "skill_count": row[6],
                "github_username": row[7],
                "github_score": row[8] or 0,
                "overall_score": row[9] or 0,
                "rank": row[10],
                "created_at": row[11]
            }
            for row in candidates
        ]
        
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed candidate information by ID."""
    try:
        query = """
            SELECT 
                c.candidate_id,
                c.candidate_name,
                c.email,
                c.phone,
                c.years_experience,
                c.education_level,
                c.skill_count,
                c.github_username,
                c.github_score,
                r.overall_score,
                r.rank,
                c.created_at
            FROM gold.dim_candidates c
            LEFT JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
            WHERE c.candidate_id = :candidate_id
        """
        
        result = db.execute(query, {"candidate_id": candidate_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        return {
            "candidate_id": row[0],
            "candidate_name": row[1],
            "email": row[2],
            "phone": row[3],
            "years_experience": row[4],
            "education_level": row[5],
            "skill_count": row[6],
            "github_username": row[7],
            "github_score": row[8] or 0,
            "overall_score": row[9] or 0,
            "rank": row[10],
            "created_at": row[11]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}/skills")
async def get_candidate_skills(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """Get all skills for a specific candidate."""
    try:
        query = """
            SELECT 
                skill_name,
                skill_category,
                proficiency_level
            FROM silver.resume_skills
            WHERE candidate_id = :candidate_id
            ORDER BY skill_category, skill_name
        """
        
        result = db.execute(query, {"candidate_id": candidate_id})
        skills = result.fetchall()
        
        if not skills:
            raise HTTPException(status_code=404, detail="No skills found for candidate")
        
        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "proficiency_level": row[2]
            }
            for row in skills
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching skills for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_candidates(
    search: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    Search candidates using natural language query.
    Searches across resume text and skills.
    """
    try:
        query = """
            SELECT DISTINCT
                c.candidate_id,
                c.candidate_name,
                c.email,
                c.years_experience,
                c.education_level,
                c.skill_count,
                r.overall_score,
                r.rank
            FROM gold.dim_candidates c
            LEFT JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
            LEFT JOIN silver.candidates sc ON c.candidate_id = sc.candidate_id
            LEFT JOIN silver.resume_skills rs ON c.candidate_id = rs.candidate_id
            WHERE (
                sc.resume_text ILIKE :query OR
                rs.skill_name ILIKE :query OR
                c.candidate_name ILIKE :query
            )
        """
        
        params = {"query": f"%{search.query}%"}
        
        if search.min_score:
            query += " AND r.overall_score >= :min_score"
            params['min_score'] = search.min_score
        
        query += " ORDER BY r.overall_score DESC NULLS LAST LIMIT :max_results"
        params['max_results'] = search.max_results
        
        result = db.execute(query, params)
        candidates = result.fetchall()
        
        return {
            "query": search.query,
            "results_count": len(candidates),
            "candidates": [
                {
                    "candidate_id": row[0],
                    "candidate_name": row[1],
                    "email": row[2],
                    "years_experience": row[3],
                    "education_level": row[4],
                    "skill_count": row[5],
                    "overall_score": row[6] or 0,
                    "rank": row[7]
                }
                for row in candidates
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
