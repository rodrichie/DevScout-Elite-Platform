"""
Skills router - Skills analytics and statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from models.database import get_db

router = APIRouter()


@router.get("/")
async def get_skills(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of skills with candidate counts.

    Returns skills aggregated from resume extractions, ordered by the number
    of candidates possessing each skill. Supports filtering by skill category.
    """
    try:
        query = """
            SELECT
                rs.skill_name,
                rs.skill_category,
                COUNT(DISTINCT rs.candidate_id) as candidate_count
            FROM silver.resume_skills rs
            WHERE 1=1
        """

        params = {"limit": limit, "skip": skip}

        if category:
            query += " AND rs.skill_category = :category"
            params['category'] = category

        query += " GROUP BY rs.skill_name, rs.skill_category"
        query += " ORDER BY candidate_count DESC LIMIT :limit OFFSET :skip"

        result = db.execute(text(query), params)
        skills = result.fetchall()

        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "candidate_count": row[2],
            }
            for row in skills
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_skill_categories(db: Session = Depends(get_db)):
    """
    Get all skill categories with skill and candidate counts.

    Returns each category (e.g., Programming Language, Framework, Database)
    along with how many distinct skills and candidates belong to it.
    """
    try:
        query = """
            SELECT
                skill_category,
                COUNT(DISTINCT skill_name) as skill_count,
                COUNT(DISTINCT candidate_id) as candidate_count
            FROM silver.resume_skills
            GROUP BY skill_category
            ORDER BY candidate_count DESC
        """

        result = db.execute(text(query))
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
    """
    Get currently trending skills.

    Returns skills flagged as trending in the gold layer dimension table,
    along with the number of candidates who have each skill.
    """
    try:
        query = """
            SELECT
                ds.skill_name,
                ds.skill_category,
                ds.skill_family,
                ds.is_trending,
                COUNT(DISTINCT rs.candidate_id) as candidate_count
            FROM gold.dim_skills ds
            LEFT JOIN silver.resume_skills rs ON ds.skill_name = rs.skill_name
            WHERE ds.is_trending = TRUE
            GROUP BY ds.skill_key, ds.skill_name, ds.skill_category, ds.skill_family, ds.is_trending
            ORDER BY candidate_count DESC
            LIMIT :limit
        """

        result = db.execute(text(query), {"limit": limit})
        skills = result.fetchall()

        return [
            {
                "skill_name": row[0],
                "skill_category": row[1],
                "skill_family": row[2],
                "is_trending": row[3],
                "candidate_count": row[4],
            }
            for row in skills
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
