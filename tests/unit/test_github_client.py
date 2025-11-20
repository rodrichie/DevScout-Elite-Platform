"""
Unit tests for GitHub Client
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from extractors.github_client import GitHubEnricher


class TestGitHubEnricher(unittest.TestCase):
    """Test cases for GitHubEnricher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = GitHubEnricher(github_token="fake_token")
    
    def test_initialization(self):
        """Test client initialization."""
        self.assertIsNotNone(self.enricher)
        self.assertEqual(self.enricher.base_url, 'https://api.github.com')
        self.assertIn('Authorization', self.enricher.headers)
    
    @patch('requests.get')
    def test_fetch_user_profile_success(self, mock_get):
        """Test successful user profile fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'login': 'testuser',
            'name': 'Test User',
            'bio': 'Software Engineer',
            'public_repos': 25,
            'followers': 100,
            'following': 50
        }
        mock_get.return_value = mock_response
        
        profile = self.enricher.fetch_user_profile('testuser')
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile['username'], 'testuser')
        self.assertEqual(profile['public_repos'], 25)
        self.assertEqual(profile['followers'], 100)
    
    @patch('requests.get')
    def test_fetch_user_profile_not_found(self, mock_get):
        """Test user profile not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        profile = self.enricher.fetch_user_profile('nonexistent')
        
        self.assertIsNone(profile)
    
    @patch('requests.get')
    def test_fetch_user_repos(self, mock_get):
        """Test repo fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'name': 'test-repo',
                'full_name': 'testuser/test-repo',
                'language': 'Python',
                'stargazers_count': 50,
                'forks_count': 10,
                'fork': False
            }
        ]
        mock_get.return_value = mock_response
        
        repos = self.enricher.fetch_user_repos('testuser', max_repos=10)
        
        self.assertGreater(len(repos), 0)
        self.assertEqual(repos[0]['name'], 'test-repo')
        self.assertEqual(repos[0]['language'], 'Python')
        self.assertEqual(repos[0]['stars'], 50)
    
    def test_calculate_account_age(self):
        """Test account age calculation."""
        profile = {
            'created_at': '2020-01-01T00:00:00Z'
        }
        
        age = self.enricher._calculate_account_age(profile)
        
        self.assertGreater(age, 1000)  # Should be more than 1000 days
    
    @patch('requests.get')
    def test_check_rate_limit(self, mock_get):
        """Test rate limit checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'resources': {
                'core': {
                    'limit': 5000,
                    'remaining': 4500,
                    'reset': 1640000000
                }
            }
        }
        mock_get.return_value = mock_response
        
        rate_limit = self.enricher.check_rate_limit()
        
        self.assertEqual(rate_limit['limit'], 5000)
        self.assertEqual(rate_limit['remaining'], 4500)


if __name__ == '__main__':
    unittest.main()
