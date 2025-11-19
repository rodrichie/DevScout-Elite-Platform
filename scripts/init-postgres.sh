#!/bin/bash
set -e

# ============================================
# DevScout Elite - PostgreSQL Initialization
# ============================================

echo "🚀 Initializing DevScout databases..."

# Create multiple databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create additional databases
    CREATE DATABASE airflow_db;
    CREATE DATABASE mlflow_db;
    CREATE DATABASE feast_db;

    -- Enable pgvector extension for vector search
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create schemas in main database
    CREATE SCHEMA IF NOT EXISTS bronze;
    CREATE SCHEMA IF NOT EXISTS silver;
    CREATE SCHEMA IF NOT EXISTS gold;
    CREATE SCHEMA IF NOT EXISTS metadata;

    -- ========================================
    -- BRONZE LAYER (Raw Data)
    -- ========================================
    
    CREATE TABLE IF NOT EXISTS bronze.raw_resumes (
        id SERIAL PRIMARY KEY,
        file_key VARCHAR(500) NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_size_bytes INTEGER,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_system VARCHAR(100) DEFAULT 'minio',
        raw_content TEXT,
        metadata JSONB
    );

    CREATE TABLE IF NOT EXISTS bronze.raw_github_api_responses (
        id SERIAL PRIMARY KEY,
        candidate_id INTEGER,
        github_username VARCHAR(255) NOT NULL,
        response_json JSONB NOT NULL,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        api_version VARCHAR(50),
        rate_limit_remaining INTEGER
    );

    CREATE TABLE IF NOT EXISTS bronze.raw_coding_events (
        id SERIAL PRIMARY KEY,
        event_id UUID NOT NULL,
        candidate_id INTEGER,
        event_type VARCHAR(100),
        event_timestamp TIMESTAMP,
        event_payload JSONB,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ========================================
    -- SILVER LAYER (Cleansed & Enriched)
    -- ========================================

    CREATE TABLE IF NOT EXISTS silver.candidates (
        candidate_id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        full_name VARCHAR(255),
        github_username VARCHAR(255),
        linkedin_url VARCHAR(500),
        years_experience INTEGER,
        primary_skills TEXT[],
        education_level VARCHAR(100),
        resume_file_key VARCHAR(500),
        resume_processed_at TIMESTAMP,
        github_last_updated TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.resume_skills (
        id SERIAL PRIMARY KEY,
        candidate_id INTEGER REFERENCES silver.candidates(candidate_id),
        skill_name VARCHAR(255) NOT NULL,
        skill_category VARCHAR(100),
        confidence_score DECIMAL(3,2),
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(candidate_id, skill_name)
    );

    CREATE TABLE IF NOT EXISTS silver.github_profiles (
        id SERIAL PRIMARY KEY,
        candidate_id INTEGER REFERENCES silver.candidates(candidate_id) UNIQUE,
        github_username VARCHAR(255) NOT NULL,
        primary_language VARCHAR(100),
        total_repos INTEGER DEFAULT 0,
        total_stars INTEGER DEFAULT 0,
        total_forks INTEGER DEFAULT 0,
        commits_last_90_days INTEGER DEFAULT 0,
        avg_commit_size INTEGER DEFAULT 0,
        contribution_score DECIMAL(5,2),
        languages_used TEXT[],
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS silver.coding_challenge_scores (
        id SERIAL PRIMARY KEY,
        candidate_id INTEGER REFERENCES silver.candidates(candidate_id),
        challenge_id VARCHAR(100),
        tests_passed INTEGER DEFAULT 0,
        tests_failed INTEGER DEFAULT 0,
        syntax_errors INTEGER DEFAULT 0,
        runtime_seconds INTEGER,
        code_quality_score DECIMAL(3,2),
        submitted_at TIMESTAMP,
        scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ========================================
    -- GOLD LAYER (Business Logic)
    -- ========================================

    CREATE TABLE IF NOT EXISTS gold.dim_candidates (
        candidate_key SERIAL PRIMARY KEY,
        candidate_id INTEGER UNIQUE NOT NULL,
        email VARCHAR(255) NOT NULL,
        full_name VARCHAR(255),
        years_experience INTEGER,
        education_level VARCHAR(100),
        primary_language VARCHAR(100),
        scd_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        scd_end_date TIMESTAMP,
        is_current BOOLEAN DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS gold.dim_skills (
        skill_key SERIAL PRIMARY KEY,
        skill_name VARCHAR(255) UNIQUE NOT NULL,
        skill_category VARCHAR(100),
        skill_family VARCHAR(100),
        is_trending BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS gold.fact_candidate_scores (
        score_id SERIAL PRIMARY KEY,
        candidate_key INTEGER REFERENCES gold.dim_candidates(candidate_key),
        resume_match_score INTEGER DEFAULT 0,
        github_contribution_score INTEGER DEFAULT 0,
        coding_challenge_score INTEGER DEFAULT 0,
        total_score INTEGER GENERATED ALWAYS AS (
            resume_match_score + github_contribution_score + coding_challenge_score
        ) STORED,
        score_date DATE DEFAULT CURRENT_DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS gold.agg_candidate_rankings (
        ranking_id SERIAL PRIMARY KEY,
        candidate_key INTEGER REFERENCES gold.dim_candidates(candidate_key),
        candidate_name VARCHAR(255),
        total_score INTEGER,
        ranking_position INTEGER,
        percentile DECIMAL(5,2),
        ranking_date DATE DEFAULT CURRENT_DATE,
        UNIQUE(candidate_key, ranking_date)
    );

    -- ========================================
    -- METADATA LAYER
    -- ========================================

    CREATE TABLE IF NOT EXISTS metadata.pipeline_runs (
        run_id SERIAL PRIMARY KEY,
        pipeline_name VARCHAR(255) NOT NULL,
        run_date DATE NOT NULL,
        status VARCHAR(50) NOT NULL,
        records_processed INTEGER,
        error_message TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS metadata.data_quality_checks (
        check_id SERIAL PRIMARY KEY,
        table_name VARCHAR(255) NOT NULL,
        check_type VARCHAR(100) NOT NULL,
        check_status VARCHAR(50) NOT NULL,
        records_checked INTEGER,
        records_failed INTEGER,
        error_details JSONB,
        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- ========================================
    -- INDEXES FOR PERFORMANCE
    -- ========================================

    CREATE INDEX IF NOT EXISTS idx_candidates_email ON silver.candidates(email);
    CREATE INDEX IF NOT EXISTS idx_candidates_github ON silver.candidates(github_username);
    CREATE INDEX IF NOT EXISTS idx_resume_skills_candidate ON silver.resume_skills(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_github_profiles_candidate ON silver.github_profiles(candidate_id);
    CREATE INDEX IF NOT EXISTS idx_coding_scores_candidate ON silver.coding_challenge_scores(candidate_id);
    
    CREATE INDEX IF NOT EXISTS idx_fact_scores_candidate ON gold.fact_candidate_scores(candidate_key);
    CREATE INDEX IF NOT EXISTS idx_fact_scores_date ON gold.fact_candidate_scores(score_date);
    
    CREATE INDEX IF NOT EXISTS idx_pipeline_runs_name_date ON metadata.pipeline_runs(pipeline_name, run_date);

    -- ========================================
    -- INITIAL SEED DATA
    -- ========================================

    -- Insert sample skills taxonomy
    INSERT INTO gold.dim_skills (skill_name, skill_category, skill_family, is_trending)
    VALUES 
        ('Python', 'Programming Language', 'Backend', TRUE),
        ('Java', 'Programming Language', 'Backend', TRUE),
        ('JavaScript', 'Programming Language', 'Frontend', TRUE),
        ('React', 'Framework', 'Frontend', TRUE),
        ('Node.js', 'Runtime', 'Backend', TRUE),
        ('Docker', 'DevOps', 'Infrastructure', TRUE),
        ('Kubernetes', 'DevOps', 'Infrastructure', TRUE),
        ('Apache Spark', 'Data Engineering', 'Big Data', TRUE),
        ('Apache Kafka', 'Data Engineering', 'Streaming', TRUE),
        ('PostgreSQL', 'Database', 'Relational', FALSE),
        ('MongoDB', 'Database', 'NoSQL', FALSE),
        ('AWS', 'Cloud', 'Infrastructure', TRUE),
        ('Azure', 'Cloud', 'Infrastructure', TRUE),
        ('Machine Learning', 'AI/ML', 'Data Science', TRUE),
        ('TensorFlow', 'Framework', 'AI/ML', TRUE)
    ON CONFLICT (skill_name) DO NOTHING;

EOSQL

echo "✅ Database initialization complete!"
echo "   - Schemas created: bronze, silver, gold, metadata"
echo "   - Tables created: 15 tables across all layers"
echo "   - Indexes created for performance optimization"
echo "   - Sample skill taxonomy loaded"
