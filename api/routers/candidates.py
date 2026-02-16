"""
Candidates router - CRUD operations for candidates
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import logging

from models.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    min_score: Optional[int] = Query(None, ge=0, le=300),
    db: Session = Depends(get_db)
):
    """
    Get list of candidates with pagination and optional score filtering.

    Returns candidates ranked by their composite score, including resume match,
    GitHub contribution, and coding challenge scores from the gold layer.
    """
    try:
        query = """
            SELECT
                dc.candidate_id,
                dc.full_name,
                dc.email,
                dc.years_experience,
                dc.education_level,
                dc.primary_language,
                sc.github_username,
                r.total_score,
                r.ranking_position,
                r.percentile,
                fs.resume_match_score,
                fs.github_contribution_score,
                fs.coding_challenge_score
            FROM gold.dim_candidates dc
            LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
            LEFT JOIN gold.fact_candidate_scores fs ON dc.candidate_key = fs.candidate_key
            LEFT JOIN silver.candidates sc ON dc.candidate_id = sc.candidate_id
            WHERE dc.is_current = TRUE
        """

        params = {}

        if min_score is not None:
            query += " AND r.total_score >= :min_score"
            params['min_score'] = min_score

        query += " ORDER BY r.ranking_position NULLS LAST LIMIT :limit OFFSET :skip"
        params['limit'] = limit
        params['skip'] = skip

        result = db.execute(text(query), params)
        candidates = result.fetchall()

        return [
            {
                "candidate_id": row[0],
                "full_name": row[1],
                "email": row[2],
                "years_experience": row[3],
                "education_level": row[4],
                "primary_language": row[5],
                "github_username": row[6],
                "total_score": row[7] or 0,
                "ranking_position": row[8],
                "percentile": float(row[9]) if row[9] else 0,
                "resume_match_score": row[10] or 0,
                "github_contribution_score": row[11] or 0,
                "coding_challenge_score": row[12] or 0,
            }
            for row in candidates
        ]

    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed candidate profile by ID.

    Returns the full candidate profile including experience, education,
    GitHub username, and individual score breakdowns from the scoring pipeline.
    """
    try:
        query = """
            SELECT
                dc.candidate_id,
                dc.full_name,
                dc.email,
                dc.years_experience,
                dc.education_level,
                dc.primary_language,
                sc.github_username,
                r.total_score,
                r.ranking_position,
                r.percentile,
                fs.resume_match_score,
                fs.github_contribution_score,
                fs.coding_challenge_score
            FROM gold.dim_candidates dc
            LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
            LEFT JOIN gold.fact_candidate_scores fs ON dc.candidate_key = fs.candidate_key
            LEFT JOIN silver.candidates sc ON dc.candidate_id = sc.candidate_id
            WHERE dc.candidate_id = :candidate_id AND dc.is_current = TRUE
        """

        result = db.execute(text(query), {"candidate_id": candidate_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Candidate not found")

        return {
            "candidate_id": row[0],
            "full_name": row[1],
            "email": row[2],
            "years_experience": row[3],
            "education_level": row[4],
            "primary_language": row[5],
            "github_username": row[6],
            "total_score": row[7] or 0,
            "ranking_position": row[8],
            "percentile": float(row[9]) if row[9] else 0,
            "resume_match_score": row[10] or 0,
            "github_contribution_score": row[11] or 0,
            "coding_challenge_score": row[12] or 0,
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
    """
    Get all skills extracted from a candidate's resume.

    Returns skills with their categories and confidence scores as
    determined by the NLP extraction pipeline.
    """
    try:
        query = """
            SELECT
                skill_name,
                skill_category,
                confidence_score
            FROM silver.resume_skills
            WHERE candidate_id = :candidate_id
            ORDER BY skill_category, skill_name
        """

        result = db.execute(text(query), {"candidate_id": candidate_id})
        skills = result.fetchall()

        if not skills:
            raise HTTPException(status_code=404, detail="No skills found for candidate")

        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "confidence_score": float(row[2]) if row[2] else 0,
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
    search: dict,
    db: Session = Depends(get_db)
):
    """
    Search candidates by name, email, or skill.

    Accepts a JSON body with `query` (search term), `max_results` (default 10),
    and optional `min_score` filter. Searches across candidate names, emails,
    and extracted skill names.
    """
    try:
        search_query = search.get("query", "")
        max_results = search.get("max_results", 10)
        min_score = search.get("min_score")

        query = """
            SELECT DISTINCT
                dc.candidate_id,
                dc.full_name,
                dc.email,
                dc.years_experience,
                dc.education_level,
                r.total_score,
                r.ranking_position
            FROM gold.dim_candidates dc
            LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
            LEFT JOIN silver.resume_skills rs ON dc.candidate_id = rs.candidate_id
            WHERE dc.is_current = TRUE
              AND (
                dc.full_name ILIKE :query
                OR rs.skill_name ILIKE :query
                OR dc.email ILIKE :query
              )
        """

        params = {"query": f"%{search_query}%", "max_results": max_results}

        if min_score:
            query += " AND r.total_score >= :min_score"
            params['min_score'] = min_score

        query += " ORDER BY r.total_score DESC NULLS LAST LIMIT :max_results"

        result = db.execute(text(query), params)
        candidates = result.fetchall()

        return {
            "query": search_query,
            "results_count": len(candidates),
            "candidates": [
                {
                    "candidate_id": row[0],
                    "full_name": row[1],
                    "email": row[2],
                    "years_experience": row[3],
                    "education_level": row[4],
                    "total_score": row[5] or 0,
                    "ranking_position": row[6],
                }
                for row in candidates
            ]
        }

    except Exception as e:
        logger.error(f"Error searching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
