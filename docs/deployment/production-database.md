# 🏥 GreenLightPA Production Database Hosting Guide
## *Cost-Effective Supabase + Fly.io Architecture*

> **Mission**: Deploy secure, scalable, and cost-effective database infrastructure for the GreenLightPA hybrid N8n + LangChain architecture.

---

## 🎯 **Production Database Architecture**

### **🏗️ Cost-Effective Multi-Tier Strategy**

```
┌─────────────────────────────────────────────────────────────────┐
│  🌍            PRODUCTION INFRASTRUCTURE                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   🚀 Fly.io Platform                       │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ ⚙️ FastAPI   │  │ 🔄 N8n      │  │ 📊 ChromaDB         │ │ │
│  │  │  Machines   │  │  Machines   │  │  Machines           │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              💾 MANAGED DATABASE LAYER                      │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ 🐘 Supabase │  │ ⚡ Upstash   │  │ 📈 Fly.io           │ │ │
│  │  │ PostgreSQL  │  │  Redis      │  │  Metrics            │ │ │
│  │  │ + pgvector  │  │  Cache      │  │                     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                🔒 SECURITY & BACKUP                         │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ 🔐 Built-in │  │ 💾 Supabase │  │ 🛡️ Fly.io           │ │ │
│  │  │ Encryption  │  │ Backups     │  │ Private Network     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ **Database Components & Hosting**

### **1. 🐘 Primary Database: Supabase PostgreSQL**

#### **Configuration**
- **Plan**: Supabase Pro ($25/month)
- **Database**: PostgreSQL 15 with pgvector extension
- **Storage**: 8GB included, auto-scaling
- **Connections**: 100 concurrent connections
- **Backups**: Daily automated backups with 7-day retention

#### **HIPAA Compliance Features**
```yaml
# Supabase Configuration
project_settings:
  name: "greenlightpa-prod"
  region: "us-east-1"
  
database:
  version: "15.1"
  extensions:
    - pgvector
    - postgis
    - pg_stat_statements
  
security:
  row_level_security: true
  ssl_enforcement: true
  
auth:
  jwt_secret: "${SUPABASE_JWT_SECRET}"
  site_url: "https://app.greenlightpa.com"
  
storage:
  file_size_limit: 50MB
  public_bucket: false
```

#### **Supabase Schema Setup**
```sql
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

-- Healthcare tables with RLS
CREATE TABLE healthcare.patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    date_of_birth DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id)
);

-- Enable RLS policies
ALTER TABLE healthcare.patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own patients" ON healthcare.patients
    FOR ALL USING (auth.uid() = user_id);

-- Vector storage with RLS
CREATE TABLE healthcare.policy_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payer_id VARCHAR(255),
    policy_text TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    user_id UUID REFERENCES auth.users(id)
);

ALTER TABLE healthcare.policy_embeddings ENABLE ROW LEVEL SECURITY;
```

### **2. ⚡ Cache Layer: Upstash Redis**

#### **Configuration**
- **Plan**: Upstash Redis Pay-as-you-go (~$10/month)
- **Memory**: 1GB with auto-scaling
- **Connections**: Global edge network
- **Persistence**: Daily snapshots

```javascript
// Upstash Redis Configuration
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

// Cache configuration
const cacheConfig = {
  defaultTTL: 3600, // 1 hour
  patientDataTTL: 1800, // 30 minutes
  policyDataTTL: 86400, // 24 hours
  sessionTTL: 28800, // 8 hours
};
```

### **3. 📊 Vector Database: ChromaDB on Fly.io**

#### **Fly.io Machine Configuration**
```toml
# fly.toml for ChromaDB
app = "greenlightpa-chromadb"
primary_region = "iad"

[build]
  image = "chromadb/chroma:latest"

[env]
  CHROMA_SERVER_HOST = "0.0.0.0"
  CHROMA_SERVER_HTTP_PORT = "8000"
  PERSIST_DIRECTORY = "/chroma/chroma"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20

  [[services.ports]]
    port = 8000

[[mounts]]
  source = "chroma_data"
  destination = "/chroma/chroma"
```

---

## 🔒 **Security & Compliance**

### **🛡️ Supabase Security Features**

```yaml
# RLS Policies for HIPAA Compliance
rls_policies:
  patients:
    - name: "Clinic staff access"
      for: "ALL"
      using: "auth.jwt() ->> 'clinic_id' = clinic_id"
    
  prior_auth_requests:
    - name: "Provider access only"
      for: "SELECT"
      using: "auth.jwt() ->> 'role' IN ('provider', 'admin')"

# Authentication Configuration
auth:
  providers:
    - email: true
    - google: false  # Disabled for HIPAA
    - github: false  # Disabled for HIPAA
  
  password_policy:
    min_length: 12
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_symbols: true
  
  session:
    timeout: 28800  # 8 hours
    refresh_token_rotation: true
```

### **🔐 Fly.io Security Configuration**

```toml
# Fly.io security settings
[env]
  NODE_ENV = "production"
  HTTPS_ONLY = "true"
  SECURE_COOKIES = "true"

[secrets]
  DATABASE_URL = "from-supabase"
  REDIS_URL = "from-upstash"
  JWT_SECRET = "generate-secure-key"
  OPENAI_API_KEY = "your-api-key"

# Private networking
[networks]
  ipv6_auto = true
  
