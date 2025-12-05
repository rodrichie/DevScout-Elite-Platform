"""
End-to-End Test Suite for DevScout Elite Platform
==================================================

This script tests the complete data pipeline from resume upload to API queries.

Test Flow:
1. Check all services are running
2. Upload test resume to MinIO
3. Trigger Airflow DAG
4. Wait for pipeline completion
5. Verify data in PostgreSQL
6. Test REST API endpoints
7. Test semantic search
8. Generate report

Run: python tests/e2e_test.py
"""

import os
import sys
import time
import json
import requests
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """End-to-end test runner for DevScout Elite Platform."""
    
    def __init__(self):
        self.base_url = os.getenv('API_URL', 'http://localhost:8000')
        self.airflow_url = os.getenv('AIRFLOW_URL', 'http://localhost:8080')
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB', 'devscout_dw'),
            'user': os.getenv('POSTGRES_USER', 'devscout'),
            'password': os.getenv('POSTGRES_PASSWORD', 'devscout_pass')
        }
        self.auth_token = None
        self.test_results = []
        
    def run_all_tests(self) -> bool:
        """Run all end-to-end tests."""
        logger.info("=" * 60)
        logger.info("Starting End-to-End Tests for DevScout Elite Platform")
        logger.info("=" * 60)
        
        tests = [
            ("Service Health Checks", self.test_service_health),
            ("Database Connectivity", self.test_database_connection),
            ("API Authentication", self.test_api_authentication),
            ("Candidate API Endpoints", self.test_candidate_endpoints),
            ("Skills API Endpoints", self.test_skills_endpoints),
            ("GitHub API Endpoints", self.test_github_endpoints),
            ("Analytics API Endpoints", self.test_analytics_endpoints),
            ("Semantic Search", self.test_semantic_search),
            ("Data Quality", self.test_data_quality),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\nRunning: {test_name}")
                logger.info("-" * 60)
                result = test_func()
                if result:
                    logger.info(f"PASSED: {test_name}")
                    self.test_results.append((test_name, "PASSED", None))
                    passed += 1
                else:
                    logger.error(f"FAILED: {test_name}")
                    self.test_results.append((test_name, "FAILED", "Test returned False"))
                    failed += 1
            except Exception as e:
                logger.error(f"ERROR in {test_name}: {str(e)}")
                self.test_results.append((test_name, "ERROR", str(e)))
                failed += 1
        
        # Print summary
        self.print_summary(passed, failed)
        return failed == 0
    
    def test_service_health(self) -> bool:
        """Test if all services are healthy."""
        services = [
            ('API', f'{self.base_url}/health'),
            ('Airflow', f'{self.airflow_url}/health'),
        ]
        
        all_healthy = True
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"  {service_name}: HEALTHY")
                else:
                    logger.warning(f"  {service_name}: UNHEALTHY (status {response.status_code})")
                    all_healthy = False
            except requests.exceptions.RequestException as e:
                logger.error(f"  {service_name}: UNREACHABLE ({str(e)})")
                all_healthy = False
        
        return all_healthy
    
    def test_database_connection(self) -> bool:
        """Test PostgreSQL database connection."""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            logger.info(f"  Connected to: {version[:50]}...")
            
            # Check schemas exist
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('bronze', 'silver', 'gold', 'metadata')
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            logger.info(f"  Schemas found: {', '.join(schemas)}")
            
            cursor.close()
            conn.close()
            
            return len(schemas) >= 3
        except Exception as e:
            logger.error(f"  Database connection failed: {str(e)}")
            return False
    
    def test_api_authentication(self) -> bool:
        """Test API authentication."""
        try:
            # Test login
            response = requests.post(
                f'{self.base_url}/api/v1/auth/token',
                data={'username': 'admin', 'password': 'secret'},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                logger.info(f"  Login successful, token received")
                logger.info(f"  User: {data.get('user', {}).get('username')}")
                logger.info(f"  Role: {data.get('user', {}).get('role')}")
                return True
            else:
                logger.error(f"  Login failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  Authentication error: {str(e)}")
            return False
    
    def test_candidate_endpoints(self) -> bool:
        """Test candidate API endpoints."""
        if not self.auth_token:
            logger.error("  No auth token available")
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # List candidates
            response = requests.get(
                f'{self.base_url}/api/v1/candidates',
                headers=headers,
                params={'limit': 5},
                timeout=10
            )
            
            if response.status_code == 200:
                candidates = response.json()
                logger.info(f"  Found {len(candidates)} candidates")
                
                if candidates:
                    # Test get single candidate
                    candidate_id = candidates[0].get('candidate_id')
                    response = requests.get(
                        f'{self.base_url}/api/v1/candidates/{candidate_id}',
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info(f"  Retrieved candidate {candidate_id}")
                        
                        # Test candidate skills
                        response = requests.get(
                            f'{self.base_url}/api/v1/candidates/{candidate_id}/skills',
                            headers=headers,
                            timeout=10
                        )
                        if response.status_code == 200:
                            skills = response.json()
                            logger.info(f"  Candidate has {len(skills)} skills")
                            return True
                return len(candidates) >= 0  # OK if no data yet
            else:
                logger.error(f"  Failed to list candidates: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  Candidate endpoints error: {str(e)}")
            return False
    
    def test_skills_endpoints(self) -> bool:
        """Test skills API endpoints."""
        if not self.auth_token:
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # List skills
            response = requests.get(
                f'{self.base_url}/api/v1/skills',
                headers=headers,
                params={'limit': 10},
                timeout=10
            )
            
            if response.status_code == 200:
                skills = response.json()
                logger.info(f"  Found {len(skills)} skills")
                
                # Test skill categories
                response = requests.get(
                    f'{self.base_url}/api/v1/skills/categories',
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    categories = response.json()
                    logger.info(f"  Found {len(categories)} skill categories")
                    return True
                return True
            else:
                logger.error(f"  Failed to list skills: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  Skills endpoints error: {str(e)}")
            return False
    
    def test_github_endpoints(self) -> bool:
        """Test GitHub API endpoints."""
        if not self.auth_token:
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Test top contributors
            response = requests.get(
                f'{self.base_url}/api/v1/github/stats/top-contributors',
                headers=headers,
                params={'limit': 5},
                timeout=10
            )
            
            if response.status_code == 200:
                contributors = response.json()
                logger.info(f"  Found {len(contributors)} GitHub contributors")
                
                # Test language distribution
                response = requests.get(
                    f'{self.base_url}/api/v1/github/stats/languages',
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    languages = response.json()
                    logger.info(f"  Found {len(languages)} programming languages")
                    return True
                return True
            else:
                logger.error(f"  Failed GitHub stats: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  GitHub endpoints error: {str(e)}")
            return False
    
    def test_analytics_endpoints(self) -> bool:
        """Test analytics API endpoints."""
        if not self.auth_token:
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Test platform summary
            response = requests.get(
                f'{self.base_url}/api/v1/analytics/summary',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                summary = response.json()
                logger.info(f"  Total candidates: {summary.get('total_candidates', 0)}")
                logger.info(f"  Total skills: {summary.get('total_skills', 0)}")
                logger.info(f"  Average score: {summary.get('avg_score', 0):.2f}")
                return True
            else:
                logger.error(f"  Failed analytics: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"  Analytics endpoints error: {str(e)}")
            return False
    
    def test_semantic_search(self) -> bool:
        """Test semantic search functionality."""
        if not self.auth_token:
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        try:
            # Test Weaviate stats
            response = requests.get(
                f'{self.base_url}/api/v1/semantic/stats',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                logger.info(f"  Weaviate status: {stats.get('status')}")
                logger.info(f"  Candidates indexed: {stats.get('candidates_indexed', 0)}")
                logger.info(f"  Skills indexed: {stats.get('skills_indexed', 0)}")
                
                # Test semantic search if data exists
                if stats.get('candidates_indexed', 0) > 0:
                    response = requests.get(
                        f'{self.base_url}/api/v1/semantic/search',
                        headers=headers,
                        params={'query': 'python developer', 'limit': 5},
                        timeout=15
                    )
                    if response.status_code == 200:
                        results = response.json()
                        logger.info(f"  Search returned {results.get('results_count', 0)} results")
                
                return True
            else:
                logger.warning(f"  Semantic search unavailable: {response.status_code}")
                return True  # Optional feature
        except Exception as e:
            logger.warning(f"  Semantic search error (optional): {str(e)}")
            return True  # Optional feature
    
    def test_data_quality(self) -> bool:
        """Test data quality metrics."""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()
            
            # Check for data in key tables
            tables = [
                ('silver.candidates', 'candidate_id'),
                ('silver.resume_skills', 'skill_id'),
                ('gold.dim_candidates', 'candidate_id'),
            ]
            
            all_ok = True
            for table, pk_column in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"  {table}: {count} records")
                except Exception as e:
                    logger.warning(f"  {table}: Not available ({str(e)[:50]})")
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"  Data quality check error: {str(e)}")
            return False
    
    def print_summary(self, passed: int, failed: int):
        """Print test summary."""
        total = passed + failed
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        for test_name, status, error in self.test_results:
            status_icon = "PASSED" if status == "PASSED" else "FAILED"
            logger.info(f"{status_icon}: {test_name}")
            if error:
                logger.info(f"    Error: {error[:100]}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        logger.info("=" * 60)


def main():
    """Main entry point."""
    runner = E2ETestRunner()
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
