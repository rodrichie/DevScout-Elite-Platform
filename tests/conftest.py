# Test fixtures and configuration
import os
import sys
import pytest

# Add scripts to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    Senior Data Engineer
    
    Email: john.doe@example.com
    Phone: 555-123-4567
    GitHub: johndoe
    
    SUMMARY
    Senior Data Engineer with 7 years of experience building scalable data pipelines
    and analytics platforms. Expert in Python, Apache Spark, and cloud technologies.
    
    SKILLS
    Programming: Python, Java, Scala, SQL
    Big Data: Apache Spark, Kafka, Airflow, Hadoop
    Cloud: AWS (S3, EMR, Glue, Redshift), Azure, GCP
    Databases: PostgreSQL, MongoDB, Cassandra, Redis
    DevOps: Docker, Kubernetes, Terraform, CI/CD
    
    EXPERIENCE
    Senior Data Engineer | Tech Corp | 2020 - Present
    - Designed and implemented data lakehouse architecture processing 10TB+ daily
    - Built real-time streaming pipelines with Kafka and Spark Streaming
    - Reduced data processing costs by 40% through optimization
    
    Data Engineer | StartupXYZ | 2018 - 2020
    - Developed ETL pipelines using Airflow and Python
    - Migrated legacy data warehouse to cloud-based solution
    
    EDUCATION
    Master of Science in Computer Science
    Stanford University, 2018
    
    Bachelor of Science in Software Engineering
    MIT, 2016
    
    CERTIFICATIONS
    - AWS Certified Solutions Architect
    - Databricks Certified Data Engineer
    - Google Cloud Professional Data Engineer
    """

@pytest.fixture
def sample_github_stats():
    """Sample GitHub statistics for testing."""
    return {
        'username': 'johndoe',
        'total_repos': 45,
        'original_repos': 30,
        'forked_repos': 15,
        'total_stars': 250,
        'total_forks': 45,
        'commits_90_days': 120,
        'active_repos_90_days': 12,
        'languages': {
            'Python': 18,
            'Java': 10,
            'JavaScript': 8,
            'Go': 5,
            'Scala': 4
        },
        'top_language': 'Python',
        'followers': 65,
        'following': 40,
        'account_age_days': 1500
    }

@pytest.fixture
def db_config():
    """Database configuration for testing."""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'devscout_test'),
        'user': os.getenv('POSTGRES_USER', 'airflow'),
        'password': os.getenv('POSTGRES_PASSWORD', 'airflow')
    }
