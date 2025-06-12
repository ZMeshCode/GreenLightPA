# 🚀 GreenLightPA Production Deployment Guide
## *Complete Infrastructure & Application Deployment*

> **Mission**: Deploy GreenLightPA's hybrid N8n + LangChain architecture to production with HIPAA compliance and enterprise-grade reliability.

---

## 🎯 **Production Architecture Summary**

### **🏗️ Infrastructure Hosting**

Your GreenLightPA production database and infrastructure will be hosted on:

1. **🐘 Amazon RDS PostgreSQL** - Primary database with pgvector extension
2. **⚡ Amazon ElastiCache Redis** - High-performance caching layer  
3. **📊 ChromaDB on EKS** - Vector database for embeddings
4. **🚀 Amazon EKS** - Kubernetes cluster for N8n and FastAPI
5. **🔒 AWS KMS + VPC** - Enterprise security and encryption

**💰 Monthly Cost**: ~$1,522 for full production stack with HIPAA compliance

---

## 📋 **Pre-Deployment Checklist**

### **✅ Prerequisites**
- [ ] AWS Account with appropriate permissions
- [ ] Domain name registered (e.g., `greenlightpa.com`)
- [ ] SSL certificate (AWS Certificate Manager)
- [ ] HIPAA Business Associate Agreements (BAAs) signed
- [ ] Environment variables and secrets prepared
- [ ] Terraform >= 1.0 installed
- [ ] kubectl and AWS CLI configured
- [ ] Docker registry access (ECR)

### **🔐 Security Requirements**
- [ ] Multi-factor authentication enabled on AWS
- [ ] IAM roles and policies configured
- [ ] VPC with private subnets designed
- [ ] Security groups with minimal access
- [ ] Encryption keys (KMS) configured
- [ ] Backup and disaster recovery plan

---

## 🚀 **Deployment Process**

### **Phase 1: Infrastructure Setup**

#### **1.1 Initialize Terraform Backend**
```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://greenlightpa-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket greenlightpa-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name greenlightpa-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

#### **1.2 Configure Environment Variables**
```bash
# Create production.tfvars
cd infrastructure/terraform

cat > production.tfvars << EOF
# General Configuration
aws_region = "us-east-1"
environment = "production"

# Database Configuration
database_password = "$(openssl rand -base64 32)"
database_name = "greenlightpa_prod"
database_username = "greenlightpa_admin"

# Network Configuration
vpc_cidr = "10.0.0.0/16"

# RDS Configuration
rds_instance_class = "db.r6g.xlarge"
rds_allocated_storage = 1000
rds_multi_az = true
rds_backup_retention = 30

# Redis Configuration
redis_node_type = "cache.r7g.large"
redis_num_clusters = 3

# EKS Configuration
eks_node_groups = {
  greenlightpa_nodes = {
    instance_types = ["r6g.large"]
    scaling_config = {
      desired_size = 3
      max_size     = 10
      min_size     = 2
    }
    disk_size = 100
  }
}

# Monitoring
alert_email_endpoints = ["ops@greenlightpa.com"]

# Security
allowed_cidr_blocks = ["10.0.0.0/16"]
EOF
```

#### **1.3 Deploy Infrastructure**
```bash
# Initialize and deploy
terraform init
terraform plan -var-file="production.tfvars"
terraform apply -var-file="production.tfvars" -auto-approve

# Save outputs for later use
terraform output -json > ../outputs.json
```

### **Phase 2: Kubernetes Setup**

#### **2.1 Configure kubectl**
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name greenlightpa-production-cluster

# Verify connection
kubectl get nodes
```

#### **2.2 Install Core Kubernetes Components**
```bash
# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"

helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=greenlightpa-production-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Install cert-manager for SSL
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### **Phase 3: Database Initialization**

#### **3.1 Run Database Migrations**
```bash
# Create migration job
kubectl apply -f - << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: database-migration
  namespace: greenlightpa-prod
