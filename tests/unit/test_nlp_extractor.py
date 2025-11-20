"""
Unit tests for NLP Extractor
"""
import unittest
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from extractors.nlp_extractor import NLPExtractor


class TestNLPExtractor(unittest.TestCase):
    """Test cases for NLPExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = NLPExtractor()
    
    def test_initialization(self):
        """Test extractor initialization."""
        self.assertIsNotNone(self.extractor)
        self.assertGreater(len(self.extractor.all_skills), 0)
        self.assertIn('programming_languages', self.extractor.skills_taxonomy)
    
    def test_extract_skills(self):
        """Test skill extraction."""
        text = "experienced with python, java, and apache spark. also skilled in docker and kubernetes."
        
        skills = self.extractor._extract_skills(text)
        
        self.assertIn('Python', skills)
        self.assertIn('Java', skills)
        self.assertIn('Apache Spark', skills)
        self.assertIn('Docker', skills)
        self.assertIn('Kubernetes', skills)
    
    def test_extract_years_experience(self):
        """Test years of experience extraction."""
        text1 = "software engineer with 5 years of experience"
        text2 = "10+ years experience in data engineering"
        text3 = "experienced developer"  # No specific years
        
        years1 = self.extractor._extract_years_experience(text1)
        years2 = self.extractor._extract_years_experience(text2)
        years3 = self.extractor._extract_years_experience(text3)
        
        self.assertEqual(years1, 5)
        self.assertEqual(years2, 10)
        self.assertEqual(years3, 0)
    
    def test_extract_education(self):
        """Test education level extraction."""
        text_phd = "completed phd in computer science"
        text_masters = "master's degree in data science"
        text_bachelors = "bachelor of science in engineering"
        text_none = "completed bootcamp"
        
        self.assertEqual(self.extractor._extract_education(text_phd), "PhD")
        self.assertEqual(self.extractor._extract_education(text_masters), "Masters")
        self.assertEqual(self.extractor._extract_education(text_bachelors), "Bachelors")
        self.assertEqual(self.extractor._extract_education(text_none), "Not Specified")
    
    def test_categorize_skills(self):
        """Test skill categorization."""
        text = "python, java, apache spark, postgresql, aws, docker"
        
        categorized = self.extractor._categorize_skills(text)
        
        self.assertIn('programming_languages', categorized)
        self.assertIn('data_engineering', categorized)
        self.assertIn('databases', categorized)
        self.assertIn('cloud_platforms', categorized)
        self.assertIn('devops', categorized)
    
    def test_extract_contact_info(self):
        """Test contact information extraction."""
        text = """
        John Doe
        Email: john.doe@example.com
        Phone: 555-123-4567
        """
        
        contact = self.extractor._extract_contact_info(text)
        
        self.assertIn('email', contact)
        self.assertIn('phone', contact)
        self.assertEqual(contact['email'], 'john.doe@example.com')
        self.assertEqual(contact['phone'], '555-123-4567')
    
    def test_calculate_skill_score(self):
        """Test skill match score calculation."""
        extracted = ['Python', 'Java', 'Spark', 'Docker']
        required = ['Python', 'Spark', 'Kubernetes']
        
        score = self.extractor.calculate_skill_score(extracted, required)
        
        # Should match 2 out of 3 required skills
        self.assertEqual(score, 0.67)
    
    def test_extract_certifications(self):
        """Test certification extraction."""
        text = "aws certified solutions architect, pmp certified, scrum master"
        
        certs = self.extractor._extract_certifications(text)
        
        self.assertGreater(len(certs), 0)
        self.assertTrue(any('aws' in cert.lower() for cert in certs))
    
    def test_extract_entities_full(self):
        """Test full entity extraction."""
        sample_text = """
        Senior Data Engineer with 5 years of experience.
        Skills: Python, Apache Spark, Kafka, AWS
        Education: Master's in Computer Science
        Certifications: AWS Certified
        Email: test@example.com
        """
        
        entities = self.extractor.extract_entities(sample_text)
        
        self.assertIn('skills', entities)
        self.assertIn('years_experience', entities)
        self.assertIn('education', entities)
        self.assertIn('contact_info', entities)
        
        self.assertGreater(len(entities['skills']), 0)
        self.assertEqual(entities['years_experience'], 5)
        self.assertEqual(entities['education'], 'Masters')


if __name__ == '__main__':
    unittest.main()
