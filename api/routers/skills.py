"""
Skills router - Skills analytics and statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.database import get_db
from ..models.schemas import SkillResponse

router = APIRouter()


@router.get("/", response_model=List[SkillResponse])
async def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    min_candidates: int = Query(1, ge=1),
    db: Session = Depends(get_db)
):
    """
    Get list of skills with popularity metrics.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **category**: Filter by skill category
    - **min_candidates**: Minimum number of candidates with skill
    """
    try:
        query = """
            SELECT 
                skill_name,
                skill_category,
                candidate_count,
                total_occurrences
            FROM gold.dim_skills
            WHERE candidate_count >= :min_candidates
        """
        
        params = {"min_candidates": min_candidates, "limit": limit, "skip": skip}
        
        if category:
            query += " AND skill_category = :category"
            params['category'] = category
        
        query += " ORDER BY candidate_count DESC LIMIT :limit OFFSET :skip"
        
        result = db.execute(query, params)
        skills = result.fetchall()
        
        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "candidate_count": row[2],
                "total_occurrences": row[3],
                "proficiency_level": "Various"
            }
            for row in skills
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_skill_categories(db: Session = Depends(get_db)):
    """Get list of all skill categories with counts."""
    try:
        query = """
            SELECT 
                skill_category,
                COUNT(DISTINCT skill_name) as skill_count,
                SUM(candidate_count) as total_candidates
            FROM gold.dim_skills
            GROUP BY skill_category
            ORDER BY total_candidates DESC
        """
        
        result = db.execute(query)
        categories = result.fetchall()
        
        return [
            {
                "category": row[0],
                "skill_count": row[1],
                "candidate_count": row[2]
            }
            for row in categories
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_skills(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending skills based on recent activity."""
    try:
        query = """
            SELECT 
                skill_name,
                skill_category,
                candidate_count,
                last_seen_at
            FROM gold.dim_skills
            WHERE last_seen_at >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY candidate_count DESC, last_seen_at DESC
            LIMIT :limit
        """
        
        result = db.execute(query, {"limit": limit})
        skills = result.fetchall()
        
        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "candidate_count": row[2],
                "last_seen": row[3].isoformat() if row[3] else None
            }
            for row in skills
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
