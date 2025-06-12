# Sprint 2: N8n Integration (3 weeks)

## 🎯 Sprint Overview

**Duration**: 3 weeks  
**Team Focus**: N8n workflow orchestration, FastAPI webhooks, LangChain API integration  
**Sprint Goal**: Establish N8n as the workflow orchestration layer that seamlessly integrates with LangChain services, enabling visual workflow management and automated healthcare data processing.

## 📋 Sprint Objectives

### Primary Goals
1. **N8n Workflow Engine**: Production-ready N8n setup with custom nodes and security
2. **API Integration Layer**: FastAPI webhooks and N8n communication protocols
3. **Core Workflow Templates**: Essential workflows for healthcare data processing
4. **LangChain Service Integration**: Seamless API calls between N8n and LangChain
5. **Monitoring & Observability**: N8n workflow monitoring and analytics
6. **Error Handling & Resilience**: Robust error handling and retry mechanisms

### Success Criteria
- [ ] N8n can trigger LangChain services via API calls
- [ ] Healthcare workflows execute end-to-end successfully
- [ ] Error handling and retry logic work properly
- [ ] Workflow execution times meet performance requirements
- [ ] All integrations are properly monitored and logged

## 🏗️ Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     N8n Workflow Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Healthcare    │  │   AI Service    │  │    Admin        │  │
│  │   Workflows     │  │  Integration    │  │   Workflows     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Integration Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    FastAPI      │  │    Webhooks     │  │   Authentication│  │
│  │   Endpoints     │  │   & Triggers    │  │    & Security   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangChain Services                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │    NLP/Code     │  │    Policy RAG   │  │   Document      │  │
│  │   Extraction    │  │     Engine      │  │   Processing    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Detailed Task Breakdown

### **Task 1: N8n Production Setup**
**Estimated Effort**: 2 days  
**Assignee**: Integration Specialist + DevOps Engineer  

#### Subtasks
- [ ] Configure N8n for production deployment
- [ ] Set up authentication and authorization
- [ ] Configure custom nodes and credentials
- [ ] Implement backup and recovery procedures
- [ ] Set up monitoring and logging

#### Production N8n Configuration
```yaml
# docker-compose.production.yml
services:
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    environment:
      # Database
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
      
      # Security
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_JWT_AUTH_ACTIVE=true
      - N8N_JWT_AUTH_HEADER=authorization
      - N8N_JWT_AUTH_HEADER_VALUE_PREFIX=Bearer
      
      # Execution
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - N8N_PAYLOAD_SIZE_MAX=64
      
      # Webhooks
      - WEBHOOK_URL=https://workflows.greenlightpa.com
      - N8N_PROTOCOL=https
      - N8N_HOST=workflows.greenlightpa.com
      
      # Logging
      - N8N_LOG_LEVEL=info
      - N8N_LOG_OUTPUT=console,file
      
    volumes:
      - n8n_data:/home/node/.n8n
      - n8n_files:/files
    
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Custom N8n Nodes
```javascript
// custom-nodes/langchain-service/LangChainService.node.ts
import { IExecuteFunctions } from 'n8n-core';
import {
    INodeExecutionData,
    INodeType,
    INodeTypeDescription,
    NodeOperationError,
} from 'n8n-workflow';

