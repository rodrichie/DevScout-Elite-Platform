"""
Presentation Layer - FastAPI Routers (Clean Architecture)
Thin layer that delegates to use cases
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..models.database import get_db
from ..infrastructure.container import get_container, DependencyContainer
from ..application.use_cases import (
    GetCandidateQuery,
    ListCandidatesQuery,
    SearchCandidatesQuery
)
from ..domain.entities import Candidate, EducationLevel

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


# DTOs (Data Transfer Objects)
class CandidateResponse(BaseModel):
    """Response model for candidate."""
    id: int
    name: str
    email: str
    phone: Optional[str]
    years_experience: int
    education_level: str
    github_username: Optional[str]
    experience_score: float
    
    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    """Response model for candidate list."""
    total: int
    candidates: List[CandidateResponse]


class SkillResponse(BaseModel):
    """Response model for skill."""
    id: Optional[int]
    name: str
    category: str
    proficiency: str
    
    class Config:
        from_attributes = True


# Mappers (Converts domain entities to DTOs)
def map_candidate_to_response(candidate: Candidate) -> CandidateResponse:
    """Map domain entity to response DTO."""
    return CandidateResponse(
        id=candidate.id.value,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        years_experience=candidate.years_experience,
        education_level=candidate.education_level.value,
        github_username=candidate.github_username,
        experience_score=candidate.calculate_experience_score()
    )


# Routes (Thin controllers)
@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Get candidate by ID.
    Delegates to use case.
    """
    container = get_container(db)
    use_case = container.get_candidate_use_case()
    
    query = GetCandidateQuery(candidate_id=candidate_id)
    candidate = await use_case.execute(query)
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} not found"
        )
    
    return map_candidate_to_response(candidate)


@router.get("/", response_model=CandidateListResponse)
async def list_candidates(
    skip: int = 0,
    limit: int = 20,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    List candidates with pagination and filtering.
    Delegates to use case.
    """
    container = get_container(db)
    use_case = container.list_candidates_use_case()
    
    query = ListCandidatesQuery(
        skip=skip,
        limit=limit,
        min_score=min_score
    )
    candidates = await use_case.execute(query)
    
    return CandidateListResponse(
        total=len(candidates),
        candidates=[map_candidate_to_response(c) for c in candidates]
    )


@router.get("/search/", response_model=List[CandidateResponse])
async def search_candidates(
    q: str,
    max_results: int = 10,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Search candidates.
    Delegates to use case.
    """
    container = get_container(db)
    use_case = container.search_candidates_use_case()
    
    query = SearchCandidatesQuery(
        query=q,
        max_results=max_results,
        min_score=min_score
    )
    candidates = await use_case.execute(query)
    
    return [map_candidate_to_response(c) for c in candidates]


@router.get("/{candidate_id}/skills", response_model=List[SkillResponse])
async def get_candidate_skills(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Get skills for a candidate.
    Delegates to use case.
    """
    container = get_container(db)
    use_case = container.get_candidate_skills_use_case()
    
    try:
        query = GetCandidateQuery(candidate_id=candidate_id)
        skills = await use_case.execute(query)
        
        return [
            SkillResponse(
                id=skill.id,
                name=skill.name,
                category=skill.category,
                proficiency=skill.proficiency.value
            )
            for skill in skills
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
