"""
GitHub router - GitHub profile analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.database import get_db

router = APIRouter()


@router.get("/stats/top-contributors")
async def get_top_contributors(
    limit: int = Query(20, ge=1, le=100),
    metric: str = Query("contribution", pattern="^(contribution|stars|repos|commits)$"),
    db: Session = Depends(get_db)
):
    """
    Get top GitHub contributors ranked by a chosen metric.

    Supports ranking by `contribution` score, `stars`, `repos`, or `commits`.
    Returns GitHub profile data from the silver layer.
    """
    try:
        order_map = {
            "contribution": "contribution_score",
            "stars": "total_stars",
            "repos": "total_repos",
            "commits": "commits_last_90_days"
        }
        order_col = order_map.get(metric, "contribution_score")

        query = f"""
            SELECT
                github_username,
                primary_language,
                total_repos,
                total_stars,
                total_forks,
                commits_last_90_days,
                contribution_score
            FROM silver.github_profiles
            ORDER BY {order_col} DESC
            LIMIT :limit
        """

        result = db.execute(text(query), {"limit": limit})
        contributors = result.fetchall()

        return [
            {
                "username": row[0],
                "primary_language": row[1],
                "total_repos": row[2],
                "total_stars": row[3],
                "total_forks": row[4],
                "commits_last_90_days": row[5],
                "contribution_score": float(row[6]) if row[6] else 0,
            }
            for row in contributors
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/languages")
async def get_language_distribution(db: Session = Depends(get_db)):
    """
    Get programming language distribution across GitHub profiles.

    Returns each primary language with user count, average repos, and
    average stars for developers using that language.
    """
    try:
        query = """
            SELECT
                primary_language,
                COUNT(*) as user_count,
                AVG(total_repos)::DECIMAL as avg_repos,
                AVG(total_stars)::DECIMAL as avg_stars
            FROM silver.github_profiles
            WHERE primary_language IS NOT NULL
            GROUP BY primary_language
            ORDER BY user_count DESC
            LIMIT 20
        """

        result = db.execute(text(query))
        languages = result.fetchall()

        return [
            {
                "language": row[0],
                "user_count": row[1],
                "avg_repos": round(float(row[2]), 1),
                "avg_stars": round(float(row[3]), 1),
            }
            for row in languages
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{username}")
async def get_github_profile(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Get a GitHub profile by username.

    Returns the full GitHub profile including repos, stars, forks,
    recent commit activity, contribution score, and languages used.
    """
    try:
        query = """
            SELECT
                g.candidate_id,
                g.github_username,
                g.primary_language,
                g.total_repos,
                g.total_stars,
                g.total_forks,
                g.commits_last_90_days,
                g.avg_commit_size,
                g.contribution_score,
                g.languages_used,
                g.fetched_at
            FROM silver.github_profiles g
            WHERE g.github_username = :username
        """

        result = db.execute(text(query), {"username": username})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="GitHub profile not found")

        return {
            "candidate_id": row[0],
            "github_username": row[1],
            "primary_language": row[2],
            "total_repos": row[3],
            "total_stars": row[4],
            "total_forks": row[5],
            "commits_last_90_days": row[6],
            "avg_commit_size": row[7],
            "contribution_score": float(row[8]) if row[8] else 0,
            "languages_used": row[9] or [],
            "fetched_at": row[10].isoformat() if row[10] else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
