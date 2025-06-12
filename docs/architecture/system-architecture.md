# System Architecture: Hybrid N8n + LangChain

## 🏗️ Architecture Overview

The GreenLightPA system employs a **hybrid architecture** that combines the visual workflow orchestration capabilities of N8n with the advanced AI processing power of LangChain. This approach provides the optimal balance of low-code workflow management and sophisticated AI capabilities for healthcare automation.

## 🎯 Architecture Principles

### **Separation of Concerns**
- **N8n**: Handles workflow orchestration, business logic, and external integrations
- **LangChain**: Manages AI processing, NLP, and RAG operations
- **FastAPI**: Provides API gateway and microservice coordination
- **PostgreSQL**: Manages data persistence and vector storage

### **Event-Driven Architecture**
- Webhook-based communication between components
- Asynchronous processing for scalability
- Message queuing for reliable delivery
- Real-time status updates and notifications

### **HIPAA-Compliant Design**
- End-to-end encryption for PHI
- Audit logging for all operations
- Role-based access control (RBAC)
- Secure credential management

## 🔧 System Components

### **Layer 1: Presentation & Interface**
```
┌─────────────────────────────────────────────────────────────────┐
│                     Presentation Layer                          │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  React/Next.js  │  │ EHR SMART Widget│  │ N8n Admin UI    │  │
│  │   Dashboard     │  │     (FHIR)      │  │   (Workflows)   │  │
│  │                 │  │                 │  │                 │  │
│  │ • PA Status     │  │ • Patient Ctx   │  │ • Flow Editor   │  │
│  │ • Analytics     │  │ • Real-time PA  │  │ • Monitoring    │  │
│  │ • User Mgmt     │  │ • Approvals     │  │ • Debugging     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **Layer 2: API Gateway & Security**
```
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              FastAPI Gateway (HTTPS/LB)                    │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │   Auth      │  │   Health    │  │     Webhook         │ │ │
│  │  │  Service    │  │   Check     │  │    Endpoints        │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • JWT Auth  │  │ • Liveness  │  │ • N8n Integration   │ │ │
│  │  │ • RBAC      │  │ • Readiness │  │ • EHR Callbacks     │ │ │
│  │  │ • SMART     │  │ • Metrics   │  │ • Payer Responses   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Layer 3: Workflow Orchestration**
```
┌─────────────────────────────────────────────────────────────────┐
│                   Workflow Orchestration Layer                  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                        N8n Engine                          │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │   FHIR      │  │   Payer     │  │     Status          │ │ │
│  │  │ Integration │  │Integration  │  │   Tracking          │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • Document  │  │ • X12 278   │  │ • Polling           │ │ │
│  │  │   Ingestion │  │ • API Calls │  │ • Notifications     │ │ │
│  │  │ • Validation│  │ • Fax/Voice │  │ • State Updates     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │  Document   │  │  Business   │  │    Notification     │ │ │
│  │  │  Processing │  │   Logic     │  │     Service         │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • Chunking  │  │ • Routing   │  │ • Email/SMS         │ │ │
│  │  │ • Metadata  │  │ • Approval  │  │ • EHR Updates       │ │ │
│  │  │ • Archival  │  │ • Retry     │  │ • Dashboard         │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Layer 4: AI Processing**
```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Processing Layer                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    LangChain Engine                        │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │    NLP      │  │    RAG      │  │      Packet         │ │ │
│  │  │ Extraction  │  │   Engine    │  │    Generation       │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • ICD-10    │  │ • Policy    │  │ • X12 278           │ │ │
│  │  │ • CPT       │  │   Matching  │  │ • Cover Letters     │ │ │
│  │  │ • HCPCS     │  │ • Citations │  │ • Supporting Docs   │ │ │
│  │  │ • NDC/SNOMED│  │ • Reasoning │  │ • Payer Forms       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │   Policy    │  │   Code      │  │    Eligibility      │ │ │
│  │  │  Matching   │  │ Detection   │  │   Verification      │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ • Necessity │  │ • Confidence│  │ • Benefits Check    │ │ │
│  │  │ • Coverage  │  │ • Validation│  │ • Prior Auths       │ │ │
│  │  │ • Evidence  │  │ • Context   │  │ • Limitations       │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Layer 5: Data Storage (Supabase + Fly.io)**
```
┌─────────────────────────────────────────────────────────────────┐
│                       Data Storage Layer                        │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Supabase    │  │  ChromaDB   │  │     Upstash Redis       │  │
│  │ PostgreSQL  │  │  (Fly.io)   │  │    (Edge Cache)         │  │
│  │+ pgvector   │  │             │  │                         │  │
│  │             │  │ • Policy    │  │ • Session Store         │  │
│  │ • Patients  │  │   Embeddings│  │ • API Cache             │  │
│  │ • PA Requests│  │ • Clinical  │  │ • Workflow State        │  │
│  │ • Audit Logs│  │   Documents │  │ • Rate Limiting         │  │
│  │ • Workflows │  │ • Knowledge │  │ • Temporary Data        │  │
│  │ • Users/Auth│  │   Base      │  │ • Global Edge           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### **Layer 6: External Integrations**
```
┌─────────────────────────────────────────────────────────────────┐
│                    External Integration Layer                   │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Payer     │  │   Twilio    │  │       FHIR/HL7          │  │
│  │   APIs      │  │   Voice     │  │    EHR Systems          │  │
│  │   (X12)     │  │   (IVR)     │  │                         │  │
│  │             │  │             │  │ • Epic                  │  │
│  │ • Change HC │  │ • Status    │  │ • Cerner                │  │
│  │ • Direct    │  │   Updates   │  │ • Allscripts            │  │
│  │   APIs      │  │ • Reminders │  │ • SMART Launch          │  │
│  │ • Legacy    │  │ • IVR Nav   │  │ • Context Sharing       │  │
│  │   Portals   │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Architecture

