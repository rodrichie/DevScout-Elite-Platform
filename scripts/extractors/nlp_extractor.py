"""
NLP Extractor - Extract skills, education, experience using spaCy and pattern matching
"""
import re
import logging
from typing import Dict, List, Set
from datetime import datetime

try:
    import spacy
    HAS_SPACY = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logging.warning("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        nlp = None
except ImportError:
    HAS_SPACY = False
    nlp = None
    logging.warning("spaCy not installed. NLP features limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPExtractor:
    """
    Extract structured information from resume text using NLP.
    Identifies skills, education, years of experience, and other entities.
    """
    
    def __init__(self):
        """Initialize NLP extractor with skill taxonomy and patterns."""
        self.nlp = nlp
        
        # Comprehensive skills taxonomy (expandable)
        self.skills_taxonomy = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 
                'rust', 'kotlin', 'swift', 'ruby', 'php', 'scala', 'r'
            ],
            'data_engineering': [
                'apache spark', 'pyspark', 'apache kafka', 'kafka', 'airflow', 
                'dbt', 'databricks', 'snowflake', 'redshift', 'bigquery',
                'hadoop', 'hive', 'presto', 'flink', 'beam', 'luigi'
            ],
            'databases': [
                'postgresql', 'mysql', 'mongodb', 'cassandra', 'redis', 
                'elasticsearch', 'dynamodb', 'oracle', 'sql server', 'sqlite',
                'neo4j', 'couchbase', 'mariadb'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'amazon web services', 'google cloud',
                'microsoft azure', 'lambda', 'ec2', 's3', 'emr', 'glue',
                'azure data factory', 'cloud functions', 'cloud storage'
            ],
            'devops': [
                'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab ci', 
                'github actions', 'terraform', 'ansible', 'helm', 'circleci',
                'travis ci', 'argocd', 'prometheus', 'grafana'
            ],
            'ml_ai': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'scikit-learn', 'keras', 'mlflow', 'kubeflow', 'sagemaker',
                'nlp', 'computer vision', 'transformers', 'bert', 'gpt'
            ],
            'web_frameworks': [
                'react', 'angular', 'vue', 'node.js', 'express', 'django',
                'flask', 'fastapi', 'spring boot', 'asp.net', 'rails'
            ],
            'data_visualization': [
                'tableau', 'power bi', 'looker', 'metabase', 'superset',
                'plotly', 'matplotlib', 'seaborn', 'd3.js', 'streamlit'
            ],
            'version_control': [
                'git', 'github', 'gitlab', 'bitbucket', 'svn'
            ],
            'testing': [
                'pytest', 'junit', 'selenium', 'cypress', 'jest', 'mocha',
                'testng', 'cucumber', 'great expectations'
            ]
        }
        
        # Flatten skills for easy searching
        self.all_skills = set()
        for category, skills in self.skills_taxonomy.items():
            self.all_skills.update(skills)
        
        # Education keywords
        self.education_patterns = {
            'PhD': [r'ph\.?d', r'doctor of philosophy', r'doctorate'],
            'Masters': [r'master[\'s]?', r'm\.?s\.?', r'm\.?sc\.?', r'mba', r'meng'],
            'Bachelors': [r'bachelor[\'s]?', r'b\.?s\.?', r'b\.?sc\.?', r'b\.?a\.?', r'b\.?tech', r'undergraduate'],
            'Associate': [r'associate', r'a\.?s\.?', r'diploma'],
            'High School': [r'high school', r'secondary', r'diploma']
        }
        
        logger.info(f"✅ NLP Extractor initialized with {len(self.all_skills)} skills")
    
    def extract_entities(self, text: str) -> Dict:
        """
        Extract all entities from resume text.
        
        Args:
            text: Resume text (cleaned)
            
        Returns:
            Dictionary with extracted entities
        """
        text_lower = text.lower()
        
        entities = {
            'skills': self._extract_skills(text_lower),
            'skills_by_category': self._categorize_skills(text_lower),
            'years_experience': self._extract_years_experience(text_lower),
            'education': self._extract_education(text_lower),
            'certifications': self._extract_certifications(text_lower),
            'companies': self._extract_companies(text),
            'contact_info': self._extract_contact_info(text),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Extracted {len(entities['skills'])} skills, "
                   f"{entities['years_experience']} years exp, "
                   f"{entities['education']} education")
        
        return entities
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract all matching skills from text."""
        found_skills = []
        
        for skill in self.all_skills:
            # Use word boundaries for exact matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                # Capitalize properly
                found_skills.append(skill.title())
        
        return sorted(list(set(found_skills)))
    
    def _categorize_skills(self, text: str) -> Dict[str, List[str]]:
        """Categorize found skills by domain."""
        categorized = {}
        
        for category, skills in self.skills_taxonomy.items():
            found = []
            for skill in skills:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    found.append(skill.title())
            
            if found:
                categorized[category] = sorted(found)
        
        return categorized
    
    def _extract_years_experience(self, text: str) -> int:
        """
        Extract years of experience from text.
        Looks for patterns like "5 years of experience", "5+ years", "5 yrs"
        """
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
            r'(?:experience|exp)(?:\s+of)?\s+(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:in|with)',
        ]
        
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                years = int(match)
                if years > max_years and years < 50:  # Sanity check
                    max_years = years
        
        return max_years
    
    def _extract_education(self, text: str) -> str:
        """Extract highest education level."""
        for level, patterns in self.education_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return level
        
        return 'Not Specified'
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract professional certifications."""
        cert_keywords = [
            'aws certified', 'azure certified', 'gcp certified',
            'pmp', 'scrum master', 'csm', 'pmi', 'cissp',
            'cka', 'ckad', 'tensorflow certified', 'databricks certified'
        ]
        
        found_certs = []
        for cert in cert_keywords:
            if cert in text:
                found_certs.append(cert.title())
        
        return found_certs
    
    def _extract_companies(self, text: str) -> List[str]:
        """
        Extract company names using spaCy NER if available.
        Falls back to pattern matching for well-known companies.
        """
        companies = []
        
        if self.nlp:
            try:
                doc = self.nlp(text[:10000])  # Limit text length for performance
                companies = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
            except Exception as e:
                logger.warning(f"spaCy NER failed: {e}")
        
        # Fallback: well-known companies
        known_companies = [
            'google', 'microsoft', 'amazon', 'facebook', 'meta', 'apple',
            'netflix', 'uber', 'airbnb', 'twitter', 'linkedin', 'salesforce',
            'oracle', 'ibm', 'intel', 'nvidia', 'adobe', 'spotify'
        ]
        
        text_lower = text.lower()
        for company in known_companies:
            if company in text_lower and company.title() not in companies:
                companies.append(company.title())
        
        return companies[:10]  # Limit to top 10
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract email and phone number."""
        contact = {}
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group()
        
        # Phone pattern (US format)
        phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            contact['phone'] = phone_match.group()
        
        return contact
    
    def calculate_skill_score(self, extracted_skills: List[str], 
                            required_skills: List[str]) -> float:
        """
        Calculate match percentage between extracted and required skills.
        
        Args:
            extracted_skills: Skills found in resume
            required_skills: Skills required for job
            
        Returns:
            Match score (0-1)
        """
        if not required_skills:
            return 1.0
        
        extracted_set = set(s.lower() for s in extracted_skills)
        required_set = set(s.lower() for s in required_skills)
        
        matches = len(extracted_set.intersection(required_set))
        score = matches / len(required_set)
        
        return round(score, 2)


# Example usage
if __name__ == "__main__":
    extractor = NLPExtractor()
    
    sample_text = """
    Senior Data Engineer with 5 years of experience in building scalable data pipelines.
    
    Skills: Python, Apache Spark, Kafka, Airflow, AWS, Docker, Kubernetes
    
    Education: B.Sc Computer Science, Stanford University
    
    Certifications: AWS Certified Solutions Architect, Databricks Certified
    
    Experience:
    - Data Engineer at Google (2020-2023)
    - Software Engineer at Microsoft (2018-2020)
    
    Contact: john.doe@email.com | 555-123-4567
    """
    
    entities = extractor.extract_entities(sample_text)
    
    print("\n📊 Extracted Entities:")
    print(f"Skills: {entities['skills']}")
    print(f"Experience: {entities['years_experience']} years")
    print(f"Education: {entities['education']}")
    print(f"Certifications: {entities['certifications']}")
    print(f"Companies: {entities['companies']}")
    print(f"Contact: {entities['contact_info']}")
