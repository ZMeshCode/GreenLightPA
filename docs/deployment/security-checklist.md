# 🔒 Security Configuration Checklist

## 📋 Overview

This comprehensive security checklist ensures GreenLightPA meets HIPAA compliance requirements and follows healthcare data security best practices. Our hybrid N8n + LangChain architecture requires special attention to AI model security, workflow data protection, and healthcare data handling.

## 🏥 HIPAA Compliance Requirements

### **Administrative Safeguards**
- [ ] **Security Officer Designated**: Assign security responsibility to specific individual
- [ ] **Workforce Training**: All team members trained on HIPAA requirements
- [ ] **Access Management**: Implement minimum necessary access principles
- [ ] **Information Lifecycle**: Document data retention and disposal procedures
- [ ] **Incident Response Plan**: Procedures for security breaches and incidents
- [ ] **Business Associate Agreements**: Signed BAAs with all third-party vendors

### **Physical Safeguards**
- [ ] **Facility Access Controls**: Secure physical access to servers/workstations
- [ ] **Workstation Use**: Controls for workstation access and usage
- [ ] **Device Controls**: Hardware inventory and access controls
- [ ] **Media Controls**: Procedures for handling storage media

### **Technical Safeguards**
- [ ] **Access Control**: Unique user identification and automatic logoff
- [ ] **Audit Controls**: System activity monitoring and logging
- [ ] **Integrity**: PHI protection from alteration or destruction
- [ ] **Person Authentication**: User identity verification
- [ ] **Transmission Security**: End-to-end encryption for data in transit

## 🛡️ Application Security Configuration

### **Authentication & Authorization**

#### **JWT Configuration**
```python
# app/core/security.py
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

class SecurityConfig:
    # Use strong secret key (256-bit)
    SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Must be 32+ characters
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return SecurityConfig.pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return SecurityConfig.pwd_context.hash(password)
```

#### **Multi-Factor Authentication (MFA)**
- [ ] **TOTP Implementation**: Time-based one-time passwords
- [ ] **Backup Codes**: Generate recovery codes for users
- [ ] **SMS Fallback**: Optional SMS-based 2FA
- [ ] **MFA Enforcement**: Require MFA for all privileged accounts

```python
# app/auth/mfa.py
import pyotp
import qrcode
from io import BytesIO

class MFAService:
    @staticmethod
    def generate_secret():
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str):
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="GreenLightPA"
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")
```

### **Data Encryption**

#### **Encryption at Rest**
- [ ] **Database Encryption**: PostgreSQL TDE (Transparent Data Encryption)
- [ ] **File System Encryption**: LUKS/dm-crypt for Linux, FileVault for macOS
- [ ] **Application-Level Encryption**: Sensitive fields encrypted before storage
- [ ] **Key Management**: AWS KMS or HashiCorp Vault for key rotation

```python
# app/core/encryption.py
from cryptography.fernet import Fernet
import base64
import os

class FieldEncryption:
    def __init__(self):
        key = os.getenv("FIELD_ENCRYPTION_KEY")
        if not key:
            raise ValueError("FIELD_ENCRYPTION_KEY must be set")
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive field data"""
        return base64.b64encode(
            self.cipher.encrypt(data.encode())
        ).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive field data"""
        return self.cipher.decrypt(
            base64.b64decode(encrypted_data.encode())
        ).decode()
```

#### **Encryption in Transit**
- [ ] **TLS 1.3**: All communications use latest TLS
- [ ] **Certificate Management**: Valid SSL certificates for all endpoints
- [ ] **HSTS Headers**: HTTP Strict Transport Security enabled
- [ ] **Certificate Pinning**: Pin certificates in production

```python
# app/core/middleware.py
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def configure_security_middleware(app: FastAPI):
    # Force HTTPS in production
    if os.getenv("ENVIRONMENT") == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["greenlightpa.com", "*.greenlightpa.com"]
    )
    
    # Security headers
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
```

### **Input Validation & Sanitization**

#### **Pydantic Models for Validation**
```python
# app/schemas/validation.py
from pydantic import BaseModel, validator, Field
import re

class PatientDataInput(BaseModel):
    patient_id: str = Field(..., regex=r'^[A-Z0-9]{6,12}$')
    diagnosis_codes: List[str] = Field(..., max_items=20)
    
    @validator('diagnosis_codes')
    def validate_icd10_codes(cls, v):
        icd10_pattern = r'^[A-Z]\d{2}(\.\d{1,3})?$'
        for code in v:
            if not re.match(icd10_pattern, code):
                raise ValueError(f'Invalid ICD-10 code: {code}')
        return v
    
    @validator('patient_id')
    def sanitize_patient_id(cls, v):
        # Remove any potential script injection
        return re.sub(r'[<>"\'/]', '', v).upper()
```

#### **SQL Injection Prevention**
- [ ] **SQLAlchemy ORM**: Use parameterized queries exclusively
- [ ] **No Raw SQL**: Avoid raw SQL queries where possible
- [ ] **Input Sanitization**: Validate all user inputs
- [ ] **Query Logging**: Log all database queries for audit

