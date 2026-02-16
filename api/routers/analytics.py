"""
Analytics router - Platform analytics and insights
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.database import get_db

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(db: Session = Depends(get_db)):
    """
    Get overall platform analytics summary.

    Returns total candidates, average experience, distinct skill count,
    average composite score, top 10 skills by candidate count, and
    score distribution across performance tiers (excellent, good, average, below_average).
    """
    try:
        total_candidates = db.execute(
            text("SELECT COUNT(*) FROM gold.dim_candidates WHERE is_current = TRUE")
        ).scalar()

        avg_experience = db.execute(
            text("SELECT AVG(years_experience) FROM gold.dim_candidates WHERE is_current = TRUE")
        ).scalar() or 0

        total_skills = db.execute(
            text("SELECT COUNT(DISTINCT skill_name) FROM silver.resume_skills")
        ).scalar()

        avg_score = db.execute(
            text("SELECT AVG(total_score) FROM gold.agg_candidate_rankings")
        ).scalar() or 0

        top_skills_result = db.execute(text("""
            SELECT skill_name, COUNT(DISTINCT candidate_id) as cnt
            FROM silver.resume_skills
            GROUP BY skill_name
            ORDER BY cnt DESC
            LIMIT 10
        """))
        top_skills = [
            {"skill": row[0], "count": row[1]}
            for row in top_skills_result.fetchall()
        ]

        score_dist_result = db.execute(text("""
            SELECT
                CASE
                    WHEN total_score >= 200 THEN 'excellent'
                    WHEN total_score >= 150 THEN 'good'
                    WHEN total_score >= 100 THEN 'average'
                    ELSE 'below_average'
                END as tier,
                COUNT(*) as count
            FROM gold.agg_candidate_rankings
            GROUP BY tier
        """))
        score_distribution = {
            row[0]: row[1]
            for row in score_dist_result.fetchall()
        }

        return {
            "total_candidates": total_candidates,
            "avg_experience": round(float(avg_experience), 2),
            "total_skills": total_skills,
            "avg_score": round(float(avg_score), 2),
            "top_skills": top_skills,
            "score_distribution": score_distribution
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-health")
async def get_pipeline_health(db: Session = Depends(get_db)):
    """
    Get data pipeline health metrics for the last 7 days.

    Returns per-pipeline statistics: total runs, successful runs,
    success rate percentage, last run timestamp, and average duration in seconds.
    """
    try:
        query = """
            SELECT
                pipeline_name,
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                MAX(run_date) as last_run,
                AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))::DECIMAL as avg_duration_seconds
            FROM metadata.pipeline_runs
            WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY pipeline_name
        """

        result = db.execute(text(query))
        pipelines = result.fetchall()

        return [
            {
                "pipeline": row[0],
                "total_runs": row[1],
                "successful_runs": row[2],
                "success_rate": round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0,
                "last_run": row[3].isoformat() if row[3] else None,
                "avg_duration_seconds": round(float(row[4]), 2) if row[4] else 0,
            }
            for row in pipelines
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/hiring")
async def get_hiring_trends(db: Session = Depends(get_db)):
    """
    Get hiring trends and talent pool insights.

    Returns experience distribution (0-2, 2-5, 5-10, 10+ years) and
    education level distribution, each with candidate counts and
    average composite scores.
    """
    try:
        exp_result = db.execute(text("""
            SELECT
                CASE
                    WHEN dc.years_experience < 2 THEN '0-2 years'
                    WHEN dc.years_experience < 5 THEN '2-5 years'
                    WHEN dc.years_experience < 10 THEN '5-10 years'
                    ELSE '10+ years'
                END as experience_range,
                COUNT(*) as count,
                AVG(r.total_score)::DECIMAL as avg_score
            FROM gold.dim_candidates dc
            LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
            WHERE dc.is_current = TRUE
            GROUP BY experience_range
            ORDER BY MIN(dc.years_experience)
        """))
        experience_distribution = [
            {
                "range": row[0],
                "count": row[1],
                "avg_score": round(float(row[2]), 2) if row[2] else 0
            }
            for row in exp_result.fetchall()
        ]

        edu_result = db.execute(text("""
            SELECT
                dc.education_level,
                COUNT(*) as count,
                AVG(r.total_score)::DECIMAL as avg_score
            FROM gold.dim_candidates dc
            LEFT JOIN gold.agg_candidate_rankings r ON dc.candidate_key = r.candidate_key
            WHERE dc.is_current = TRUE
            GROUP BY dc.education_level
            ORDER BY avg_score DESC NULLS LAST
        """))
        education_distribution = [
            {
                "level": row[0],
                "count": row[1],
                "avg_score": round(float(row[2]), 2) if row[2] else 0
            }
            for row in edu_result.fetchall()
        ]

        return {
            "experience_distribution": experience_distribution,
            "education_distribution": education_distribution
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
