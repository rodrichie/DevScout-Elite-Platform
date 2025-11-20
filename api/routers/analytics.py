"""
Analytics router - Platform analytics and insights
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.schemas import AnalyticsResponse

router = APIRouter()


@router.get("/summary", response_model=AnalyticsResponse)
async def get_analytics_summary(db: Session = Depends(get_db)):
    """Get overall platform analytics summary."""
    try:
        # Total candidates
        total_candidates_query = "SELECT COUNT(*) FROM gold.dim_candidates"
        total_candidates = db.execute(total_candidates_query).scalar()
        
        # Average experience
        avg_exp_query = "SELECT AVG(years_experience) FROM gold.dim_candidates"
        avg_experience = db.execute(avg_exp_query).scalar() or 0
        
        # Total skills
        total_skills_query = "SELECT COUNT(DISTINCT skill_name) FROM gold.dim_skills"
        total_skills = db.execute(total_skills_query).scalar()
        
        # Average score
        avg_score_query = "SELECT AVG(overall_score) FROM gold.agg_candidate_rankings"
        avg_score = db.execute(avg_score_query).scalar() or 0
        
        # Top skills
        top_skills_query = """
            SELECT skill_name, candidate_count
            FROM gold.dim_skills
            ORDER BY candidate_count DESC
            LIMIT 10
        """
        top_skills_result = db.execute(top_skills_query)
        top_skills = [
            {"skill": row[0], "count": row[1]}
            for row in top_skills_result.fetchall()
        ]
        
        # Score distribution
        score_dist_query = """
            SELECT 
                performance_tier,
                COUNT(*) as count
            FROM gold.agg_candidate_rankings
            GROUP BY performance_tier
        """
        score_dist_result = db.execute(score_dist_query)
        score_distribution = {
            row[0]: row[1]
            for row in score_dist_result.fetchall()
        }
        
        return {
            "total_candidates": total_candidates,
            "avg_experience": round(avg_experience, 2),
            "total_skills": total_skills,
            "avg_score": round(avg_score, 2),
            "top_skills": top_skills,
            "score_distribution": score_distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline-health")
async def get_pipeline_health(db: Session = Depends(get_db)):
    """Get pipeline execution health metrics."""
    try:
        query = """
            SELECT 
                pipeline_name,
                COUNT(*) as total_runs,
                SUM(CASE WHEN run_status = 'success' THEN 1 ELSE 0 END) as successful_runs,
                AVG(execution_time_seconds) as avg_execution_time,
                MAX(run_date) as last_run
            FROM metadata.pipeline_runs
            WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY pipeline_name
        """
        
        result = db.execute(query)
        pipelines = result.fetchall()
        
        return [
            {
                "pipeline": row[0],
                "total_runs": row[1],
                "successful_runs": row[2],
                "success_rate": round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0,
                "avg_execution_time": round(row[3], 2) if row[3] else 0,
                "last_run": row[4].isoformat() if row[4] else None
            }
            for row in pipelines
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/hiring")
async def get_hiring_trends(db: Session = Depends(get_db)):
    """Get hiring trends and insights."""
    try:
        # Experience distribution
        exp_dist_query = """
            SELECT 
                CASE 
                    WHEN years_experience < 2 THEN '0-2 years'
                    WHEN years_experience < 5 THEN '2-5 years'
                    WHEN years_experience < 10 THEN '5-10 years'
                    ELSE '10+ years'
                END as experience_range,
                COUNT(*) as count,
                AVG(c.github_score) as avg_github_score
            FROM gold.dim_candidates c
            JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
            GROUP BY experience_range
            ORDER BY MIN(years_experience)
        """
        
        exp_result = db.execute(exp_dist_query)
        experience_distribution = [
            {
                "range": row[0],
                "count": row[1],
                "avg_github_score": round(row[2], 2) if row[2] else 0
            }
            for row in exp_result.fetchall()
        ]
        
        # Education distribution
        edu_dist_query = """
            SELECT 
                education_level,
                COUNT(*) as count,
                AVG(r.overall_score) as avg_score
            FROM gold.dim_candidates c
            JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
            GROUP BY education_level
            ORDER BY AVG(r.overall_score) DESC
        """
        
        edu_result = db.execute(edu_dist_query)
        education_distribution = [
            {
                "level": row[0],
                "count": row[1],
                "avg_score": round(row[2], 2) if row[2] else 0
            }
            for row in edu_result.fetchall()
        ]
        
        return {
            "experience_distribution": experience_distribution,
            "education_distribution": education_distribution
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))