export class LangChainService implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'LangChain Service',
        name: 'langChainService',
        group: ['ai'],
        version: 1,
        description: 'Integrate with GreenLightPA LangChain services',
        defaults: {
            name: 'LangChain Service',
        },
        inputs: ['main'],
        outputs: ['main'],
        credentials: [
            {
                name: 'langChainApi',
                required: true,
            },
        ],
        properties: [
            {
                displayName: 'Operation',
                name: 'operation',
                type: 'options',
                options: [
                    {
                        name: 'Extract Clinical Codes',
                        value: 'extractCodes',
                    },
                    {
                        name: 'Policy RAG Query',
                        value: 'policyRag',
                    },
                    {
                        name: 'Process FHIR Document',
                        value: 'processFhir',
                    },
                ],
                default: 'extractCodes',
            },
            {
                displayName: 'Clinical Text',
                name: 'clinicalText',
                type: 'string',
                typeOptions: {
                    alwaysOpenEditWindow: true,
                    rows: 5,
                },
                displayOptions: {
                    show: {
                        operation: ['extractCodes'],
                    },
                },
                default: '',
                required: true,
            },
        ],
    };

    async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
        const items = this.getInputData();
        const returnData: INodeExecutionData[] = [];
        const operation = this.getNodeParameter('operation', 0) as string;

        for (let i = 0; i < items.length; i++) {
            try {
                let responseData;
                
                if (operation === 'extractCodes') {
                    const clinicalText = this.getNodeParameter('clinicalText', i) as string;
                    
                    responseData = await this.helpers.httpRequest({
                        method: 'POST',
                        url: 'http://fastapi:8000/api/v1/langchain/extract-codes',
                        body: {
                            text: clinicalText,
                            metadata: items[i].json,
                        },
                        json: true,
                    });
                }
                
                returnData.push({
                    json: responseData,
                });
            } catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: {
                            error: error.message,
                        },
                    });
                    continue;
                }
                throw new NodeOperationError(this.getNode(), error);
            }
        }

        return [returnData];
    }
}
```

#### Acceptance Criteria
- N8n is running in production mode with database persistence
- Authentication and security are properly configured
- Custom nodes for LangChain integration are installed
- Monitoring and logging are operational

---

### **Task 2: FastAPI Webhook Integration**
**Estimated Effort**: 2 days  
**Assignee**: Backend Engineer  

#### Subtasks
- [ ] Create webhook endpoints for N8n integration
- [ ] Implement authentication for N8n requests
- [ ] Design API contracts for workflow communication
- [ ] Add request validation and error handling
- [ ] Create webhook management interface

#### FastAPI Webhook Implementation
```python
# app/api/v1/endpoints/webhooks.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

