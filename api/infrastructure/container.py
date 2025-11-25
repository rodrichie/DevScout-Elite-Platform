"""
Infrastructure Layer - Dependency Injection Container
Configures and wires up all dependencies
"""
from functools import lru_cache
from sqlalchemy.orm import Session

from ..domain.repositories import ICandidateRepository, ISkillRepository
from ..infrastructure.postgres_repositories import (
    PostgreSQLCandidateRepository,
    PostgreSQLSkillRepository
)
from ..application.use_cases import (
    GetCandidateUseCase,
    ListCandidatesUseCase,
    SearchCandidatesUseCase,
    GetCandidateSkillsUseCase,
    CreateCandidateUseCase
)


class DependencyContainer:
    """
    Dependency Injection Container.
    Centralizes dependency creation and management.
    """
    
    def __init__(self, db_session: Session):
        self._db_session = db_session
        self._candidate_repo: Optional[ICandidateRepository] = None
        self._skill_repo: Optional[ISkillRepository] = None
    
    def candidate_repository(self) -> ICandidateRepository:
        """Get candidate repository instance."""
        if not self._candidate_repo:
            self._candidate_repo = PostgreSQLCandidateRepository(self._db_session)
        return self._candidate_repo
    
    def skill_repository(self) -> ISkillRepository:
        """Get skill repository instance."""
        if not self._skill_repo:
            self._skill_repo = PostgreSQLSkillRepository(self._db_session)
        return self._skill_repo
    
    def get_candidate_use_case(self) -> GetCandidateUseCase:
        """Get use case for retrieving a candidate."""
        return GetCandidateUseCase(self.candidate_repository())
    
    def list_candidates_use_case(self) -> ListCandidatesUseCase:
        """Get use case for listing candidates."""
        return ListCandidatesUseCase(self.candidate_repository())
    
    def search_candidates_use_case(self) -> SearchCandidatesUseCase:
        """Get use case for searching candidates."""
        return SearchCandidatesUseCase(self.candidate_repository())
    
    def get_candidate_skills_use_case(self) -> GetCandidateSkillsUseCase:
        """Get use case for retrieving candidate skills."""
        return GetCandidateSkillsUseCase(
            self.candidate_repository(),
            self.skill_repository()
        )
    
    def create_candidate_use_case(self) -> CreateCandidateUseCase:
        """Get use case for creating a candidate."""
        return CreateCandidateUseCase(self.candidate_repository())


# Dependency provider for FastAPI
def get_container(db: Session) -> DependencyContainer:
    """
    FastAPI dependency provider.
    Creates a new container instance per request.
    """
    return DependencyContainer(db)
