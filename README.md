# 🚀 DevScout Elite Platform
## Enterprise-Grade Hiring Intelligence System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Data Engineering](https://img.shields.io/badge/Data%20Engineering-Advanced-purple.svg)](https://github.com)

> **A production-grade data engineering showcase** that demonstrates the "Holy Trinity" of modern data engineering: **Batch Processing**, **Real-Time Streaming**, and **Advanced Analytics** (NLP + Vector Search).

---

## 📋 Table of Contents

- [Executive Summary](#executive-summary)
- [Architecture Overview](#architecture-overview)
- [Tech Stack & Justification](#tech-stack--justification)
- [Quick Start](#quick-start)
- [Data Pipeline Design](#data-pipeline-design)
- [Project Structure](#project-structure)
- [Advanced Features](#advanced-features)
- [Performance Metrics](#performance-metrics)
- [For Recruiters](#for-recruiters)

---

## 🎯 Executive Summary

**DevScout Elite Platform** is an intelligent hiring system designed to process multi-source candidate data through a modern lakehouse architecture. The platform ingests unstructured resumes, enriches profiles with GitHub activity, and scores live coding performance in real-time.

### 🏆 Key Differentiators

| Feature | Technology | Business Value |
|---------|-----------|----------------|
| **Medallion Architecture** | Bronze → Silver → Gold layers | Data quality progression & auditability |
| **Event-Driven Design** | Apache Kafka | Decoupled, scalable microservices |
| **Vector Search** | Weaviate + Embeddings | Semantic skill matching (90%+ accuracy) |
| **Stream Processing** | Spark Structured Streaming | Real-time coding assessment |
| **Data Orchestration** | Apache Airflow | Automated, monitored pipelines |
| **Infrastructure as Code** | Docker Compose | One-command deployment |

### 💼 Skills Demonstrated

✅ **Distributed Systems**: Kafka + Spark for horizontal scaling  
✅ **Data Modeling**: Medallion architecture + dbt transformations  
✅ **Engineering Best Practices**: Testing, CI/CD, Infrastructure as Code  
✅ **Machine Learning Operations**: NLP pipelines + vector embeddings  
✅ **Cloud-Ready Architecture**: Containerized, AWS/Azure compatible

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
├──────────────┬──────────────────────┬─────────────────────────┤
│   Resumes    │   GitHub API         │   Live Coding Events   │
│  (PDF/DOCX)  │   (REST/GraphQL)     │   (Kafka Streams)      │
└──────┬───────┴──────────┬───────────┴──────────┬──────────────┘
       │                  │                       │
       v                  v                       v
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
├─────────────┬──────────────────────┬──────────────────────────┤
│  Airflow    │   Kafka Connect      │   Kafka Producers        │
│  (Batch)    │   (CDC/API)          │   (Real-time Events)     │
└─────┬───────┴──────────┬───────────┴──────────┬───────────────┘
      │                  │                       │
      v                  v                       v
┌─────────────────────────────────────────────────────────────────┐
│                 BRONZE LAYER (Raw Data Lake)                     │
│   MinIO S3 Compatible Storage | Delta Lake Format                │
│   Partitioned by: date, source, candidate_id                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│              PROCESSING LAYER (Spark + dbt)                      │
├─────────────────────┬──────────────────────────────────────────┤
│  Apache Spark       │   dbt Core (SQL Transformations)          │
│  - PySpark ETL      │   - Data Quality Tests                    │
│  - ML Feature Eng   │   - Incremental Models                    │
│  - NLP Pipeline     │   - Business Logic                        │
└─────────┬───────────┴──────────┬───────────────────────────────┘
          │                      │
          v                      v
┌─────────────────────────────────────────────────────────────────┐
│          SILVER LAYER (Cleaned & Validated)                      │
│   Delta Tables | Great Expectations Quality Checks               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│                GOLD LAYER (Analytics-Ready)                      │
│   Postgres Data Warehouse | Fact & Dimension Tables              │
│   + Vector Database (Weaviate) for Semantic Search               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────────┐
│                     SERVING LAYER                                │
├──────────────────┬──────────────────────────────────────────────┤
│  GraphQL API     │   Streamlit Dashboard  │   ML Inference API  │
│  (FastAPI)       │   (Analytics)          │   (Feast + MLflow)  │
└──────────────────┴────────────────────────┴─────────────────────┘
```

---

## 🎨 Key Features That Make This Stand Out

### 1. **Event-Driven Architecture**
- Kafka topics for each data domain (resumes, github, coding_challenges)
- Schema Registry with Avro for type safety
- Dead Letter Queues for error handling

### 2. **Delta Lake (ACID Transactions)**
- Time travel for debugging
- MERGE operations for upserts
- Schema evolution without breaking pipelines

### 3. **Feature Store (Feast)**
- Centralized feature definitions
- Consistent train/serve features
- Point-in-time correct joins

### 4. **Advanced NLP**
- Resume skill extraction with spaCy + custom models
- Semantic similarity with sentence-transformers
- Job description matching using cosine similarity

### 5. **Real-time ML Inference**
- Streaming feature computation
- Sub-100ms prediction latency
- A/B testing framework ready

### 6. **Full Observability**
- Prometheus metrics for all pipelines
- Grafana dashboards for monitoring
- OpenTelemetry traces across services
- Data lineage with dbt docs

### 7. **Data Quality as Code**
- Great Expectations checkpoints in CI/CD
- Automated alerts on quality issues
- Contract testing between layers

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | Apache Airflow | DAG-based workflow management |
| **Streaming** | Kafka + Zookeeper | Event bus & message broker |
| **Batch Processing** | Apache Spark (PySpark) | Distributed data processing |
| **Data Lake** | MinIO (S3 compatible) | Object storage |
| **Table Format** | Delta Lake | ACID transactions on data lake |
| **Transformation** | dbt Core | SQL-based transformations |
| **Data Warehouse** | PostgreSQL 15 | Structured analytics |
| **Vector Search** | Weaviate | Semantic similarity search |
| **Feature Store** | Feast | ML feature management |
| **ML Tracking** | MLflow | Experiment tracking |
| **API** | FastAPI + Strawberry GraphQL | Data serving layer |
| **Dashboard** | Streamlit | Interactive analytics |
| **Monitoring** | Prometheus + Grafana | Metrics & visualization |
| **Data Quality** | Great Expectations | Automated testing |
| **Containerization** | Docker + Docker Compose | Local development |
| **IaC (Optional)** | Terraform | Cloud deployment ready |

---

## 🚦 Quick Start

### Prerequisites
- Docker Desktop 4.20+
- Docker Compose 2.17+
- 16GB RAM minimum (32GB recommended)
- 50GB free disk space

### Launch the Platform

```powershell
# Clone the repository
git clone https://github.com/yourusername/devscout-elite.git
cd devscout-elite

# Start all services (takes 3-5 minutes first time)
make up

# Check service health
make health

# View logs
make logs
```

**Access Points:**
- Airflow: http://localhost:8080 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Grafana: http://localhost:3001 (admin/admin)
- Streamlit Dashboard: http://localhost:8501
- GraphQL API: http://localhost:8000/graphql

---

## 📊 Data Pipelines

### 1. Resume Processing Pipeline (`resume_etl_dag`)

**Schedule:** Triggered on file upload to MinIO  
**Runtime:** ~2-5 minutes per batch

```python
extract_resume → parse_text → extract_skills → 
generate_embeddings → quality_check → load_to_silver
```

**Key Features:**
- OCR for scanned PDFs (Tesseract)
- Multi-language support (spaCy models: en, es, fr)
- Named Entity Recognition: Skills, Education, Experience
- Vector embeddings: `all-MiniLM-L6-v2` (384 dimensions)

### 2. GitHub Activity Analyzer (`github_ingestion_dag`)

**Schedule:** Daily at 2 AM UTC  
**Runtime:** ~10 minutes for 1000 candidates

```python
fetch_profile → analyze_repos → calculate_metrics → 
detect_tech_stack → compute_contributions → load_to_silver
```

**Metrics Calculated:**
- Commit frequency & patterns
- Code review participation
- Language proficiency scores
- Open source contribution index
- Repository quality score

### 3. Live Coding Stream Processor (`coding_challenge_streaming`)

**Mode:** Continuous (24/7)  
**Latency:** <500ms end-to-end

```python
kafka_consume → spark_streaming → window_aggregations → 
ml_inference → postgres_sink
```

**Real-time Metrics:**
- Syntax errors per minute
- Test pass rate
- Code execution time
- Problem-solving patterns
- Candidate stress indicators

### 4. ML Feature Pipeline (`feature_engineering_dag`)

**Schedule:** Every 6 hours  
**Runtime:** ~15 minutes

```python
compute_features → feast_materialize → model_training → 
mlflow_tracking → model_registry
```

---

## 🧪 Data Quality Framework

### Great Expectations Suites

```yaml
Bronze Layer Checks:
  - File format validation
  - Schema conformance
  - Null value thresholds

Silver Layer Checks:
  - Referential integrity
  - Business rule validation
  - Statistical bounds

Gold Layer Checks:
  - Aggregation accuracy
  - Completeness metrics
  - Freshness SLAs
```

### dbt Tests

- **Uniqueness**: Primary keys across all models
- **Not Null**: Critical fields validation
- **Accepted Values**: Enum fields
- **Relationships**: Foreign key integrity
- **Custom**: Domain-specific logic

---

## 📈 Monitoring & Observability

### Grafana Dashboards

1. **Pipeline Health Dashboard**
   - Task success rates
   - Processing durations
   - Error rates by pipeline

2. **Data Quality Dashboard**
   - GX validation results
   - Data freshness metrics
   - Volume anomalies

3. **ML Model Performance**
   - Prediction latency
   - Model accuracy over time
   - Feature drift detection

### Prometheus Metrics

```python
# Custom metrics exposed
pipeline_duration_seconds
data_quality_score
candidate_processing_rate
vector_search_latency_ms
kafka_consumer_lag
```

---

## 🔬 Advanced Features

### Semantic Resume Search

```python
# Vector similarity search
query = "Senior Python engineer with Kubernetes experience"
results = weaviate_client.search(
    query_vector=embed(query),
    top_k=10,
    min_similarity=0.85
)
```

### Real-time Candidate Scoring

```python
# Streaming ML inference
features = feast_client.get_online_features(
    feature_refs=["candidate:skill_match", "candidate:experience_years"],
    entity_rows=[{"candidate_id": 12345}]
)
score = model.predict(features)
```

### A/B Testing Framework

```python
# Split traffic between models
if candidate_id % 2 == 0:
    model = mlflow.load_model("champion")
else:
    model = mlflow.load_model("challenger")
```

---

## 📁 Project Structure

```
devscout-elite/
├── airflow/
│   ├── dags/
│   │   ├── resume_etl_dag.py
│   │   ├── github_ingestion_dag.py
│   │   ├── feature_engineering_dag.py
│   │   └── ml_training_dag.py
│   ├── plugins/
│   └── config/
├── dbt_project/
│   ├── models/
│   │   ├── bronze/
│   │   ├── silver/
│   │   └── gold/
│   ├── tests/
│   └── macros/
├── spark_jobs/
│   ├── resume_processor.py
│   ├── github_analyzer.py
│   └── streaming_consumer.py
├── ml_models/
│   ├── training/
│   ├── inference/
│   └── feature_store/
├── api/
│   ├── graphql/
│   ├── rest/
│   └── websocket/
├── dashboard/
│   └── streamlit_app.py
├── infrastructure/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.spark
│   │   └── Dockerfile.airflow
│   ├── terraform/
│   └── kubernetes/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── monitoring/
│   ├── prometheus/
│   └── grafana/
├── scripts/
│   ├── generate_mock_data.py
│   ├── kafka_producer.py
│   └── db_migrations.py
├── Makefile
├── requirements.txt
└── README.md
```

---

## 🎓 Learning Outcomes

This project demonstrates:

✅ **Data Engineering Fundamentals**
- Batch vs. streaming processing
- ETL/ELT patterns
- Data modeling (Kimball dimensional)

✅ **Distributed Systems**
- Horizontal scaling with Spark
- Message queuing with Kafka
- Container orchestration

✅ **Modern Data Stack**
- Lakehouse architecture
- dbt for transformations
- Feature stores for ML

✅ **Software Engineering Best Practices**
- CI/CD pipelines
- Unit + integration testing
- Infrastructure as Code

✅ **ML Engineering**
- Feature engineering
- Model serving
- A/B testing

---

## 🚀 Roadmap

- [ ] **Phase 1**: Core Infrastructure (Week 1)
- [ ] **Phase 2**: Batch Pipelines (Week 2)
- [ ] **Phase 3**: Streaming Pipelines (Week 3)
- [ ] **Phase 4**: ML & Serving Layer (Week 4)
- [ ] **Phase 5**: Observability & Optimization (Week 5)

---

## 🤝 Contributing

This is a portfolio project, but feedback is welcome!

---

## 📄 License

MIT License - feel free to use this as inspiration for your own projects.

---

## 📞 Contact

**Your Name** | [LinkedIn](https://linkedin.com/in/yourprofile) | [GitHub](https://github.com/yourusername)

*Built to showcase advanced data engineering skills for top-tier roles*
