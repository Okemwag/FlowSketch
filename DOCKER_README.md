# FlowSketch Docker Setup

This document explains how to run FlowSketch using Docker and Docker Compose.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Make (optional, for using Makefile commands)

## Quick Start

1. **Clone the repository and navigate to the project directory**

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start the development environment**
   ```bash
   make dev-setup
   # OR manually:
   docker-compose build
   docker-compose up -d
   docker-compose exec backend python manage.py migrate
   ```

4. **Access the application**
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs/
   - Admin Interface: http://localhost:8000/admin/

## Services

The Docker Compose setup includes the following services:

### Core Services
- **backend**: Django application server
- **db**: PostgreSQL database
- **redis**: Redis for Celery message broker

### Background Services
- **celery_worker**: Celery worker for background tasks
- **celery_beat**: Celery beat scheduler

### Production Services
- **nginx**: Reverse proxy and static file server (production only)

## Environment Configuration

Key environment variables in `.env`:

```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=flowsketch
DB_USER=postgres
DB_PASSWORD=postgres

# Email (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Development Commands

Using Make (recommended):
```bash
make up              # Start all services
make down            # Stop all services
make logs            # View logs
make shell           # Django shell
make test            # Run tests
make migrate         # Run migrations
make createsuperuser # Create admin user
```

Using Docker Compose directly:
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f
docker-compose exec backend python manage.py shell
```

## Production Deployment

1. **Set up production environment**
   ```bash
   cp .env.example .env
   # Configure production values in .env
   ```

2. **Deploy with production configuration**
   ```bash
   make prod-deploy
   # OR manually:
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```

3. **Production features**
   - Gunicorn WSGI server
   - Nginx reverse proxy
   - Static file serving
   - Security headers
   - Rate limiting

## Database Management

### Migrations
```bash
make migrate
# OR
docker-compose exec backend python manage.py migrate
```

### Create Superuser
```bash
make createsuperuser
# OR
docker-compose exec backend python manage.py createsuperuser
```

### Database Backup
```bash
make backup-db
# Creates backup_YYYYMMDD_HHMMSS.sql
```

### Database Restore
```bash
make restore-db
# Prompts for backup file path
```

### Reset Database
```bash
make db-reset
# Completely resets database and recreates
```

## Testing

### Run All Tests
```bash
make test
# OR
docker-compose exec backend python -m pytest
```

### Run Tests with Coverage
```bash
make test-coverage
# OR
docker-compose exec backend python -m pytest --cov=. --cov-report=html
```

### Run Specific Tests
```bash
docker-compose exec backend python -m pytest core/tests/test_text_parser.py -v
```

## Monitoring and Debugging

### View Logs
```bash
make logs              # All services
make logs-backend      # Backend only
docker-compose logs -f celery_worker  # Celery worker
```

### Health Check
```bash
make health
# Checks if all services are responding
```

### Access Service Shells
```bash
make shell          # Django shell
make shell-db       # PostgreSQL shell
docker-compose exec redis redis-cli  # Redis CLI
```

## Volumes and Data Persistence

The setup uses Docker volumes for data persistence:

- `postgres_data`: Database data
- `redis_data`: Redis data
- `backend_media`: Uploaded media files
- `backend_logs`: Application logs
- `backend_static`: Static files

## Troubleshooting

### Common Issues

1. **Port conflicts**
   - Change ports in docker-compose.yml if 8000, 5432, or 6379 are in use

2. **Permission issues**
   - Ensure Docker has proper permissions
   - On Linux, add user to docker group: `sudo usermod -aG docker $USER`

3. **Database connection errors**
   - Wait for database to be ready: `docker-compose logs db`
   - Check database health: `make health`

4. **Static files not loading**
   - Run: `make collectstatic`

5. **Celery tasks not processing**
   - Check worker logs: `docker-compose logs celery_worker`
   - Verify Redis connection: `docker-compose exec redis redis-cli ping`

### Clean Reset
```bash
make clean          # Remove all containers, images, and volumes
make dev-setup      # Rebuild everything
```

## Security Considerations

For production deployment:

1. **Change default passwords**
   - Set strong `SECRET_KEY`
   - Use secure database passwords
   - Configure Redis password

2. **Configure HTTPS**
   - Set up SSL certificates
   - Update Nginx configuration

3. **Environment variables**
   - Never commit `.env` files
   - Use Docker secrets for sensitive data

4. **Network security**
   - Configure firewall rules
   - Use private networks
   - Enable fail2ban for rate limiting

## Performance Tuning

### Database
- Adjust PostgreSQL settings in docker-compose.yml
- Monitor query performance
- Set up connection pooling

### Backend
- Tune Gunicorn workers
- Configure caching
- Optimize Django settings

### Nginx
- Enable gzip compression
- Configure caching headers
- Tune worker processes

## Backup Strategy

1. **Database backups**
   ```bash
   # Daily backup cron job
   0 2 * * * /path/to/project && make backup-db
   ```

2. **Media files**
   ```bash
   # Backup media volume
   docker run --rm -v flowsketch_backend_media:/data -v $(pwd):/backup alpine tar czf /backup/media_backup.tar.gz -C /data .
   ```

3. **Configuration**
   - Version control all configuration files
   - Backup environment variables securely