### **Primary PA Processing Flow**
```mermaid
sequenceDiagram
    participant EHR
    participant N8n
    participant FastAPI
    participant LangChain
    participant ChromaDB
    participant Payer
    
    EHR->>N8n: FHIR Bundle (Webhook)
    N8n->>N8n: Validate FHIR
    N8n->>FastAPI: Store Bundle
    N8n->>FastAPI: Trigger LangChain
    
    FastAPI->>LangChain: Extract Codes
    LangChain->>LangChain: NLP Processing
    LangChain->>ChromaDB: Vector Search
    ChromaDB-->>LangChain: Policy Matches
    LangChain-->>FastAPI: Extracted Codes + Policy Analysis
    
    FastAPI->>N8n: Processing Complete (Webhook)
    N8n->>N8n: Generate PA Packet
    N8n->>Payer: Submit PA (API/Fax/Voice)
    Payer-->>N8n: Status Update
    N8n->>EHR: Update PA Status
```

### **Policy Update Flow**
```mermaid
sequenceDiagram
    participant Scheduler
    participant N8n
    participant Scraper
    participant LangChain
    participant ChromaDB
    
    Scheduler->>N8n: Trigger Policy Update (Cron)
    N8n->>Scraper: Get Payer Policy URLs
    Scraper->>Scraper: Download Policy PDFs
    Scraper-->>N8n: Policy Documents
    
    N8n->>LangChain: Process Policy Documents
    LangChain->>LangChain: Chunk & Embed
    LangChain->>ChromaDB: Update Vector Store
    ChromaDB-->>LangChain: Confirmation
    LangChain-->>N8n: Update Complete
    
    N8n->>N8n: Log Update Results
```

### **Error Handling Flow**
```mermaid
sequenceDiagram
    participant Component
    participant N8n
    participant ErrorHandler
    participant Monitoring
    participant Human
    
    Component->>N8n: Process Failure
    N8n->>ErrorHandler: Log Error
    ErrorHandler->>ErrorHandler: Evaluate Retry
    
    alt Retry Available
        ErrorHandler->>N8n: Schedule Retry
        N8n->>Component: Retry Process
    else Max Retries Exceeded
        ErrorHandler->>Monitoring: Alert
        ErrorHandler->>Human: Manual Review Queue
        Human->>N8n: Manual Resolution
    end
```

## 🔧 Integration Patterns

### **N8n ↔ LangChain Communication**

