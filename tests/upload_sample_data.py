"""
Upload Sample Data to DevScout Elite Platform
==============================================

This script uploads sample resumes and test data to the platform.

Run: python tests/upload_sample_data.py
"""

import os
import io
import logging
from datetime import datetime
from minio import Minio
from minio.error import S3Error

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataUploader:
    """Upload sample data to MinIO and trigger processing."""
    
    def __init__(self):
        self.minio_client = Minio(
            os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin'),
            secret_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin'),
            secure=False
        )
        self.bucket_name = "bronze-resumes"
    
    def setup_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to create bucket: {str(e)}")
            return False
    
    def upload_sample_resumes(self):
        """Upload sample resume files."""
        sample_data_dir = os.path.join('tests', 'sample_data')
        
        if not os.path.exists(sample_data_dir):
            logger.warning(f"Sample data directory not found: {sample_data_dir}")
            return False
        
        uploaded = 0
        for filename in os.listdir(sample_data_dir):
            if filename.endswith('.txt') or filename.endswith('.pdf'):
                filepath = os.path.join(sample_data_dir, filename)
                try:
                    # Upload file
                    self.minio_client.fput_object(
                        self.bucket_name,
                        filename,
                        filepath
                    )
                    logger.info(f"Uploaded: {filename}")
                    uploaded += 1
                except S3Error as e:
                    logger.error(f"Failed to upload {filename}: {str(e)}")
        
        logger.info(f"Total files uploaded: {uploaded}")
        return uploaded > 0
    
    def create_synthetic_resumes(self):
        """Create additional synthetic resume data."""
        candidates = [
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@example.com',
                'skills': ['Python', 'Machine Learning', 'TensorFlow', 'Pandas', 'AWS'],
                'experience': 5,
                'education': 'Master',
                'github': 'sarahjohnson'
            },
            {
                'name': 'Michael Chen',
                'email': 'michael.chen@example.com',
                'skills': ['Java', 'Spring Boot', 'Kubernetes', 'PostgreSQL', 'Kafka'],
                'experience': 8,
                'education': 'Bachelor',
                'github': 'mchen'
            },
            {
                'name': 'Emily Rodriguez',
                'email': 'emily.rodriguez@example.com',
                'skills': ['JavaScript', 'React', 'Node.js', 'MongoDB', 'Docker'],
                'experience': 4,
                'education': 'Bachelor',
                'github': 'emilyrodriguez'
            },
            {
                'name': 'David Kim',
                'email': 'david.kim@example.com',
                'skills': ['Python', 'Django', 'FastAPI', 'Redis', 'Celery', 'PostgreSQL'],
                'experience': 6,
                'education': 'Master',
                'github': 'davidkim'
            },
            {
                'name': 'Lisa Anderson',
                'email': 'lisa.anderson@example.com',
                'skills': ['Go', 'Kubernetes', 'Docker', 'Prometheus', 'Terraform'],
                'experience': 7,
                'education': 'Bachelor',
                'github': 'landerson'
            }
        ]
        
        uploaded = 0
        for candidate in candidates:
            resume_text = self.generate_resume_text(candidate)
            filename = f"resume_{candidate['name'].replace(' ', '_').lower()}.txt"
            
            try:
                # Upload as bytes
                data = resume_text.encode('utf-8')
                self.minio_client.put_object(
                    self.bucket_name,
                    filename,
                    io.BytesIO(data),
                    length=len(data),
                    content_type='text/plain'
                )
                logger.info(f"Created synthetic resume: {filename}")
                uploaded += 1
            except S3Error as e:
                logger.error(f"Failed to upload {filename}: {str(e)}")
        
        logger.info(f"Total synthetic resumes created: {uploaded}")
        return uploaded > 0
    
    def generate_resume_text(self, candidate: dict) -> str:
        """Generate resume text from candidate data."""
        skills_text = ', '.join(candidate['skills'])
        
        resume = f"""
{candidate['name']}
Software Engineer

Contact:
Email: {candidate['email']}
GitHub: github.com/{candidate['github']}

SUMMARY
Experienced software engineer with {candidate['experience']} years of expertise in modern technologies.
Passionate about building scalable systems and clean code.

EXPERIENCE

Software Engineer | Tech Company | {2024 - candidate['experience']} - Present
- Developed full-stack applications using modern frameworks
- Collaborated with cross-functional teams
- Implemented best practices and code reviews
- Technologies: {skills_text}

EDUCATION

{candidate['education']} of Science in Computer Science
University | {2024 - candidate['experience'] - 4} - {2024 - candidate['experience']}

TECHNICAL SKILLS

{skills_text}

GITHUB PROFILE
Username: {candidate['github']}
"""
        return resume.strip()
    
    def list_uploaded_files(self):
        """List all files in the bucket."""
        try:
            objects = self.minio_client.list_objects(self.bucket_name)
            files = [obj.object_name for obj in objects]
            logger.info(f"Files in bucket ({len(files)}):")
            for f in files:
                logger.info(f"  - {f}")
            return files
        except S3Error as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("DevScout Elite Platform - Sample Data Upload")
    logger.info("=" * 60)
    
    uploader = DataUploader()
    
    # Setup bucket
    if not uploader.setup_bucket():
        logger.error("Failed to setup bucket. Is MinIO running?")
        return
    
    # Upload sample resumes
    logger.info("\nUploading sample resumes...")
    uploader.upload_sample_resumes()
    
    # Create synthetic resumes
    logger.info("\nCreating synthetic resumes...")
    uploader.create_synthetic_resumes()
    
    # List all files
    logger.info("\nFinal bucket contents:")
    uploader.list_uploaded_files()
    
    logger.info("\n" + "=" * 60)
    logger.info("Upload complete!")
    logger.info("Next: Trigger Airflow DAG 'resume_etl_v1' to process resumes")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
