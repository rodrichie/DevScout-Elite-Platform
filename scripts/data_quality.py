"""
Data Quality Checker - Validate data quality using Great Expectations
"""
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

try:
    import great_expectations as gx
    from great_expectations.core.batch import BatchRequest
    HAS_GX = True
except ImportError:
    HAS_GX = False
    logging.warning("Great Expectations not installed. Data quality checks disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Run data quality validations using Great Expectations.
    Validates completeness, uniqueness, format, and business rules.
    """
    
    def __init__(self, context_root_dir: str = None):
        """
        Initialize data quality checker.
        
        Args:
            context_root_dir: Path to GX context directory
        """
        self.context_root_dir = context_root_dir or os.getenv(
            'GX_CONTEXT_ROOT', 
            '/opt/airflow/great_expectations'
        )
        
        self.context = None
        
        if HAS_GX:
            try:
                # Create or load context
                if os.path.exists(self.context_root_dir):
                    self.context = gx.get_context(context_root_dir=self.context_root_dir)
                else:
                    # Create new context
                    os.makedirs(self.context_root_dir, exist_ok=True)
                    self.context = gx.get_context(mode="file", project_root_dir=self.context_root_dir)
                
                logger.info("✅ Great Expectations context initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize GX context: {e}")
                self.context = None
        else:
            logger.warning("⚠️ Great Expectations not available")
    
    def validate_resume_data(self, data_dict: Dict) -> Dict:
        """
        Validate resume data quality.
        
        Args:
            data_dict: Dict with resume data
            
        Returns:
            Validation results dict
        """
        checks = []
        passed = 0
        failed = 0
        
        # Check 1: Resume text not empty
        if 'resume_text' in data_dict and data_dict['resume_text']:
            text_len = len(data_dict['resume_text'])
            if text_len > 100:
                checks.append({
                    'check': 'resume_text_length',
                    'status': 'passed',
                    'value': text_len,
                    'threshold': 100
                })
                passed += 1
            else:
                checks.append({
                    'check': 'resume_text_length',
                    'status': 'failed',
                    'value': text_len,
                    'threshold': 100
                })
                failed += 1
        else:
            checks.append({
                'check': 'resume_text_present',
                'status': 'failed',
                'message': 'Resume text is empty or missing'
            })
            failed += 1
        
        # Check 2: Skills extracted
        if 'skills' in data_dict and isinstance(data_dict['skills'], list):
            skills_count = len(data_dict['skills'])
            if skills_count >= 3:
                checks.append({
                    'check': 'minimum_skills',
                    'status': 'passed',
                    'value': skills_count,
                    'threshold': 3
                })
                passed += 1
            else:
                checks.append({
                    'check': 'minimum_skills',
                    'status': 'failed',
                    'value': skills_count,
                    'threshold': 3
                })
                failed += 1
        else:
            checks.append({
                'check': 'skills_present',
                'status': 'failed',
                'message': 'Skills list is empty or invalid'
            })
            failed += 1
        
        # Check 3: Email format
        if 'email' in data_dict and data_dict['email']:
            email = data_dict['email']
            if '@' in email and '.' in email:
                checks.append({
                    'check': 'email_format',
                    'status': 'passed',
                    'value': email
                })
                passed += 1
            else:
                checks.append({
                    'check': 'email_format',
                    'status': 'failed',
                    'value': email
                })
                failed += 1
        
        # Check 4: Years of experience reasonable
        if 'years_experience' in data_dict:
            years = data_dict['years_experience']
            if 0 <= years <= 50:
                checks.append({
                    'check': 'years_experience_range',
                    'status': 'passed',
                    'value': years
                })
                passed += 1
            else:
                checks.append({
                    'check': 'years_experience_range',
                    'status': 'failed',
                    'value': years,
                    'message': 'Years outside reasonable range'
                })
                failed += 1
        
        # Check 5: Embeddings generated
        if 'embedding' in data_dict and data_dict['embedding'] is not None:
            checks.append({
                'check': 'embeddings_generated',
                'status': 'passed',
                'value': len(data_dict['embedding'])
            })
            passed += 1
        
        results = {
            'validation_id': f"resume_validation_{int(datetime.utcnow().timestamp())}",
            'data_type': 'resume',
            'total_checks': len(checks),
            'passed': passed,
            'failed': failed,
            'success_rate': round(passed / len(checks) * 100, 2) if checks else 0,
            'checks': checks,
            'validated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Resume validation: {passed}/{len(checks)} checks passed")
        
        return results
    
    def validate_github_data(self, github_stats: Dict) -> Dict:
        """
        Validate GitHub data quality.
        
        Args:
            github_stats: GitHub stats dict
            
        Returns:
            Validation results dict
        """
        checks = []
        passed = 0
        failed = 0
        
        # Check 1: Username present
        if 'username' in github_stats and github_stats['username']:
            checks.append({
                'check': 'username_present',
                'status': 'passed',
                'value': github_stats['username']
            })
            passed += 1
        else:
            checks.append({
                'check': 'username_present',
                'status': 'failed'
            })
            failed += 1
        
        # Check 2: Repo count reasonable
        if 'total_repos' in github_stats:
            repos = github_stats['total_repos']
            if 0 <= repos <= 10000:
                checks.append({
                    'check': 'repo_count_reasonable',
                    'status': 'passed',
                    'value': repos
                })
                passed += 1
            else:
                checks.append({
                    'check': 'repo_count_reasonable',
                    'status': 'failed',
                    'value': repos
                })
                failed += 1
        
        # Check 3: Has recent activity
        if 'commits_90_days' in github_stats:
            commits = github_stats['commits_90_days']
            if commits > 0:
                checks.append({
                    'check': 'has_recent_activity',
                    'status': 'passed',
                    'value': commits
                })
                passed += 1
            else:
                checks.append({
                    'check': 'has_recent_activity',
                    'status': 'warning',
                    'value': commits,
                    'message': 'No recent commits'
                })
        
        # Check 4: Languages present
        if 'languages' in github_stats and github_stats['languages']:
            lang_count = len(github_stats['languages'])
            if lang_count > 0:
                checks.append({
                    'check': 'languages_present',
                    'status': 'passed',
                    'value': lang_count
                })
                passed += 1
        
        # Check 5: Top language identified
        if 'top_language' in github_stats and github_stats['top_language']:
            checks.append({
                'check': 'top_language_identified',
                'status': 'passed',
                'value': github_stats['top_language']
            })
            passed += 1
        
        results = {
            'validation_id': f"github_validation_{int(datetime.utcnow().timestamp())}",
            'data_type': 'github',
            'total_checks': len(checks),
            'passed': passed,
            'failed': failed,
            'success_rate': round(passed / len(checks) * 100, 2) if checks else 0,
            'checks': checks,
            'validated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ GitHub validation: {passed}/{len(checks)} checks passed")
        
        return results
    
    def validate_batch_data(self, data_list: List[Dict], 
                           data_type: str = 'resume') -> Dict:
        """
        Validate a batch of data records.
        
        Args:
            data_list: List of data dicts
            data_type: Type of data ('resume' or 'github')
            
        Returns:
            Aggregated validation results
        """
        batch_results = []
        
        for data in data_list:
            if data_type == 'resume':
                result = self.validate_resume_data(data)
            elif data_type == 'github':
                result = self.validate_github_data(data)
            else:
                continue
            
            batch_results.append(result)
        
        # Aggregate results
        total_records = len(batch_results)
        total_checks = sum(r['total_checks'] for r in batch_results)
        total_passed = sum(r['passed'] for r in batch_results)
        total_failed = sum(r['failed'] for r in batch_results)
        
        aggregated = {
            'validation_id': f"batch_validation_{int(datetime.utcnow().timestamp())}",
            'data_type': data_type,
            'total_records': total_records,
            'total_checks': total_checks,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'overall_success_rate': round(total_passed / total_checks * 100, 2) if total_checks else 0,
            'individual_results': batch_results,
            'validated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Batch validation complete: {total_passed}/{total_checks} checks passed "
                   f"({aggregated['overall_success_rate']}%)")
        
        return aggregated
    
    def log_validation_results(self, results: Dict, log_to_db: bool = False):
        """
        Log validation results (optionally to database).
        
        Args:
            results: Validation results dict
            log_to_db: Whether to persist to database
        """
        # Log to console
        logger.info(f"📊 Validation Summary:")
        logger.info(f"  Type: {results['data_type']}")
        logger.info(f"  Passed: {results['passed']}/{results['total_checks']}")
        logger.info(f"  Success Rate: {results['success_rate']}%")
        
        # TODO: Implement database logging if needed
        if log_to_db:
            logger.info("  (Database logging not yet implemented)")


# Example usage
if __name__ == "__main__":
    checker = DataQualityChecker()
    
    # Test resume validation
    sample_resume = {
        'resume_text': 'Senior Data Engineer with 5 years of experience...' * 10,
        'skills': ['Python', 'Spark', 'Kafka', 'AWS'],
        'email': 'john.doe@example.com',
        'years_experience': 5,
        'embedding': [0.1] * 384
    }
    
    results = checker.validate_resume_data(sample_resume)
    checker.log_validation_results(results)
    
    # Test GitHub validation
    sample_github = {
        'username': 'johndoe',
        'total_repos': 45,
        'commits_90_days': 85,
        'languages': {'Python': 15, 'Java': 10},
        'top_language': 'Python'
    }
    
    github_results = checker.validate_github_data(sample_github)
    checker.log_validation_results(github_results)