#### **API Call Pattern**
```javascript
// N8n HTTP Request Node
{
  "method": "POST",
  "url": "http://fastapi:8000/api/v1/langchain/extract-codes",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpHeaderAuth",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {{$env.LANGCHAIN_API_TOKEN}}"
  },
  "body": {
    "clinical_text": "={{$json.clinicalText}}",
    "patient_id": "={{$json.patientId}}",
    "metadata": {
      "encounter_id": "={{$json.encounterId}}",
      "timestamp": "={{new Date().toISOString()}}"
    }
  }
}
```

#### **Webhook Response Pattern**
```python
# FastAPI Webhook Handler
@router.post("/n8n/webhook/extraction-complete")
async def handle_extraction_complete(
    payload: ExtractionWebhookPayload,
    background_tasks: BackgroundTasks
):
    # Process extraction results
    extraction_result = await process_extraction_results(payload)
    
    # Trigger next N8n workflow step
    background_tasks.add_task(
        trigger_n8n_workflow,
        "policy-analysis",
        extraction_result
    )
    
    return {"status": "accepted", "next_step": "policy_analysis"}
```

### **State Management Pattern**

#### **Workflow State Persistence**
```python
# Workflow State Service
class WorkflowStateService:
    async def save_state(self, execution_id: str, state: Dict[str, Any]):
        """Persist workflow state to database"""
        await self.db.execute(
            "INSERT INTO workflow_states (execution_id, state_data, updated_at) "
            "VALUES ($1, $2, NOW()) "
            "ON CONFLICT (execution_id) DO UPDATE SET "
            "state_data = $2, updated_at = NOW()",
            execution_id, json.dumps(state)
        )
    
    async def get_state(self, execution_id: str) -> Dict[str, Any]:
        """Retrieve workflow state from database"""
        result = await self.db.fetchrow(
            "SELECT state_data FROM workflow_states WHERE execution_id = $1",
            execution_id
        )
        return json.loads(result['state_data']) if result else {}
```

### **Error Recovery Pattern**

#### **Circuit Breaker Implementation**
```python
# Circuit breaker for external API calls
@circuit_breaker(failure_threshold=3, timeout=30)
async def call_payer_api(payer_id: str, pa_data: Dict[str, Any]):
    """Call payer API with circuit breaker protection"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.{payer_id}.com/prior-auth",
            json=pa_data,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

## 📊 Performance Architecture

### **Scaling Strategy**

#### **Horizontal Scaling**
```yaml
# Kubernetes Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n-workers
spec:
  replicas: 3
  selector:
    matchLabels:
      app: n8n-worker
  template:
    metadata:
      labels:
        app: n8n-worker
    spec:
      containers:
      - name: n8n
        image: n8nio/n8n:latest
        env:
        - name: EXECUTIONS_MODE
          value: "queue"
        - name: QUEUE_BULL_REDIS_HOST
          value: "redis-cluster"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

#### **Load Balancing**
```nginx
# Nginx Load Balancer Configuration
upstream n8n_backend {
    least_conn;
    server n8n-1:5678 max_fails=3 fail_timeout=30s;
    server n8n-2:5678 max_fails=3 fail_timeout=30s;
    server n8n-3:5678 max_fails=3 fail_timeout=30s;
}

upstream fastapi_backend {
    least_conn;
    server fastapi-1:8000 max_fails=3 fail_timeout=30s;
    server fastapi-2:8000 max_fails=3 fail_timeout=30s;
    server fastapi-3:8000 max_fails=3 fail_timeout=30s;
}
```

### **Caching Strategy**

#### **Multi-Level Caching**
```python
# Caching Layer Implementation
class CacheService:
    def __init__(self):
        self.redis = Redis(host='redis-cluster')
        self.local_cache = TTLCache(maxsize=1000, ttl=300)
    
    async def get_cached_result(self, key: str) -> Optional[Any]:
        # L1: Local cache (fastest)
        if key in self.local_cache:
            return self.local_cache[key]
        
        # L2: Redis cache (fast)
        result = await self.redis.get(key)
        if result:
            parsed_result = json.loads(result)
            self.local_cache[key] = parsed_result
            return parsed_result
        
        return None
    
    async def set_cached_result(self, key: str, value: Any, ttl: int = 3600):
        # Store in both caches
        self.local_cache[key] = value
        await self.redis.setex(key, ttl, json.dumps(value))
```

