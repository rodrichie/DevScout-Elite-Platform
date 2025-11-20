# DevScout Elite Platform - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Architecture](#data-architecture)
5. [Security Architecture](#security-architecture)
6. [Deployment Architecture](#deployment-architecture)
7. [Scalability & Performance](#scalability--performance)
8. [Monitoring & Observability](#monitoring--observability)

---

## System Overview

DevScout Elite Platform is a cloud-native, microservices-based hiring intelligence system that implements a modern data lakehouse architecture. The platform processes multi-source candidate data through a medallion architecture (Bronze → Silver → Gold) and provides real-time analytics and semantic search capabilities.

### Key Architectural Patterns

- **Medallion Architecture**: Progressive data refinement through Bronze, Silver, and Gold layers
- **Event-Driven Architecture**: Kafka-based async communication between services
- **Microservices**: Loosely coupled, independently deployable services
- **API-First**: RESTful API with OAuth2 authentication
- **Infrastructure as Code**: Docker Compose and Kubernetes manifests

---

## Architecture Principles

### 1. Separation of Concerns
- **Ingestion**: MinIO, Kafka
- **Processing**: Spark, Python scripts
- **Storage**: PostgreSQL, Weaviate
- **Orchestration**: Airflow
- **Serving**: FastAPI, Streamlit

### 2. Scalability
- **Horizontal Scaling**: Stateless services, containerized workloads
- **Vertical Scaling**: Resource limits configurable per service
- **Auto-scaling**: Kubernetes HPA for production

### 3. Reliability
- **Retry Logic**: Exponential backoff for external APIs
- **Health Checks**: Liveness and readiness probes
- **Data Quality**: Great Expectations validation
- **Pipeline Monitoring**: Airflow + Prometheus

### 4. Security
- **Authentication**: OAuth2 with JWT tokens
- **Authorization**: Role-based access control
- **Secrets Management**: Environment variables, Kubernetes secrets
- **Network Isolation**: Docker networks, Kubernetes namespaces

### 5. Observability
- **Logging**: Structured logging with Python logging
- **Metrics**: Prometheus exporters
- **Visualization**: Grafana dashboards
- **Tracing**: Pipeline execution tracking

---

## Component Architecture

### Ingestion Layer

#### MinIO (S3-Compatible Storage)
- **Purpose**: Store raw resume files (PDF/DOCX)
- **Scalability**: Distributed object storage
- **Integration**: boto3 client in Python scripts
- **Backup**: Configurable replication

#### Kafka (Message Broker)
- **Purpose**: Event streaming for coding challenges
- **Topics**: `coding-events`
- **Partitions**: Configurable for parallelism
- **Retention**: 7-day default

#### Airflow (Orchestration)
- **DAGs**: 
  - `resume_etl_v1`: 8 tasks for resume processing
  - `github_ingestion_v1`: 6 tasks for GitHub enrichment
- **Executor**: CeleryExecutor (production) / SequentialExecutor (dev)
- **Scheduling**: Cron expressions
- **Monitoring**: Built-in UI at port 8080

### Processing Layer

#### Apache Spark
- **Batch Processing**: Resume text extraction, NLP
- **Streaming**: Kafka consumer with windowed aggregations
- **Cluster**: 1 master + 2 workers (configurable)
- **Storage**: Parquet format for intermediate data

#### Python Scripts
- **Resume Parser**: PDF/DOCX extraction with OCR fallback
- **NLP Extractor**: spaCy + HuggingFace Transformers
- **GitHub Client**: REST API integration with rate limiting
- **Metrics Calculator**: Custom scoring algorithms

#### dbt (Transformations)
- **Models**: 7 SQL models (staging, dimensions, facts, aggregates)
- **Tests**: Data quality checks (uniqueness, not-null, relationships)
- **Documentation**: Auto-generated lineage

### Storage Layer

#### PostgreSQL (Analytical Database)
- **Schemas**: bronze, silver, gold, metadata
- **Extensions**: pgvector for vector search
- **Indexes**: B-tree, GIN for JSON columns
- **Partitioning**: Future enhancement for large tables

#### Weaviate (Vector Database)
- **Classes**: Candidate, Skill
- **Vectorizer**: text2vec-transformers
- **Query Types**: Near text, hybrid search
- **Scalability**: Horizontal sharding

### Serving Layer

#### FastAPI (REST API)
- **Endpoints**: 30+ for candidates, skills, GitHub, analytics
- **Authentication**: OAuth2 password flow with JWT
- **Validation**: Pydantic models
- **Documentation**: Auto-generated Swagger UI

#### Streamlit (Dashboard)
- **Pages**: 4 (Dashboard, Search, Monitoring, Analytics)
- **Charts**: Plotly for interactive visualizations
- **Caching**: 60-second TTL for queries
- **Refresh**: Configurable auto-refresh

---

## Data Architecture

### Medallion Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Bronze Layer (Raw)                                           │
├──────────────────────────────────────────────────────────────┤
│ - bronze.resumes: Raw resume files metadata                 │
│ - bronze.github_raw: Unprocessed GitHub API responses       │
│ - Minimal transformation, append-only                        │
└──────────────────────────────────────────────────────────────┘
                              │
                              v
┌──────────────────────────────────────────────────────────────┐
│ Silver Layer (Cleaned)                                       │
├──────────────────────────────────────────────────────────────┤
│ - silver.candidates: Deduplicated, validated candidate data │
│ - silver.resume_skills: Extracted skills with proficiency   │
│ - silver.github_profiles: Cleaned GitHub metrics            │
│ - Data quality checks applied                               │
└──────────────────────────────────────────────────────────────┘
                              │
                              v
┌──────────────────────────────────────────────────────────────┐
│ Gold Layer (Aggregated)                                      │
├──────────────────────────────────────────────────────────────┤
│ - gold.dim_candidates: Candidate dimension with enrichment  │
│ - gold.dim_skills: Skill dimension with popularity          │
│ - gold.fact_candidate_scores: Scoring fact table            │
│ - gold.agg_candidate_rankings: Rankings with percentiles    │
└──────────────────────────────────────────────────────────────┘
```

### Data Models

#### Candidate Domain
- **candidate_id** (PK): Auto-incrementing integer
- **candidate_name**: Full name
- **email** (Unique): Contact email
- **resume_text**: Full extracted text
- **skills**: Array/JSON of technical skills
- **years_experience**: Integer
- **education_level**: Enum (High School, Bachelor, Master, PhD)

#### Skills Domain
- **skill_id** (PK)
- **skill_name** (Unique)
- **skill_category**: Programming, Database, Cloud, etc.
- **candidate_count**: Number of candidates with skill
- **proficiency_levels**: Distribution of proficiency

#### GitHub Domain
- **github_id** (PK)
- **candidate_id** (FK)
- **github_username** (Unique)
- **metrics**: JSON with repos, stars, forks, contributions
- **quality_scores**: Calculated scores (0-100)

### Data Flow

1. **Ingestion**: Resume uploaded to MinIO → Airflow detects new file
2. **Extraction**: Parse PDF/DOCX → Extract text → Store in Bronze
3. **Enrichment**: NLP extraction → GitHub API calls → Validation
4. **Loading**: Insert into Silver → dbt transforms to Gold
5. **Serving**: FastAPI queries Gold → Streamlit visualizes

---

## Security Architecture

### Authentication Flow

```
1. User → POST /api/v1/auth/token (username + password)
2. API validates credentials against user database
3. API generates JWT token (30-min expiry)
4. User stores token
5. User → API requests with "Authorization: Bearer <token>"
6. API validates JWT signature and expiry
7. API extracts user role and applies RBAC
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all endpoints |
| **Recruiter** | Read-only access to candidates, skills, analytics |
| **User** | Basic search and view capabilities |

### Security Best Practices

- **Password Hashing**: bcrypt with salt
- **JWT Secrets**: Environment variables, rotatable
- **HTTPS**: TLS 1.3 in production
- **CORS**: Configurable allowed origins
- **SQL Injection**: Parameterized queries
- **XSS Prevention**: Output encoding in Streamlit

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
Services:
  - Airflow (scheduler, webserver, workers)
  - PostgreSQL (database)
  - MinIO (object storage)
  - Kafka + Zookeeper (streaming)
  - Spark (master + workers)
  - Weaviate (vector DB)
  - FastAPI (REST API)
  - Streamlit (dashboard)
  - Prometheus + Grafana (monitoring)
  - MLflow (ML tracking)

Networks:
  - devscout-network (internal)

Volumes:
  - postgres-data
  - minio-data
  - airflow-logs
```

### Kubernetes (Production)

```
Namespace: devscout

Deployments:
  - postgres (StatefulSet, 1 replica, 20Gi PVC)
  - fastapi (Deployment, 3-10 replicas with HPA)
  - weaviate (Deployment, 1 replica)
  - airflow-scheduler (Deployment, 1 replica)
  - airflow-webserver (Deployment, 2 replicas)

Services:
  - postgres-service (ClusterIP)
  - fastapi-service (LoadBalancer)
  - weaviate-service (ClusterIP)

ConfigMaps:
  - devscout-config (environment variables)

Secrets:
  - devscout-secrets (passwords, JWT keys)

Ingress:
  - devscout-ingress (HTTPS with cert-manager)

HorizontalPodAutoscaler:
  - fastapi-hpa (3-10 replicas, 70% CPU, 80% memory)
```

---

## Scalability & Performance

### Horizontal Scaling

- **FastAPI**: Stateless, scales to 10+ replicas
- **Spark Workers**: Add workers for more parallel tasks
- **Kafka Partitions**: Increase for higher throughput
- **PostgreSQL**: Read replicas for query workload

### Performance Optimizations

#### Database
- **Indexes**: B-tree on primary keys, foreign keys
- **Query Optimization**: EXPLAIN ANALYZE for slow queries
- **Connection Pooling**: SQLAlchemy pool (5-20 connections)
- **Materialized Views**: Pre-aggregated analytics

#### API
- **Caching**: Redis for frequently accessed data
- **Pagination**: Limit results to 100 max
- **Async I/O**: FastAPI async endpoints
- **Load Balancing**: Round-robin for K8s pods

#### Streaming
- **Batch Processing**: Spark micro-batches (5-10 sec)
- **Backpressure**: Kafka consumer lag monitoring
- **Windowing**: Tumbling windows for aggregations

### Capacity Planning

| Component | Dev | Prod (Small) | Prod (Large) |
|-----------|-----|--------------|--------------|
| FastAPI Replicas | 1 | 3 | 10 |
| Spark Workers | 2 | 3 | 10 |
| Kafka Partitions | 1 | 3 | 10 |
| PostgreSQL vCPU | 2 | 4 | 8 |
| PostgreSQL RAM | 4GB | 16GB | 64GB |
| Total RAM | 16GB | 64GB | 256GB |

---

## Monitoring & Observability

### Metrics (Prometheus)

- **Application Metrics**:
  - API request rate, latency, error rate
  - Database connection pool usage
  - Kafka consumer lag
  - Pipeline execution time

- **System Metrics**:
  - CPU, memory, disk usage per container
  - Network I/O
  - Garbage collection (Python)

### Dashboards (Grafana)

1. **API Dashboard**: Request rate, p95 latency, error rate by endpoint
2. **Pipeline Dashboard**: DAG success rate, task duration, failures
3. **Data Quality Dashboard**: Validation pass rate, data completeness
4. **Infrastructure Dashboard**: CPU, memory, disk, network

### Alerting Rules

- API error rate > 5% for 5 minutes
- Pipeline failure > 2 consecutive runs
- Database connection pool > 90% for 5 minutes
- Kafka consumer lag > 10,000 messages
- Disk usage > 85%

### Log Aggregation

- **Structured Logging**: JSON format with timestamps, levels, context
- **Centralized**: All logs to stdout/stderr, collected by Docker/K8s
- **Retention**: 7 days for development, 30 days for production
- **Search**: ELK stack (future enhancement)

---

## Future Enhancements

### Phase 2
- Multi-tenancy support
- Advanced ML models (candidate ranking predictions)
- Real-time dashboard updates (WebSockets)
- A/B testing framework

### Phase 3
- Terraform infrastructure code
- Disaster recovery strategy
- Cost optimization analysis
- Compliance certifications (GDPR, SOC2)

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Apache Airflow](https://airflow.apache.org/)
- [Apache Spark](https://spark.apache.org/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Weaviate](https://weaviate.io/)
- [Kubernetes](https://kubernetes.io/)

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-11-20  
**Maintained By**: DevScout Engineering Team