spec:
  template:
    spec:
      containers:
      - name: migration
        image: greenlightpa/app:latest
        command: ["alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
      restartPolicy: Never
EOF

# Wait for migration to complete
kubectl wait --for=condition=complete job/database-migration --timeout=300s
```

#### **3.2 Initialize Database Schema**
```bash
# Apply initial schema and data
kubectl exec -it deployment/greenlightpa-app -- python scripts/init_production_db.py
```

### **Phase 4: Application Deployment**

#### **4.1 Deploy FastAPI Application**
```bash
# Apply FastAPI deployment
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: greenlightpa-app
  namespace: greenlightpa-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: greenlightpa-app
  template:
    metadata:
      labels:
        app: greenlightpa-app
    spec:
      containers:
      - name: app
        image: greenlightpa/app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
EOF
```

#### **4.2 Deploy N8n Workflow Engine**
```bash
# Install N8n using Helm
helm repo add n8n https://n8nio.github.io/n8n-helm-charts
helm install n8n n8n/n8n \
  --namespace greenlightpa-prod \
  --values - << EOF
replicaCount: 2

image:
  tag: "latest"

config:
  database:
    type: postgres
    postgresdb:
      host: $(terraform output -raw rds_endpoint)
      port: 5432
      database: n8n
      user: greenlightpa_admin
      password: $(terraform output -raw database_password)

  executions:
    mode: queue
    
persistence:
  enabled: true
  size: 10Gi

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

ingress:
  enabled: true
  className: "alb"
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
  - host: n8n.greenlightpa.com
    paths:
    - path: /
      pathType: Prefix
  tls:
  - secretName: n8n-tls
    hosts:
    - n8n.greenlightpa.com
EOF
```

#### **4.3 Deploy ChromaDB**
```bash
# Deploy ChromaDB StatefulSet
kubectl apply -f k8s/chromadb-statefulset.yaml

# Verify deployment
kubectl get pods -l app=chromadb
```

### **Phase 5: Monitoring & Observability**

#### **5.1 Deploy Prometheus & Grafana**
```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus-values.yaml
```

#### **5.2 Configure Log Aggregation**
```bash
# Install Fluent Bit for log shipping
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit \
  --namespace logging \
  --create-namespace \
  --set cloudWatch.enabled=true \
  --set cloudWatch.region=us-east-1
```

### **Phase 6: Security Hardening**

#### **6.1 Network Policies**
```bash
# Apply network security policies
kubectl apply -f k8s/security/network-policies.yaml
```

#### **6.2 Pod Security Standards**
```bash
# Enable pod security standards
kubectl label namespace greenlightpa-prod \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

---

## 🔒 **Security Configuration**

### **🛡️ HIPAA Compliance**

1. **Data Encryption**
   - All data encrypted at rest using AWS KMS
   - TLS 1.3 for data in transit
   - Application-level encryption for PHI fields

2. **Access Controls**
   - Role-based access control (RBAC)
   - Multi-factor authentication required
   - Audit logging for all database access

3. **Network Security**
   - Private VPC with no internet gateway
   - Security groups with minimal required access
   - VPC endpoints for AWS services

### **🔐 Secrets Management**

```bash
# Store database credentials
kubectl create secret generic database-credentials \
  --from-literal=url="$(terraform output -raw database_url)" \
  --namespace greenlightpa-prod

# Store Redis credentials  
kubectl create secret generic redis-credentials \
  --from-literal=url="$(terraform output -raw redis_url)" \
  --namespace greenlightpa-prod

# Store API keys
kubectl create secret generic api-credentials \
  --from-literal=openai-key="$OPENAI_API_KEY" \
  --from-literal=langchain-key="$LANGCHAIN_API_KEY" \
  --namespace greenlightpa-prod
```

---

## 📊 **Post-Deployment Verification**

### **✅ Health Checks**

```bash
# Run comprehensive health check
./scripts/production-health-check.sh

# Expected results:
# ✅ RDS PostgreSQL - Healthy
# ✅ ElastiCache Redis - Healthy  
# ✅ EKS Cluster - Healthy
# ✅ FastAPI Application - Healthy
# ✅ N8n Workflows - Healthy
# ✅ ChromaDB - Healthy
# ✅ SSL Certificates - Valid
# ✅ Monitoring - Active
```

### **🎯 Performance Testing**

```bash
# Load testing
kubectl run load-test --image=fortio/fortio --rm -it -- \
  load -qps 100 -t 60s -c 8 https://api.greenlightpa.com/health

# Database performance test
kubectl exec -it deployment/greenlightpa-app -- \
  python scripts/performance_test.py
```

### **🔍 Security Validation**

```bash
# Run security scan
kubectl run security-scan --image=aquasec/trivy --rm -it -- \
  image greenlightpa/app:latest

# Verify encryption
aws rds describe-db-instances \
  --db-instance-identifier greenlightpa-prod-postgres \
  --query 'DBInstances[0].StorageEncrypted'
```

---

## 📈 **Operational Procedures**

### **🚨 Incident Response**

1. **Alerts Configuration**
   - Database CPU > 80%
   - Application error rate > 1%
   - Failed health checks
   - Security policy violations

2. **Escalation Process**
   - Level 1: Auto-scaling triggers
   - Level 2: On-call engineer notification
   - Level 3: Management escalation

### **💾 Backup & Recovery**

```bash
# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier greenlightpa-prod-postgres \
  --db-snapshot-identifier greenlightpa-manual-$(date +%Y%m%d%H%M%S)

# Test restore procedure
./scripts/test-restore.sh
```

### **🔄 Updates & Maintenance**

```bash
# Application updates
kubectl set image deployment/greenlightpa-app \
  app=greenlightpa/app:v2.0.0 \
  --namespace greenlightpa-prod

# Rolling update verification
kubectl rollout status deployment/greenlightpa-app
```

---

## 🎯 **Success Criteria**

### **✅ Production Readiness Checklist**
- [ ] All infrastructure deployed via Terraform
- [ ] Applications running in EKS with auto-scaling
- [ ] Database encrypted and backed up
- [ ] Monitoring and alerting configured
- [ ] Security policies enforced
- [ ] HIPAA compliance validated
- [ ] Load testing completed
- [ ] Disaster recovery tested
- [ ] Documentation updated
- [ ] Team training completed

### **📊 Key Performance Indicators**
- **🎯 Uptime**: 99.9% availability
- **⚡ Response Time**: <200ms API response
- **🔒 Security**: Zero security incidents
- **💰 Cost**: Within $1,600/month budget
- **📈 Throughput**: Handle 10k PA requests/day

---

## 🚀 **Next Steps**

After successful deployment:

1. **🔄 Sprint 1: Core AI Pipeline** - Implement LangChain NLP extraction
2. **📚 Sprint 2: Policy RAG Engine** - Deploy vector search and policy matching
3. **⚙️ Sprint 3: N8n Integration** - Build workflow automation
4. **📊 Sprint 4: Dashboard & Monitoring** - Create user interfaces
5. **🏥 Sprint 5: Pilot Deployment** - Roll out to first clinic

---

*📅 Last Updated: June 2025*  
*🏷️ Version: 1.0.0*  
*🏗️ Architecture: AWS Production Deployment Guide* 