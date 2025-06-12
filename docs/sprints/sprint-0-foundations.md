# Sprint 0: Foundations (2 weeks)

## 🎯 Sprint Overview

**Duration**: 2 weeks  
**Team Focus**: Infrastructure setup, environment configuration, and foundational services  
**Sprint Goal**: Establish a solid foundation for the hybrid N8n + LangChain architecture with all necessary infrastructure components.

## 📋 Sprint Objectives

### Primary Goals
1. **Repository & Project Setup**: Version control, branching strategy, and project structure
2. **Development Environment**: Local development stack with Docker
3. **CI/CD Pipeline**: GitHub Actions workflow for automated testing and deployment
4. **Infrastructure Setup**: Core services (PostgreSQL, Redis, N8n, ChromaDB)
5. **Security Foundation**: Environment configuration, secrets management, HIPAA compliance setup
6. **Documentation**: Technical documentation and onboarding guides

### Success Criteria
- [ ] All team members can run the full stack locally
- [ ] CI/CD pipeline successfully builds and tests the application
- [ ] Core infrastructure services are running and accessible
- [ ] Security configurations are HIPAA-compliant
- [ ] Documentation is complete and accessible

## 🏗️ Architecture Components to Implement

```
┌─────────────────────────────────────────────────────────────────┐
│                    Development Environment                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    FastAPI      │  │      N8n        │  │   PostgreSQL    │  │
│  │   (Port 8000)   │  │   (Port 5678)   │  │   (Port 5432)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │     Redis       │  │    ChromaDB     │  │   Monitoring    │  │
│  │   (Port 6379)   │  │   (Port 8000)   │  │   (Various)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Detailed Task Breakdown

### **Task 1: Repository & Project Setup**
**Estimated Effort**: 0.5 days  
**Assignee**: DevOps Engineer  

#### Subtasks
- [ ] Initialize Git repository with proper `.gitignore`
- [ ] Set up branch protection rules (main, develop)
- [ ] Configure issue templates and PR templates
- [ ] Create project structure following Python best practices
- [ ] Set up pre-commit hooks (black, isort, mypy)

#### Deliverables
```bash
GreenLightPA/
├── app/
│   ├── api/v1/endpoints/
│   ├── core/
│   ├── services/
│   ├── models/
│   └── schemas/
├── docs/
├── scripts/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .github/workflows/
```

#### Acceptance Criteria
- Repository follows conventional structure
- Branch protection prevents direct pushes to main
- Pre-commit hooks enforce code quality

---

### **Task 2: Environment Configuration**
**Estimated Effort**: 1 day  
**Assignee**: Backend Engineer  

#### Subtasks
- [ ] Create comprehensive `.env.example` with all required variables
- [ ] Implement environment-specific configurations
- [ ] Set up secrets management strategy
- [ ] Configure logging with appropriate levels
- [ ] Implement health check endpoints

#### Configuration Files
```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # N8n Configuration
    N8N_HOST: str = "localhost"
    N8N_PORT: int = 5678
    N8N_WEBHOOK_URL: str
    N8N_API_KEY: str
    
    # LangChain
    OPENAI_API_KEY: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "greenlightpa"
    
    # Security
    JWT_SECRET_KEY: str
    
    class Config:
        env_file = ".env"
```

#### Acceptance Criteria
- All configuration is externalized to environment variables
- Sensitive data is not committed to repository
- Health check endpoints return service status

---

### **Task 3: Database Setup**
**Estimated Effort**: 1.5 days  
**Assignee**: Backend Engineer  

#### Subtasks
- [ ] Set up PostgreSQL with Docker Compose
- [ ] Install and configure pgvector extension
- [ ] Create database schemas for application data
- [ ] Set up Alembic for database migrations
- [ ] Configure Redis for caching and sessions
- [ ] Create database initialization scripts

#### Database Schema
```sql
-- Core application tables
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE prior_auth_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id),
    request_data JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector storage for policies
CREATE TABLE policy_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payer_id VARCHAR(255),
    policy_text TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Acceptance Criteria
- PostgreSQL with pgvector is running in Docker
- Database migrations work correctly
- Redis is configured and accessible
- Connection pooling is properly configured

---

### **Task 4: N8n Workflow Engine Setup**
**Estimated Effort**: 1.5 days  
**Assignee**: Integration Specialist  

#### Subtasks
- [ ] Deploy N8n using Docker Compose
- [ ] Configure N8n with custom settings
- [ ] Set up basic authentication and security
- [ ] Create workspace and initial workflow templates
- [ ] Configure webhook endpoints
- [ ] Test N8n → FastAPI communication

#### N8n Configuration
```yaml
# docker-compose.yml N8n service
n8n:
  image: n8nio/n8n:latest
  ports:
    - "5678:5678"
  environment:
    - N8N_BASIC_AUTH_ACTIVE=true
    - N8N_BASIC_AUTH_USER=${N8N_USER}
    - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    - N8N_HOST=${N8N_HOST}
    - N8N_PROTOCOL=http
    - WEBHOOK_URL=http://localhost:5678/
  volumes:
    - n8n_data:/home/node/.n8n
  depends_on:
    - postgres
```

