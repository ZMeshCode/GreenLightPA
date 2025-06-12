# 🔑 API Keys & Configuration Setup Guide
## *Complete Setup for Hybrid N8n + LangChain + Supabase Architecture*

> **Mission**: Configure all API keys, secrets, and environment variables needed to get GreenLightPA's hybrid architecture fully operational.

---

## 🎯 **Setup Overview**

After Sprint 0 foundations, this is our critical next step to establish secure communication between all components:

### **🏗️ Architecture Components Requiring Configuration**
1. **🐘 Supabase** - Database + Auth + Storage
2. **⚡ Upstash Redis** - Edge caching 
3. **🚀 Fly.io** - Container hosting
4. **🧠 OpenAI** - LLM services
5. **📊 LangSmith** - AI observability
6. **⚙️ N8n** - Workflow orchestration
7. **📞 Twilio** - Voice/SMS services
8. **💰 Change Healthcare** - Payer APIs
9. **🔐 Security** - JWT secrets & encryption

---

## 📋 **Pre-Setup Checklist**

### **Required Accounts**
- [ ] **Supabase Account** (Sign up at supabase.com)
- [ ] **Upstash Account** (Sign up at upstash.com)
- [ ] **Fly.io Account** (Sign up at fly.io)
- [ ] **OpenAI API Account** (platform.openai.com)
- [ ] **LangSmith Account** (smith.langchain.com)
- [ ] **Twilio Account** (twilio.com)
- [ ] **Change Healthcare Developer Account** (developers.changehealthcare.com)

### **Tools Needed**
```bash
# Install required CLI tools
brew install flyctl                    # Fly.io CLI
npm install -g @supabase/cli          # Supabase CLI
curl -sSL https://upstash.com/cli | bash  # Upstash CLI (optional)
```

---

## 🐘 **1. Supabase Setup (Database + Auth)**

### **1.1 Create Supabase Project**
```bash
# Login to Supabase
supabase login

# Create new project
supabase projects create greenlightpa-prod --region us-east-1

# Get project details
supabase projects list
```

### **1.2 Configure Database**
```sql
-- Connect to your Supabase project
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create application schemas
CREATE SCHEMA IF NOT EXISTS healthcare;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Enable Row Level Security
ALTER SCHEMA healthcare ENABLE ROW LEVEL SECURITY;
ALTER SCHEMA workflows ENABLE ROW LEVEL SECURITY;
```

### **1.3 Collect Supabase Credentials**
```bash
# Get from Supabase Dashboard > Settings > API
SUPABASE_URL="https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Database connection (Settings > Database)
SUPABASE_DB_HOST="db.your-project-ref.supabase.co"
SUPABASE_DB_PASSWORD="your-database-password"
SUPABASE_DATABASE_URL="postgresql://postgres:${SUPABASE_DB_PASSWORD}@${SUPABASE_DB_HOST}:5432/postgres"
```

---

## ⚡ **2. Upstash Redis Setup**

### **2.1 Create Redis Database**
```bash
# Via Upstash Console or CLI
# Create Redis database in us-east-1 region
# Choose Global with REST API enabled
```

### **2.2 Collect Upstash Credentials**
```bash
# Get from Upstash Console > Database > Details
UPSTASH_REDIS_REST_URL="https://your-redis-id.upstash.io"
UPSTASH_REDIS_REST_TOKEN="your-rest-token"
UPSTASH_REDIS_URL="redis://default:your-password@your-redis-id.upstash.io:6379"
```

---

## 🚀 **3. Fly.io Setup**

### **3.1 Authentication & Setup**
```bash
# Login to Fly.io
flyctl auth login

# Create organization (if needed)
flyctl orgs create greenlightpa

# Verify setup
flyctl auth whoami
```

### **3.2 Prepare App Names**
```bash
# Reserve app names for our services
flyctl apps create greenlightpa-api --org greenlightpa
flyctl apps create greenlightpa-n8n --org greenlightpa  
flyctl apps create greenlightpa-chromadb --org greenlightpa
```

---

## 🧠 **4. OpenAI API Setup**

### **4.1 Create API Key**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create new secret key
3. Set usage limits and billing alerts

### **4.2 API Configuration**
```bash
# OpenAI API credentials
OPENAI_API_KEY="sk-proj-your-openai-key-here"
OPENAI_ORG_ID="org-your-organization-id"  # Optional
```

---

## 📊 **5. LangSmith Setup (AI Observability)**

