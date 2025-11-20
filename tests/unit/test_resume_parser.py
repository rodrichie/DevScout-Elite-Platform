"""
Unit tests for Resume Parser
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from parsers.resume_parser import ResumeParser


class TestResumeParser(unittest.TestCase):
    """Test cases for ResumeParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ResumeParser(minio_endpoint="localhost:9000")
    
    def test_initialization(self):
        """Test parser initialization."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.minio_endpoint, "localhost:9000")
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        raw_text = "  This   is  a   \n\n test!  "
        cleaned = self.parser.clean_text(raw_text)
        
        self.assertEqual(cleaned, "this is a test")
        self.assertNotIn('\n', cleaned)
        self.assertNotIn('  ', cleaned)
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        file_key = "resumes/john_doe_resume.pdf"
        metadata = self.parser.extract_metadata(file_key)
        
        self.assertIn('file_key', metadata)
        self.assertIn('file_name', metadata)
        self.assertIn('file_type', metadata)
        self.assertIn('extracted_at', metadata)
        
        self.assertEqual(metadata['file_key'], file_key)
        self.assertEqual(metadata['file_name'], "john_doe_resume.pdf")
        self.assertEqual(metadata['file_type'], ".pdf")
    
    @patch('parsers.resume_parser.PyPDF2.PdfReader')
    def test_extract_from_pdf_native(self, mock_pdf_reader):
        """Test native PDF text extraction."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample resume text"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        pdf_bytes = b"fake pdf content"
        text = self.parser._extract_from_pdf(pdf_bytes)
        
        self.assertIn("Sample resume text", text)
    
    def test_clean_text_special_characters(self):
        """Test cleaning of special characters."""
        text_with_special = "Email: john@example.com (555) 123-4567"
        cleaned = self.parser.clean_text(text_with_special)
        
        # Should preserve email and phone format characters
        self.assertIn("@", cleaned)
        self.assertIn("-", cleaned)
        self.assertIn("(", cleaned)
    
    def test_clean_text_empty_input(self):
        """Test cleaning empty text."""
        cleaned = self.parser.clean_text("")
        self.assertEqual(cleaned, "")
    
    def test_metadata_parser_version(self):
        """Test metadata includes parser version."""
        metadata = self.parser.extract_metadata("test.pdf")
        
        self.assertIn('parser_version', metadata)
        self.assertEqual(metadata['parser_version'], '1.0.0')


class TestResumeParserIntegration(unittest.TestCase):
    """Integration tests for resume parsing workflow."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.parser = ResumeParser()
    
    def test_full_extraction_workflow(self):
        """Test complete extraction workflow."""
        # This would test the full pipeline in an integration environment
        # For now, just verify the parser is properly configured
        
        self.assertIsNotNone(self.parser)
        self.assertTrue(hasattr(self.parser, 'extract_text'))
        self.assertTrue(hasattr(self.parser, 'clean_text'))
        self.assertTrue(hasattr(self.parser, 'extract_metadata'))


if __name__ == '__main__':
    unittest.main()
