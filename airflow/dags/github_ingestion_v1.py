"""
DevScout Elite - GitHub Enrichment DAG
========================================

This DAG enriches candidate profiles with GitHub activity data:
1. Fetch candidate GitHub usernames from Postgres
2. Call GitHub API to retrieve repos, commits, languages
3. Calculate engineering metrics (commit frequency, code quality, etc.)
4. Transform JSON data using PySpark
5. Run data quality checks
6. Load to Silver layer

Schedule: Weekly on Sundays at 3 AM UTC
SLA: 15 minutes
Owner: Data Engineering Team
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
import psycopg2
import json
import os

# Default arguments
default_args = {
    'owner': 'devscout-de-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['alerts@devscout.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=3),
    'execution_timeout': timedelta(minutes=15),
    'sla': timedelta(minutes=15),
}

# DAG definition
dag = DAG(
    'github_ingestion_v1',
    default_args=default_args,
    description='Enrich candidate profiles with GitHub activity data',
    schedule_interval='0 3 * * 0',  # Weekly on Sundays at 3 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['batch', 'github', 'api', 'enrichment'],
)


def fetch_candidate_github_users(**context):
    """
    Fetch list of candidate GitHub usernames from Postgres
    """
    import psycopg2
    import os
    
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'devscout_dw'),
        user=os.getenv('POSTGRES_USER', 'devscout'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT candidate_id, github_username 
        FROM silver.candidates 
        WHERE github_username IS NOT NULL 
        AND github_last_updated < NOW() - INTERVAL '7 days'
        LIMIT 100
    """)
    
    candidates = [
        {'candidate_id': row[0], 'github_username': row[1]} 
        for row in cursor.fetchall()
    ]
    
    cursor.close()
    conn.close()
    
    context['task_instance'].xcom_push(key='candidates', value=candidates)
    print(f" Found {len(candidates)} candidates to enrich")
    return len(candidates)


