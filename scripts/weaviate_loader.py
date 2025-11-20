"""
Weaviate Loader - Load candidates and skills into Weaviate for semantic search
"""
import os
import logging
from typing import List, Dict, Any
import weaviate
from weaviate.util import generate_uuid5
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://airflow:airflow@postgres:5432/devscout"
)


class WeaviateLoader:
    """Load data from PostgreSQL to Weaviate."""
    
    def __init__(self):
        """Initialize connections."""
        self.client = weaviate.Client(WEAVIATE_URL)
        self.pg_conn = psycopg2.connect(DATABASE_URL)
        
    def check_schema(self) -> bool:
        """Check if schema exists in Weaviate."""
        try:
            schema = self.client.schema.get()
            classes = [c['class'] for c in schema.get('classes', [])]
            return 'Candidate' in classes and 'Skill' in classes
        except Exception as e:
            logger.error(f"Error checking schema: {e}")
            return False
    
    def create_schema(self, schema_path: str = "/opt/airflow/weaviate/schema.json"):
        """Create Weaviate schema from JSON file."""
        try:
            import json
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Delete existing schema
            self.client.schema.delete_all()
            
            # Create new schema
            for class_obj in schema['classes']:
                self.client.schema.create_class(class_obj)
            
            logger.info("✅ Weaviate schema created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            return False
    
    def load_candidates(self, batch_size: int = 100) -> int:
        """Load candidates from PostgreSQL to Weaviate."""
        try:
            query = """
                SELECT 
                    c.candidate_id,
                    c.candidate_name,
                    c.email,
                    sc.resume_text,
                    c.years_experience,
                    c.education_level,
                    c.github_username,
                    c.all_skills,
                    COALESCE(r.overall_score, 0) as overall_score
                FROM gold.dim_candidates c
                LEFT JOIN silver.candidates sc ON c.candidate_id = sc.candidate_id
                LEFT JOIN gold.agg_candidate_rankings r ON c.candidate_id = r.candidate_id
                WHERE sc.resume_text IS NOT NULL
            """
            
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                candidates = cursor.fetchall()
            
            logger.info(f"Loading {len(candidates)} candidates to Weaviate...")
            
            # Batch import
            self.client.batch.configure(batch_size=batch_size)
            
            with self.client.batch as batch:
                for candidate in candidates:
                    properties = {
                        "candidateId": candidate['candidate_id'],
                        "candidateName": candidate['candidate_name'],
                        "email": candidate['email'],
                        "resumeText": candidate['resume_text'][:10000],  # Limit text length
                        "skills": candidate['all_skills'].split(', ') if candidate['all_skills'] else [],
                        "yearsExperience": candidate['years_experience'],
                        "educationLevel": candidate['education_level'],
                        "githubUsername": candidate['github_username'] or "",
                        "overallScore": float(candidate['overall_score'])
                    }
                    
                    # Generate consistent UUID based on candidate_id
                    uuid = generate_uuid5(candidate['candidate_id'], "Candidate")
                    
                    batch.add_data_object(
                        data_object=properties,
                        class_name="Candidate",
                        uuid=uuid
                    )
            
            logger.info(f"✅ Loaded {len(candidates)} candidates to Weaviate")
            return len(candidates)
            
        except Exception as e:
            logger.error(f"Error loading candidates: {e}")
            raise
    
    def load_skills(self, batch_size: int = 100) -> int:
        """Load skills from PostgreSQL to Weaviate."""
        try:
            query = """
                SELECT 
                    skill_name,
                    skill_category,
                    candidate_count
                FROM gold.dim_skills
                WHERE candidate_count >= 1
            """
            
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                skills = cursor.fetchall()
            
            logger.info(f"Loading {len(skills)} skills to Weaviate...")
            
            # Batch import
            self.client.batch.configure(batch_size=batch_size)
            
            with self.client.batch as batch:
                for skill in skills:
                    # Generate description for better semantic search
                    description = f"{skill['skill_name']} is a {skill['skill_category']} skill. "
                    description += f"It appears in {skill['candidate_count']} candidate profiles."
                    
                    properties = {
                        "skillName": skill['skill_name'],
                        "skillCategory": skill['skill_category'],
                        "description": description,
                        "candidateCount": skill['candidate_count']
                    }
                    
                    # Generate consistent UUID
                    uuid = generate_uuid5(skill['skill_name'], "Skill")
                    
                    batch.add_data_object(
                        data_object=properties,
                        class_name="Skill",
                        uuid=uuid
                    )
            
            logger.info(f"✅ Loaded {len(skills)} skills to Weaviate")
            return len(skills)
            
        except Exception as e:
            logger.error(f"Error loading skills: {e}")
            raise
    
    def semantic_search_candidates(
        self,
        query: str,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on candidates."""
        try:
            result = (
                self.client.query
                .get("Candidate", [
                    "candidateId", "candidateName", "email", "skills",
                    "yearsExperience", "educationLevel", "githubUsername",
                    "overallScore"
                ])
                .with_near_text({"concepts": [query]})
                .with_additional(["certainty", "distance"])
                .with_limit(limit)
                .do()
            )
            
            candidates = result.get('data', {}).get('Get', {}).get('Candidate', [])
            
            # Filter by min_score (certainty)
            filtered = [
                c for c in candidates
                if c.get('_additional', {}).get('certainty', 0) >= min_score
            ]
            
            logger.info(f"Found {len(filtered)} candidates matching query: '{query}'")
            return filtered
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    def find_similar_candidates(
        self,
        candidate_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find candidates similar to a given candidate."""
        try:
            # Get reference candidate
            result = (
                self.client.query
                .get("Candidate", ["candidateId", "resumeText"])
                .with_where({
                    "path": ["candidateId"],
                    "operator": "Equal",
                    "valueInt": candidate_id
                })
                .do()
            )
            
            candidates = result.get('data', {}).get('Get', {}).get('Candidate', [])
            if not candidates:
                return []
            
            reference_text = candidates[0]['resumeText']
            
            # Find similar
            result = (
                self.client.query
                .get("Candidate", [
                    "candidateId", "candidateName", "email", "skills",
                    "yearsExperience", "overallScore"
                ])
                .with_near_text({"concepts": [reference_text]})
                .with_additional(["certainty"])
                .with_limit(limit + 1)  # +1 to exclude self
                .do()
            )
            
            similar = result.get('data', {}).get('Get', {}).get('Candidate', [])
            
            # Exclude the reference candidate
            similar = [c for c in similar if c['candidateId'] != candidate_id][:limit]
            
            logger.info(f"Found {len(similar)} similar candidates to ID {candidate_id}")
            return similar
            
        except Exception as e:
            logger.error(f"Error finding similar candidates: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get Weaviate statistics."""
        try:
            candidate_count = (
                self.client.query
                .aggregate("Candidate")
                .with_meta_count()
                .do()
            )
            
            skill_count = (
                self.client.query
                .aggregate("Skill")
                .with_meta_count()
                .do()
            )
            
            return {
                "candidates": candidate_count['data']['Aggregate']['Candidate'][0]['meta']['count'],
                "skills": skill_count['data']['Aggregate']['Skill'][0]['meta']['count']
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"candidates": 0, "skills": 0}
    
    def close(self):
        """Close connections."""
        self.pg_conn.close()


def main():
    """Main execution function."""
    loader = WeaviateLoader()
    
    try:
        # Check/create schema
        if not loader.check_schema():
            logger.info("Creating Weaviate schema...")
            loader.create_schema()
        else:
            logger.info("Weaviate schema already exists")
        
        # Load data
        candidates_loaded = loader.load_candidates()
        skills_loaded = loader.load_skills()
        
        # Get stats
        stats = loader.get_stats()
        
        logger.info("=" * 50)
        logger.info("Weaviate Load Summary:")
        logger.info(f"  Candidates: {stats['candidates']}")
        logger.info(f"  Skills: {stats['skills']}")
        logger.info("=" * 50)
        
        # Example semantic search
        results = loader.semantic_search_candidates("senior python developer with AWS experience", limit=5)
        logger.info(f"\nExample search results: {len(results)} candidates found")
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