#### Acceptance Criteria
- N8n is accessible via web interface
- Basic authentication is working
- Webhook endpoints are configured
- Can create and execute simple workflows

---

### **Task 5: LangChain Foundation**
**Estimated Effort**: 2 days  
**Assignee**: AI Engineer  

#### Subtasks
- [ ] Install and configure LangChain dependencies
- [ ] Set up ChromaDB for development vector storage
- [ ] Create basic LangChain service structure
- [ ] Implement OpenAI integration with proper error handling
- [ ] Create embedding service for document processing
- [ ] Set up LangSmith for observability

#### LangChain Service Structure
```python
# app/services/langchain_service.py
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import LLMChain

class LangChainService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
    
    async def initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        self.vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
    
    async def process_clinical_document(self, text: str):
        """Process clinical document and extract codes"""
        # Implementation coming in Sprint 1
        pass
```

#### Acceptance Criteria
- LangChain is properly configured with OpenAI
- ChromaDB is running and accessible
- Basic embedding functionality works
- LangSmith tracing is configured

---

### **Task 6: Docker & Orchestration**
**Estimated Effort**: 1 day  
**Assignee**: DevOps Engineer  

#### Subtasks
- [ ] Create comprehensive Docker Compose configuration
- [ ] Write Dockerfile for FastAPI application
- [ ] Set up development vs production configurations
- [ ] Configure networking between services
- [ ] Create startup and shutdown scripts
- [ ] Document local development setup

#### Docker Compose Services
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/greenlightpa
    
  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: greenlightpa
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_HOST=localhost
    volumes:
      - n8n_data:/home/node/.n8n
```

#### Acceptance Criteria
- All services start with single command
- Services can communicate with each other
- Persistent volumes are properly configured
- Local development environment is fully functional

---

### **Task 7: CI/CD Pipeline**
**Estimated Effort**: 1.5 days  
**Assignee**: DevOps Engineer  

#### Subtasks
- [ ] Create GitHub Actions workflow for CI
- [ ] Set up automated testing pipeline
- [ ] Configure code quality checks
- [ ] Set up security scanning
- [ ] Create deployment workflow templates
- [ ] Configure environment-specific deployments

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run code quality checks
      run: |
        black --check .
        isort --check-only .
        mypy .
    
    - name: Run tests
      run: |
        pytest --cov=app tests/
```

#### Acceptance Criteria
- CI pipeline runs on every PR and push
- All code quality checks pass
- Test coverage is tracked and reported
- Security scanning is integrated

---

### **Task 8: Security & Compliance Setup**
**Estimated Effort**: 1 day  
**Assignee**: Backend + DevOps Engineers  

#### Subtasks
- [ ] Implement JWT authentication framework
- [ ] Set up CORS and security headers
- [ ] Configure HTTPS for all services
- [ ] Implement audit logging framework
- [ ] Create security configuration checklist
- [ ] Document HIPAA compliance measures

#### Security Configuration
```python
# app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
```

#### Acceptance Criteria
- JWT authentication is working
- All endpoints are properly secured
- Audit logging captures all operations
- HIPAA compliance checklist is documented

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
# tests/test_config.py
def test_settings_loading():
    """Test that settings load correctly"""
    from app.core.config import get_settings
    settings = get_settings()
    assert settings.DATABASE_URL is not None

# tests/test_health.py
def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### **Integration Tests**
- Database connection and migration tests
- N8n webhook integration tests
- LangChain service initialization tests
- Redis caching functionality tests

### **Security Tests**
- Authentication and authorization tests
- Input validation and sanitization tests
- Security header validation tests

## 📊 Sprint Metrics

### **Definition of Done**
- [ ] All tasks completed and tested
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Security review passed
- [ ] Integration tests passing
- [ ] Ready for next sprint

### **Key Performance Indicators**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Setup Time | <30 minutes | Time for new developer to run full stack |
| Test Coverage | >80% | Automated testing coverage |
| Build Time | <5 minutes | CI pipeline execution time |
| Security Score | A grade | Security scanning results |

## 🔄 Sprint Retrospective Preparation

### **Questions to Address**
1. **What went well?**
   - Which setup processes were smooth?
   - What tools/technologies were easy to integrate?

2. **What could be improved?**
   - Which setup steps were challenging?
   - What documentation was missing or unclear?

3. **What should we start/stop/continue?**
   - Start: New tools or processes that would help
   - Stop: Inefficient practices discovered
   - Continue: Successful patterns to maintain

### **Action Items for Next Sprint**
- Identify any infrastructure improvements needed
- Document lessons learned for future sprints
- Plan any architectural adjustments based on foundation learnings

## 📚 Resources & References

### **Documentation Links**
- [N8n Documentation](https://docs.n8n.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL + pgvector Setup](https://github.com/pgvector/pgvector)

### **Setup Guides**
- [Local Development Setup](../deployment/development-setup.md)
- [Docker Configuration Guide](../deployment/docker-setup.md)
- [Security Configuration Checklist](../deployment/security-checklist.md)

---

**Sprint 0 Success Criteria**: By the end of this sprint, any developer should be able to clone the repository, run `docker-compose up`, and have a fully functional development environment with all core services running and integrated. 