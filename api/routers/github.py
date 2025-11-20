"""
GitHub router - GitHub profile analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..models.schemas import GitHubProfileResponse

router = APIRouter()


@router.get("/{username}", response_model=GitHubProfileResponse)
async def get_github_profile(
    username: str,
    db: Session = Depends(get_db)
):
    """Get GitHub profile by username."""
    try:
        query = """
            SELECT 
                candidate_id,
                github_username,
                total_repos,
                total_stars,
                total_forks,
                followers_count,
                contributions_90_days,
                top_language,
                code_quality_score,
                contribution_score,
                impact_score,
                (code_quality_score * 0.4 + contribution_score * 0.4 + impact_score * 0.2) as overall_github_score
            FROM silver.github_profiles
            WHERE github_username = :username
        """
        
        result = db.execute(query, {"username": username})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="GitHub profile not found")
        
        return {
            "candidate_id": row[0],
            "github_username": row[1],
            "total_repos": row[2],
            "total_stars": row[3],
            "total_forks": row[4],
            "followers_count": row[5],
            "contributions_90_days": row[6],
            "top_language": row[7],
            "code_quality_score": row[8],
            "contribution_score": row[9],
            "impact_score": row[10],
            "overall_github_score": row[11]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/top-contributors")
async def get_top_contributors(
    limit: int = Query(20, ge=1, le=100),
    metric: str = Query("overall", regex="^(overall|stars|repos|contributions)$"),
    db: Session = Depends(get_db)
):
    """Get top GitHub contributors by various metrics."""
    try:
        order_by = {
            "overall": "(code_quality_score * 0.4 + contribution_score * 0.4 + impact_score * 0.2)",
            "stars": "total_stars",
            "repos": "total_repos",
            "contributions": "contributions_90_days"
        }[metric]
        
        query = f"""
            SELECT 
                github_username,
                total_repos,
                total_stars,
                contributions_90_days,
                top_language,
                (code_quality_score * 0.4 + contribution_score * 0.4 + impact_score * 0.2) as overall_score
            FROM silver.github_profiles
            ORDER BY {order_by} DESC
            LIMIT :limit
        """
        
        result = db.execute(query, {"limit": limit})
        contributors = result.fetchall()
        
        return [
            {
                "username": row[0],
                "total_repos": row[1],
                "total_stars": row[2],
                "contributions_90_days": row[3],
                "top_language": row[4],
                "overall_score": round(row[5], 2)
            }
            for row in contributors
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/languages")
async def get_language_distribution(db: Session = Depends(get_db)):
    """Get distribution of programming languages."""
    try:
        query = """
            SELECT 
                top_language,
                COUNT(*) as user_count,
                AVG(total_repos) as avg_repos,
                AVG(total_stars) as avg_stars
            FROM silver.github_profiles
            WHERE top_language IS NOT NULL
            GROUP BY top_language
            ORDER BY user_count DESC
            LIMIT 20
        """
        
        result = db.execute(query)
        languages = result.fetchall()
        
        return [
            {
                "language": row[0],
                "user_count": row[1],
                "avg_repos": round(row[2], 1),
                "avg_stars": round(row[3], 1)
            }
            for row in languages
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
