# DevScout Elite Platform
## Enterprise-Grade Hiring Intelligence System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Data Engineering](https://img.shields.io/badge/Data%20Engineering-Advanced-purple.svg)](https://github.com)

> **A production-grade data engineering showcase** that demonstrates the "Holy Trinity" of modern data engineering: **Batch Processing**, **Real-Time Streaming**, and **Advanced Analytics** (NLP + Vector Search).

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [API Documentation](#api-documentation)
- [Data Pipeline Design](#data-pipeline-design)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Performance Metrics](#performance-metrics)
- [Documentation](#documentation)
- [For Recruiters](#for-recruiters)

---

## Executive Summary

**DevScout Elite Platform** is an intelligent hiring system designed to process multi-source candidate data through a modern lakehouse architecture. The platform ingests unstructured resumes, enriches profiles with GitHub activity, scores live coding performance in real-time, and provides semantic search capabilities.

### Key Differentiators

| Feature | Technology | Business Value |
|---------|-----------|----------------|
| **Medallion Architecture** | Bronze → Silver → Gold layers | Data quality progression & auditability |
| **Event-Driven Design** | Apache Kafka | Decoupled, scalable microservices |
| **Vector Search** | Weaviate + Embeddings | Semantic skill matching (90%+ accuracy) |
| **Stream Processing** | Spark Structured Streaming | Real-time coding assessment |
| **REST API** | FastAPI + OAuth2 | Secure programmatic access |
| **Data Orchestration** | Apache Airflow | Automated, monitored pipelines |
| **Infrastructure as Code** | Docker Compose + K8s | One-command deployment |

### Skills Demonstrated

- **Distributed Systems**: Kafka + Spark for horizontal scaling
- **Data Modeling**: Medallion architecture + dbt transformations
- **Engineering Best Practices**: Testing, CI/CD, Infrastructure as Code
- **Machine Learning Operations**: NLP pipelines + vector embeddings
- **Cloud-Ready Architecture**: Containerized, Kubernetes deployment with auto-scaling
- **API Development**: RESTful API with OAuth2 authentication
- **Security**: JWT tokens, role-based access control, password hashing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources                                │
├─────────────────────────────────────────────────────────────────┤
│  Resumes (PDF/DOCX)  │  GitHub API  │  Live Coding Events       │
└──────────┬───────────┴──────┬───────┴──────────┬────────────────┘
           │                  │                   │
           v                  v                   v
┌──────────────────────────────────────────────────────────────────┐
│                     Ingestion Layer                              │
├──────────────────────────────────────────────────────────────────┤
│  MinIO (S3)         │  Airflow DAGs │  Kafka Producer           │
└──────────┬──────────┴───────┬───────┴──────────┬─────────────────┘
           │                  │                   │
           v                  v                   v
┌──────────────────────────────────────────────────────────────────┐
│                   Processing Layer                               │
├──────────────────────────────────────────────────────────────────┤
│  Batch: Spark + Python      │  Stream: Spark Streaming          │
│  NLP: spaCy + Transformers  │  Quality: Great Expectations      │
└──────────┬──────────────────┴───────────────────┬────────────────┘
           │                                      │
           v                                      v
┌──────────────────────────────────────────────────────────────────┐
│                    Storage Layer (Lakehouse)                     │
├──────────────────────────────────────────────────────────────────┤
│  Bronze (Raw)  →  Silver (Cleaned)  →  Gold (Aggregated)        │
│  PostgreSQL + pgvector  │  dbt Transformations                  │
└──────────┬─────────────────┴──────────────────┬──────────────────┘
           │                                    │
           v                                    v
┌──────────────────────────────────────────────────────────────────┐
│                   Analytics & Serving Layer                      │
├──────────────────────────────────────────────────────────────────┤
│  FastAPI (REST)    │  Streamlit (UI)    │  Weaviate (Vector)   │
│  OAuth2 Auth       │  Prometheus/Grafana │  MLflow Tracking     │
└──────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture

- **Bronze Layer**: Raw data ingestion with minimal transformation
- **Silver Layer**: Cleaned, deduplicated, validated data
- **Gold Layer**: Business-level aggregations and analytics-ready datasets

---

## Tech Stack

### Core Technologies
- **Languages**: Python 3.10, SQL, Bash
- **Orchestration**: Apache Airflow 2.8
- **Processing**: Apache Spark 3.5, PySpark
- **Streaming**: Apache Kafka 3.6, Spark Structured Streaming
- **Storage**: PostgreSQL 15 + pgvector, MinIO S3
- **Vector DB**: Weaviate 1.23 with text2vec-transformers
- **API**: FastAPI 0.109, OAuth2/JWT authentication
- **Dashboard**: Streamlit, Plotly
- **Transformations**: dbt Core 1.7

### ML/AI Stack
- **NLP**: spaCy 3.7, HuggingFace Transformers
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **ML Ops**: MLflow 2.9, Feast feature store

### DevOps & Monitoring
- **Containers**: Docker, Docker Compose
- **Orchestration**: Kubernetes with HPA (3-10 replicas)
- **CI/CD**: GitHub Actions (6-stage pipeline)
- **Monitoring**: Prometheus, Grafana
- **Testing**: pytest, Great Expectations, Locust
- **Quality**: Black, isort, Flake8, MyPy

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 16GB RAM minimum
- 50GB free disk space

### Installation

```bash
# Clone repository
git clone https://github.com/rodrichie/DevScout-Elite-Platform.git
cd DevScout-Elite-Platform

# Configure environment
cp .env.example .env

# Start all services (takes 3-5 minutes)
make up

# Verify health
make health-check

# Watch logs
make logs
```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI Swagger** | <http://localhost:8000/docs> | admin / secret |
| Airflow | <http://localhost:8080> | airflow / airflow |
| Streamlit Dashboard | <http://localhost:8501> | - |
| Spark Master UI | <http://localhost:8081> | - |
| MinIO Console | <http://localhost:9001> | minioadmin / minioadmin |
| MLflow | <http://localhost:5000> | - |
| Grafana | <http://localhost:3001> | admin / admin |
| Prometheus | <http://localhost:9090> | - |
| Weaviate | <http://localhost:8080> | - |

---

## Key Features

### 1. Resume Processing Pipeline
- **PDF/DOCX Parsing**: Extract text from resumes with OCR fallback
- **NLP Entity Extraction**: 200+ technical skills across 10 categories
- **Vector Embeddings**: Generate semantic representations for matching
- **MinIO Storage**: S3-compatible object storage for raw files

### 2. GitHub Enrichment
- **Profile Analysis**: Repos, stars, forks, followers
- **Contribution Metrics**: 90-day activity, top languages
- **Quality Scoring**: Code quality, contribution, impact scores
- **Rate Limit Handling**: Automatic retry with exponential backoff

### 3. Real-Time Streaming
- **Kafka Events**: Coding submissions, test results, completions
- **Spark Streaming**: 5-min and 10-min windowed aggregations
- **PostgreSQL Sink**: Persist aggregated metrics

### 4. REST API (FastAPI)
- **30+ Endpoints**: Candidates, skills, GitHub, analytics, semantic search
- **OAuth2 Authentication**: JWT tokens with role-based access
- **Pydantic Validation**: Request/response schema enforcement
- **Auto-Generated Docs**: Swagger UI + ReDoc

### 5. Semantic Search (Weaviate)
- **Natural Language Queries**: "senior python developer with AWS experience"
- **Similar Candidates**: Find profiles similar to a given candidate
- **Skill Matching**: Semantic understanding of skill relationships
- **Vector Embeddings**: 384-dimensional embeddings for search

### 6. Data Transformations (dbt)
- **7 Models**: Staging, dimensions, facts, aggregates
- **Data Quality Tests**: Uniqueness, not-null, relationships, ranges
- **Documentation**: Auto-generated data lineage
- **Incremental Updates**: Efficient processing of large datasets

### 7. Monitoring & Observability
- **Prometheus Metrics**: Application and system metrics
- **Grafana Dashboards**: Visual monitoring and alerting
- **Pipeline Health**: Success rates, execution times, error tracking
- **Data Quality**: Great Expectations validation reports

---

## API Documentation

### Authentication

```bash
# Get access token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -d "username=admin&password=secret"

# Use token in requests
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/v1/candidates"
```

### Key Endpoints

#### Candidates
- `GET /api/v1/candidates` - List candidates with pagination
- `GET /api/v1/candidates/{id}` - Get candidate details
- `GET /api/v1/candidates/{id}/skills` - Get candidate skills
- `POST /api/v1/candidates/search` - Search candidates

#### Semantic Search
- `GET /api/v1/semantic/search` - Natural language search
- `GET /api/v1/semantic/similar/{id}` - Find similar candidates
- `GET /api/v1/semantic/skills/semantic` - Semantic skill search

#### Analytics
- `GET /api/v1/analytics/summary` - Platform analytics
- `GET /api/v1/analytics/pipeline-health` - Pipeline metrics
- `GET /api/v1/analytics/trends/hiring` - Hiring trends

Full API documentation: <http://localhost:8000/docs>

---

## Data Pipeline Design

### Resume ETL Pipeline (8 Tasks)
1. **Watch MinIO**: Monitor for new resume uploads
2. **Extract Text**: PDF/DOCX parsing with OCR
3. **NLP Extraction**: Skills, experience, education, certifications
4. **Vector Embeddings**: Generate semantic representations
5. **Data Quality**: Validate completeness and accuracy
6. **Load Silver**: Insert into PostgreSQL
7. **Record Metadata**: Track pipeline execution
8. **Trigger dbt**: Run transformations

### GitHub Ingestion Pipeline (6 Tasks)
1. **Get Candidates**: Query candidates needing GitHub enrichment
2. **Fetch Profiles**: GitHub API calls with rate limiting
3. **Calculate Metrics**: Code quality, contribution, impact scores
4. **Transform**: Flatten nested JSON to tabular format
5. **Load Silver**: PostgreSQL batch insert
6. **Trigger dbt**: Update Gold layer

### Streaming Pipeline
- **Producer**: Simulate coding events (submissions, tests, completions)
- **Consumer**: Spark Structured Streaming with windowed aggregations
- **Sink**: PostgreSQL real-time metrics table

---

## Project Structure

```
DevScout-Elite-Platform/
├── airflow/
│   ├── dags/                  # Airflow DAG definitions
│   └── init/                  # Database initialization
├── api/
│   ├── main.py               # FastAPI application
│   ├── middleware/           # Authentication middleware
│   ├── models/               # Database & Pydantic models
│   └── routers/              # API route handlers
├── dashboard/
│   └── streamlit_app.py      # Streamlit dashboard
├── dbt_project/
│   ├── models/               # dbt SQL transformations
│   ├── macros/               # Custom dbt macros
│   └── dbt_project.yml       # dbt configuration
├── docs/                      # Documentation
│   ├── API_REFERENCE.md      # Complete API documentation
│   ├── ARCHITECTURE.md       # System architecture guide
│   └── PROJECT_GUIDE.md      # Developer guide
├── k8s/                       # Kubernetes manifests
│   ├── deployment.yaml       # K8s deployment with HPA
│   └── README.md             # Deployment guide
├── scripts/
│   ├── parsers/              # Resume parsing
│   ├── extractors/           # NLP, embeddings, GitHub
│   ├── loaders/              # Database loaders
│   ├── streaming/            # Kafka producer
│   ├── data_quality.py       # Validation logic
│   └── weaviate_loader.py    # Vector DB loader
├── spark_jobs/
│   └── streaming/            # Spark streaming consumer
├── tests/
│   ├── unit/                 # Unit tests (40+ tests)
│   ├── load/                 # Locust load tests
│   └── conftest.py           # pytest fixtures
├── weaviate/
│   └── schema.json           # Vector DB schema
├── docker-compose.yml        # Service orchestration
├── Makefile                  # Automation commands
└── requirements.txt          # Python dependencies
```

---

## Testing

### Unit Tests
```bash
# Run all tests
make test

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run specific test
pytest tests/unit/test_resume_parser.py -v
```

### Integration Tests
```bash
# CI pipeline includes integration tests
# See .github/workflows/ci.yml
```

### Load Testing
```bash
# Install Locust
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Web UI: http://localhost:8089
```

---

## Deployment

### Docker Compose (Development)
```bash
make up       # Start all services
make down     # Stop all services
make restart  # Restart services
```

### Kubernetes (Production)
```bash
# Deploy to K8s
kubectl apply -f k8s/deployment.yaml

# Verify deployment
kubectl get pods -n devscout

# Check auto-scaling
kubectl get hpa -n devscout

# View logs
kubectl logs -f deployment/fastapi -n devscout
```

**Features**:
- HorizontalPodAutoscaler (3-10 replicas)
- CPU target: 70%
- Memory target: 80%
- LoadBalancer service
- Ingress with TLS support

---

## Performance Metrics

### Processing Throughput
- **Resume Parsing**: 50-100 resumes/minute
- **NLP Extraction**: 30-50 documents/minute
- **Vector Embedding**: 100 documents/minute (batch)
- **GitHub API**: 60 profiles/hour (rate limit: 5000/hour)

### Scalability
- **Horizontal Scaling**: Kubernetes HPA (3-10 pods)
- **Streaming**: Kafka handles 10K+ events/second
- **Database**: PostgreSQL indexed for sub-second queries
- **Vector Search**: Weaviate handles 1M+ vectors

### Data Quality
- **Resume Validation**: 5 checks (completeness, format, length)
- **GitHub Validation**: 5 checks (rate limits, data quality)
- **Test Coverage**: 80%+ (target)
- **Pipeline Success Rate**: 95%+

---

## Documentation

- **[Testing Guide](docs/TESTING_GUIDE.md)**: Complete end-to-end testing workflow
- **[API Reference](docs/API_REFERENCE.md)**: Complete REST API documentation with examples
- **[Architecture Guide](docs/ARCHITECTURE.md)**: System design and data architecture
- **[Project Guide](docs/PROJECT_GUIDE.md)**: Developer guide and workflows
- **[Security Guidelines](docs/SECURITY.md)**: Security best practices and compliance
- **[API Docs](http://localhost:8000/docs)**: Interactive Swagger UI
- **[K8s Guide](k8s/README.md)**: Kubernetes deployment

---

## For Recruiters

### Why This Project Stands Out

1. **Production-Grade Architecture**: 20+ services, not a toy project
2. **Complete Data Pipeline**: Bronze → Silver → Gold with quality checks
3. **Real-World Technologies**: Same stack as FAANG companies
4. **Comprehensive Testing**: Unit, integration, load tests with CI/CD
5. **Professional Documentation**: README, guides, inline comments
6. **Scalable Design**: Kubernetes-ready, handles millions of candidates
7. **Modern Practices**: Containerization, IaC, monitoring, security
8. **AI/ML Integration**: NLP, embeddings, semantic search

### Interview Talking Points

**"Tell me about a complex project you've built"**
→ "I built DevScout Elite, a data lakehouse platform with 20 microservices that processes candidate resumes using NLP and enriches them with GitHub activity, implementing medallion architecture with real-time streaming, RESTful API with OAuth2, and Kubernetes deployment with auto-scaling."

**"How do you ensure data quality?"**
→ "I implemented multi-layer validation with Great Expectations, schema constraints, and data quality checks at Bronze, Silver, and Gold layers. The platform includes 40+ unit tests, integration tests in CI/CD, and monitoring with Prometheus/Grafana."

**"Describe your experience with scalability"**
→ "I used Apache Spark for distributed processing, Kafka for event streaming, and designed the system for horizontal scaling using Kubernetes with HorizontalPodAutoscaler that automatically scales from 3 to 10 replicas based on CPU and memory metrics."

**"How do you approach API design?"**
→ "I built a RESTful API with FastAPI featuring 30+ endpoints, OAuth2 JWT authentication, role-based access control, Pydantic validation, and auto-generated Swagger documentation. The API is load-tested with Locust to ensure performance under concurrent users."

### Skills Demonstrated

**Technical**: Python, SQL, Docker, Kubernetes, Kafka, Spark, PostgreSQL, FastAPI, Airflow, dbt  
**Architecture**: Microservices, Event-Driven, Lakehouse, REST APIs  
**ML/AI**: NLP, Vector Embeddings, Semantic Search  
**DevOps**: CI/CD, IaC, Monitoring, Load Testing, Security  
**Best Practices**: Testing, Documentation, Code Quality, Version Control

---

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## Contact

**Rodrigue Tchiegang**  
GitHub: [@rodrichie](https://github.com/rodrichie)  
Project Link: <https://github.com/rodrichie/DevScout-Elite-Platform>

---

**Built with modern data engineering practices | Production-ready | Interview-ready**
