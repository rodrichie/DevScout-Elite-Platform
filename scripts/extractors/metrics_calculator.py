"""
Metrics Calculator - Calculate engineering quality metrics from GitHub data
"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculate data engineering quality metrics from GitHub activity.
    Metrics include code quality score, contribution consistency, impact score.
    """
    
    def __init__(self):
        """Initialize metrics calculator with scoring weights."""
        self.weights = {
            'repos': 0.15,
            'stars': 0.20,
            'commits': 0.25,
            'languages': 0.15,
            'consistency': 0.15,
            'recency': 0.10
        }
        
        logger.info("✅ Metrics calculator initialized")
    
    def calculate_all_metrics(self, github_stats: Dict) -> Dict:
        """
        Calculate all engineering metrics from GitHub stats.
        
        Args:
            github_stats: Dict from GitHubEnricher.fetch_contribution_stats()
            
        Returns:
            Dict with calculated metrics
        """
        metrics = {
            'username': github_stats.get('username'),
            'code_quality_score': self._calculate_code_quality_score(github_stats),
            'contribution_score': self._calculate_contribution_score(github_stats),
            'impact_score': self._calculate_impact_score(github_stats),
            'consistency_score': self._calculate_consistency_score(github_stats),
            'diversity_score': self._calculate_diversity_score(github_stats),
            'recency_score': self._calculate_recency_score(github_stats),
            'overall_score': 0.0,  # Will be calculated
            'percentile_rank': None,  # Requires comparison with other candidates
            'calculated_at': datetime.utcnow().isoformat()
        }
        
        # Calculate overall score (weighted average)
        metrics['overall_score'] = self._calculate_overall_score(metrics)
        
        # Add raw stats for reference
        metrics['raw_stats'] = {
            'total_repos': github_stats.get('total_repos', 0),
            'total_stars': github_stats.get('total_stars', 0),
            'total_commits': github_stats.get('commits_90_days', 0),
            'languages_count': len(github_stats.get('languages', {})),
            'top_language': github_stats.get('top_language'),
            'followers': github_stats.get('followers', 0)
        }
        
        logger.info(f"✅ Calculated metrics for {metrics['username']}: "
                   f"Overall={metrics['overall_score']:.2f}")
        
        return metrics
    
    def _calculate_code_quality_score(self, stats: Dict) -> float:
        """
        Calculate code quality score based on stars, forks, and repo health.
        
        Score components:
        - Stars per repo (popularity indicator)
        - Forks per repo (usefulness indicator)
        - Original vs forked repos ratio
        
        Returns: 0-100
        """
        total_repos = stats.get('total_repos', 0)
        original_repos = stats.get('original_repos', 0)
        total_stars = stats.get('total_stars', 0)
        total_forks = stats.get('total_forks', 0)
        
        if total_repos == 0:
            return 0.0
        
        # Stars per repo (capped at 50 stars/repo for scoring)
        stars_per_repo = min(total_stars / total_repos, 50) / 50 * 30
        
        # Forks per repo (capped at 10 forks/repo)
        forks_per_repo = min(total_forks / total_repos, 10) / 10 * 20
        
        # Original vs forked ratio
        original_ratio = original_repos / total_repos * 30
        
        # Active repos indicator (has commits in last 90 days)
        active_repos = stats.get('active_repos_90_days', 0)
        activity_score = min(active_repos / max(original_repos, 1), 1.0) * 20
        
        score = stars_per_repo + forks_per_repo + original_ratio + activity_score
        
        return round(score, 2)
    
    def _calculate_contribution_score(self, stats: Dict) -> float:
        """
        Calculate contribution score based on commit frequency and volume.
        
        Score components:
        - Total commits in last 90 days
        - Number of active repos
        - Commit consistency
        
        Returns: 0-100
        """
        commits_90d = stats.get('commits_90_days', 0)
        active_repos = stats.get('active_repos_90_days', 0)
        
        # Commits score (capped at 200 commits for 90 days)
        commits_score = min(commits_90d / 200, 1.0) * 50
        
        # Active repos score (capped at 10 repos)
        repos_score = min(active_repos / 10, 1.0) * 30
        
        # Frequency score (commits per repo)
        if active_repos > 0:
            frequency = commits_90d / active_repos
            frequency_score = min(frequency / 20, 1.0) * 20
        else:
            frequency_score = 0
        
        score = commits_score + repos_score + frequency_score
        
        return round(score, 2)
    
    def _calculate_impact_score(self, stats: Dict) -> float:
        """
        Calculate impact score based on followers, stars, and community engagement.
        
        Score components:
        - Followers (influence)
        - Total stars (reach)
        - Forks (adoption)
        
        Returns: 0-100
        """
        followers = stats.get('followers', 0)
        total_stars = stats.get('total_stars', 0)
        total_forks = stats.get('total_forks', 0)
        
        # Followers score (capped at 100 followers)
        followers_score = min(followers / 100, 1.0) * 40
        
        # Stars score (capped at 500 stars)
        stars_score = min(total_stars / 500, 1.0) * 40
        
        # Forks score (capped at 100 forks)
        forks_score = min(total_forks / 100, 1.0) * 20
        
        score = followers_score + stars_score + forks_score
        
        return round(score, 2)
    
    def _calculate_consistency_score(self, stats: Dict) -> float:
        """
        Calculate consistency score based on account age and activity pattern.
        
        Score components:
        - Account longevity
        - Sustained activity (commits in recent period)
        - Repo maintenance (recent updates)
        
        Returns: 0-100
        """
        account_age_days = stats.get('account_age_days', 0)
        commits_90d = stats.get('commits_90_days', 0)
        active_repos = stats.get('active_repos_90_days', 0)
        
        # Longevity score (capped at 3 years = 1095 days)
        longevity_score = min(account_age_days / 1095, 1.0) * 40
        
        # Activity consistency (has recent commits)
        if commits_90d > 0:
            activity_score = 30
        elif commits_90d > 10:
            activity_score = 40
        else:
            activity_score = 10
        
        # Maintenance score (actively maintaining multiple repos)
        maintenance_score = min(active_repos / 5, 1.0) * 30
        
        score = longevity_score + activity_score + maintenance_score
        
        return round(score, 2)
    
    def _calculate_diversity_score(self, stats: Dict) -> float:
        """
        Calculate diversity score based on language variety and breadth.
        
        Score components:
        - Number of languages used
        - Distribution across languages
        
        Returns: 0-100
        """
        languages = stats.get('languages', {})
        
        if not languages:
            return 0.0
        
        num_languages = len(languages)
        
        # Language count score (capped at 10 languages)
        count_score = min(num_languages / 10, 1.0) * 60
        
        # Distribution score (penalize single-language developers)
        total_repos = sum(languages.values())
        if total_repos > 0:
            max_lang_count = max(languages.values())
            diversity_ratio = 1 - (max_lang_count / total_repos)
            distribution_score = diversity_ratio * 40
        else:
            distribution_score = 0
        
        score = count_score + distribution_score
        
        return round(score, 2)
    
    def _calculate_recency_score(self, stats: Dict) -> float:
        """
        Calculate recency score based on how recent the activity is.
        
        Score components:
        - Has activity in last 90 days
        - Frequency of recent activity
        
        Returns: 0-100
        """
        commits_90d = stats.get('commits_90_days', 0)
        
        if commits_90d == 0:
            return 0.0
        
        # Has recent activity (binary)
        has_activity = 40
        
        # Frequency of activity
        frequency_score = min(commits_90d / 100, 1.0) * 60
        
        score = has_activity + frequency_score
        
        return round(score, 2)
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """
        Calculate overall weighted score from component scores.
        
        Args:
            metrics: Dict with individual metric scores
            
        Returns:
            Weighted overall score (0-100)
        """
        overall = (
            metrics['code_quality_score'] * 0.25 +
            metrics['contribution_score'] * 0.25 +
            metrics['impact_score'] * 0.15 +
            metrics['consistency_score'] * 0.15 +
            metrics['diversity_score'] * 0.10 +
            metrics['recency_score'] * 0.10
        )
        
        return round(overall, 2)
    
    def calculate_percentile(self, candidate_scores: List[float], 
                            target_score: float) -> int:
        """
        Calculate percentile rank for a candidate score.
        
        Args:
            candidate_scores: List of all candidate overall scores
            target_score: Score to calculate percentile for
            
        Returns:
            Percentile rank (0-100)
        """
        if not candidate_scores:
            return 50  # Default to median
        
        sorted_scores = sorted(candidate_scores)
        below_count = sum(1 for s in sorted_scores if s < target_score)
        
        percentile = (below_count / len(sorted_scores)) * 100
        
        return int(percentile)
    
    def rank_candidates(self, all_metrics: List[Dict]) -> List[Dict]:
        """
        Rank candidates by overall score and assign percentiles.
        
        Args:
            all_metrics: List of metric dicts for all candidates
            
        Returns:
            Sorted list with rankings
        """
        # Sort by overall score descending
        sorted_candidates = sorted(
            all_metrics, 
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )
        
        # Assign ranks
        for i, candidate in enumerate(sorted_candidates):
            candidate['rank'] = i + 1
            candidate['percentile_rank'] = int((1 - i / len(sorted_candidates)) * 100)
        
        return sorted_candidates


# Example usage
if __name__ == "__main__":
    calculator = MetricsCalculator()
    
    # Sample GitHub stats
    sample_stats = {
        'username': 'john_doe',
        'total_repos': 45,
        'original_repos': 30,
        'forked_repos': 15,
        'total_stars': 250,
        'total_forks': 45,
        'commits_90_days': 85,
        'active_repos_90_days': 8,
        'languages': {
            'Python': 15,
            'JavaScript': 10,
            'Java': 8,
            'Go': 5,
            'SQL': 7
        },
        'top_language': 'Python',
        'followers': 42,
        'following': 30,
        'account_age_days': 1200
    }
    
    # Calculate metrics
    metrics = calculator.calculate_all_metrics(sample_stats)
    
    print("\n📊 Calculated Metrics:")
    print(f"  Code Quality: {metrics['code_quality_score']}")
    print(f"  Contribution: {metrics['contribution_score']}")
    print(f"  Impact: {metrics['impact_score']}")
    print(f"  Consistency: {metrics['consistency_score']}")
    print(f"  Diversity: {metrics['diversity_score']}")
    print(f"  Recency: {metrics['recency_score']}")
    print(f"\n  🏆 Overall Score: {metrics['overall_score']}/100")
