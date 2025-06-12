# 🚀 Local Development Setup Guide

## 📋 Prerequisites

### **System Requirements**
- **OS**: macOS, Linux, or Windows with WSL2
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 10GB free space
- **Docker**: Latest version with Docker Compose
- **Git**: Version 2.30+
- **Python**: 3.11+ (for local development)

### **Required Accounts & API Keys**
- **OpenAI API Key**: For LangChain LLM integration
- **LangSmith Account**: For AI observability (optional for development)
- **Docker Hub Account**: For pulling container images

## 🛠️ Quick Start

### **1. Clone the Repository**
```bash
# Clone the repository
git clone https://github.com/your-org/GreenLightPA.git
cd GreenLightPA

# Check out develop branch for latest features
git checkout develop
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp config.example.env .env

# Edit the .env file with your configuration
nano .env  # or use your preferred editor
```

### **3. Required Environment Variables**
```bash
# Database Configuration
DATABASE_URL=postgresql://greenlight_user:dev_password_123@localhost:5432/greenlightpa_dev
POSTGRES_USER=greenlight_user
POSTGRES_PASSWORD=dev_password_123
POSTGRES_DB=greenlightpa_dev

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# N8n Configuration
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=dev_n8n_pass_123

# LangChain & AI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here  # Optional
LANGCHAIN_PROJECT=greenlightpa-dev
LANGCHAIN_TRACING_V2=true

# FastAPI Configuration
SECRET_KEY=dev_jwt_secret_key_change_in_production
DEBUG=true
LOG_LEVEL=DEBUG

# ChromaDB Configuration
CHROMA_DB_PATH=./data/chroma_db
CHROMA_PORT=8000

# Security (Development Only)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost:5678"]
```

### **4. Start All Services**
```bash
# Start the complete development stack
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

### **5. Verify Installation**
```bash
# Check all services are running
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Access N8n interface
open http://localhost:5678
```

## 🏗️ Service Architecture

### **Development Stack Overview**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Local Development Stack                       │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    FastAPI      │  │      N8n        │  │   PostgreSQL    │  │
│  │ localhost:8000  │  │ localhost:5678  │  │ localhost:5432  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │     Redis       │  │    ChromaDB     │  │   pgAdmin       │  │
│  │ localhost:6379  │  │ localhost:8001  │  │ localhost:5050  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **Service Access Points**
| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI API** | http://localhost:8000 | N/A |
| **FastAPI Docs** | http://localhost:8000/docs | N/A |
| **N8n Workflow UI** | http://localhost:5678 | admin / dev_n8n_pass_123 |
| **PostgreSQL** | localhost:5432 | greenlight_user / dev_password_123 |
| **pgAdmin** | http://localhost:5050 | admin@greenlight.dev / admin |
| **Redis** | localhost:6379 | No auth (dev only) |
| **ChromaDB** | http://localhost:8001 | N/A |

## 🔧 Detailed Setup Instructions

### **Step 1: Docker Environment Setup**

#### **Install Docker & Docker Compose**
```bash
# macOS (using Homebrew)
brew install --cask docker

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

#### **Verify Docker Installation**
```bash
docker --version
docker-compose --version
docker run hello-world
```

### **Step 2: Database Initialization**

#### **PostgreSQL with pgvector**
The docker-compose configuration automatically sets up PostgreSQL with the pgvector extension for vector similarity search.

```bash
# Check PostgreSQL is running
docker-compose exec postgres psql -U greenlight_user -d greenlightpa_dev -c "SELECT version();"

# Verify pgvector extension
docker-compose exec postgres psql -U greenlight_user -d greenlightpa_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### **Run Database Migrations**
```bash
# Install Python dependencies locally (optional)
pip install -r requirements.txt

# Run database migrations
docker-compose exec app alembic upgrade head

# Or run migrations directly
python -m alembic upgrade head
```

### **Step 3: N8n Workflow Engine Setup**

#### **Access N8n Interface**
1. Navigate to http://localhost:5678
2. Login with: `admin` / `dev_n8n_pass_123`
3. Create your first workflow

#### **Configure N8n Webhooks**
```bash
# Test webhook endpoint
curl -X POST http://localhost:5678/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

#### **Import Sample Workflows**
```bash
# Copy sample workflows
cp docs/workflows/samples/*.json ./n8n_data/workflows/

# Restart N8n to load workflows
docker-compose restart n8n
```

### **Step 4: LangChain & AI Services**

#### **Verify OpenAI Connection**
```bash
# Test OpenAI API connection
docker-compose exec app python -c "
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model='gpt-4o-mini')
print(llm.invoke('Hello, world!'))
"
```