class WebhookPayload(BaseModel):
    workflow_id: str
    execution_id: str
    node_name: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class N8nWebhookService:
    def __init__(self):
        self.webhook_handlers = {
            'clinical_document_processed': self.handle_clinical_document,
            'policy_query_completed': self.handle_policy_query,
            'pa_status_update': self.handle_pa_status_update,
        }
    
    async def handle_clinical_document(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Handle clinical document processing completion"""
        try:
            # Extract processed data
            extracted_codes = payload.data.get('extracted_codes')
            patient_id = payload.data.get('patient_id')
            
            # Store results in database
            await self.store_extraction_results(patient_id, extracted_codes)
            
            # Trigger next workflow step
            await self.trigger_policy_analysis(patient_id, extracted_codes)
            
            return {"status": "success", "next_step": "policy_analysis"}
            
        except Exception as e:
            logger.error(f"Error handling clinical document: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def handle_policy_query(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Handle policy query completion"""
        policy_result = payload.data.get('policy_result')
        request_id = payload.data.get('request_id')
        
        # Update PA request with policy analysis
        await self.update_pa_request(request_id, policy_result)
        
        return {"status": "success", "next_step": "packet_generation"}

@router.post("/n8n/webhook/{webhook_type}")
async def handle_n8n_webhook(
    webhook_type: str,
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    token: str = Depends(security)
):
    """Generic webhook handler for N8n workflows"""
    
    # Validate N8n token
    if not await validate_n8n_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid N8n token")
    
    webhook_service = N8nWebhookService()
    
    if webhook_type not in webhook_service.webhook_handlers:
        raise HTTPException(status_code=404, detail=f"Webhook type {webhook_type} not found")
    
    # Process webhook in background
    background_tasks.add_task(
        webhook_service.webhook_handlers[webhook_type],
        payload
    )
    
    return {"status": "accepted", "execution_id": payload.execution_id}

@router.post("/n8n/trigger/{workflow_name}")
async def trigger_n8n_workflow(
    workflow_name: str,
    data: Dict[str, Any],
    token: str = Depends(security)
):
    """Trigger N8n workflow from FastAPI"""
    
    if not await validate_n8n_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    n8n_client = N8nClient()
    execution_id = await n8n_client.trigger_workflow(workflow_name, data)
    
    return {"execution_id": execution_id, "status": "triggered"}
```

#### N8n Client Library
```python
# app/services/n8n_client.py
import httpx
import asyncio
from typing import Dict, Any, Optional
from app.core.config import get_settings

class N8nClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"http://{self.settings.N8N_HOST}:{self.settings.N8N_PORT}"
        self.auth = (self.settings.N8N_USER, self.settings.N8N_PASSWORD)
    
    async def trigger_workflow(self, workflow_name: str, data: Dict[str, Any]) -> str:
        """Trigger N8n workflow by name"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/webhook/{workflow_name}",
                json=data,
                auth=self.auth,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("executionId")
    
    async def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/rest/executions/{execution_id}",
                auth=self.auth
            )
            response.raise_for_status()
            return response.json()
    
    async def wait_for_completion(self, execution_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for workflow completion with timeout"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_workflow_status(execution_id)
            
            if status.get("finished"):
                return status
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Workflow {execution_id} did not complete within {timeout}s")
            
            await asyncio.sleep(5)  # Poll every 5 seconds
```

#### Acceptance Criteria
- FastAPI can receive webhooks from N8n workflows
- Authentication between N8n and FastAPI is working
- Background task processing is implemented
- Error handling and retries are configured

---

### **Task 3: Core Healthcare Workflows**
**Estimated Effort**: 4 days  
**Assignee**: Integration Specialist + AI Engineer  

#### Subtasks
- [ ] Implement FHIR document ingestion workflow
- [ ] Create clinical code extraction workflow
- [ ] Build policy analysis workflow
- [ ] Develop PA packet generation workflow
- [ ] Create status tracking and notification workflows

#### FHIR Document Ingestion Workflow
```json
{
  "name": "FHIR Document Ingestion",
  "description": "Process incoming FHIR documents and extract clinical data",
  "nodes": [
    {
      "id": "webhook-trigger",
      "name": "FHIR Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "fhir-ingestion",
        "httpMethod": "POST",
        "responseMode": "responseNode"
      },
      "position": [120, 200]
    },
    {
      "id": "validate-fhir",
      "name": "Validate FHIR Bundle",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// FHIR validation logic\nconst bundle = $input.first().json;\n\n// Validate bundle structure\nif (!bundle.resourceType || bundle.resourceType !== 'Bundle') {\n  throw new Error('Invalid FHIR Bundle format');\n}\n\n// Extract key resources\nconst patient = bundle.entry?.find(e => e.resource?.resourceType === 'Patient')?.resource;\nconst encounter = bundle.entry?.find(e => e.resource?.resourceType === 'Encounter')?.resource;\nconst documentReference = bundle.entry?.find(e => e.resource?.resourceType === 'DocumentReference')?.resource;\n\nif (!patient || !encounter) {\n  throw new Error('Missing required Patient or Encounter resource');\n}\n\nreturn {\n  bundle,\n  patient: {\n    id: patient.id,\n    name: patient.name?.[0]?.given?.[0] + ' ' + patient.name?.[0]?.family,\n    birthDate: patient.birthDate,\n    gender: patient.gender\n  },\n  encounter: {\n    id: encounter.id,\n    status: encounter.status,\n    class: encounter.class?.display,\n    period: encounter.period\n  },\n  documentReference: documentReference ? {\n    id: documentReference.id,\n    type: documentReference.type?.coding?.[0]?.display,\n    content: documentReference.content\n  } : null,\n  validatedAt: new Date().toISOString()\n};"
      },
      "position": [320, 200]
    },
    {
      "id": "store-bundle",
      "name": "Store FHIR Bundle",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "fhir_bundles",
        "columns": "patient_id, encounter_id, bundle_data, metadata, created_at",
        "values": "={{$node['Validate FHIR Bundle'].json.patient.id}}, ={{$node['Validate FHIR Bundle'].json.encounter.id}}, ={{JSON.stringify($node['Validate FHIR Bundle'].json.bundle)}}, ={{JSON.stringify($node['Validate FHIR Bundle'].json)}}, NOW()"
      },
      "position": [520, 200]
    },
    {
      "id": "extract-clinical-text",
      "name": "Extract Clinical Text",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "const data = $input.first().json;\nconst documentRef = data.documentReference;\n\nlet clinicalText = '';\n\nif (documentRef && documentRef.content) {\n  for (const content of documentRef.content) {\n    if (content.attachment) {\n      if (content.attachment.data) {\n        // Base64 encoded content\n        clinicalText += Buffer.from(content.attachment.data, 'base64').toString('utf-8');\n      } else if (content.attachment.url) {\n        // URL reference - would need to fetch\n        clinicalText += `[Document URL: ${content.attachment.url}]`;\n      }\n    }\n  }\n}\n\n// If no document reference, look for narrative in encounter\nif (!clinicalText && data.encounter) {\n  clinicalText = data.encounter.text?.div || 'No clinical text found';\n}\n\nreturn {\n  ...data,\n  clinicalText,\n  textLength: clinicalText.length,\n  extractedAt: new Date().toISOString()\n};"
      },
      "position": [720, 200]
    },
    {
      "id": "trigger-langchain",
      "name": "Trigger LangChain Processing",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/n8n/trigger/extract-clinical-codes",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "patient_id",
              "value": "={{$node['Extract Clinical Text'].json.patient.id}}"
            },
            {
              "name": "encounter_id", 
              "value": "={{$node['Extract Clinical Text'].json.encounter.id}}"
            },
            {
              "name": "clinical_text",
              "value": "={{$node['Extract Clinical Text'].json.clinicalText}}"
            },
            {
              "name": "bundle_id",
              "value": "={{$node['Store FHIR Bundle'].json.insertId}}"
            }
          ]
        }
      },
      "position": [920, 200]
    },
    {
      "id": "success-response",
      "name": "Success Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "status": 200,
        "body": {
          "status": "success",
          "message": "FHIR bundle processed successfully",
          "bundle_id": "={{$node['Store FHIR Bundle'].json.insertId}}",
          "patient_id": "={{$node['Extract Clinical Text'].json.patient.id}}",
          "processing_triggered": true
        }
      },
      "position": [1120, 200]
    }
  ],
  "connections": {
    "FHIR Webhook": {
      "main": [["Validate FHIR Bundle"]]
    },
    "Validate FHIR Bundle": {
      "main": [["Store FHIR Bundle"]]
    },
    "Store FHIR Bundle": {
      "main": [["Extract Clinical Text"]]
    },
    "Extract Clinical Text": {
      "main": [["Trigger LangChain Processing"]]
    },
    "Trigger LangChain Processing": {
      "main": [["Success Response"]]
    }
  }
}
```

#### Clinical Code Extraction Workflow
```json
{
  "name": "Clinical Code Extraction",
  "description": "Extract medical codes using LangChain NLP services",
  "nodes": [
    {
      "id": "webhook-trigger",
      "name": "Code Extraction Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "extract-clinical-codes",
        "httpMethod": "POST"
      }
    },
    {
      "id": "langchain-extraction",
      "name": "LangChain Code Extraction",
      "type": "langChainService",
      "parameters": {
        "operation": "extractCodes",
        "clinicalText": "={{$json.clinical_text}}"
      }
    },
    {
      "id": "validate-codes",
      "name": "Validate Extracted Codes",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "const codes = $input.first().json;\n\n// Filter codes by confidence threshold\nconst confidenceThreshold = 0.7;\n\nconst validatedCodes = {\n  icd10_codes: codes.icd10_codes?.filter(c => c.confidence >= confidenceThreshold) || [],\n  cpt_codes: codes.cpt_codes?.filter(c => c.confidence >= confidenceThreshold) || [],\n  hcpcs_codes: codes.hcpcs_codes?.filter(c => c.confidence >= confidenceThreshold) || [],\n  ndc_codes: codes.ndc_codes?.filter(c => c.confidence >= confidenceThreshold) || [],\n  snomed_codes: codes.snomed_codes?.filter(c => c.confidence >= confidenceThreshold) || []\n};\n\n// Calculate overall metrics\nconst totalCodes = Object.values(validatedCodes).flat().length;\nconst avgConfidence = Object.values(validatedCodes).flat()\n  .reduce((sum, code) => sum + code.confidence, 0) / totalCodes || 0;\n\nreturn {\n  ...validatedCodes,\n  extraction_metadata: {\n    total_codes_extracted: totalCodes,\n    average_confidence: avgConfidence,\n    confidence_threshold: confidenceThreshold,\n    extracted_at: new Date().toISOString()\n  }\n};"
      }
    },
    {
      "id": "store-results",
      "name": "Store Extraction Results",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "code_extractions",
        "columns": "patient_id, encounter_id, bundle_id, extracted_codes, extraction_metadata, created_at",
        "values": "={{$json.patient_id}}, ={{$json.encounter_id}}, ={{$json.bundle_id}}, ={{JSON.stringify($node['Validate Extracted Codes'].json)}}, ={{JSON.stringify($node['Validate Extracted Codes'].json.extraction_metadata)}}, NOW()"
      }
    },
    {
      "id": "trigger-policy-analysis",
      "name": "Trigger Policy Analysis",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/n8n/trigger/policy-analysis",
        "body": "={{\n  JSON.stringify({\n    patient_id: $json.patient_id,\n    encounter_id: $json.encounter_id,\n    extracted_codes: $node['Validate Extracted Codes'].json,\n    extraction_id: $node['Store Extraction Results'].json.insertId\n  })\n}}"
      }
    }
  ]
}
```

#### Acceptance Criteria
- FHIR documents are processed end-to-end successfully
- Clinical codes are extracted with acceptable accuracy
- Workflows handle errors gracefully and provide meaningful feedback
- Integration between N8n and LangChain services is seamless

---

### **Task 4: Error Handling & Resilience**
**Estimated Effort**: 2 days  
**Assignee**: Integration Specialist + Backend Engineer  

#### Subtasks
- [ ] Implement retry logic for failed API calls
- [ ] Create error handling workflows
- [ ] Set up dead letter queues for failed executions
- [ ] Implement circuit breaker patterns
- [ ] Create monitoring and alerting for failures

#### Error Handling Patterns
```json
{
  "name": "Error Handler Template",
  "description": "Reusable error handling pattern for N8n workflows",
  "nodes": [
    {
      "id": "error-detector",
      "name": "Error Detector",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.error}}",
              "operation": "exists"
            }
          ]
        }
      }
    },
    {
      "id": "retry-logic",
      "name": "Retry Logic",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "const execution = $execution;\nconst maxRetries = 3;\nconst currentRetry = execution.metadata?.retry_count || 0;\n\nif (currentRetry < maxRetries) {\n  // Exponential backoff\n  const delay = Math.pow(2, currentRetry) * 1000;\n  \n  return {\n    action: 'retry',\n    delay: delay,\n    retry_count: currentRetry + 1,\n    max_retries: maxRetries,\n    original_error: $json.error\n  };\n} else {\n  return {\n    action: 'dead_letter',\n    retry_count: currentRetry,\n    final_error: $json.error,\n    failed_at: new Date().toISOString()\n  };\n}"
      }
    },
    {
      "id": "log-error",
      "name": "Log Error",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "workflow_errors",
        "columns": "workflow_id, execution_id, node_name, error_message, retry_count, created_at",
        "values": "={{$workflow.id}}, ={{$execution.id}}, ={{$node.name}}, ={{$json.error.message}}, ={{$json.retry_count || 0}}, NOW()"
      }
    },
    {
      "id": "send-alert",
      "name": "Send Alert",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/alerts/workflow-error",
        "body": "={{\n  JSON.stringify({\n    workflow_id: $workflow.id,\n    execution_id: $execution.id,\n    error: $json.error,\n    severity: $json.retry_count >= 3 ? 'HIGH' : 'MEDIUM'\n  })\n}}"
      }
    }
  ]
}
```

#### Circuit Breaker Implementation
```python
# app/services/circuit_breaker.py
import time
import asyncio
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    timeout: int = 60
    expected_exception: type = Exception

class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.config.timeout
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN

# Usage in N8n integration
langchain_circuit_breaker = CircuitBreaker(
    CircuitBreakerConfig(failure_threshold=3, timeout=30)
)
```

#### Acceptance Criteria
- Failed API calls are automatically retried with exponential backoff
- Circuit breaker prevents cascading failures
- All errors are properly logged and monitored
- Dead letter queue handles permanently failed executions

---

## 🧪 Testing & Validation

### **Integration Testing**
```python
# tests/integration/test_n8n_integration.py
import pytest
import asyncio
from app.services.n8n_client import N8nClient
from app.services.langchain_service import LangChainService

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow from N8n trigger to LangChain processing"""
    
    # Sample FHIR bundle
    fhir_bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle-123",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-123",
                    "name": [{"given": ["John"], "family": "Doe"}]
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "encounter-123",
                    "status": "finished"
                }
            }
        ]
    }
    
    # Trigger N8n workflow
    n8n_client = N8nClient()
    execution_id = await n8n_client.trigger_workflow(
        "fhir-document-ingestion",
        fhir_bundle
    )
    
    # Wait for completion
    result = await n8n_client.wait_for_completion(execution_id, timeout=60)
    
    assert result["finished"] is True
    assert result["data"]["status"] == "success"

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in N8n workflows"""
    
    # Invalid FHIR bundle
    invalid_bundle = {"invalid": "data"}
    
    n8n_client = N8nClient()
    execution_id = await n8n_client.trigger_workflow(
        "fhir-document-ingestion",
        invalid_bundle
    )
    
    result = await n8n_client.wait_for_completion(execution_id, timeout=30)
    
    # Should fail gracefully
    assert result["finished"] is True
    assert "error" in result["data"]
```

## 📊 Sprint Deliverables

### **Technical Deliverables**
- [ ] Production-ready N8n deployment
- [ ] FastAPI webhook integration
- [ ] Core healthcare workflow templates
- [ ] Custom N8n nodes for LangChain integration
- [ ] Error handling and retry mechanisms
- [ ] Integration test suite

### **Documentation Deliverables**
- [ ] N8n workflow documentation
- [ ] API integration guide
- [ ] Error handling patterns
- [ ] Monitoring and troubleshooting guide

### **Performance Metrics**
| Metric | Target | Current |
|--------|--------|---------|
| Workflow Execution Time | <30s | TBD |
| API Response Time | <5s | TBD |
| Error Rate | <1% | TBD |
| Retry Success Rate | >80% | TBD |

## 🔄 Sprint Retrospective

### **Integration Challenges**
- Authentication between N8n and FastAPI
- Workflow execution monitoring
- Error propagation across systems
- Data consistency during failures

### **Next Sprint Preparation**
- [ ] Policy document ingestion requirements
- [ ] Vector store optimization needs
- [ ] Payer integration planning
- [ ] Performance optimization opportunities

---

**Sprint 2 Success Criteria**: N8n workflows can successfully trigger LangChain services, process healthcare data end-to-end, handle errors gracefully, and maintain audit trails for all operations. 