[[networks.machines]]
  internal = true  # Private network only
```

---

## 💾 **Backup & Monitoring**

### **🔄 Automated Backup Strategy**

```yaml
# Supabase Backups (Built-in)
backups:
  daily_snapshots: true
  retention_days: 7
  point_in_time_recovery: true  # Pro plan feature
  
# Fly.io Volume Snapshots
volumes:
  chromadb_data:
    snapshot_schedule: "daily"
    retention_days: 30
```

### **📊 Monitoring Setup**

```javascript
// Monitoring configuration
const monitoring = {
  supabase: {
    metrics: ['connections', 'queries_per_second', 'storage_usage'],
    alerts: {
      connection_limit: 80,  // 80% of 100 connections
      query_latency: 500,    // 500ms threshold
      storage_usage: 7000    // 7GB of 8GB
    }
  },
  
  flyio: {
    metrics: ['cpu_usage', 'memory_usage', 'request_latency'],
    alerts: {
      cpu_usage: 80,
      memory_usage: 85,
      request_latency: 1000
    }
  }
};
```

---

## 📈 **Scaling Strategy**

### **🎯 Performance Targets**
| 📊 **Metric** | 🎯 **Target** | 📏 **Implementation** |
|---|---|---|
| **Database Latency** | <100ms | Supabase edge network + connection pooling |
| **Cache Hit Rate** | >90% | Upstash Redis with intelligent caching |
| **Availability** | 99.9% | Supabase HA + Fly.io multi-region |
| **Throughput** | 10k requests/day | Horizontal scaling with Fly.io machines |

### **📊 Auto-Scaling Configuration**

```toml
# Fly.io auto-scaling
[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  max_machines_running = 10

[[http_service.checks]]
  grace_period = "5s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"
```

---

## 💰 **Cost Optimization**

### **💵 Monthly Production Costs**

| 🏷️ **Component** | 💵 **Monthly Cost** | 📝 **Configuration** |
|---|---|---|
| **Supabase Pro** | $25 | PostgreSQL + pgvector + Auth + Storage |
| **Upstash Redis** | $10 | 1GB Redis with global edge |
| **Fly.io FastAPI** | $30-50 | 2-4 shared CPU machines |
| **Fly.io N8n** | $30-50 | 2-4 shared CPU machines |
| **Fly.io ChromaDB** | $20-30 | 1-2 machines with volumes |
| **Domain + SSL** | $15 | Custom domain + certificates |
| **Monitoring** | $10 | Basic observability stack |
| **🎯 Total** | **≈ $140-180** | **~90% cost reduction vs AWS** |

### **🔄 Cost Scaling**
- **0-1k requests/day**: $75-100/month
- **1k-10k requests/day**: $140-180/month  
- **10k+ requests/day**: $250-350/month (still 5x cheaper than AWS)

---

## 🚀 **Deployment Architecture**

### **📋 Deployment Stack**

```yaml
# docker-compose.override.yml for production
version: '3.8'

services:
  app:
    image: greenlightpa/app:latest
    environment:
      - DATABASE_URL=${SUPABASE_DATABASE_URL}
      - REDIS_URL=${UPSTASH_REDIS_URL}
      - CHROMADB_URL=http://chromadb:8000
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    deploy:
      platform: fly.io
      
  n8n:
    image: n8nio/n8n:latest
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=${SUPABASE_DB_HOST}
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=${SUPABASE_DB_PASSWORD}
    deploy:
      platform: fly.io
      
  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma
    deploy:
      platform: fly.io
```

---

## 🎯 **Migration Path**

### **🔄 From Development to Production**

1. **Database Migration**
   ```bash
   # Export development data
   pg_dump greenlightpa_dev > dev_backup.sql
   
   # Import to Supabase
   psql "${SUPABASE_DATABASE_URL}" < dev_backup.sql
   ```

2. **Environment Transition**
   ```bash
   # Update environment variables
   fly secrets set DATABASE_URL="${SUPABASE_DATABASE_URL}"
   fly secrets set REDIS_URL="${UPSTASH_REDIS_URL}"
   fly secrets set SUPABASE_URL="${SUPABASE_URL}"
   ```

3. **Deploy Applications**
   ```bash
   # Deploy FastAPI
   fly deploy --app greenlightpa-api
   
   # Deploy N8n
   fly deploy --app greenlightpa-n8n
   
   # Deploy ChromaDB
   fly deploy --app greenlightpa-chromadb
   ```

---

## 🎯 **Success Criteria**

### **✅ Production Readiness Checklist**
- [ ] Supabase project configured with RLS policies
- [ ] Upstash Redis cache deployed and configured
- [ ] Fly.io applications deployed with auto-scaling
- [ ] Custom domain with SSL certificates
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested
- [ ] HIPAA compliance validated
- [ ] Performance benchmarks achieved
- [ ] Security audit completed
- [ ] Team training on new stack

### **🏆 Key Performance Indicators**
- **🎯 Uptime**: 99.9% availability
- **⚡ Latency**: <200ms API response time
- **📈 Scalability**: Handle 10k PA requests/day
- **🔒 Security**: Zero security incidents
- **💰 Cost**: Stay within $200/month budget
- **🚀 Deployment**: <5 minute deployments

---

*📅 Last Updated: June 2025*  
*🏷️ Version: 2.0.0*  
*🏗️ Architecture: Supabase + Fly.io Production* 