## 🔒 Security Architecture

### **Authentication & Authorization Flow**
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Auth0
    participant FastAPI
    participant N8n
    participant Database
    
    User->>Frontend: Login Request
    Frontend->>Auth0: OIDC Authentication
    Auth0-->>Frontend: JWT Token
    Frontend->>FastAPI: API Request + JWT
    
    FastAPI->>FastAPI: Validate JWT
    FastAPI->>Database: Check Permissions
    Database-->>FastAPI: User Roles
    FastAPI->>N8n: Trigger Workflow (if authorized)
    N8n-->>FastAPI: Workflow Result
    FastAPI-->>Frontend: API Response
```

### **Data Encryption**

#### **At Rest**
```sql
-- Field-level encryption for PHI
CREATE TABLE patient_data (
    id UUID PRIMARY KEY,
    patient_id VARCHAR(255),
    encrypted_name BYTEA,  -- AES-256 encrypted
    encrypted_dob BYTEA,   -- AES-256 encrypted
    encrypted_ssn BYTEA,   -- AES-256 encrypted
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### **In Transit**
```yaml
# TLS Configuration
tls:
  version: "1.3"
  cipher_suites:
    - "TLS_AES_256_GCM_SHA384"
    - "TLS_CHACHA20_POLY1305_SHA256"
  certificate_path: "/etc/ssl/certs/greenlightpa.crt"
  private_key_path: "/etc/ssl/private/greenlightpa.key"
```

### **Audit Logging**
```python
# Comprehensive audit logging
class AuditLogger:
    async def log_access(self, user_id: str, resource: str, action: str, result: str):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "result": result,
            "ip_address": self.get_client_ip(),
            "user_agent": self.get_user_agent()
        }
        
        # Store in audit table
        await self.db.execute(
            "INSERT INTO audit_logs (data) VALUES ($1)",
            json.dumps(audit_entry)
        )
        
        # Send to SIEM if high-risk action
        if action in ["DELETE", "EXPORT", "ADMIN_ACCESS"]:
            await self.send_to_siem(audit_entry)
```

## 📈 Monitoring & Observability

### **Metrics Collection**
```python
# Prometheus metrics for N8n workflows
from prometheus_client import Counter, Histogram, Gauge

workflow_executions = Counter(
    'n8n_workflow_executions_total',
    'Total workflow executions',
    ['workflow_name', 'status']
)

workflow_duration = Histogram(
    'n8n_workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_name']
)

active_workflows = Gauge(
    'n8n_active_workflows',
    'Number of currently active workflows'
)
```

### **Health Checks**
```python
# Comprehensive health check endpoint
@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check N8n connectivity
    try:
        n8n_response = await check_n8n_health()
        health_status["services"]["n8n"] = "healthy"
    except Exception as e:
        health_status["services"]["n8n"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check LangChain services
    try:
        langchain_response = await check_langchain_health()
        health_status["services"]["langchain"] = "healthy"
    except Exception as e:
        health_status["services"]["langchain"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
```

## 🚀 Deployment Architecture

### **Container Orchestration**
```yaml
# Docker Compose for development
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: greenlightpa
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  n8n:
    image: n8nio/n8n:latest
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - N8N_BASIC_AUTH_ACTIVE=true
    depends_on:
      - postgres
      - redis
    volumes:
      - n8n_data:/home/node/.n8n
  
  fastapi:
    build: .
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/greenlightpa
    depends_on:
      - postgres
      - redis
      - n8n
```

### **Production Kubernetes**
```yaml
# Kubernetes deployment for production
apiVersion: v1
kind: Namespace
metadata:
  name: greenlightpa

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: greenlightpa-api
  namespace: greenlightpa
spec:
  replicas: 3
  selector:
    matchLabels:
      app: greenlightpa-api
  template:
    metadata:
      labels:
        app: greenlightpa-api
    spec:
      containers:
      - name: fastapi
        image: greenlightpa/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

**This hybrid architecture provides a robust, scalable, and maintainable foundation for automating prior authorization workflows while maintaining the flexibility to adapt to changing healthcare requirements and payer integrations.** 