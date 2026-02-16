"""
DevScout Elite Platform - Sample Data Generator
Generates realistic candidate, skill, and GitHub profile data.
"""
import os
import sys
import time
import random
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)


def connect_db():
    """Connect to PostgreSQL with retries."""
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "devscout_dw")
    user = os.getenv("POSTGRES_USER", "devscout")
    password = os.getenv("POSTGRES_PASSWORD", "devscout_pass")

    for attempt in range(30):
        try:
            conn = psycopg2.connect(
                host=host, port=port, dbname=db, user=user, password=password
            )
            conn.autocommit = False
            print(f"  Connected to database on attempt {attempt + 1}")
            return conn
        except psycopg2.OperationalError:
            print(f"  Waiting for database... (attempt {attempt + 1}/30)")
            time.sleep(2)

    print("  Failed to connect to database after 30 attempts")
    sys.exit(1)


def check_already_seeded(conn):
    """Check if data already exists."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM silver.candidates")
    count = cursor.fetchone()[0]
    cursor.close()
    if count > 0:
        print(f"  Database already seeded ({count} candidates). Skipping.")
        return True
    return False


SKILLS = {
    "Programming Language": ["Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#", "Ruby", "PHP", "Scala", "Kotlin", "Swift"],
    "Framework": ["React", "Angular", "Vue.js", "Django", "Flask", "Spring Boot", "Express.js", "FastAPI", "Next.js", "TensorFlow", "PyTorch"],
    "DevOps": ["Docker", "Kubernetes", "Terraform", "Jenkins", "GitHub Actions", "CI/CD", "Ansible", "Helm"],
    "Database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB"],
    "Cloud": ["AWS", "Azure", "GCP", "Heroku", "DigitalOcean"],
    "Data Engineering": ["Apache Spark", "Apache Kafka", "Airflow", "dbt", "Snowflake", "Databricks", "Flink"],
    "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "MLOps", "scikit-learn"],
}

EDUCATION_LEVELS = ["Bachelor's", "Master's", "PhD", "Associate's", "Self-taught", "Bootcamp"]
LANGUAGES = ["Python", "JavaScript", "Java", "Go", "TypeScript", "Rust", "C++", "Ruby", "Scala", "Kotlin"]


def generate_candidates(n=300):
    """Generate candidate records."""
    candidates = []
    for i in range(n):
        years_exp = random.choices(
            range(0, 26),
            weights=[3, 5, 8, 10, 10, 9, 8, 7, 6, 5, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            k=1
        )[0]
        candidates.append({
            "email": f"candidate{i+1}@{fake.free_email_domain()}",
            "full_name": fake.name(),
            "github_username": f"{fake.user_name()}{random.randint(1,99)}",
            "linkedin_url": f"https://linkedin.com/in/{fake.user_name()}",
            "years_experience": years_exp,
            "primary_skills": random.sample(
                [s for skills in SKILLS.values() for s in skills],
                k=random.randint(3, 8)
            ),
            "education_level": random.choice(EDUCATION_LEVELS),
        })
    return candidates


def load_candidates(conn, candidates):
    """Load candidates into silver.candidates."""
    cursor = conn.cursor()
    values = [
        (
            c["email"], c["full_name"], c["github_username"],
            c["linkedin_url"], c["years_experience"], c["primary_skills"],
            c["education_level"]
        )
        for c in candidates
    ]
    execute_values(
        cursor,
        """INSERT INTO silver.candidates
            (email, full_name, github_username, linkedin_url,
             years_experience, primary_skills, education_level)
        VALUES %s
        ON CONFLICT (email) DO NOTHING
        RETURNING candidate_id""",
        values,
        template="(%s, %s, %s, %s, %s, %s::TEXT[], %s)"
    )
    ids = [row[0] for row in cursor.fetchall()]
    conn.commit()
    cursor.close()

    for i, cid in enumerate(ids):
        candidates[i]["candidate_id"] = cid
    print(f"  Loaded {len(ids)} candidates")
    return [c for c in candidates if "candidate_id" in c]


def generate_and_load_skills(conn, candidates):
    """Generate and load resume skills."""
    cursor = conn.cursor()
    rows = []
    for c in candidates:
        num_skills = random.randint(4, 12)
        all_skills = [(s, cat) for cat, skills in SKILLS.items() for s in skills]
        selected = random.sample(all_skills, min(num_skills, len(all_skills)))
        for skill_name, skill_category in selected:
            rows.append((
                c["candidate_id"],
                skill_name,
                skill_category,
                round(random.uniform(0.4, 1.0), 2),
            ))

    execute_values(
        cursor,
        """INSERT INTO silver.resume_skills
            (candidate_id, skill_name, skill_category, confidence_score)
        VALUES %s
        ON CONFLICT (candidate_id, skill_name) DO NOTHING""",
        rows
    )
    conn.commit()
    cursor.close()
    print(f"  Loaded {len(rows)} skill records")


def generate_and_load_github(conn, candidates):
    """Generate and load GitHub profiles."""
    cursor = conn.cursor()
    rows = []
    for c in candidates:
        if random.random() < 0.15:
            continue
        repos = random.randint(5, 120)
        stars = random.randint(0, repos * 20)
        forks = random.randint(0, stars // 3 + 1)
        commits = random.randint(10, 500)
        rows.append((
            c["candidate_id"],
            c["github_username"],
            random.choice(LANGUAGES),
            repos,
            stars,
            forks,
            commits,
            random.randint(50, 500),
            round(random.uniform(20, 95), 2),
            random.sample(LANGUAGES, k=random.randint(2, 5)),
        ))

    execute_values(
        cursor,
        """INSERT INTO silver.github_profiles
            (candidate_id, github_username, primary_language,
             total_repos, total_stars, total_forks,
             commits_last_90_days, avg_commit_size,
             contribution_score, languages_used)
        VALUES %s
        ON CONFLICT (candidate_id) DO NOTHING""",
        rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::TEXT[])"
    )
    conn.commit()
    cursor.close()
    print(f"  Loaded {len(rows)} GitHub profiles")


def generate_and_load_coding_challenges(conn, candidates):
    """Generate coding challenge scores."""
    cursor = conn.cursor()
    rows = []
    for c in candidates:
        num_challenges = random.randint(0, 5)
        for j in range(num_challenges):
            passed = random.randint(5, 20)
            failed = random.randint(0, 5)
            rows.append((
                c["candidate_id"],
                f"challenge-{random.randint(100,999)}",
                passed,
                failed,
                random.randint(0, 3),
                random.randint(30, 600),
                round(random.uniform(0.3, 1.0), 2),
                fake.date_time_between(start_date="-60d", end_date="now"),
            ))

    execute_values(
        cursor,
        """INSERT INTO silver.coding_challenge_scores
            (candidate_id, challenge_id, tests_passed, tests_failed,
             syntax_errors, runtime_seconds, code_quality_score, submitted_at)
        VALUES %s""",
        rows
    )
    conn.commit()
    cursor.close()
    print(f"  Loaded {len(rows)} coding challenge scores")


def populate_gold_layer(conn):
    """Populate gold layer aggregates."""
    cursor = conn.cursor()

    # dim_candidates
    cursor.execute("""
        INSERT INTO gold.dim_candidates
            (candidate_id, email, full_name, years_experience,
             education_level, primary_language)
        SELECT
            c.candidate_id,
            c.email,
            c.full_name,
            c.years_experience,
            c.education_level,
            g.primary_language
        FROM silver.candidates c
        LEFT JOIN silver.github_profiles g ON c.candidate_id = g.candidate_id
        ON CONFLICT (candidate_id) DO NOTHING
    """)
    print("  Populated gold.dim_candidates")

    # fact_candidate_scores
    cursor.execute("""
        INSERT INTO gold.fact_candidate_scores
            (candidate_key, resume_match_score, github_contribution_score,
             coding_challenge_score, score_date)
        SELECT
            dc.candidate_key,
            (30 + random() * 70)::INTEGER as resume_match_score,
            COALESCE(
                (g.contribution_score * 0.6 + g.total_stars * 0.01 + g.total_repos * 0.1)::INTEGER,
                (20 + random() * 40)::INTEGER
            ) as github_contribution_score,
            COALESCE(
                (SELECT AVG(cs.code_quality_score) * 100
                 FROM silver.coding_challenge_scores cs
                 WHERE cs.candidate_id = dc.candidate_id)::INTEGER,
                (25 + random() * 50)::INTEGER
            ) as coding_challenge_score,
            CURRENT_DATE
        FROM gold.dim_candidates dc
        LEFT JOIN silver.github_profiles g ON dc.candidate_id = g.candidate_id
    """)
    print("  Populated gold.fact_candidate_scores")

    # agg_candidate_rankings
    cursor.execute("""
        INSERT INTO gold.agg_candidate_rankings
            (candidate_key, candidate_name, total_score,
             ranking_position, percentile, ranking_date)
        SELECT
            fs.candidate_key,
            dc.full_name,
            fs.total_score,
            ROW_NUMBER() OVER (ORDER BY fs.total_score DESC) as ranking_position,
            ROUND(
                (PERCENT_RANK() OVER (ORDER BY fs.total_score ASC) * 100)::DECIMAL,
                2
            ) as percentile,
            CURRENT_DATE
        FROM gold.fact_candidate_scores fs
        JOIN gold.dim_candidates dc ON fs.candidate_key = dc.candidate_key
        ON CONFLICT (candidate_key, ranking_date) DO NOTHING
    """)
    print("  Populated gold.agg_candidate_rankings")

    # Pipeline metadata
    for pipeline in ["resume_etl", "github_ingestion", "coding_challenge_processor"]:
        for days_ago in range(7):
            cursor.execute("""
                INSERT INTO metadata.pipeline_runs
                    (pipeline_name, run_date, status, records_processed, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                pipeline,
                datetime.now().date() - timedelta(days=days_ago),
                random.choice(["success", "success", "success", "success", "failed"]),
                random.randint(50, 500),
                datetime.now() - timedelta(days=days_ago, hours=random.randint(1, 12)),
                datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 1)),
            ))
    print("  Populated metadata.pipeline_runs")

    conn.commit()
    cursor.close()


def main():
    """Main execution."""
    print("=" * 50)
    print("  DEVSCOUT ELITE -- DATA SEEDER")
    print("=" * 50)

    conn = connect_db()

    if check_already_seeded(conn):
        return

    print("\n  Generating candidates...")
    candidates = generate_candidates(n=300)
    candidates = load_candidates(conn, candidates)

    print("  Generating skills...")
    generate_and_load_skills(conn, candidates)

    print("  Generating GitHub profiles...")
    generate_and_load_github(conn, candidates)

    print("  Generating coding challenges...")
    generate_and_load_coding_challenges(conn, candidates)

    print("\n  Populating gold layer...")
    populate_gold_layer(conn)

    conn.close()

    print("\n  Data generation complete!")
    print(f"    Candidates: {len(candidates)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
