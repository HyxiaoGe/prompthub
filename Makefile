.PHONY: help init up down backend backend-local frontend test lint seed migrate sdk-test sdk-lint logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Infrastructure ===

up: ## Start all services (PostgreSQL + Redis + Backend)
	docker-compose up -d

down: ## Stop all services
	docker-compose down

up-infra: ## Start only PostgreSQL + Redis (no backend)
	docker-compose up -d postgres redis

wait-db: ## Wait for PostgreSQL to be ready
	@echo "Waiting for PostgreSQL..."
	@until docker exec prompthub-postgres pg_isready -U prompthub > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "PostgreSQL is ready."

init: ## First-time setup: Docker → wait DB → migrate → seed
	docker-compose up -d postgres redis
	@$(MAKE) wait-db
	cd backend && uv sync
	cd backend && uv run alembic upgrade head
	cd backend && uv run python -m scripts.seed_data
	docker-compose up -d backend
	@echo "Done! All services running. Visit http://localhost:8000/docs"

reset-db: ## Reset database (destroy + recreate)
	docker-compose down -v
	docker-compose up -d postgres
	@$(MAKE) wait-db
	cd backend && uv run alembic upgrade head
	cd backend && uv run python -m scripts.seed_data

# === Backend ===

backend: ## Start backend in Docker (background, with hot-reload)
	docker-compose up -d backend

backend-local: ## Start backend locally (foreground, for debugging)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

backend-rebuild: ## Rebuild backend image (after dependency changes)
	docker-compose build backend
	docker-compose up -d backend

logs: ## Tail backend logs
	docker-compose logs -f backend

logs-all: ## Tail all service logs
	docker-compose logs -f

# === Database ===

migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new msg="add xxx table")
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

seed: ## Load seed data
	cd backend && uv run python -m scripts.seed_data

# === Frontend ===

frontend: ## Start Next.js frontend (dev mode)
	cd frontend && pnpm dev

frontend-build: ## Build frontend for production
	cd frontend && pnpm build

# === Quality ===

test: ## Run backend tests
	cd backend && uv run pytest -v

lint: ## Lint backend code
	cd backend && uv run ruff check . && uv run ruff format --check .

format: ## Format backend code
	cd backend && uv run ruff format .

# === SDK ===

sdk-test: ## Run SDK tests
	cd sdk && uv run pytest -v

sdk-lint: ## Lint SDK code
	cd sdk && uv run ruff check . && uv run ruff format --check .

sdk-format: ## Format SDK code
	cd sdk && uv run ruff format .

# === All-in-one ===

dev: up frontend ## Start everything (Docker services + frontend)