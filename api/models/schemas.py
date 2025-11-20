"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime


class CandidateBase(BaseModel):
    """Base candidate model."""
    candidate_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = None
    years_experience: int = Field(0, ge=0, le=50)
    education_level: str


class CandidateCreate(CandidateBase):
    """Model for creating a candidate."""
    resume_text: str


class CandidateResponse(CandidateBase):
    """Model for candidate response."""
    candidate_id: int
    skill_count: int
    github_username: Optional[str] = None
    github_score: float
    overall_score: float
    rank: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SkillBase(BaseModel):
    """Base skill model."""
    skill_name: str
    skill_category: str
    proficiency_level: Optional[str] = "Intermediate"


class SkillResponse(SkillBase):
    """Model for skill response."""
    candidate_count: int
    total_occurrences: int
    
    class Config:
        from_attributes = True


class GitHubProfileResponse(BaseModel):
    """Model for GitHub profile response."""
    candidate_id: int
    github_username: str
    total_repos: int
    total_stars: int
    total_forks: int
    followers_count: int
    contributions_90_days: int
    top_language: Optional[str] = None
    code_quality_score: float
    contribution_score: float
    impact_score: float
    overall_github_score: float
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Model for search query."""
    query: str = Field(..., min_length=1)
    max_results: int = Field(10, ge=1, le=100)
    min_score: Optional[float] = Field(None, ge=0, le=100)
    required_skills: Optional[List[str]] = None


class AnalyticsResponse(BaseModel):
    """Model for analytics response."""
    total_candidates: int
    avg_experience: float
    total_skills: int
    avg_score: float
    top_skills: List[Dict[str, any]]
    score_distribution: Dict[str, int]
