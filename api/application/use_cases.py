"""
Application Layer - Use Cases (Business Logic)
Orchestrates domain entities and repositories
"""
from typing import List, Optional
from dataclasses import dataclass

from ..domain.entities import Candidate, CandidateId, Skill
from ..domain.repositories import ICandidateRepository, ISkillRepository


@dataclass
class GetCandidateQuery:
    """Query to get a single candidate."""
    candidate_id: int


@dataclass
class ListCandidatesQuery:
    """Query to list candidates with filters."""
    skip: int = 0
    limit: int = 20
    min_score: Optional[float] = None


@dataclass
class SearchCandidatesQuery:
    """Query to search candidates."""
    query: str
    max_results: int = 10
    min_score: Optional[float] = None


class GetCandidateUseCase:
    """
    Use case: Retrieve a single candidate by ID.
    Follows Single Responsibility Principle.
    """
    
    def __init__(self, candidate_repo: ICandidateRepository):
        self._candidate_repo = candidate_repo
    
    async def execute(self, query: GetCandidateQuery) -> Optional[Candidate]:
        """Execute the use case."""
        candidate_id = CandidateId(query.candidate_id)
        return await self._candidate_repo.get_by_id(candidate_id)


class ListCandidatesUseCase:
    """
    Use case: List candidates with pagination and filtering.
    """
    
    def __init__(self, candidate_repo: ICandidateRepository):
        self._candidate_repo = candidate_repo
    
    async def execute(self, query: ListCandidatesQuery) -> List[Candidate]:
        """Execute the use case."""
        candidates = await self._candidate_repo.get_all(
            skip=query.skip,
            limit=query.limit
        )
        
        # Apply score filter if specified
        if query.min_score is not None:
            candidates = [
                c for c in candidates 
                if c.calculate_experience_score() >= query.min_score
            ]
        
        return candidates


class SearchCandidatesUseCase:
    """
    Use case: Search candidates based on criteria.
    """
    
    def __init__(self, candidate_repo: ICandidateRepository):
        self._candidate_repo = candidate_repo
    
    async def execute(self, query: SearchCandidatesQuery) -> List[Candidate]:
        """Execute the use case."""
        return await self._candidate_repo.search(
            query=query.query,
            min_score=query.min_score
        )


class GetCandidateSkillsUseCase:
    """
    Use case: Get all skills for a candidate.
    """
    
    def __init__(
        self,
        candidate_repo: ICandidateRepository,
        skill_repo: ISkillRepository
    ):
        self._candidate_repo = candidate_repo
        self._skill_repo = skill_repo
    
    async def execute(self, query: GetCandidateQuery) -> List[Skill]:
        """Execute the use case."""
        candidate_id = CandidateId(query.candidate_id)
        
        # Verify candidate exists
        candidate = await self._candidate_repo.get_by_id(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate {query.candidate_id} not found")
        
        # Get skills
        return await self._skill_repo.get_by_candidate(candidate_id)


class CreateCandidateUseCase:
    """
    Use case: Create a new candidate.
    Validates business rules.
    """
    
    def __init__(self, candidate_repo: ICandidateRepository):
        self._candidate_repo = candidate_repo
    
    async def execute(self, candidate: Candidate) -> CandidateId:
        """Execute the use case."""
        # Business rule: Check for duplicate email
        existing = await self._candidate_repo.find_by_email(candidate.email)
        if existing:
            raise ValueError(f"Candidate with email {candidate.email} already exists")
        
        # Save candidate
        return await self._candidate_repo.save(candidate)