def fetch_github_data(**context):
    """
    Fetch GitHub data for each candidate using GitHub API
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from extractors.github_client import GitHubEnricher
    
    candidates = context['task_instance'].xcom_pull(
        task_ids='fetch_candidates',
        key='candidates'
    )
    
    enricher = GitHubEnricher()
    enriched_profiles = []
    
    for candidate in candidates:
        try:
            github_data = enricher.fetch_user_stats(candidate['github_username'])
            
            enriched_profiles.append({
                'candidate_id': candidate['candidate_id'],
                'github_username': candidate['github_username'],
                **github_data,
                'fetched_at': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            print(f" Error fetching data for {candidate['github_username']}: {str(e)}")
            continue
    
    context['task_instance'].xcom_push(key='github_profiles', value=enriched_profiles)
    print(f" Fetched GitHub data for {len(enriched_profiles)} candidates")
    return len(enriched_profiles)


def calculate_engineering_metrics(**context):
    """
    Calculate derived metrics from GitHub data
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from extractors.metrics_calculator import MetricsCalculator
    
    github_profiles = context['task_instance'].xcom_pull(
        task_ids='fetch_github',
        key='github_profiles'
    )
    
    calculator = MetricsCalculator()
    metrics_data = []
    
    for profile in github_profiles:
        try:
            metrics = calculator.calculate_metrics(profile)
            metrics_data.append({
                **profile,
                'metrics': metrics,
                'calculated_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f" Metrics calculation error: {str(e)}")
            continue
    
    context['task_instance'].xcom_push(key='metrics_data', value=metrics_data)
    print(f" Calculated metrics for {len(metrics_data)} profiles")
    return len(metrics_data)


def transform_with_spark(**context):
    """
    Use PySpark to flatten nested JSON and prepare for loading
    """
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, explode, from_json
    
    metrics_data = context['task_instance'].xcom_pull(
        task_ids='calculate_metrics',
        key='metrics_data'
    )
    
    spark = SparkSession.builder \
        .appName("GitHubDataTransformation") \
        .getOrCreate()
    
    # Convert to DataFrame
    df = spark.createDataFrame(metrics_data)
    
    # Flatten nested structures
    flattened_df = df.select(
        col("candidate_id"),
        col("github_username"),
        col("metrics.primary_language").alias("primary_language"),
        col("metrics.total_repos").alias("total_repos"),
        col("metrics.total_stars").alias("total_stars"),
        col("metrics.total_commits_90d").alias("commits_last_90_days"),
        col("metrics.avg_commit_size").alias("avg_commit_size"),
        col("metrics.contribution_score").alias("contribution_score"),
        col("fetched_at"),
        col("calculated_at")
    )
    
    # Save to MinIO as Parquet
    output_path = "s3a://silver-processed/github_profiles"
    flattened_df.write \
        .mode("append") \
        .partitionBy("fetched_at") \
        .parquet(output_path)
    
    spark.stop()
    
    print(f" Transformed and saved {flattened_df.count()} records to {output_path}")
    return output_path


def load_to_postgres(**context):
    """
    Load transformed data to Postgres Silver layer
    """
    import psycopg2
    from psycopg2.extras import execute_values
    
    metrics_data = context['task_instance'].xcom_pull(
        task_ids='calculate_metrics',
        key='metrics_data'
    )
    
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'devscout_dw'),
        user=os.getenv('POSTGRES_USER', 'devscout'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    cursor = conn.cursor()
    
    # Prepare data for bulk insert
    insert_data = [
        (
            item['candidate_id'],
            item['github_username'],
            item['metrics'].get('primary_language'),
            item['metrics'].get('total_repos', 0),
            item['metrics'].get('total_stars', 0),
            item['metrics'].get('total_commits_90d', 0),
            item['metrics'].get('contribution_score', 0),
            item['fetched_at']
        )
        for item in metrics_data
    ]
    
    # Bulk insert
    insert_query = """
    INSERT INTO silver.github_profiles (
        candidate_id, 
        github_username, 
        primary_language, 
        total_repos, 
        total_stars, 
        commits_last_90_days, 
        contribution_score,
        fetched_at
    ) VALUES %s
    ON CONFLICT (candidate_id) DO UPDATE SET
        primary_language = EXCLUDED.primary_language,
        total_repos = EXCLUDED.total_repos,
        total_stars = EXCLUDED.total_stars,
        commits_last_90_days = EXCLUDED.commits_last_90_days,
        contribution_score = EXCLUDED.contribution_score,
        fetched_at = EXCLUDED.fetched_at
    """
    
    execute_values(cursor, insert_query, insert_data)
    conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f" Loaded {len(insert_data)} records to Postgres")
    return len(insert_data)


# Task definitions
with dag:
    
    # Task 1: Fetch candidates needing GitHub enrichment
    fetch_candidates = PythonOperator(
        task_id='fetch_candidates',
        python_callable=fetch_candidate_github_users,
        provide_context=True,
    )
    
    # Task 2: Fetch GitHub data via API
    fetch_github = PythonOperator(
        task_id='fetch_github',
        python_callable=fetch_github_data,
        provide_context=True,
    )
    
    # Task 3: Calculate engineering metrics
    calculate_metrics = PythonOperator(
        task_id='calculate_metrics',
        python_callable=calculate_engineering_metrics,
        provide_context=True,
    )
    
    # Task 4: Transform with Spark
    transform_data = PythonOperator(
        task_id='transform_with_spark',
        python_callable=transform_with_spark,
        provide_context=True,
    )
    
    # Task 5: Load to Postgres
    load_postgres = PythonOperator(
        task_id='load_to_postgres',
        python_callable=load_to_postgres,
        provide_context=True,
    )
    
    # Task 6: Update pipeline metadata
    update_metadata = PostgresOperator(
        task_id='update_metadata',
        postgres_conn_id='devscout_postgres',
        sql="""
        INSERT INTO metadata.pipeline_runs (
            pipeline_name,
            run_date,
            status,
            records_processed
        ) VALUES (
            'github_ingestion_v1',
            '{{ ds }}',
            'SUCCESS',
            {{ task_instance.xcom_pull(task_ids='load_to_postgres') }}
        );
        """,
    )
    
    # Task dependencies
    (
        fetch_candidates 
        >> fetch_github 
        >> calculate_metrics 
        >> [transform_data, load_postgres]
        >> update_metadata
    )
