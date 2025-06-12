# 🐳 Docker Configuration Guide

## 📋 Overview

This guide covers the Docker containerization strategy for GreenLightPA's hybrid N8n + LangChain architecture. Our setup uses Docker Compose to orchestrate multiple services including FastAPI, N8n, PostgreSQL, Redis, and ChromaDB.

## 🏗️ Container Architecture

### **Multi-Service Stack**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   greenlightpa  │  │      n8n        │  │   postgres      │  │
│  │   (FastAPI)     │  │  (Workflows)    │  │  (Database)     │  │
│  │   Port: 8000    │  │   Port: 5678    │  │   Port: 5432    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │     redis       │  │    chromadb     │  │    pgadmin      │  │
│  │   (Cache)       │  │   (Vectors)     │  │  (DB Admin)     │  │
│  │   Port: 6379    │  │   Port: 8001    │  │   Port: 5050    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📄 Docker Compose Configuration

### **Main docker-compose.yml**
```yaml
version: '3.8'

services:
  # FastAPI Application
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    container_name: greenlightpa_app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-true}
      - LOG_LEVEL=${LOG_LEVEL:-DEBUG}
    volumes:
      - .:/app
      - ./data/chroma_db:/app/data/chroma_db
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - greenlightpa_network
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # PostgreSQL Database with pgvector
  postgres:
    image: pgvector/pgvector:pg16
    container_name: greenlightpa_postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - greenlightpa_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: greenlightpa_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - greenlightpa_network
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf

  # N8n Workflow Engine
  n8n:
    image: n8nio/n8n:latest
    container_name: greenlightpa_n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=${N8N_PROTOCOL:-http}
      - N8N_BASIC_AUTH_ACTIVE=${N8N_BASIC_AUTH_ACTIVE:-true}
      - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
      - WEBHOOK_URL=${N8N_WEBHOOK_URL}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB_NAME:-n8n}
      - DB_POSTGRESDB_USER=${POSTGRES_USER}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/home/node/.n8n/workflows
    networks:
      - greenlightpa_network
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  # ChromaDB Vector Database
  chromadb:
    image: chromadb/chroma:latest
    container_name: greenlightpa_chromadb
    ports:
      - "8001:8000"
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    volumes:
      - chromadb_data:/chroma/chroma
    networks:
      - greenlightpa_network
    restart: unless-stopped

  # pgAdmin (Development only)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: greenlightpa_pgadmin
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@greenlightpa.dev}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./config/pgadmin/servers.json:/pgadmin4/servers.json
    networks:
      - greenlightpa_network
    depends_on:
      - postgres
    restart: unless-stopped
    profiles:
      - development

# Networks
networks:
  greenlightpa_network:
    driver: bridge
    name: greenlightpa_network

# Volumes
volumes:
  postgres_data:
    name: greenlightpa_postgres_data
  redis_data:
    name: greenlightpa_redis_data
  n8n_data:
    name: greenlightpa_n8n_data
  chromadb_data:
    name: greenlightpa_chromadb_data
  pgadmin_data:
    name: greenlightpa_pgadmin_data
```

## 🐳 Application Dockerfile

### **Multi-stage Dockerfile**
```dockerfile
# Base Python image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash greenlightpa
USER greenlightpa
WORKDIR /app

# Install Python dependencies
COPY --chown=greenlightpa:greenlightpa requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
COPY --chown=greenlightpa:greenlightpa requirements-dev.txt .
RUN pip install --no-cache-dir --user -r requirements-dev.txt

# Copy application code
COPY --chown=greenlightpa:greenlightpa . .

# Expose port
EXPOSE 8000

# Command for development (with hot reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy application code
COPY --chown=greenlightpa:greenlightpa app/ ./app/
COPY --chown=greenlightpa:greenlightpa alembic/ ./alembic/
COPY --chown=greenlightpa:greenlightpa alembic.ini .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## ⚙️ Configuration Files

### **Redis Configuration** (`config/redis.conf`)
```conf
# Redis configuration for development
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence (disabled for development)
save ""

# Logging
loglevel notice
logfile ""

# Security (development only)
protected-mode no
```

### **pgAdmin Servers** (`config/pgadmin/servers.json`)
```json
{
    "Servers": {
        "1": {
            "Name": "GreenLightPA PostgreSQL",
            "Group": "Servers",
            "Host": "postgres",
            "Port": 5432,
            "MaintenanceDB": "greenlightpa_dev",
            "Username": "greenlight_user",
            "SSLMode": "prefer",
            "SSLCert": "<STORAGE_DIR>/.postgresql/postgresql.crt",
            "SSLKey": "<STORAGE_DIR>/.postgresql/postgresql.key",
            "SSLCompression": 0,
            "Timeout": 10,
            "UseSSHTunnel": 0,
            "TunnelPort": "22",
            "TunnelAuthentication": 0
        }
    }
}
```

### **Database Initialization** (`scripts/init-db.sql`)
```sql
-- Initialize database for GreenLightPA
-- This script runs automatically when PostgreSQL container starts

-- Create the main database if it doesn't exist
SELECT 'CREATE DATABASE greenlightpa_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'greenlightpa_dev')\gexec

-- Create N8n database if it doesn't exist
SELECT 'CREATE DATABASE n8n'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec

-- Connect to the main database
\c greenlightpa_dev;

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create basic schema
CREATE SCHEMA IF NOT EXISTS healthcare;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE greenlightpa_dev TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA healthcare TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA workflows TO greenlight_user;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO greenlight_user;