```python
# app/db/base.py
from sqlalchemy.orm import Session
from sqlalchemy import text

class SecureDatabase:
    @staticmethod
    def safe_query(db: Session, query: str, params: dict):
        """Execute parameterized query safely"""
        return db.execute(text(query), params)
    
    @staticmethod
    def validate_input(data: dict) -> dict:
        """Validate and sanitize input data"""
        # Remove null bytes and control characters
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
            else:
                cleaned[key] = value
        return cleaned
```

## 🔐 N8n Workflow Security

### **N8n Configuration Security**
- [ ] **Authentication Enabled**: Basic auth or OAuth configured
- [ ] **HTTPS Only**: TLS encryption for all N8n communications
- [ ] **Webhook Security**: Implement webhook authentication
- [ ] **Credential Encryption**: N8n credentials properly encrypted
- [ ] **Access Controls**: Role-based access to workflows

```yaml
# N8n security configuration
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=${N8N_USER}
N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
N8N_PROTOCOL=https
N8N_HOST=workflows.greenlightpa.com
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}  # 32+ characters
```

### **Workflow Data Protection**
- [ ] **Data Minimization**: Only process necessary PHI in workflows
- [ ] **Temporary Storage**: Clear sensitive data from workflow memory
- [ ] **Audit Logging**: Log all workflow executions with PHI access
- [ ] **Error Handling**: Prevent PHI leakage in error messages

```javascript
// N8n workflow security node
module.exports = {
  async execute() {
    try {
      // Process patient data
      const result = await processPatientData(this.getInputData());
      
      // Clear sensitive data from memory
      this.clearSensitiveData();
      
      return result;
    } catch (error) {
      // Log error without exposing PHI
      this.logSecureError(error);
      throw new Error('Processing failed - see audit logs');
    }
  },
  
  clearSensitiveData() {
    // Clear sensitive variables
    delete this.nodeExecutionData.phi_data;
    delete this.nodeExecutionData.patient_info;
  }
};
```

## 🧠 LangChain AI Security

### **Model Security Configuration**
- [ ] **API Key Security**: Secure storage and rotation of OpenAI keys
- [ ] **Data Filtering**: Remove PHI before sending to external models
- [ ] **Local Models**: Use on-premises models for sensitive data
- [ ] **Output Filtering**: Scan model outputs for potential PHI leakage

```python
# app/services/secure_langchain.py
import re
from typing import Dict, Any
from langchain.schema import BaseMessage

class SecureLangChainService:
    def __init__(self):
        self.phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b\d{10}\b',  # Phone number
        ]
    
    def sanitize_input(self, text: str) -> str:
        """Remove potential PHI from input"""
        sanitized = text
        for pattern in self.phi_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        return sanitized
    
    def validate_output(self, output: str) -> str:
        """Ensure output doesn't contain PHI"""
        for pattern in self.phi_patterns:
            if re.search(pattern, output):
                raise SecurityError("Model output contains potential PHI")
        return output
```

### **Vector Database Security**
- [ ] **Access Controls**: Restrict ChromaDB/pgvector access
- [ ] **Data Encryption**: Encrypt vector embeddings
- [ ] **Anonymization**: Remove direct identifiers from stored vectors
- [ ] **Retention Policies**: Implement data lifecycle management

```python
# app/services/secure_vectorstore.py
class SecureVectorStore:
    def __init__(self):
        self.encryption = FieldEncryption()
    
    def store_document(self, doc: str, metadata: Dict[str, Any]):
        # Remove direct identifiers
        sanitized_metadata = self.anonymize_metadata(metadata)
        
        # Encrypt sensitive content
        encrypted_content = self.encryption.encrypt(doc)
        
        # Store with audit trail
        self.audit_log.log_storage(
            action="document_stored",
            metadata=sanitized_metadata,
            timestamp=datetime.utcnow()
        )
        
        return self.vector_store.add_documents([encrypted_content])
```

## 🗄️ Database Security

### **PostgreSQL Security Configuration**
```sql
-- Enable SSL connections only
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/server.key';

-- Configure authentication
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Audit logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- Row Level Security for PHI
CREATE POLICY patient_access_policy ON patients
    USING (current_user_id() = assigned_provider_id);

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

### **Database Access Controls**
- [ ] **Role-Based Access**: Implement least privilege principle
- [ ] **Connection Encryption**: SSL/TLS for all connections
- [ ] **Audit Logging**: Log all database access and changes
- [ ] **Backup Encryption**: Encrypt all database backups

```sql
-- Create roles with minimal permissions
CREATE ROLE greenlightpa_app;
GRANT CONNECT ON DATABASE greenlightpa TO greenlightpa_app;
GRANT USAGE ON SCHEMA healthcare TO greenlightpa_app;
GRANT SELECT, INSERT, UPDATE ON healthcare.patients TO greenlightpa_app;

-- Audit table for all PHI access
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(50),
    table_name VARCHAR(100),
    record_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address INET
);
```

## 📊 Audit Logging & Monitoring

### **Comprehensive Audit Trail**
```python
# app/core/audit.py
from enum import Enum
from sqlalchemy.orm import Session

