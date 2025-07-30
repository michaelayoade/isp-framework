.PHONY: help test test-docker test-local build up down clean logs

# Default target
help:
	@echo "ISP Framework - Available Commands:"
	@echo ""
	@echo "  test         - Run full backend test suite in Docker (recommended)"
	@echo "  test-local   - Run tests in local venv (fast, limited services)"
	@echo "  build        - Build all Docker images"
	@echo "  up           - Start all services"
	@echo "  down         - Stop all services"
	@echo "  clean        - Remove containers, volumes, and images"
	@echo "  logs         - Show logs from all services"
	@echo ""

# Run full-stack tests in Docker with all services (Postgres, Redis, MinIO)
test: test-docker

test-docker:
	@echo "🧪 Running full-stack backend tests in Docker..."
	docker compose -f docker-compose.yml -f docker-compose.test.yml \
		run --rm backend-tests

# Run tests locally in venv (faster but limited service availability)
test-local:
	@echo "🧪 Running backend tests locally in venv..."
	cd backend && python -m pytest tests/ -v

# Build all Docker images
build:
	@echo "🔨 Building Docker images..."
	docker compose build

# Start all services
up:
	@echo "🚀 Starting all services..."
	docker compose up -d

# Stop all services
down:
	@echo "🛑 Stopping all services..."
	docker compose down

# Clean up containers, volumes, and images
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker compose down -v --remove-orphans
	docker system prune -f

# Show logs from all services
logs:
	@echo "📋 Showing logs from all services..."
	docker compose logs -f
