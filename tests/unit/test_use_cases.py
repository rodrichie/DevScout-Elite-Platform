"""
Example Unit Tests - Demonstrating Testability with DI
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from api.domain.entities import Candidate, CandidateId, Skill, EducationLevel, ProficiencyLevel
from api.domain.repositories import ICandidateRepository, ISkillRepository
from api.application.use_cases import (
    GetCandidateUseCase,
    GetCandidateQuery,
    ListCandidatesUseCase,
    ListCandidatesQuery,
    CreateCandidateUseCase
)


@pytest.fixture
def mock_candidate_repo():
    """Mock candidate repository."""
    return Mock(spec=ICandidateRepository)


@pytest.fixture
def mock_skill_repo():
    """Mock skill repository."""
    return Mock(spec=ISkillRepository)


@pytest.fixture
def sample_candidate():
    """Sample candidate for testing."""
    return Candidate(
        id=CandidateId(1),
        name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        years_experience=5,
        education_level=EducationLevel.BACHELOR,
        skills=[
            Skill(id=1, name="Python", category="Programming", proficiency=ProficiencyLevel.EXPERT),
            Skill(id=2, name="FastAPI", category="Framework", proficiency=ProficiencyLevel.ADVANCED)
        ],
        github_username="johndoe",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestGetCandidateUseCase:
    """Test suite for GetCandidateUseCase."""
    
    @pytest.mark.asyncio
    async def test_get_candidate_success(self, mock_candidate_repo, sample_candidate):
        """Test successful candidate retrieval."""
        # Arrange
        mock_candidate_repo.get_by_id = AsyncMock(return_value=sample_candidate)
        use_case = GetCandidateUseCase(mock_candidate_repo)
        query = GetCandidateQuery(candidate_id=1)
        
        # Act
        result = await use_case.execute(query)
        
        # Assert
        assert result == sample_candidate
        mock_candidate_repo.get_by_id.assert_called_once_with(CandidateId(1))
    
    @pytest.mark.asyncio
    async def test_get_candidate_not_found(self, mock_candidate_repo):
        """Test candidate not found scenario."""
        # Arrange
        mock_candidate_repo.get_by_id = AsyncMock(return_value=None)
        use_case = GetCandidateUseCase(mock_candidate_repo)
        query = GetCandidateQuery(candidate_id=999)
        
        # Act
        result = await use_case.execute(query)
        
        # Assert
        assert result is None
        mock_candidate_repo.get_by_id.assert_called_once_with(CandidateId(999))


class TestListCandidatesUseCase:
    """Test suite for ListCandidatesUseCase."""
    
    @pytest.mark.asyncio
    async def test_list_candidates_with_pagination(self, mock_candidate_repo, sample_candidate):
        """Test listing candidates with pagination."""
        # Arrange
        mock_candidates = [sample_candidate]
        mock_candidate_repo.get_all = AsyncMock(return_value=mock_candidates)
        use_case = ListCandidatesUseCase(mock_candidate_repo)
        query = ListCandidatesQuery(skip=0, limit=20)
        
        # Act
        result = await use_case.execute(query)
        
        # Assert
        assert len(result) == 1
        assert result[0] == sample_candidate
        mock_candidate_repo.get_all.assert_called_once_with(skip=0, limit=20)
    
    @pytest.mark.asyncio
    async def test_list_candidates_with_score_filter(self, mock_candidate_repo, sample_candidate):
        """Test filtering candidates by minimum score."""
        # Arrange
        mock_candidates = [sample_candidate]
        mock_candidate_repo.get_all = AsyncMock(return_value=mock_candidates)
        use_case = ListCandidatesUseCase(mock_candidate_repo)
        query = ListCandidatesQuery(skip=0, limit=20, min_score=75.0)
        
        # Act
        result = await use_case.execute(query)
        
        # Assert
        # Sample candidate has 5 years experience = 80.0 score
        assert len(result) == 1
        assert result[0].calculate_experience_score() >= 75.0


class TestCreateCandidateUseCase:
    """Test suite for CreateCandidateUseCase."""
    
    @pytest.mark.asyncio
    async def test_create_candidate_success(self, mock_candidate_repo):
        """Test successful candidate creation."""
        # Arrange
        new_candidate = Candidate(
            id=None,
            name="Jane Smith",
            email="jane@example.com",
            phone="+1987654321",
            years_experience=3,
            education_level=EducationLevel.MASTER,
            skills=[],
            github_username="janesmith",
            created_at=None,
            updated_at=None
        )
        mock_candidate_repo.find_by_email = AsyncMock(return_value=None)
        mock_candidate_repo.save = AsyncMock(return_value=CandidateId(2))
        use_case = CreateCandidateUseCase(mock_candidate_repo)
        
        # Act
        result = await use_case.execute(new_candidate)
        
        # Assert
        assert result == CandidateId(2)
        mock_candidate_repo.find_by_email.assert_called_once_with("jane@example.com")
        mock_candidate_repo.save.assert_called_once_with(new_candidate)
    
    @pytest.mark.asyncio
    async def test_create_candidate_duplicate_email(self, mock_candidate_repo, sample_candidate):
        """Test duplicate email validation."""
        # Arrange
        new_candidate = Candidate(
            id=None,
            name="Another John",
            email="john@example.com",  # Same email as existing
            phone="+1111111111",
            years_experience=2,
            education_level=EducationLevel.BACHELOR,
            skills=[],
            github_username="anotherjohn",
            created_at=None,
            updated_at=None
        )
        mock_candidate_repo.find_by_email = AsyncMock(return_value=sample_candidate)
        use_case = CreateCandidateUseCase(mock_candidate_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(new_candidate)
        
        mock_candidate_repo.find_by_email.assert_called_once_with("john@example.com")


class TestCandidateEntity:
    """Test suite for Candidate entity business logic."""
    
    def test_calculate_experience_score_expert(self):
        """Test score calculation for 10+ years experience."""
        candidate = Candidate(
            id=None,
            name="Expert Dev",
            email="expert@example.com",
            phone=None,
            years_experience=15,
            education_level=EducationLevel.PHD,
            skills=[],
            github_username=None,
            created_at=None,
            updated_at=None
        )
        
        assert candidate.calculate_experience_score() == 100.0
    
    def test_calculate_experience_score_mid_level(self):
        """Test score calculation for 5-9 years experience."""
        candidate = Candidate(
            id=None,
            name="Mid Dev",
            email="mid@example.com",
            phone=None,
            years_experience=7,
            education_level=EducationLevel.BACHELOR,
            skills=[],
            github_username=None,
            created_at=None,
            updated_at=None
        )
        
        # 80.0 + (7-5)*4.0 = 88.0
        assert candidate.calculate_experience_score() == 88.0
    
    def test_validate_empty_name(self):
        """Test validation for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            Candidate(
                id=None,
                name="",
                email="test@example.com",
                phone=None,
                years_experience=5,
                education_level=EducationLevel.BACHELOR,
                skills=[],
                github_username=None,
                created_at=None,
                updated_at=None
            )
    
    def test_validate_invalid_email(self):
        """Test validation for invalid email."""
        with pytest.raises(ValueError, match="Invalid email"):
            Candidate(
                id=None,
                name="Test User",
                email="invalid-email",
                phone=None,
                years_experience=5,
                education_level=EducationLevel.BACHELOR,
                skills=[],
                github_username=None,
                created_at=None,
                updated_at=None
            )
    
    def test_validate_negative_experience(self):
        """Test validation for negative experience."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Candidate(
                id=None,
                name="Test User",
                email="test@example.com",
                phone=None,
                years_experience=-1,
                education_level=EducationLevel.BACHELOR,
                skills=[],
                github_username=None,
                created_at=None,
                updated_at=None
            )