class AuditAction(Enum):
    PHI_ACCESS = "phi_access"
    DATA_EXPORT = "data_export"
    WORKFLOW_EXECUTION = "workflow_execution"
    MODEL_INFERENCE = "model_inference"

class AuditLogger:
    def __init__(self, db: Session):
        self.db = db
    
    def log_phi_access(self, user_id: str, patient_id: str, 
                      action: str, ip_address: str):
        audit_entry = AuditLog(
            user_id=user_id,
            action=AuditAction.PHI_ACCESS.value,
            details={
                "patient_id": patient_id,
                "action": action,
                "ip_address": ip_address
            },
            timestamp=datetime.utcnow()
        )
        self.db.add(audit_entry)
        self.db.commit()
```

### **Security Monitoring**
- [ ] **Failed Login Alerts**: Monitor and alert on failed attempts
- [ ] **Unusual Access Patterns**: Detect anomalous data access
- [ ] **Data Export Monitoring**: Track all data exports and downloads
- [ ] **AI Model Usage**: Monitor LLM API calls and responses

```python
# app/monitoring/security_monitor.py
class SecurityMonitor:
    def __init__(self):
        self.alert_threshold = 5  # Failed attempts
        self.time_window = 300  # 5 minutes
    
    def check_failed_logins(self, ip_address: str):
        recent_failures = self.get_recent_failures(ip_address)
        if len(recent_failures) >= self.alert_threshold:
            self.send_security_alert(
                f"Multiple failed logins from {ip_address}"
            )
            # Implement IP blocking
            self.block_ip(ip_address)
```

## 🌐 Network Security

### **Firewall Configuration**
```bash
# iptables rules for production
# Allow only necessary ports
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # SSH (restrict to specific IPs)
iptables -A INPUT -p tcp --dport 5432 -j DROP   # Block direct DB access
iptables -A INPUT -p tcp --dport 6379 -j DROP   # Block direct Redis access

# Default deny
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
```

### **API Gateway Security**
- [ ] **Rate Limiting**: Implement request rate limits
- [ ] **IP Whitelisting**: Restrict access to known IPs
- [ ] **WAF Protection**: Web Application Firewall
- [ ] **DDoS Protection**: CloudFlare or AWS Shield

```python
# app/middleware/rate_limiting.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.route("/api/v1/patients")
@limiter.limit("10/minute")  # Limit PHI access
async def get_patients(request: Request):
    return await process_patient_request(request)
```

## 🧪 Security Testing

### **Automated Security Scanning**
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit Security Linter
        run: bandit -r app/ -f json -o bandit-report.json
      
      - name: Run Safety Check
        run: safety check --json --output safety-report.json
      
      - name: Run Semgrep
        run: semgrep --config=auto app/
      
      - name: Docker Security Scan
        run: docker run --rm -v $(pwd):/app aquasec/trivy fs /app
```

### **Penetration Testing Checklist**
- [ ] **SQL Injection Testing**: Test all input fields
- [ ] **XSS Testing**: Cross-site scripting vulnerability check
- [ ] **Authentication Testing**: Test MFA and session management
- [ ] **Authorization Testing**: Verify access controls
- [ ] **API Security Testing**: Test all API endpoints

## 📋 Security Incident Response

### **Incident Response Plan**
1. **Detection**: Automated alerts and monitoring
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threats and vulnerabilities
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Post-incident review

### **Breach Notification Requirements**
- [ ] **HIPAA Notification**: 60 days to HHS, 60 days to affected individuals
- [ ] **State Notifications**: Comply with state breach notification laws
- [ ] **Business Associate Notifications**: Notify within 60 days
- [ ] **Documentation**: Maintain detailed incident records

```python
# app/security/incident_response.py
class IncidentResponse:
    def handle_security_incident(self, incident_type: str, details: dict):
        # Log incident
        self.log_incident(incident_type, details)
        
        # Assess severity
        severity = self.assess_severity(incident_type, details)
        
        # Notify appropriate parties
        if severity >= SeverityLevel.HIGH:
            self.notify_security_team()
            self.initiate_containment()
        
        # Check if PHI is involved
        if self.involves_phi(details):
            self.initiate_breach_protocol()
```

## ✅ Security Verification Checklist

### **Pre-Production Security Review**
- [ ] All passwords use strong, unique values
- [ ] SSL/TLS certificates are valid and properly configured
- [ ] All default credentials have been changed
- [ ] Security headers are implemented
- [ ] Input validation is comprehensive
- [ ] Error handling doesn't leak sensitive information
- [ ] Audit logging captures all required events
- [ ] Backup and recovery procedures are tested
- [ ] Incident response plan is documented and tested
- [ ] All team members are trained on security procedures

### **Ongoing Security Maintenance**
- [ ] **Weekly**: Review security logs and alerts
- [ ] **Monthly**: Update dependencies and security patches
- [ ] **Quarterly**: Conduct security assessments
- [ ] **Annually**: Full penetration testing and HIPAA compliance audit

---

**🎯 Security Objective**: Maintain the highest level of security for healthcare data while enabling innovative AI-powered prior authorization automation. This checklist ensures GreenLightPA meets all regulatory requirements and industry security standards. 