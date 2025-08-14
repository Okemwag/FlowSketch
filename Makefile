# FlowSketch Docker Management

.PHONY: help build up down logs shell test clean migrate collectstatic createsuperuser

# Default target
help:
	@echo "FlowSketch Docker Commands:"
	@echo "  build          - Build all Docker images"
	@echo "  up             - Start all services in development mode"
	@echo "  up-prod        - Start all services in production mode"
	@echo "  down           - Stop all services"
	@echo "  logs           - Show logs from all services"
	@echo "  logs-backend   - Show logs from backend service"
	@echo "  shell          - Open shell in backend container"
	@echo "  shell-db       - Open PostgreSQL shell"
	@echo "  test           - Run tests in backend container"
	@echo "  migrate        - Run Django migrations"
	@echo "  collectstatic  - Collect static files"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  clean          - Remove all containers, images, and volumes"
	@echo "  restart        - Restart all services"

# Build all images
build:
	docker-compose build

# Development commands
up:
	docker-compose up -d
	@echo "Services started. Backend available at http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/api/docs/"

up-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production services started. Backend available at http://localhost"

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

# Shell access
shell:
	docker-compose exec backend python manage.py shell

shell-db:
	docker-compose exec db psql -U postgres -d flowsketch

# Django management commands
migrate:
	docker-compose exec backend python manage.py migrate

collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

# Testing
test:
	docker-compose exec backend python -m pytest

test-coverage:
	docker-compose exec backend python -m pytest --cov=. --cov-report=html

# Maintenance
restart:
	docker-compose restart

clean:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -f

# Database operations
db-reset:
	docker-compose down
	docker volume rm flowsketch_postgres_data
	docker-compose up -d db
	sleep 10
	make migrate
	make createsuperuser

# Backup and restore
backup-db:
	docker-compose exec db pg_dump -U postgres flowsketch > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T db psql -U postgres flowsketch < $$backup_file

# Development helpers
dev-setup:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	make build
	make up
	sleep 15
	make migrate
	@echo "Development environment ready!"

# Production deployment
prod-deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py migrate
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
	@echo "Production deployment complete!"

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/api/docs/ > /dev/null 2>&1 && echo "✓ Backend is healthy" || echo "✗ Backend is not responding"
	@docker-compose exec db pg_isready -U postgres > /dev/null 2>&1 && echo "✓ Database is healthy" || echo "✗ Database is not responding"
	@docker-compose exec redis redis-cli ping > /dev/null 2>&1 && echo "✓ Redis is healthy" || echo "✗ Redis is not responding"