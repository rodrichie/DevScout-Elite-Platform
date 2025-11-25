"""
Domain Layer - Core Business Entities
Independent of frameworks and external concerns
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class EducationLevel(str, Enum):
    """Education level enumeration."""
    HIGH_SCHOOL = "High School"
    ASSOCIATE = "Associate"
    BACHELOR = "Bachelor"
    MASTER = "Master"
    PHD = "PhD"


class ProficiencyLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


@dataclass(frozen=True)
class CandidateId:
    """Value object for Candidate ID."""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("Candidate ID must be positive")


@dataclass
class Candidate:
    """
    Core Candidate entity.
    Represents a candidate in the hiring system.
    """
    id: Optional[CandidateId]
    name: str
    email: str
    phone: Optional[str]
    years_experience: int
    education_level: EducationLevel
    skills: List['Skill']
    github_username: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Candidate name cannot be empty")
        if not self.email or '@' not in self.email:
            raise ValueError("Invalid email address")
        if self.years_experience < 0:
            raise ValueError("Years of experience cannot be negative")
    
    def add_skill(self, skill: 'Skill') -> None:
        """Add a skill to the candidate."""
        if skill not in self.skills:
            self.skills.append(skill)
    
    def calculate_experience_score(self) -> float:
        """Calculate score based on experience."""
        if self.years_experience >= 10:
            return 100.0
        elif self.years_experience >= 5:
            return 80.0 + (self.years_experience - 5) * 4.0
        else:
            return 50.0 + self.years_experience * 6.0


@dataclass
class Skill:
    """
    Skill entity.
    Represents a technical skill.
    """
    id: Optional[int]
    name: str
    category: str
    proficiency: ProficiencyLevel
    
    def __post_init__(self):
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Skill name cannot be empty")
        if not self.category:
            raise ValueError("Skill category cannot be empty")


@dataclass
class GitHubProfile:
    """
    GitHub profile entity.
    Represents a candidate's GitHub activity.
    """
    candidate_id: CandidateId
    username: str
    total_repos: int
    total_stars: int
    total_forks: int
    followers_count: int
    contributions_90_days: int
    primary_language: Optional[str]
    
    def calculate_activity_score(self) -> float:
        """Calculate GitHub activity score."""
        repo_score = min(self.total_repos * 2, 30)
        star_score = min(self.total_stars * 0.5, 25)
        follower_score = min(self.followers_count * 0.3, 20)
        contribution_score = min(self.contributions_90_days * 0.1, 25)
        
        return repo_score + star_score + follower_score + contribution_score


@dataclass
class Resume:
    """
    Resume document entity.
    Represents a parsed resume.
    """
    id: Optional[int]
    candidate_id: Optional[CandidateId]
    file_name: str
    file_path: str
    raw_text: str
    parsed_data: dict
    uploaded_at: datetime
    processed: bool = False
    
    def mark_as_processed(self) -> None:
        """Mark resume as successfully processed."""
        self.processed = True