### **5.1 Create LangSmith Account**
1. Go to [LangSmith](https://smith.langchain.com)
2. Create account and workspace
3. Create API key

### **5.2 LangSmith Configuration**
```bash
# LangSmith credentials
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="ls__your-langsmith-key"
LANGCHAIN_PROJECT="greenlightpa-prod"
```

---

## ⚙️ **6. N8n Configuration**

### **6.1 Generate N8n Secrets**
```bash
# Generate secure encryption key (32+ characters)
N8N_ENCRYPTION_KEY=$(openssl rand -base64 32)

# Basic auth credentials for N8n UI
N8N_BASIC_AUTH_USER="admin"
N8N_BASIC_AUTH_PASSWORD=$(openssl rand -base64 16)
```

### **6.2 N8n Environment Variables**
```bash
# N8n configuration
N8N_HOST="greenlightpa-n8n.fly.dev"
N8N_PORT=5678
N8N_PROTOCOL="https"
N8N_WEBHOOK_URL="https://greenlightpa-n8n.fly.dev/webhook"
N8N_ENCRYPTION_KEY="${N8N_ENCRYPTION_KEY}"
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER="${N8N_BASIC_AUTH_USER}"
N8N_BASIC_AUTH_PASSWORD="${N8N_BASIC_AUTH_PASSWORD}"
```

---

## 📞 **7. Twilio Setup (Voice/SMS)**

### **7.1 Create Twilio Account**
1. Sign up at [Twilio Console](https://console.twilio.com)
2. Get phone number for IVR
3. Create API credentials

### **7.2 Twilio Configuration**
```bash
# Twilio credentials
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your-auth-token"
TWILIO_PHONE_NUMBER="+1234567890"
```

---

## 💰 **8. Change Healthcare API**

### **8.1 Developer Account Setup**
1. Apply for [Change Healthcare Developer Account](https://developers.changehealthcare.com)
2. Complete sandbox registration
3. Generate API credentials

### **8.2 Change Healthcare Configuration**
```bash
# Change Healthcare API
CHANGE_HEALTHCARE_API_KEY="your-change-healthcare-key"
CHANGE_HEALTHCARE_CLIENT_ID="your-client-id"
CHANGE_HEALTHCARE_CLIENT_SECRET="your-client-secret"
CHANGE_HEALTHCARE_ENDPOINT="https://api.changehealthcare.com"
```

---

## 🔐 **9. Security Secrets Generation**

### **9.1 Generate JWT Secrets**
```bash
# Generate secure JWT secret (256-bit)
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Generate field-level encryption key
FIELD_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### **9.2 Generate Application Secrets**
```bash
# FastAPI secret key
SECRET_KEY=$(openssl rand -base64 32)

# CORS configuration for production
CORS_ORIGINS='["https://app.greenlightpa.com","https://greenlightpa-n8n.fly.dev"]'
```

---

## 📄 **10. Complete Environment Configuration**

### **10.1 Development Environment (`.env.development`)**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database - Supabase
DATABASE_URL="${SUPABASE_DATABASE_URL}"
SUPABASE_URL="${SUPABASE_URL}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"
SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY}"

# Cache - Upstash Redis
REDIS_URL="${UPSTASH_REDIS_URL}"
UPSTASH_REDIS_REST_URL="${UPSTASH_REDIS_REST_URL}"
UPSTASH_REDIS_REST_TOKEN="${UPSTASH_REDIS_REST_TOKEN}"

# AI Services
OPENAI_API_KEY="${OPENAI_API_KEY}"
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY}"
LANGCHAIN_PROJECT="greenlightpa-dev"

# N8n Configuration
N8N_HOST="localhost"
N8N_PORT=5678
N8N_WEBHOOK_URL="http://localhost:5678/webhook"
N8N_ENCRYPTION_KEY="${N8N_ENCRYPTION_KEY}"
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER="${N8N_BASIC_AUTH_USER}"
N8N_BASIC_AUTH_PASSWORD="${N8N_BASIC_AUTH_PASSWORD}"

# ChromaDB
CHROMA_HOST="localhost"
CHROMA_PORT=8001
CHROMA_PERSIST_DIRECTORY="./data/chroma_db"

# External APIs
TWILIO_ACCOUNT_SID="${TWILIO_ACCOUNT_SID}"
TWILIO_AUTH_TOKEN="${TWILIO_AUTH_TOKEN}"
TWILIO_PHONE_NUMBER="${TWILIO_PHONE_NUMBER}"
CHANGE_HEALTHCARE_API_KEY="${CHANGE_HEALTHCARE_API_KEY}"

# Security
SECRET_KEY="${SECRET_KEY}"
JWT_SECRET_KEY="${JWT_SECRET_KEY}"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
FIELD_ENCRYPTION_KEY="${FIELD_ENCRYPTION_KEY}"

# CORS
CORS_ORIGINS='["http://localhost:3000","http://localhost:8000","http://localhost:5678"]'
```

### **10.2 Production Environment (Fly.io Secrets)**
```bash
# Set production secrets in Fly.io
flyctl secrets set -a greenlightpa-api \
  DATABASE_URL="${SUPABASE_DATABASE_URL}" \
  SUPABASE_URL="${SUPABASE_URL}" \
  SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}" \
  SUPABASE_SERVICE_ROLE_KEY="${SUPABASE_SERVICE_ROLE_KEY}" \
  REDIS_URL="${UPSTASH_REDIS_URL}" \
  OPENAI_API_KEY="${OPENAI_API_KEY}" \
  LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY}" \
  SECRET_KEY="${SECRET_KEY}" \
  JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
  FIELD_ENCRYPTION_KEY="${FIELD_ENCRYPTION_KEY}"

flyctl secrets set -a greenlightpa-n8n \
  DB_POSTGRESDB_HOST="${SUPABASE_DB_HOST}" \
  DB_POSTGRESDB_PASSWORD="${SUPABASE_DB_PASSWORD}" \
  N8N_ENCRYPTION_KEY="${N8N_ENCRYPTION_KEY}" \
  N8N_BASIC_AUTH_USER="${N8N_BASIC_AUTH_USER}" \
  N8N_BASIC_AUTH_PASSWORD="${N8N_BASIC_AUTH_PASSWORD}"
```

---

## 🧪 **11. Configuration Testing**

### **11.1 Test Database Connection**
```python
# test_connections.py
import asyncio
import asyncpg
import redis
import openai
from supabase import create_client, Client

async def test_supabase():
    """Test Supabase connection"""
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    
    # Test database connection
    result = supabase.table('_test').select('*').execute()
    print("✅ Supabase connection successful")

async def test_upstash_redis():
    """Test Upstash Redis connection"""
    import redis
    r = redis.from_url(os.getenv("UPSTASH_REDIS_URL"))
    r.ping()
    print("✅ Upstash Redis connection successful")

def test_openai():
    """Test OpenAI API"""
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.models.list()
    print("✅ OpenAI API connection successful")

async def test_all_connections():
    """Test all external connections"""
    await test_supabase()
    await test_upstash_redis()
    test_openai()
    print("🎉 All connections successful!")

if __name__ == "__main__":
    asyncio.run(test_all_connections())
```

### **11.2 Test Script Execution**
```bash
# Run connection tests
python scripts/test_connections.py

# Expected output:
# ✅ Supabase connection successful
# ✅ Upstash Redis connection successful  
# ✅ OpenAI API connection successful
# 🎉 All connections successful!
```

---

## 🔄 **12. Docker Compose Update**

### **12.1 Update docker-compose.yml**
```yaml
# Update docker-compose.yml with new environment variables
services:
  app:
    environment:
      # Database - Supabase (fallback to local for dev)
      - DATABASE_URL=${SUPABASE_DATABASE_URL:-postgresql://greenlight_user:dev_password_123@postgres:5432/greenlightpa_dev}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      
      # Cache - Upstash (fallback to local Redis)
      - REDIS_URL=${UPSTASH_REDIS_URL:-redis://redis:6379/0}
      
      # AI Services
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-greenlightpa-dev}
      
      # Security
      - SECRET_KEY=${SECRET_KEY:-dev_secret_change_in_production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev_jwt_secret}
```

---

## 🚀 **13. Deployment Commands**

### **13.1 Development Startup**
```bash
# Load environment variables
export $(cat .env.development | xargs)

# Start local development
docker-compose --profile development up -d

# Verify all services
curl http://localhost:8000/health
curl http://localhost:5678
curl http://localhost:8001/api/v1/heartbeat
```

### **13.2 Production Deployment**
```bash
# Deploy FastAPI to Fly.io
flyctl deploy -a greenlightpa-api

# Deploy N8n to Fly.io  
flyctl deploy -a greenlightpa-n8n

# Deploy ChromaDB to Fly.io
flyctl deploy -a greenlightpa-chromadb

# Verify deployments
flyctl status -a greenlightpa-api
flyctl logs -a greenlightpa-api
```

---

## 📋 **14. Configuration Verification Checklist**

### **✅ Infrastructure Connectivity**
- [ ] Supabase database accessible with pgvector extension
- [ ] Upstash Redis cache responding to ping
- [ ] Fly.io apps deployed and healthy
- [ ] All secrets properly set in Fly.io

### **✅ AI Services**
- [ ] OpenAI API key working with model access
- [ ] LangSmith tracing enabled and logging
- [ ] ChromaDB accepting vector operations

### **✅ Workflow Integration**
- [ ] N8n UI accessible with basic auth
- [ ] N8n can connect to Supabase database
- [ ] N8n webhooks reachable from FastAPI

### **✅ External APIs**
- [ ] Twilio credentials valid for SMS/voice
- [ ] Change Healthcare sandbox access confirmed

### **✅ Security**
- [ ] All secrets using secure random generation
- [ ] JWT tokens properly configured
- [ ] CORS settings appropriate for environment
- [ ] Field-level encryption keys generated

---

## 🎯 **Next Steps After Configuration**

Once all API keys and configuration are set up:

1. **🧪 Sprint 1**: Core AI Pipeline Development
   - LangChain NLP extraction testing
   - ChromaDB vector operations
   - RAG pipeline implementation

2. **🔄 Sprint 2**: N8n Integration
   - Workflow creation and testing
   - FastAPI webhook integration
   - Error handling and retry logic

3. **📚 Sprint 3**: Policy RAG Engine
   - Policy document ingestion
   - Vector optimization
   - LLM prompt engineering

---

*📅 Last Updated: June 2025*  
*🏷️ Version: 1.0.0*  
*🏗️ Architecture: Hybrid N8n + LangChain + Supabase* 