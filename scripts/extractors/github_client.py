"""
GitHub Client - Fetch candidate data from GitHub API
"""
import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubEnricher:
    """
    Enrich candidate profiles with GitHub activity data.
    Fetches repos, commits, stars, languages, and contribution patterns.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            github_token: GitHub Personal Access Token (optional but recommended)
        """
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            logger.info("✅ GitHub client initialized with authentication")
        else:
            logger.warning("⚠️ No GitHub token provided. Rate limit: 60 req/hour")
    
    def fetch_user_profile(self, username: str) -> Optional[Dict]:
        """
        Fetch user profile information.
        
        Args:
            username: GitHub username
            
        Returns:
            User profile dict or None if not found
        """
        try:
            url = f"{self.base_url}/users/{username}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Fetched profile: {username}")
                
                return {
                    'username': data.get('login'),
                    'name': data.get('name'),
                    'bio': data.get('bio'),
                    'company': data.get('company'),
                    'location': data.get('location'),
                    'email': data.get('email'),
                    'blog': data.get('blog'),
                    'public_repos': data.get('public_repos', 0),
                    'followers': data.get('followers', 0),
                    'following': data.get('following', 0),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at'),
                    'avatar_url': data.get('avatar_url')
                }
            elif response.status_code == 404:
                logger.warning(f"❌ User not found: {username}")
                return None
            else:
                logger.error(f"❌ GitHub API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching profile {username}: {e}")
            return None
    
    def fetch_user_repos(self, username: str, max_repos: int = 100) -> List[Dict]:
        """
        Fetch user's public repositories.
        
        Args:
            username: GitHub username
            max_repos: Maximum number of repos to fetch
            
        Returns:
            List of repository dicts
        """
        repos = []
        page = 1
        per_page = min(100, max_repos)
        
        try:
            while len(repos) < max_repos:
                url = f"{self.base_url}/users/{username}/repos"
                params = {
                    'page': page,
                    'per_page': per_page,
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                response = requests.get(url, headers=self.headers, 
                                      params=params, timeout=10)
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                for repo in data:
                    repos.append({
                        'name': repo.get('name'),
                        'full_name': repo.get('full_name'),
                        'description': repo.get('description'),
                        'language': repo.get('language'),
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0),
                        'watchers': repo.get('watchers_count', 0),
                        'size_kb': repo.get('size', 0),
                        'is_fork': repo.get('fork', False),
                        'created_at': repo.get('created_at'),
                        'updated_at': repo.get('updated_at'),
                        'pushed_at': repo.get('pushed_at'),
                        'topics': repo.get('topics', []),
                        'url': repo.get('html_url')
                    })
                
                if len(data) < per_page:
                    break
                
                page += 1
            
            logger.info(f"✅ Fetched {len(repos)} repos for {username}")
            return repos
            
        except Exception as e:
            logger.error(f"❌ Error fetching repos for {username}: {e}")
            return repos
    
    def fetch_user_commits(self, username: str, 
                          days_back: int = 90) -> List[Dict]:
        """
        Fetch user's recent commit activity across all repos.
        
        Args:
            username: GitHub username
            days_back: Look back period in days
            
        Returns:
            List of commit summaries by repo
        """
        since_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        commits_by_repo = []
        
        try:
            # Get user repos first
            repos = self.fetch_user_repos(username, max_repos=50)
            
            for repo in repos[:20]:  # Limit to top 20 repos to avoid rate limits
                repo_name = repo['full_name']
                
                url = f"{self.base_url}/repos/{repo_name}/commits"
                params = {
                    'author': username,
                    'since': since_date,
                    'per_page': 100
                }
                
                response = requests.get(url, headers=self.headers, 
                                      params=params, timeout=10)
                
                if response.status_code == 200:
                    commits = response.json()
                    
                    if commits:
                        commits_by_repo.append({
                            'repo': repo_name,
                            'commit_count': len(commits),
                            'last_commit': commits[0]['commit']['author']['date'] if commits else None,
                            'languages': [repo.get('language')]
                        })
            
            logger.info(f"✅ Analyzed commits for {username} in {len(commits_by_repo)} repos")
            return commits_by_repo
            
        except Exception as e:
            logger.error(f"❌ Error fetching commits for {username}: {e}")
            return commits_by_repo
    
    def fetch_contribution_stats(self, username: str) -> Dict:
        """
        Fetch contribution statistics.
        
        Args:
            username: GitHub username
            
        Returns:
            Dict with contribution stats
        """
        try:
            # Get recent activity (last 90 days)
            commits = self.fetch_user_commits(username, days_back=90)
            
            total_commits = sum(c['commit_count'] for c in commits)
            active_repos = len(commits)
            
            # Get language distribution from repos
            repos = self.fetch_user_repos(username, max_repos=100)
            languages = {}
            for repo in repos:
                if not repo['is_fork'] and repo['language']:
                    lang = repo['language']
                    languages[lang] = languages.get(lang, 0) + 1
            
            # Calculate activity score (simple heuristic)
            profile = self.fetch_user_profile(username)
            
            stats = {
                'username': username,
                'total_repos': len(repos),
                'original_repos': len([r for r in repos if not r['is_fork']]),
                'forked_repos': len([r for r in repos if r['is_fork']]),
                'total_stars': sum(r['stars'] for r in repos),
                'total_forks': sum(r['forks'] for r in repos),
                'commits_90_days': total_commits,
                'active_repos_90_days': active_repos,
                'languages': languages,
                'top_language': max(languages.items(), key=lambda x: x[1])[0] if languages else None,
                'followers': profile.get('followers', 0) if profile else 0,
                'following': profile.get('following', 0) if profile else 0,
                'account_age_days': self._calculate_account_age(profile) if profile else 0,
                'fetched_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Computed contribution stats for {username}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error computing stats for {username}: {e}")
            return {'username': username, 'error': str(e)}
    
    def _calculate_account_age(self, profile: Dict) -> int:
        """Calculate account age in days."""
        if not profile or 'created_at' not in profile:
            return 0
        
        try:
            created = datetime.fromisoformat(profile['created_at'].replace('Z', '+00:00'))
            age = (datetime.now(created.tzinfo) - created).days
            return age
        except:
            return 0
    
    def check_rate_limit(self) -> Dict:
        """
        Check current GitHub API rate limit status.
        
        Returns:
            Dict with rate limit info
        """
        try:
            url = f"{self.base_url}/rate_limit"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                core = data['resources']['core']
                
                return {
                    'limit': core['limit'],
                    'remaining': core['remaining'],
                    'reset_at': datetime.fromtimestamp(core['reset']).isoformat(),
                    'used': core['limit'] - core['remaining']
                }
            
            return {'error': 'Could not fetch rate limit'}
            
        except Exception as e:
            logger.error(f"❌ Error checking rate limit: {e}")
            return {'error': str(e)}


# Example usage
if __name__ == "__main__":
    # Initialize client (use token for higher rate limits)
    enricher = GitHubEnricher()
    
    # Check rate limit
    rate_limit = enricher.check_rate_limit()
    print(f"\n🔍 Rate Limit: {rate_limit}")
    
    # Test with a sample username
    username = "torvalds"  # Linus Torvalds as example
    
    print(f"\n📊 Fetching data for: {username}")
    
    # Fetch profile
    profile = enricher.fetch_user_profile(username)
    if profile:
        print(f"\n👤 Profile:")
        print(f"  Name: {profile['name']}")
        print(f"  Repos: {profile['public_repos']}")
        print(f"  Followers: {profile['followers']}")
    
    # Fetch contribution stats
    stats = enricher.fetch_contribution_stats(username)
    print(f"\n📈 Contribution Stats:")
    print(f"  Total Repos: {stats.get('total_repos', 0)}")
    print(f"  Total Stars: {stats.get('total_stars', 0)}")
    print(f"  Commits (90d): {stats.get('commits_90_days', 0)}")
    print(f"  Top Language: {stats.get('top_language', 'N/A')}")
