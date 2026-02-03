# E-Commerce Data Warehouse Makefile
# Provides convenient commands for development and deployment

.PHONY: help build up down logs clean test lint format docs backup restore

# Default target
help: ## Show this help message
	@echo "E-Commerce Data Warehouse - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# DEVELOPMENT COMMANDS
# =============================================================================

build: ## Build all Docker containers
	@echo "Building Docker containers..."
	docker-compose build --no-cache

up: ## Start all services
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started. Access points:"
	@echo "  - Airflow UI: http://localhost:8080"
	@echo "  - Monitoring Dashboard: http://localhost:5000"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"

up-build: ## Build and start all services
	@echo "Building and starting all services..."
	docker-compose up --build -d

down: ## Stop all services
	@echo "Stopping all services..."
	docker-compose down

down-volumes: ## Stop all services and remove volumes
	@echo "Stopping all services and removing volumes..."
	docker-compose down -v

restart: ## Restart all services
	@echo "Restarting all services..."
	docker-compose restart

# =============================================================================
# MONITORING COMMANDS
# =============================================================================

logs: ## Show logs from all services
	docker-compose logs -f

logs-etl: ## Show ETL service logs
	docker-compose logs -f etl

logs-airflow: ## Show Airflow logs
	docker-compose logs -f airflow-webserver airflow-scheduler

logs-monitoring: ## Show monitoring service logs
	docker-compose logs -f monitoring

status: ## Show status of all services
	@echo "Service Status:"
	docker-compose ps

health: ## Check health of all services
	@echo "Health Check Results:"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# =============================================================================
# DATABASE COMMANDS
# =============================================================================

db-connect: ## Connect to PostgreSQL database
	docker-compose exec postgres psql -U postgres -d ecommerce_dw

db-backup: ## Backup PostgreSQL database
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres ecommerce_dw > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

db-restore: ## Restore PostgreSQL database from backup (usage: make db-restore BACKUP_FILE=backup.sql)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "Usage: make db-restore BACKUP_FILE=backup.sql"; \
		exit 1; \
	fi
	@echo "Restoring database from $(BACKUP_FILE)..."
	docker-compose exec -T postgres psql -U postgres -d ecommerce_dw < $(BACKUP_FILE)

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS ecommerce_dw;"; \
		docker-compose exec postgres psql -U postgres -c "CREATE DATABASE ecommerce_dw;"; \
		echo "Database reset complete."; \
	else \
		echo "Database reset cancelled."; \
	fi

# =============================================================================
# ETL COMMANDS
# =============================================================================

etl-run: ## Run ETL pipeline manually
	@echo "Running ETL pipeline..."
	docker-compose exec etl python main.py

etl-test: ## Run ETL tests
	@echo "Running ETL tests..."
	docker-compose exec etl python -m pytest tests/ -v

etl-validate: ## Run data validation checks
	@echo "Running data validation..."
	docker-compose exec etl python -c "from data_quality import DataQualityChecker; from database import DatabaseManager; db = DatabaseManager(); db.connect(); checker = DataQualityChecker(db); checker.run_all_checks(); checker.print_results()"

# =============================================================================
# AIRFLOW COMMANDS
# =============================================================================

airflow-init: ## Initialize Airflow database
	@echo "Initializing Airflow database..."
	docker-compose exec airflow-webserver airflow db init

airflow-user: ## Create Airflow admin user
	@echo "Creating Airflow admin user..."
	docker-compose exec airflow-webserver airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com \
		--password admin

airflow-dags: ## List Airflow DAGs
	docker-compose exec airflow-webserver airflow dags list

airflow-trigger: ## Trigger ETL DAG manually
	docker-compose exec airflow-webserver airflow dags trigger ecommerce_etl_pipeline

# =============================================================================
# TESTING COMMANDS
# =============================================================================

test: ## Run all tests
	@echo "Running all tests..."
	docker-compose exec etl python -m pytest tests/ -v
	@echo "Running data quality checks..."
	$(MAKE) etl-validate

