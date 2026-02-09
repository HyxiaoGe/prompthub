.PHONY: help up down backend frontend test lint seed migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Infrastructure ===

up: ## Start PostgreSQL + Redis
	docker-compose up -d

down: ## Stop all services
	docker-compose down

reset-db: ## Reset database (destroy + recreate)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 3
	cd backend && alembic upgrade head
	cd backend && python scripts/seed_data.py

# === Backend ===

backend: ## Start FastAPI backend (dev mode)
	cd backend && uvicorn app.main:app --reload --port 8000

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new msg="add xxx table")
	cd backend && alembic revision --autogenerate -m "$(msg)"

seed: ## Load seed data
	cd backend && python scripts/seed_data.py

# === Frontend ===

frontend: ## Start Next.js frontend (dev mode)
	cd frontend && pnpm dev

frontend-build: ## Build frontend for production
	cd frontend && pnpm build

# === Quality ===

test: ## Run backend tests
	cd backend && pytest -v

lint: ## Lint backend code
	cd backend && ruff check . && ruff format --check .

format: ## Format backend code
	cd backend && ruff format .

# === All-in-one ===

dev: up ## Start everything for development
	@echo "Starting backend and frontend..."
	@make -j2 backend frontend
