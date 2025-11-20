"""
Silver Layer Loader - Load processed data into Silver tables
"""
import os
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import execute_batch, Json
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    logging.warning("psycopg2 not installed. Database operations disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SilverLoader:
    """
    Load processed resume and GitHub data into Silver layer tables.
    Handles candidates, resume_skills, github_profiles tables.
    """
    
    def __init__(self, db_config: Dict = None):
        """
        Initialize loader with database configuration.
        
        Args:
            db_config: Dict with keys: host, port, database, user, password
        """
        self.db_config = db_config or self._get_default_config()
        self.connection = None
        
        if HAS_PSYCOPG2:
            try:
                self.connection = self._connect()
                logger.info(" Database connection established")
            except Exception as e:
                logger.error(f" Failed to connect to database: {e}")
                self.connection = None
        else:
            logger.warning(" psycopg2 not available. Database operations disabled.")
    
    def _get_default_config(self) -> Dict:
        """Get default database config from environment."""
        return {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'devscout'),
            'user': os.getenv('POSTGRES_USER', 'airflow'),
            'password': os.getenv('POSTGRES_PASSWORD', 'airflow')
        }
    
    def _connect(self):
        """Establish database connection."""
        return psycopg2.connect(**self.db_config)
    
    def load_candidate(self, candidate_data: Dict) -> int:
        """
        Load candidate record to silver.candidates table.
        
        Args:
            candidate_data: Dict with candidate information
            
        Returns:
            Candidate ID (int)
        """
        if not self.connection:
            logger.error(" No database connection")
            return -1
        
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO silver.candidates (
                    candidate_name,
                    email,
                    phone,
                    years_experience,
                    education_level,
                    resume_text,
                    created_at
                ) VALUES (
                    %(name)s,
                    %(email)s,
                    %(phone)s,
                    %(years_experience)s,
                    %(education)s,
                    %(resume_text)s,
                    %(created_at)s
                )
                ON CONFLICT (email) DO UPDATE
                SET 
                    candidate_name = EXCLUDED.candidate_name,
                    years_experience = EXCLUDED.years_experience,
                    education_level = EXCLUDED.education_level,
                    resume_text = EXCLUDED.resume_text,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING candidate_id;
            """
            
            params = {
                'name': candidate_data.get('name', 'Unknown'),
                'email': candidate_data.get('email', f"candidate_{datetime.utcnow().timestamp()}@unknown.com"),
                'phone': candidate_data.get('phone'),
                'years_experience': candidate_data.get('years_experience', 0),
                'education': candidate_data.get('education', 'Not Specified'),
                'resume_text': candidate_data.get('resume_text', ''),
                'created_at': datetime.utcnow()
            }
            
            cursor.execute(query, params)
            candidate_id = cursor.fetchone()[0]
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f" Loaded candidate: {candidate_id}")
            return candidate_id
            
        except Exception as e:
            logger.error(f" Error loading candidate: {e}")
            self.connection.rollback()
            return -1
    
    def load_resume_skills(self, candidate_id: int, skills: List[str],
                          skills_by_category: Dict = None) -> int:
        """
        Load skills for a candidate to silver.resume_skills table.
        
        Args:
            candidate_id: Candidate ID
            skills: List of skill names
            skills_by_category: Optional dict of skills organized by category
            
        Returns:
            Number of skills inserted
        """
        if not self.connection:
            logger.error(" No database connection")
            return 0
        
        try:
            cursor = self.connection.cursor()
            
            # Delete existing skills for this candidate
            cursor.execute(
                "DELETE FROM silver.resume_skills WHERE candidate_id = %s",
                (candidate_id,)
            )
            
            # Prepare batch insert
            query = """
                INSERT INTO silver.resume_skills (
                    candidate_id,
                    skill_name,
                    skill_category,
                    proficiency_level,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s
                )
            """
            
            # Build skill records
            skill_records = []
            for skill in skills:
                category = self._get_skill_category(skill, skills_by_category)
                proficiency = self._estimate_proficiency(skill, candidate_id)
                
                skill_records.append((
                    candidate_id,
                    skill,
                    category,
                    proficiency,
                    datetime.utcnow()
                ))
            
            # Batch insert
            execute_batch(cursor, query, skill_records)
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f" Loaded {len(skill_records)} skills for candidate {candidate_id}")
            return len(skill_records)
            
        except Exception as e:
            logger.error(f" Error loading skills: {e}")
            self.connection.rollback()
            return 0
    
    def load_github_profile(self, candidate_id: int, 
                           github_data: Dict,
                           metrics: Dict = None) -> bool:
        """
        Load GitHub profile data to silver.github_profiles table.
        
        Args:
            candidate_id: Candidate ID
            github_data: GitHub stats dict from GitHubEnricher
            metrics: Optional metrics dict from MetricsCalculator
            
        Returns:
            Success boolean
        """
        if not self.connection:
            logger.error(" No database connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO silver.github_profiles (
                    candidate_id,
                    github_username,
                    total_repos,
                    total_stars,
                    total_forks,
                    followers_count,
                    contributions_90_days,
                    top_language,
                    languages_json,
                    code_quality_score,
                    contribution_score,
                    impact_score,
                    created_at
                ) VALUES (
                    %(candidate_id)s,
                    %(username)s,
                    %(total_repos)s,
                    %(total_stars)s,
                    %(total_forks)s,
                    %(followers)s,
                    %(commits_90_days)s,
                    %(top_language)s,
                    %(languages_json)s,
                    %(code_quality_score)s,
                    %(contribution_score)s,
                    %(impact_score)s,
                    %(created_at)s
                )
                ON CONFLICT (candidate_id) DO UPDATE
                SET
                    github_username = EXCLUDED.github_username,
                    total_repos = EXCLUDED.total_repos,
                    total_stars = EXCLUDED.total_stars,
                    total_forks = EXCLUDED.total_forks,
                    followers_count = EXCLUDED.followers_count,
                    contributions_90_days = EXCLUDED.contributions_90_days,
                    top_language = EXCLUDED.top_language,
                    languages_json = EXCLUDED.languages_json,
                    code_quality_score = EXCLUDED.code_quality_score,
                    contribution_score = EXCLUDED.contribution_score,
                    impact_score = EXCLUDED.impact_score,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            params = {
                'candidate_id': candidate_id,
                'username': github_data.get('username'),
                'total_repos': github_data.get('total_repos', 0),
                'total_stars': github_data.get('total_stars', 0),
                'total_forks': github_data.get('total_forks', 0),
                'followers': github_data.get('followers', 0),
                'commits_90_days': github_data.get('commits_90_days', 0),
                'top_language': github_data.get('top_language'),
                'languages_json': Json(github_data.get('languages', {})),
                'code_quality_score': metrics.get('code_quality_score', 0) if metrics else 0,
                'contribution_score': metrics.get('contribution_score', 0) if metrics else 0,
                'impact_score': metrics.get('impact_score', 0) if metrics else 0,
                'created_at': datetime.utcnow()
            }
            
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            
            logger.info(f" Loaded GitHub profile for candidate {candidate_id}")
            return True
            
        except Exception as e:
            logger.error(f" Error loading GitHub profile: {e}")
            self.connection.rollback()
            return False
    
    def _get_skill_category(self, skill: str, 
                           skills_by_category: Dict = None) -> str:
        """Determine skill category."""
        if skills_by_category:
            for category, category_skills in skills_by_category.items():
                if skill in category_skills:
                    return category.replace('_', ' ').title()
        
        return 'General'
    
    def _estimate_proficiency(self, skill: str, candidate_id: int) -> str:
        """
        Estimate proficiency level (placeholder logic).
        In production, this could use context from resume text.
        """
        # Simple heuristic: return 'Advanced' for now
        return 'Advanced'
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info(" Database connection closed")


# Example usage
if __name__ == "__main__":
    loader = SilverLoader()
    
    # Sample candidate data
    candidate_data = {
        'name': 'Jane Doe',
        'email': 'jane.doe@example.com',
        'phone': '555-123-4567',
        'years_experience': 5,
        'education': 'Bachelors',
        'resume_text': 'Senior Data Engineer with expertise in...'
    }
    
    # Load candidate
    candidate_id = loader.load_candidate(candidate_data)
    print(f" Candidate ID: {candidate_id}")
    
    # Load skills
    skills = ['Python', 'Apache Spark', 'Kafka', 'AWS', 'Docker']
    skills_count = loader.load_resume_skills(candidate_id, skills)
    print(f" Loaded {skills_count} skills")
    
    # Load GitHub profile
    github_data = {
        'username': 'janedoe',
        'total_repos': 25,
        'total_stars': 150,
        'total_forks': 30,
        'followers': 45,
        'commits_90_days': 85,
        'top_language': 'Python',
        'languages': {'Python': 15, 'Java': 5, 'JavaScript': 5}
    }
    
    metrics = {
        'code_quality_score': 75.5,
        'contribution_score': 82.3,
        'impact_score': 68.9
    }
    
    success = loader.load_github_profile(candidate_id, github_data, metrics)
    print(f" GitHub profile loaded: {success}")
    
    loader.close()
