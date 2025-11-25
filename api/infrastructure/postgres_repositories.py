"""
Infrastructure Layer - PostgreSQL Repository Implementation
Adapters that implement domain repository interfaces
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from ..domain.entities import (
    Candidate, CandidateId, Skill, GitHubProfile,
    EducationLevel, ProficiencyLevel
)
from ..domain.repositories import (
    ICandidateRepository, ISkillRepository, IGitHubRepository
)

logger = logging.getLogger(__name__)


class PostgreSQLCandidateRepository(ICandidateRepository):
    """
    PostgreSQL implementation of candidate repository.
    Dependency Inversion Principle: Depends on abstraction (ICandidateRepository).
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    async def get_by_id(self, candidate_id: CandidateId) -> Optional[Candidate]:
        """Retrieve candidate by ID."""
        try:
            query = text("""
                SELECT 
                    candidate_id, candidate_name, email, phone,
                    years_experience, education_level, github_username,
                    created_at, updated_at
                FROM silver.candidates
                WHERE candidate_id = :id
            """)
            
            result = self._session.execute(query, {"id": candidate_id.value})
            row = result.fetchone()
            
            if not row:
                return None
            
            # Get skills for candidate
            skills = await self._get_candidate_skills(candidate_id)
            
            return Candidate(
                id=candidate_id,
                name=row[1],
                email=row[2],
                phone=row[3],
                years_experience=row[4],
                education_level=EducationLevel(row[5]),
                skills=skills,
                github_username=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
        except Exception as e:
            logger.error(f"Error fetching candidate: {e}")
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 20) -> List[Candidate]:
        """Retrieve all candidates with pagination."""
        try:
            query = text("""
                SELECT 
                    candidate_id, candidate_name, email, phone,
                    years_experience, education_level, github_username,
                    created_at, updated_at
                FROM silver.candidates
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """)
            
            result = self._session.execute(query, {"limit": limit, "skip": skip})
            rows = result.fetchall()
            
            candidates = []
            for row in rows:
                candidate_id = CandidateId(row[0])
                skills = await self._get_candidate_skills(candidate_id)
                
                candidates.append(Candidate(
                    id=candidate_id,
                    name=row[1],
                    email=row[2],
                    phone=row[3],
                    years_experience=row[4],
                    education_level=EducationLevel(row[5]),
                    skills=skills,
                    github_username=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                ))
            
            return candidates
        except Exception as e:
            logger.error(f"Error fetching candidates: {e}")
            return []
    
    async def save(self, candidate: Candidate) -> CandidateId:
        """Save or update candidate."""
        try:
            if candidate.id:
                # Update existing
                query = text("""
                    UPDATE silver.candidates
                    SET candidate_name = :name, email = :email, phone = :phone,
                        years_experience = :experience, education_level = :education,
                        github_username = :github, updated_at = NOW()
                    WHERE candidate_id = :id
                    RETURNING candidate_id
                """)
                result = self._session.execute(query, {
                    "id": candidate.id.value,
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "experience": candidate.years_experience,
                    "education": candidate.education_level.value,
                    "github": candidate.github_username
                })
            else:
                # Insert new
                query = text("""
                    INSERT INTO silver.candidates 
                    (candidate_name, email, phone, years_experience, 
                     education_level, github_username, created_at, updated_at)
                    VALUES (:name, :email, :phone, :experience, :education, 
                            :github, NOW(), NOW())
                    RETURNING candidate_id
                """)
                result = self._session.execute(query, {
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "experience": candidate.years_experience,
                    "education": candidate.education_level.value,
                    "github": candidate.github_username
                })
            
            self._session.commit()
            row = result.fetchone()
            return CandidateId(row[0])
            
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error saving candidate: {e}")
            raise
    
    async def delete(self, candidate_id: CandidateId) -> bool:
        """Delete candidate by ID."""
        try:
            query = text("DELETE FROM silver.candidates WHERE candidate_id = :id")
            self._session.execute(query, {"id": candidate_id.value})
            self._session.commit()
            return True
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error deleting candidate: {e}")
            return False
    
    async def find_by_email(self, email: str) -> Optional[Candidate]:
        """Find candidate by email."""
        try:
            query = text("""
                SELECT candidate_id FROM silver.candidates WHERE email = :email
            """)
            result = self._session.execute(query, {"email": email})
            row = result.fetchone()
            
            if row:
                return await self.get_by_id(CandidateId(row[0]))
            return None
        except Exception as e:
            logger.error(f"Error finding candidate by email: {e}")
            return None
    
    async def search(self, query: str, min_score: Optional[float] = None) -> List[Candidate]:
        """Search candidates by criteria."""
        # Implementation would use full-text search or vector search
        return await self.get_all()
    
    async def _get_candidate_skills(self, candidate_id: CandidateId) -> List[Skill]:
        """Helper to get skills for a candidate."""
        try:
            query = text("""
                SELECT skill_id, skill_name, skill_category, proficiency_level
                FROM silver.resume_skills
                WHERE candidate_id = :id
            """)
            result = self._session.execute(query, {"id": candidate_id.value})
            rows = result.fetchall()
            
            return [
                Skill(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    proficiency=ProficiencyLevel(row[3]) if row[3] else ProficiencyLevel.INTERMEDIATE
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching skills: {e}")
            return []


class PostgreSQLSkillRepository(ISkillRepository):
    """PostgreSQL implementation of skill repository."""
    
    def __init__(self, session: Session):
        self._session = session
    
    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        """Retrieve skill by ID."""
        try:
            query = text("""
                SELECT skill_id, skill_name, skill_category, proficiency_level
                FROM silver.resume_skills
                WHERE skill_id = :id
            """)
            result = self._session.execute(query, {"id": skill_id})
            row = result.fetchone()
            
            if row:
                return Skill(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    proficiency=ProficiencyLevel(row[3]) if row[3] else ProficiencyLevel.INTERMEDIATE
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching skill: {e}")
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 50) -> List[Skill]:
        """Retrieve all skills."""
        try:
            query = text("""
                SELECT DISTINCT skill_name, skill_category
                FROM silver.resume_skills
                ORDER BY skill_name
                LIMIT :limit OFFSET :skip
            """)
            result = self._session.execute(query, {"limit": limit, "skip": skip})
            rows = result.fetchall()
            
            return [
                Skill(
                    id=None,
                    name=row[0],
                    category=row[1],
                    proficiency=ProficiencyLevel.INTERMEDIATE
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching skills: {e}")
            return []
    
    async def get_by_candidate(self, candidate_id: CandidateId) -> List[Skill]:
        """Get skills for a specific candidate."""
        try:
            query = text("""
                SELECT skill_id, skill_name, skill_category, proficiency_level
                FROM silver.resume_skills
                WHERE candidate_id = :id
            """)
            result = self._session.execute(query, {"id": candidate_id.value})
            rows = result.fetchall()
            
            return [
                Skill(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    proficiency=ProficiencyLevel(row[3]) if row[3] else ProficiencyLevel.INTERMEDIATE
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching candidate skills: {e}")
            return []
    
    async def save(self, skill: Skill) -> int:
        """Save skill."""
        # Implementation details
        return 0