#### **Initialize ChromaDB Vector Store**
```bash
# Create ChromaDB collection
docker-compose exec app python -c "
from app.services.langchain_service import LangChainService
service = LangChainService()
service.initialize_vector_store()
print('ChromaDB initialized successfully')
"
```

### **Step 5: Development Tools Setup**

#### **Install Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

#### **Setup IDE Configuration**

**VS Code Settings** (`.vscode/settings.json`):
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## 🧪 Testing Your Setup

### **Health Check Script**
```bash
#!/bin/bash
# scripts/health_check.sh

echo "🏥 GreenLightPA Development Environment Health Check"
echo "=================================================="

# Check Docker services
echo "📦 Checking Docker services..."
docker-compose ps

# Check API health
echo "🔍 Testing FastAPI health..."
curl -f http://localhost:8000/health || echo "❌ FastAPI not responding"

# Check N8n
echo "⚙️ Testing N8n..."
curl -f http://localhost:5678 || echo "❌ N8n not responding"

# Check PostgreSQL
echo "🐘 Testing PostgreSQL..."
docker-compose exec -T postgres pg_isready -U greenlight_user || echo "❌ PostgreSQL not ready"

# Check Redis
echo "⚡ Testing Redis..."
docker-compose exec -T redis redis-cli ping || echo "❌ Redis not responding"

echo "✅ Health check complete!"
```

### **Run Integration Tests**
```bash
# Run full test suite
docker-compose exec app pytest tests/ -v

# Run specific test categories
docker-compose exec app pytest tests/integration/ -v
docker-compose exec app pytest tests/unit/ -v

# Run with coverage
docker-compose exec app pytest --cov=app tests/
```

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### **Docker Issues**
```bash
# Service won't start
docker-compose down
docker-compose up --build

# Port conflicts
docker-compose down
sudo lsof -i :8000  # Check what's using the port
docker-compose up
```

#### **Database Issues**
```bash
# Reset database
docker-compose down -v  # ⚠️ This deletes all data
docker-compose up -d postgres
docker-compose exec app alembic upgrade head
```

#### **N8n Issues**
```bash
# Reset N8n data
docker-compose down
docker volume rm greenlightpa_n8n_data
docker-compose up -d n8n
```

#### **Environment Variable Issues**
```bash
# Verify environment is loaded
docker-compose exec app python -c "
from app.core.config import get_settings
settings = get_settings()
print(f'Database URL: {settings.DATABASE_URL}')
print(f'N8n Host: {settings.N8N_HOST}')
"
```

### **Performance Optimization**

#### **Docker Resources**
```bash
# Increase Docker memory (macOS/Windows)
# Docker Desktop → Preferences → Resources → Memory: 8GB

# Linux: Edit daemon.json
sudo nano /etc/docker/daemon.json
{
  "default-runtime": "runc",
  "runtimes": {
    "runc": {
      "path": "runc"
    }
  }
}
```

#### **Database Performance**
```sql
-- Connect to PostgreSQL and run
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements,auto_explain';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
```

## 🔄 Daily Development Workflow

### **Starting Development**
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f app

# Watch for file changes (if using volume mounts)
# FastAPI will auto-reload on code changes
```

### **Making Changes**
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, test locally
docker-compose exec app pytest tests/

# Commit with pre-commit hooks
git add .
git commit -m "feat: your feature description"
```

### **Ending Development**
```bash
# Stop services (keeps data)
docker-compose stop

# Or stop and remove containers (keeps volumes)
docker-compose down

# Full cleanup (⚠️ deletes all data)
docker-compose down -v
```

## 📚 Next Steps

After completing this setup:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Create N8n Workflows**: Start with the sample workflows in `/docs/workflows/`
3. **Run Tests**: Execute `docker-compose exec app pytest tests/`
4. **Read Sprint Documentation**: Continue with Sprint 1 implementation
5. **Join Team Sync**: Review project roadmap and current sprint goals

## 🆘 Getting Help

### **Documentation**
- [Architecture Overview](../architecture/system-architecture.md)
- [Sprint Planning](../sprints/sprint-roadmap.md)
- [Workflow Templates](../workflows/n8n-templates.md)

### **Support Channels**
- **Technical Issues**: Create GitHub issue with `setup` label
- **Questions**: Check project README.md or team documentation
- **Urgent**: Contact DevOps engineer

---

**🎉 Congratulations!** You now have a fully functional GreenLightPA development environment. Your hybrid N8n + LangChain architecture is ready for healthcare prior-authorization automation development! 