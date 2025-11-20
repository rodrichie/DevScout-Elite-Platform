"""
DevScout Elite - Resume Processing DAG
=======================================

This DAG orchestrates the resume processing pipeline:
1. Watch for new PDF/DOCX resumes in MinIO
2. Extract text using OCR (pytesseract) and docx parser
3. Clean and normalize text
4. Extract skills, education, and experience using spaCy NER
5. Generate vector embeddings using HuggingFace transformers
6. Run data quality checks with Great Expectations
7. Load to Silver layer (MinIO Parquet + Weaviate vectors)

Schedule: Daily at 2 AM UTC
SLA: 30 minutes
Owner: Data Engineering Team
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.task_group import TaskGroup

# Default arguments
default_args = {
    'owner': 'devscout-de-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['alerts@devscout.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
    'sla': timedelta(minutes=30),
}

# DAG definition
dag = DAG(
    'resume_etl_v1',
    default_args=default_args,
    description='Extract, transform, and load resume data (Bronze  Silver)',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    catchup=False,
    max_active_runs=1,
    tags=['batch', 'resumes', 'nlp', 'medallion-architecture'],
)


def watch_minio_bucket(**context):
    """
    Scan MinIO bucket for new resume files
    Returns list of file keys to process
    """
    from minio import Minio
    import os
    
    client = Minio(
        "minio:9000",
        access_key=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        secret_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        secure=False
    )
    
    bucket_name = "bronze-resumes"
    objects = client.list_objects(bucket_name, recursive=True)
    
    # Filter for PDF and DOCX files
    resume_files = [
        obj.object_name for obj in objects 
        if obj.object_name.lower().endswith(('.pdf', '.docx'))
    ]
    
    context['task_instance'].xcom_push(key='resume_files', value=resume_files)
    print(f" Found {len(resume_files)} resumes to process")
    return resume_files


def extract_text_from_resumes(**context):
    """
    Extract raw text from PDF/DOCX files
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from parsers.resume_parser import ResumeParser
    
    resume_files = context['task_instance'].xcom_pull(
        task_ids='watch_bucket', 
        key='resume_files'
    )
    
    parser = ResumeParser()
    extracted_data = []
    
    for file_key in resume_files:
        try:
            text = parser.extract_text(file_key)
            extracted_data.append({
                'file_key': file_key,
                'raw_text': text,
                'extracted_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f" Error processing {file_key}: {str(e)}")
            continue
    
    context['task_instance'].xcom_push(key='extracted_texts', value=extracted_data)
    print(f" Extracted text from {len(extracted_data)} resumes")
    return len(extracted_data)


def extract_skills_with_nlp(**context):
    """
    Use spaCy NER to extract skills, education, experience
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from extractors.nlp_extractor import NLPExtractor
    
    extracted_data = context['task_instance'].xcom_pull(
        task_ids='extract_text',
        key='extracted_texts'
    )
    
    nlp_extractor = NLPExtractor()
    enriched_data = []
    
    for item in extracted_data:
        try:
            entities = nlp_extractor.extract_entities(item['raw_text'])
            enriched_data.append({
                **item,
                'skills': entities.get('skills', []),
                'education': entities.get('education', []),
                'years_experience': entities.get('years_experience', 0),
                'entities_extracted_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f" NLP error for {item['file_key']}: {str(e)}")
            continue
    
    context['task_instance'].xcom_push(key='enriched_data', value=enriched_data)
    print(f" Extracted entities from {len(enriched_data)} resumes")
    return len(enriched_data)


def generate_embeddings(**context):
    """
    Generate vector embeddings using HuggingFace sentence-transformers
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from extractors.vector_embeddings import VectorEmbedder
    
    enriched_data = context['task_instance'].xcom_pull(
        task_ids='extract_skills',
        key='enriched_data'
    )
    
    embedder = VectorEmbedder()
    vector_data = []
    
    for item in enriched_data:
        try:
            # Create a combined text representation
            combined_text = f"{item['raw_text'][:1000]} Skills: {', '.join(item['skills'])}"
            vector = embedder.encode(combined_text)
            
            vector_data.append({
                **item,
                'embedding_vector': vector.tolist(),
                'vector_generated_at': datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f" Embedding error for {item['file_key']}: {str(e)}")
            continue
    
    context['task_instance'].xcom_push(key='vector_data', value=vector_data)
    print(f" Generated embeddings for {len(vector_data)} resumes")
    return len(vector_data)


def run_data_quality_checks(**context):
    """
    Validate data using Great Expectations
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from data_quality import DataQualityChecker
    
    vector_data = context['task_instance'].xcom_pull(
        task_ids='generate_embeddings',
        key='vector_data'
    )
    
    checker = DataQualityChecker()
    validation_results = checker.validate_resume_data(vector_data)
    
    if not validation_results['success']:
        raise ValueError(f" Data quality checks failed: {validation_results['errors']}")
    
    print(f" Data quality checks passed")
    return validation_results


def load_to_silver_layer(**context):
    """
    Load processed data to Silver layer (MinIO + Weaviate)
    """
    import sys
    sys.path.append('/opt/airflow/scripts')
    
    from loaders.silver_loader import SilverLoader
    
    vector_data = context['task_instance'].xcom_pull(
        task_ids='generate_embeddings',
        key='vector_data'
    )
    
    loader = SilverLoader()
    
    # Save to MinIO as Parquet
    parquet_path = loader.save_to_minio(vector_data, 'silver-processed')
    
    # Save vectors to Weaviate
    weaviate_ids = loader.save_to_weaviate(vector_data)
    
    print(f" Loaded {len(vector_data)} records to Silver layer")
    print(f"   - Parquet: {parquet_path}")
    print(f"   - Weaviate: {len(weaviate_ids)} vectors")
    
    return {
        'records_loaded': len(vector_data),
        'parquet_path': parquet_path,
        'weaviate_ids': len(weaviate_ids)
    }


# Task definitions
with dag:
    
    # Task 1: Watch for new resumes in MinIO
    watch_bucket = PythonOperator(
        task_id='watch_bucket',
        python_callable=watch_minio_bucket,
        provide_context=True,
    )
    
    # Task 2: Extract text from PDFs/DOCX
    extract_text = PythonOperator(
        task_id='extract_text',
        python_callable=extract_text_from_resumes,
        provide_context=True,
    )
    
    # Task 3: Extract skills with NLP
    extract_skills = PythonOperator(
        task_id='extract_skills',
        python_callable=extract_skills_with_nlp,
        provide_context=True,
    )
    
    # Task 4: Generate vector embeddings
    generate_vectors = PythonOperator(
        task_id='generate_embeddings',
        python_callable=generate_embeddings,
        provide_context=True,
    )
    
    # Task 5: Data quality checks
    quality_check = PythonOperator(
        task_id='quality_check',
        python_callable=run_data_quality_checks,
        provide_context=True,
    )
    
    # Task 6: Load to Silver layer
    load_silver = PythonOperator(
        task_id='load_to_silver',
        python_callable=load_to_silver_layer,
        provide_context=True,
    )
    
    # Task 7: Update metadata table in Postgres
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
            'resume_etl_v1',
            '{{ ds }}',
            'SUCCESS',
            {{ task_instance.xcom_pull(task_ids='load_to_silver')['records_loaded'] }}
        );
        """,
    )
    
    # Task 8: Trigger dbt run (for Gold layer transformations)
    trigger_dbt = SparkSubmitOperator(
        task_id='trigger_dbt_run',
        application='/opt/airflow/scripts/trigger_dbt.py',
        conn_id='spark_default',
        verbose=True,
    )
    
    # Task dependencies
    (
        watch_bucket 
        >> extract_text 
        >> extract_skills 
        >> generate_vectors 
        >> quality_check 
        >> load_silver 
        >> [update_metadata, trigger_dbt]
    )
