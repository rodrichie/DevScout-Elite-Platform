.PHONY: help up down restart logs ps clean test ci build-images init-db run-dbt seed-data

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)DevScout Elite Platform - Data Engineering Showcase$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Operations

up: ## Start all services (main command to launch platform)
	@echo "$(BLUE)🚀 Starting DevScout Elite Platform...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ All services started!$(NC)"
	@echo ""
	@echo "$(YELLOW)📍 Access Points:$(NC)"
	@echo "  • Airflow UI:    http://localhost:8080 (airflow/airflow)"
	@echo "  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
	@echo "  • Spark Master:  http://localhost:8089"
	@echo "  • Weaviate:      http://localhost:8081"
	@echo "  • Dashboard:     http://localhost:8501"
	@echo "  • API:           http://localhost:8000/docs"
	@echo "  • Grafana:       http://localhost:3001 (admin/admin)"
	@echo "  • Jupyter:       http://localhost:8888 (token: devscout)"
	@echo ""
	@echo "$(GREEN)Wait 60 seconds for all services to initialize, then run 'make ci'$(NC)"

down: ## Stop all services
	@echo "$(RED)⏹️  Stopping all services...$(NC)"
	@docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	@docker-compose restart

logs: ## View logs from all services
	@docker-compose logs -f

ps: ## Show running containers
	@docker-compose ps

clean: ## Stop services and remove all volumes (⚠️  DESTRUCTIVE)
	@echo "$(RED)⚠️  WARNING: This will delete all data!$(NC)"
	@echo "Press Ctrl+C to cancel or Enter to continue..."
	@read
	@docker-compose down -v
	@echo "$(GREEN)✅ Cleaned successfully$(NC)"

##@ Development

build-images: ## Build custom Docker images
	@echo "$(BLUE)🔨 Building custom Docker images...$(NC)"
	@docker-compose build

init-db: ## Initialize databases and create schemas
	@echo "$(BLUE)📊 Initializing databases...$(NC)"
	@docker-compose exec postgres psql -U devscout -d devscout_dw -f /docker-entrypoint-initdb.d/init.sh
	@echo "$(GREEN)✅ Database initialized$(NC)"

run-dbt: ## Run dbt transformations (Bronze → Silver → Gold)
	@echo "$(BLUE)🔄 Running dbt transformations...$(NC)"
	@docker-compose exec dbt dbt run --profiles-dir . --project-dir .
	@docker-compose exec dbt dbt test --profiles-dir . --project-dir .
	@echo "$(GREEN)✅ dbt run completed$(NC)"

seed-data: ## Load sample data for testing
	@echo "$(BLUE)🌱 Seeding sample data...$(NC)"
	@python scripts/seed_sample_data.py
	@echo "$(GREEN)✅ Sample data loaded$(NC)"

##@ Testing & Quality

e2e-test: ## Run end-to-end tests (complete platform test)
	@echo "$(BLUE)🎯 Running end-to-end tests...$(NC)"
	@python tests/e2e_test.py

upload-sample-data: ## Upload sample resumes to MinIO
	@echo "$(BLUE)📤 Uploading sample data...$(NC)"
	@python tests/upload_sample_data.py

quick-test: ## Quick validation of core services
	@echo "$(BLUE)⚡ Running quick tests...$(NC)"
	@curl -s http://localhost:8000/health && echo "$(GREEN)✅ API is healthy$(NC)" || echo "$(RED)❌ API is down$(NC)"
	@curl -s http://localhost:8080/health && echo "$(GREEN)✅ Airflow is healthy$(NC)" || echo "$(RED)❌ Airflow is down$(NC)"

ci: ## Run all tests and quality checks (run this after setup)
	@echo "$(BLUE)🧪 Running CI checks...$(NC)"
	@echo ""
	@echo "$(YELLOW)1️⃣  Unit Tests$(NC)"
	@docker-compose exec -T dbt pytest /usr/app/tests/unit -v
	@echo ""
	@echo "$(YELLOW)2️⃣  Data Quality Tests$(NC)"
	@python scripts/data_quality_check.py
	@echo ""
	@echo "$(YELLOW)3️⃣  Integration Tests$(NC)"
	@docker-compose exec -T dbt pytest /usr/app/tests/integration -v
	@echo ""
	@echo "$(GREEN)✅ All checks passed!$(NC)"