-- Connect to N8n database
\c n8n;

-- Grant permissions for N8n
GRANT ALL PRIVILEGES ON DATABASE n8n TO greenlight_user;
```

## 🔧 Environment Configuration

### **Development Environment** (`.env.development`)
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
POSTGRES_DB=greenlightpa_dev
POSTGRES_USER=greenlight_user
POSTGRES_PASSWORD=dev_password_123
DATABASE_URL=postgresql://greenlight_user:dev_password_123@postgres:5432/greenlightpa_dev

# N8n
N8N_HOST=localhost
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=dev_n8n_pass_123
N8N_ENCRYPTION_KEY=dev_encryption_key_change_in_production
N8N_DB_NAME=n8n

# pgAdmin
PGADMIN_EMAIL=admin@greenlightpa.dev
PGADMIN_PASSWORD=admin

# Security
SECRET_KEY=dev_jwt_secret_key_change_in_production
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost:5678"]

# AI Services
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=greenlightpa-dev
```

### **Production Environment** (`.env.production`)
```bash
# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (use secrets management in production)
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=${DATABASE_URL}

# N8n
N8N_HOST=${N8N_HOST}
N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

# Security
SECRET_KEY=${SECRET_KEY}
CORS_ORIGINS=${CORS_ORIGINS}

# AI Services
OPENAI_API_KEY=${OPENAI_API_KEY}
LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
LANGCHAIN_PROJECT=greenlightpa-prod
```

## 🚀 Docker Operations

### **Development Commands**
```bash
# Start development environment
docker-compose --profile development up -d

# Build and start with fresh images
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f app  # Specific service

# Execute commands in containers
docker-compose exec app bash
docker-compose exec postgres psql -U greenlight_user -d greenlightpa_dev

# Run database migrations
docker-compose exec app alembic upgrade head

# Run tests
docker-compose exec app pytest tests/ -v

# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### **Production Commands**
```bash
# Deploy production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Health check all services
docker-compose exec app curl -f http://localhost:8000/health
docker-compose exec n8n curl -f http://localhost:5678
docker-compose exec postgres pg_isready -U greenlight_user

# Monitor resources
docker stats
docker-compose top

# Backup data
docker-compose exec postgres pg_dump -U greenlight_user greenlightpa_dev > backup.sql
docker run --rm -v greenlightpa_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup.tar.gz -C /data .
```

## 📊 Monitoring & Observability

### **Health Checks**
```yaml
# Add to each service in docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### **Resource Limits**
```yaml
# Add to services that need resource constraints
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '0.5'
    reservations:
      memory: 512M
      cpus: '0.25'
```

### **Logging Configuration**
```yaml
# Add to services for centralized logging
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔒 Security Considerations

### **Network Security**
```yaml
# Internal network for service communication
networks:
  greenlightpa_internal:
    internal: true
  greenlightpa_external:
    driver: bridge

services:
  app:
    networks:
      - greenlightpa_external
      - greenlightpa_internal
  
  postgres:
    networks:
      - greenlightpa_internal  # Only internal access
```

### **Secrets Management**
```yaml
# Use Docker secrets for production
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt

services:
  app:
    secrets:
      - postgres_password
      - jwt_secret
```

## 🧪 Testing Docker Setup

### **Test Script** (`scripts/test_docker.sh`)
```bash
#!/bin/bash
set -e

echo "🐳 Testing Docker setup..."

# Start services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Test each service
echo "🔍 Testing FastAPI..."
curl -f http://localhost:8000/health || exit 1

echo "⚙️ Testing N8n..."
curl -f http://localhost:5678 || exit 1

echo "🐘 Testing PostgreSQL..."
docker-compose exec -T postgres pg_isready -U greenlight_user || exit 1

echo "⚡ Testing Redis..."
docker-compose exec -T redis redis-cli ping || exit 1

echo "🧠 Testing ChromaDB..."
curl -f http://localhost:8001/api/v1/heartbeat || exit 1

echo "✅ All services are healthy!"

# Run application tests
echo "🧪 Running application tests..."
docker-compose exec -T app pytest tests/ --tb=short

echo "🎉 Docker setup test completed successfully!"
```

## 🐛 Troubleshooting

### **Common Issues**

#### **Port Conflicts**
```bash
# Check what's using a port
sudo lsof -i :8000

# Change ports in docker-compose.yml if needed
```

#### **Volume Permissions**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

#### **Service Dependencies**
```bash
# Check service startup order
docker-compose logs postgres
docker-compose logs app

# Restart with proper dependencies
docker-compose down
docker-compose up -d postgres
sleep 10
docker-compose up -d
```

#### **Memory Issues**
```bash
# Increase Docker memory allocation
# Docker Desktop → Preferences → Resources → Memory: 8GB

# Or add memory limits to docker-compose.yml
```

## 📚 Best Practices

### **Development**
1. **Use bind mounts** for code that changes frequently
2. **Use named volumes** for persistent data
3. **Enable hot reload** for development
4. **Use health checks** for all services
5. **Keep logs** structured and searchable

### **Production**
1. **Use multi-stage builds** to reduce image size
2. **Run as non-root user** for security
3. **Set resource limits** for all services
4. **Use secrets management** for sensitive data
5. **Implement proper backup** strategies

---

**🎯 Result**: With this Docker configuration, you have a robust, scalable, and maintainable containerized environment for your GreenLightPA hybrid architecture that works consistently across development, staging, and production environments. 