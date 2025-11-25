"""
Domain Layer - Repository Interfaces (Ports)
Defines contracts for data access without implementation details
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Candidate, CandidateId, Skill, GitHubProfile, Resume


class ICandidateRepository(ABC):
    """Interface for candidate repository."""
    
    @abstractmethod
    async def get_by_id(self, candidate_id: CandidateId) -> Optional[Candidate]:
        """Retrieve candidate by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Candidate]:
        """Retrieve all candidates with pagination."""
        pass
    
    @abstractmethod
    async def save(self, candidate: Candidate) -> CandidateId:
        """Save or update candidate."""
        pass
    
    @abstractmethod
    async def delete(self, candidate_id: CandidateId) -> bool:
        """Delete candidate by ID."""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[Candidate]:
        """Find candidate by email."""
        pass
    
    @abstractmethod
    async def search(self, query: str, min_score: Optional[float] = None) -> List[Candidate]:
        """Search candidates by criteria."""
        pass


class ISkillRepository(ABC):
    """Interface for skill repository."""
    
    @abstractmethod
    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        """Retrieve skill by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Skill]:
        """Retrieve all skills."""
        pass
    
    @abstractmethod
    async def get_by_candidate(self, candidate_id: CandidateId) -> List[Skill]:
        """Get skills for a specific candidate."""
        pass
    
    @abstractmethod
    async def save(self, skill: Skill) -> int:
        """Save skill."""
        pass


class IGitHubRepository(ABC):
    """Interface for GitHub data repository."""
    
    @abstractmethod
    async def get_by_candidate(self, candidate_id: CandidateId) -> Optional[GitHubProfile]:
        """Get GitHub profile for candidate."""
        pass
    
    @abstractmethod
    async def save(self, profile: GitHubProfile) -> bool:
        """Save GitHub profile."""
        pass
    
    @abstractmethod
    async def get_top_contributors(self, limit: int = 20) -> List[GitHubProfile]:
        """Get top GitHub contributors."""
        pass


class IResumeRepository(ABC):
    """Interface for resume repository."""
    
    @abstractmethod
    async def save(self, resume: Resume) -> int:
        """Save resume."""
        pass
    
    @abstractmethod
    async def get_unprocessed(self, limit: int = 10) -> List[Resume]:
        """Get unprocessed resumes."""
        pass
    
    @abstractmethod
    async def mark_processed(self, resume_id: int) -> bool:
        """Mark resume as processed."""
        pass
