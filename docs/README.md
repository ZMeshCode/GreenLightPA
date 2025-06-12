# GreenLightPA Documentation

Welcome to the GreenLightPA project documentation. This comprehensive guide covers the hybrid N8n + LangChain architecture for automating prior authorization processes in healthcare.

## 📋 Table of Contents

### 🏗️ Architecture & Design
- [**Project Overview**](.cursor/rules/project-overview.mdc) - Complete technical specification
- [**System Architecture**](architecture/system-architecture.md) - Detailed architecture diagrams and data flow
- [**Integration Patterns**](architecture/integration-patterns.md) - N8n ↔ LangChain communication protocols

### 🛠️ Technology Stack
- [**Tech Stack Overview**](tech-stack/overview.md) - Complete technology choices and rationale
- [**N8n Workflow Engine**](tech-stack/n8n-setup.md) - Workflow orchestration platform
- [**LangChain AI Framework**](tech-stack/langchain-setup.md) - AI/ML processing pipeline
- [**Database & Storage**](tech-stack/database-setup.md) - PostgreSQL, ChromaDB, Redis configuration
- [**External Integrations**](tech-stack/integrations.md) - Payer APIs, FHIR, Twilio setup

### 🚀 Sprint Documentation
- [**Sprint 0: Foundations**](sprints/sprint-0-foundations.md) - Initial setup and infrastructure
- [**Sprint 1: Core AI Pipeline**](sprints/sprint-1-ai-pipeline.md) - LangChain NLP and RAG implementation
- [**Sprint 2: N8n Integration**](sprints/sprint-2-n8n-integration.md) - Workflow orchestration setup
- [**Sprint 3: Policy RAG Engine**](sprints/sprint-3-policy-rag.md) - Vector store and policy matching
- [**Sprint 4: Hybrid Orchestration**](sprints/sprint-4-hybrid-orchestration.md) - N8n-LangChain integration
- [**Sprint 5: Payer Integration**](sprints/sprint-5-payer-integration.md) - Multi-channel submission workflows
- [**Sprint 6: Dashboard & Monitoring**](sprints/sprint-6-dashboard-monitoring.md) - UI and observability
- [**Sprint 7: Testing & Hardening**](sprints/sprint-7-testing-hardening.md) - Security and performance
- [**Sprint 8: Pilot Deployment**](sprints/sprint-8-pilot-deployment.md) - Production readiness

### 🔄 Workflow Templates
- [**N8n Workflow Library**](workflows/n8n-templates.md) - Reusable workflow components
- [**FHIR Data Processing**](workflows/fhir-processing.md) - Healthcare data ingestion workflows
- [**Policy Scraping**](workflows/policy-scraping.md) - Automated policy document ingestion
- [**Payer Submission**](workflows/payer-submission.md) - Multi-channel PA submission workflows

### 🚢 Deployment & Operations
- [**Development Setup**](deployment/development-setup.md) - Local development environment
- [**Docker Configuration**](deployment/docker-setup.md) - Containerization and orchestration
- [**Production Deployment**](deployment/production-deployment.md) - AWS EKS deployment guide
- [**Monitoring & Observability**](deployment/monitoring.md) - LangSmith + N8n + Prometheus setup

## 🎯 Quick Start Guide

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+
- Node.js 18+ (for N8n)

### 1. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd GreenLightPA

# Copy environment configuration
cp config.example.env .env

# Install Python dependencies
pip install -r requirements.txt

# Start infrastructure services
docker-compose up -d postgres redis
```

### 2. N8n Setup
```bash
# Start N8n (self-hosted)
docker run -d --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=password \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n
```

### 3. LangChain Services
```bash
# Start the FastAPI application
uvicorn app.main:app --reload --port 8000

# Initialize ChromaDB for development
python -c "from app.services.embedding_service import EmbeddingService; EmbeddingService().initialize_collections()"
```

### 4. Access Points
- **FastAPI API**: http://localhost:8000/docs
- **N8n Workflow UI**: http://localhost:5678
- **React Dashboard**: http://localhost:3000 (after frontend setup)

## 📊 Project Metrics & KPIs

| Metric | Target | Current Status |
|--------|--------|---------------|
| Draft Accuracy | ≥95% | 🔄 In Development |
| System Latency | <5s | 🔄 In Development |
| Workflow Reliability | ≥99.5% | 🔄 In Development |
| AI Model Accuracy | ≥92% | 🔄 In Development |
| Turnaround Time | <24h avg | 🔄 In Development |

## 🤝 Contributing

1. **Follow Sprint Guidelines**: Each sprint has specific deliverables and acceptance criteria
2. **Code Standards**: Use Black, isort, and mypy for Python code quality
3. **Documentation**: Update relevant docs when making changes
4. **Testing**: Maintain test coverage >80%
5. **Security**: Follow HIPAA compliance guidelines

## 🔒 Security & Compliance

- **HIPAA Compliance**: All PHI handling follows HIPAA guidelines
- **Data Encryption**: TLS 1.3 for transit, AES-256 for rest
- **Access Controls**: RBAC implementation with audit trails
- **BAAs Required**: OpenAI, AWS, and other third-party services

## 📞 Support & Contact

- **Technical Issues**: Open GitHub issues with appropriate labels
- **Architecture Questions**: Review architecture documentation
- **Sprint Planning**: Reference sprint-specific documentation

---

*Last Updated: January 2024*
*Project Version: 1.0.0-alpha* 