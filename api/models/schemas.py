"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CandidateResponse(BaseModel):
    candidate_id: int
    full_name: str
    email: str
    years_experience: int
    education_level: str
    primary_language: Optional[str] = None
    github_username: Optional[str] = None
    total_score: int = 0
    ranking_position: Optional[int] = None
    percentile: float = 0
    resume_match_score: int = 0
    github_contribution_score: int = 0
    coding_challenge_score: int = 0

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str
    years_experience: int = Field(0, ge=0, le=50)
    education_level: str


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    max_results: int = Field(10, ge=1, le=100)
    min_score: Optional[int] = Field(None, ge=0, le=300)
    required_skills: Optional[List[str]] = None


class AnalyticsResponse(BaseModel):
    total_candidates: int
    avg_experience: float
    total_skills: int
    avg_score: float
    top_skills: List[Dict[str, Any]]
    score_distribution: Dict[str, int]