test-data: ## Run data validation tests
	@echo "Running data validation tests..."
	docker-compose exec postgres psql -U postgres -d ecommerce_dw -f /app/test_queries.sql

test-performance: ## Run performance tests
	@echo "Running performance tests..."
	@time docker-compose exec etl python main.py

# =============================================================================
# CODE QUALITY COMMANDS
# =============================================================================

lint: ## Run code linting
	@echo "Running code linting..."
	docker-compose exec etl python -m flake8 . --max-line-length=100 --exclude=__pycache__

format: ## Format code with black
	@echo "Formatting code..."
	docker-compose exec etl python -m black . --line-length=100

type-check: ## Run type checking with mypy
	@echo "Running type checking..."
	docker-compose exec etl python -m mypy . --ignore-missing-imports

# =============================================================================
# CLEANUP COMMANDS
# =============================================================================

clean: ## Clean up Docker resources
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	@echo "Cleaning up all Docker resources..."
	docker-compose down -v --rmi all
	docker system prune -a -f
	docker volume prune -f

clean-logs: ## Clean up log files
	@echo "Cleaning up log files..."
	find . -name "*.log" -type f -delete
	docker-compose exec airflow-webserver find /opt/airflow/logs -name "*.log" -type f -delete

# =============================================================================
# DOCUMENTATION COMMANDS
# =============================================================================

docs: ## Generate documentation
	@echo "Generating documentation..."
	@echo "Documentation available in:"
	@echo "  - README.md"
	@echo "  - ARCHITECTURE.md"
	@echo "  - DATA_MODEL.md"
	@echo "  - PROJECT_SUMMARY.md"

docs-serve: ## Serve documentation locally (requires Python with mkdocs)
	@echo "Serving documentation..."
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo "mkdocs not found. Install with: pip install mkdocs"; \
	fi

# =============================================================================
# DEPLOYMENT COMMANDS
# =============================================================================

deploy-prod: ## Deploy to production (requires production docker-compose file)
	@echo "Deploying to production..."
	@if [ -f docker-compose.prod.yml ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d; \
	else \
		echo "Production configuration not found. Create docker-compose.prod.yml"; \
	fi

deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	@if [ -f docker-compose.staging.yml ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d; \
	else \
		echo "Staging configuration not found. Create docker-compose.staging.yml"; \
	fi

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

shell-etl: ## Open shell in ETL container
	docker-compose exec etl /bin/bash

shell-postgres: ## Open shell in PostgreSQL container
	docker-compose exec postgres /bin/bash

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

env-check: ## Check environment configuration
	@echo "Environment Configuration Check:"
	@echo "================================"
	@if [ -f .env ]; then \
		echo "✓ .env file exists"; \
	else \
		echo "✗ .env file missing (copy from .env.example)"; \
	fi
	@echo "Docker version: $$(docker --version)"
	@echo "Docker Compose version: $$(docker-compose --version)"

setup: ## Initial project setup
	@echo "Setting up E-Commerce Data Warehouse..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file from template"; \
	fi
	@echo "✓ Setup complete. Run 'make up' to start services."

# =============================================================================
# INFORMATION COMMANDS
# =============================================================================

info: ## Show project information
	@echo "E-Commerce Data Warehouse"
	@echo "========================"
	@echo "Version: 2.0.0"
	@echo "Services: PostgreSQL, Redis, ETL, Airflow, Monitoring"
	@echo "Data Volume: 284 source records, 895+ warehouse records"
	@echo "Technologies: Python, PostgreSQL, Apache Airflow, Redis, Docker"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup"
	@echo "  2. make up"
	@echo "  3. make airflow-user"
	@echo "  4. Open http://localhost:8080 (Airflow)"
	@echo "  5. Open http://localhost:5000 (Monitoring)"

ports: ## Show service ports
	@echo "Service Ports:"
	@echo "=============="
	@echo "PostgreSQL:    5432"
	@echo "Redis:         6379"
	@echo "Airflow UI:    8080"
	@echo "Monitoring:    5000"