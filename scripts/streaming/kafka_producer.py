"""
Kafka Producer - Stream coding challenge events to Kafka
"""
import os
import logging
import json
from typing import Dict, Any
from datetime import datetime

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    logging.warning("kafka-python not installed. Kafka streaming disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodingEventProducer:
    """
    Stream coding challenge events to Kafka for real-time processing.
    Tracks: code submissions, test results, execution time, errors.
    """
    
    def __init__(self, bootstrap_servers: str = None, topic: str = None):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker address
            topic: Kafka topic name
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS', 
            'kafka:9092'
        )
        self.topic = topic or os.getenv('KAFKA_TOPIC', 'coding-events')
        self.producer = None
        
        if HAS_KAFKA:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Wait for all replicas
                    retries=3,
                    max_in_flight_requests_per_connection=1
                )
                logger.info(f" Kafka producer connected to {self.bootstrap_servers}")
            except Exception as e:
                logger.error(f" Failed to connect to Kafka: {e}")
                self.producer = None
        else:
            logger.warning(" Kafka not available. Events will be logged only.")
    
    def send_event(self, event_data: Dict) -> bool:
        """
        Send a single event to Kafka.
        
        Args:
            event_data: Event data dict
            
        Returns:
            Success boolean
        """
        # Add metadata
        enriched_event = {
            **event_data,
            'event_id': f"event_{int(datetime.utcnow().timestamp() * 1000)}",
            'timestamp': datetime.utcnow().isoformat(),
            'producer': 'CodingEventProducer'
        }
        
        if self.producer:
            try:
                future = self.producer.send(self.topic, value=enriched_event)
                
                # Wait for confirmation (blocking)
                record_metadata = future.get(timeout=10)
                
                logger.info(f" Event sent: {enriched_event['event_id']} "
                           f"(partition={record_metadata.partition}, offset={record_metadata.offset})")
                return True
                
            except KafkaError as e:
                logger.error(f" Kafka error: {e}")
                return False
            except Exception as e:
                logger.error(f" Failed to send event: {e}")
                return False
        else:
            # Fallback: log event to console
            logger.info(f" Event (no Kafka): {json.dumps(enriched_event, indent=2)}")
            return True
    
    def send_code_submission_event(self, candidate_id: int, 
                                   challenge_id: str,
                                   code: str,
                                   language: str) -> bool:
        """
        Send code submission event.
        
        Args:
            candidate_id: Candidate ID
            challenge_id: Challenge identifier
            code: Submitted code
            language: Programming language
            
        Returns:
            Success boolean
        """
        event = {
            'event_type': 'code_submission',
            'candidate_id': candidate_id,
            'challenge_id': challenge_id,
            'language': language,
            'code_length': len(code),
            'code_hash': hash(code),  # For duplicate detection
        }
        
        return self.send_event(event)
    
    def send_test_result_event(self, candidate_id: int,
                              challenge_id: str,
                              tests_passed: int,
                              tests_total: int,
                              execution_time_ms: float,
                              errors: list = None) -> bool:
        """
        Send test execution result event.
        
        Args:
            candidate_id: Candidate ID
            challenge_id: Challenge identifier
            tests_passed: Number of tests passed
            tests_total: Total number of tests
            execution_time_ms: Execution time in milliseconds
            errors: List of error messages
            
        Returns:
            Success boolean
        """
        event = {
            'event_type': 'test_result',
            'candidate_id': candidate_id,
            'challenge_id': challenge_id,
            'tests_passed': tests_passed,
            'tests_total': tests_total,
            'success_rate': round(tests_passed / tests_total * 100, 2) if tests_total > 0 else 0,
            'execution_time_ms': execution_time_ms,
            'errors': errors or [],
            'has_errors': bool(errors)
        }
        
        return self.send_event(event)
    
    def send_challenge_completion_event(self, candidate_id: int,
                                       challenge_id: str,
                                       final_score: float,
                                       time_taken_seconds: int,
                                       attempts: int) -> bool:
        """
        Send challenge completion event.
        
        Args:
            candidate_id: Candidate ID
            challenge_id: Challenge identifier
            final_score: Final score (0-100)
            time_taken_seconds: Total time taken
            attempts: Number of submission attempts
            
        Returns:
            Success boolean
        """
        event = {
            'event_type': 'challenge_completion',
            'candidate_id': candidate_id,
            'challenge_id': challenge_id,
            'final_score': final_score,
            'time_taken_seconds': time_taken_seconds,
            'attempts': attempts,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        return self.send_event(event)
    
    def send_live_coding_metric(self, candidate_id: int,
                               session_id: str,
                               metric_type: str,
                               metric_value: float,
                               metadata: Dict = None) -> bool:
        """
        Send real-time coding metrics (keystrokes, IDE events, etc.).
        
        Args:
            candidate_id: Candidate ID
            session_id: Live coding session ID
            metric_type: Type of metric (keystrokes, copy_paste, debugging_time, etc.)
            metric_value: Metric value
            metadata: Additional metadata
            
        Returns:
            Success boolean
        """
        event = {
            'event_type': 'live_coding_metric',
            'candidate_id': candidate_id,
            'session_id': session_id,
            'metric_type': metric_type,
            'metric_value': metric_value,
            'metadata': metadata or {}
        }
        
        return self.send_event(event)
    
    def flush(self):
        """Flush any buffered events."""
        if self.producer:
            self.producer.flush()
            logger.info(" Kafka producer flushed")
    
    def close(self):
        """Close Kafka producer connection."""
        if self.producer:
            self.producer.close()
            logger.info(" Kafka producer closed")


# Example usage
if __name__ == "__main__":
    producer = CodingEventProducer()
    
    # Simulate code submission
    print("\n Sending code submission event...")
    producer.send_code_submission_event(
        candidate_id=1,
        challenge_id="challenge_data_pipeline",
        code="def process_data():\n    pass",
        language="python"
    )
    
    # Simulate test results
    print("\n Sending test result event...")
    producer.send_test_result_event(
        candidate_id=1,
        challenge_id="challenge_data_pipeline",
        tests_passed=8,
        tests_total=10,
        execution_time_ms=1250.5,
        errors=["Test 3 failed: Expected 100, got 99"]
    )
    
    # Simulate challenge completion
    print("\n Sending completion event...")
    producer.send_challenge_completion_event(
        candidate_id=1,
        challenge_id="challenge_data_pipeline",
        final_score=85.5,
        time_taken_seconds=3600,
        attempts=3
    )
    
    # Simulate live coding metric
    print("\n Sending live coding metric...")
    producer.send_live_coding_metric(
        candidate_id=1,
        session_id="session_123",
        metric_type="keystrokes_per_minute",
        metric_value=45.2,
        metadata={"editor": "vscode", "language": "python"}
    )
    
    producer.flush()
    producer.close()
    
    print("\n All events sent successfully!")
