"""
Unit tests for Metrics Calculator
"""
import unittest
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

from extractors.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    """Test cases for MetricsCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()
        
        self.sample_stats = {
            'username': 'testuser',
            'total_repos': 50,
            'original_repos': 35,
            'forked_repos': 15,
            'total_stars': 300,
            'total_forks': 60,
            'commits_90_days': 100,
            'active_repos_90_days': 10,
            'languages': {
                'Python': 20,
                'JavaScript': 15,
                'Java': 10,
                'Go': 5
            },
            'top_language': 'Python',
            'followers': 50,
            'following': 30,
            'account_age_days': 1200
        }
    
    def test_initialization(self):
        """Test calculator initialization."""
        self.assertIsNotNone(self.calculator)
        self.assertIn('repos', self.calculator.weights)
        self.assertEqual(sum(self.calculator.weights.values()), 1.0)
    
    def test_calculate_code_quality_score(self):
        """Test code quality score calculation."""
        score = self.calculator._calculate_code_quality_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIsInstance(score, float)
    
    def test_calculate_contribution_score(self):
        """Test contribution score calculation."""
        score = self.calculator._calculate_contribution_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_impact_score(self):
        """Test impact score calculation."""
        score = self.calculator._calculate_impact_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_consistency_score(self):
        """Test consistency score calculation."""
        score = self.calculator._calculate_consistency_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_diversity_score(self):
        """Test diversity score calculation."""
        score = self.calculator._calculate_diversity_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_recency_score(self):
        """Test recency score calculation."""
        score = self.calculator._calculate_recency_score(self.sample_stats)
        
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_calculate_all_metrics(self):
        """Test complete metrics calculation."""
        metrics = self.calculator.calculate_all_metrics(self.sample_stats)
        
        self.assertIn('username', metrics)
        self.assertIn('code_quality_score', metrics)
        self.assertIn('contribution_score', metrics)
        self.assertIn('impact_score', metrics)
        self.assertIn('overall_score', metrics)
        self.assertIn('raw_stats', metrics)
        
        # Overall score should be weighted average
        self.assertGreater(metrics['overall_score'], 0)
        self.assertLessEqual(metrics['overall_score'], 100)
    
    def test_calculate_percentile(self):
        """Test percentile calculation."""
        all_scores = [20, 40, 50, 60, 70, 80, 90]
        target_score = 70
        
        percentile = self.calculator.calculate_percentile(all_scores, target_score)
        
        self.assertGreaterEqual(percentile, 0)
        self.assertLessEqual(percentile, 100)
        # 70 is better than 4 out of 7, so ~57th percentile
        self.assertAlmostEqual(percentile, 57, delta=10)
    
    def test_rank_candidates(self):
        """Test candidate ranking."""
        candidates = [
            {'username': 'user1', 'overall_score': 85},
            {'username': 'user2', 'overall_score': 92},
            {'username': 'user3', 'overall_score': 78}
        ]
        
        ranked = self.calculator.rank_candidates(candidates)
        
        # Should be sorted by score descending
        self.assertEqual(ranked[0]['username'], 'user2')
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[1]['username'], 'user1')
        self.assertEqual(ranked[2]['username'], 'user3')
        
        # Check percentiles assigned
        self.assertIn('percentile_rank', ranked[0])
        self.assertGreater(ranked[0]['percentile_rank'], ranked[2]['percentile_rank'])
    
    def test_zero_repos_handling(self):
        """Test handling of zero repos edge case."""
        zero_stats = self.sample_stats.copy()
        zero_stats['total_repos'] = 0
        
        score = self.calculator._calculate_code_quality_score(zero_stats)
        
        self.assertEqual(score, 0.0)


if __name__ == '__main__':
    unittest.main()