test: ## Run unit tests only
	@echo "$(BLUE)🧪 Running unit tests...$(NC)"
	@docker-compose exec dbt pytest /usr/app/tests/unit -v

test-integration: ## Run integration tests
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@docker-compose exec dbt pytest /usr/app/tests/integration -v

test-coverage: ## Generate test coverage report
	@echo "$(BLUE)📊 Generating coverage report...$(NC)"
	@docker-compose exec dbt pytest /usr/app/tests --cov=scripts --cov-report=html
	@echo "$(GREEN)✅ Coverage report generated at htmlcov/index.html$(NC)"

lint: ## Run code linting
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@docker-compose exec dbt black /usr/app --check
	@docker-compose exec dbt flake8 /usr/app
	@docker-compose exec dbt mypy /usr/app

format: ## Auto-format code
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@docker-compose exec dbt black /usr/app
	@docker-compose exec dbt isort /usr/app

##@ Data Pipelines

trigger-resume-pipeline: ## Manually trigger resume processing DAG
	@echo "$(BLUE)▶️  Triggering resume pipeline...$(NC)"
	@curl -X POST "http://localhost:8080/api/v1/dags/resume_etl_v1/dagRuns" \
		-H "Content-Type: application/json" \
		-u "airflow:airflow" \
		-d '{"conf":{}}'

trigger-github-pipeline: ## Manually trigger GitHub enrichment DAG
	@echo "$(BLUE)▶️  Triggering GitHub pipeline...$(NC)"
	@curl -X POST "http://localhost:8080/api/v1/dags/github_ingestion_v1/dagRuns" \
		-H "Content-Type: application/json" \
		-u "airflow:airflow" \
		-d '{"conf":{}}'

run-streaming: ## Start Kafka streaming job
	@echo "$(BLUE)🌊 Starting Kafka streaming consumer...$(NC)"
	@docker-compose exec spark-master spark-submit \
		--master spark://spark-master:7077 \
		--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
		/opt/spark-jobs/streaming/coding_events_consumer.py

##@ Monitoring

health-check: ## Check health of all services
	@echo "$(BLUE)❤️  Checking service health...$(NC)"
	@echo ""
	@echo "$(YELLOW)Postgres:$(NC) $$(docker-compose exec -T postgres pg_isready -U devscout && echo '✅ Healthy' || echo '❌ Down')"
	@echo "$(YELLOW)MinIO:$(NC)    $$(curl -s http://localhost:9000/minio/health/live && echo '✅ Healthy' || echo '❌ Down')"
	@echo "$(YELLOW)Kafka:$(NC)    $$(docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo '✅ Healthy' || echo '❌ Down')"
	@echo "$(YELLOW)Airflow:$(NC)  $$(curl -s http://localhost:8080/health && echo '✅ Healthy' || echo '❌ Down')"

stats: ## Show resource usage statistics
	@echo "$(BLUE)📊 Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

##@ Utilities

shell-airflow: ## Open shell in Airflow container
	@docker-compose exec airflow-webserver bash

shell-spark: ## Open shell in Spark Master container
	@docker-compose exec spark-master bash

shell-dbt: ## Open shell in dbt container
	@docker-compose exec dbt bash

shell-postgres: ## Open PostgreSQL CLI
	@docker-compose exec postgres psql -U devscout -d devscout_dw

backup-db: ## Backup PostgreSQL database
	@echo "$(BLUE)💾 Backing up database...$(NC)"
	@docker-compose exec -T postgres pg_dump -U devscout devscout_dw > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Backup complete$(NC)"

##@ Documentation

docs: ## Generate project documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	@docker-compose exec dbt dbt docs generate --profiles-dir . --project-dir .
	@docker-compose exec dbt dbt docs serve --port 8082
	@echo "$(GREEN)✅ Documentation available at http://localhost:8082$(NC)"

architecture-diagram: ## Generate architecture diagram
	@echo "$(BLUE)🏗️  Generating architecture diagram...$(NC)"
	@python scripts/generate_architecture_diagram.py
	@echo "$(GREEN)✅ Diagram saved to docs/architecture.png$(NC)"
