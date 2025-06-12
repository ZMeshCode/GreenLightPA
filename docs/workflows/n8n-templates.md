# N8n Workflow Templates

## 🎯 Overview

This document contains reusable N8n workflow templates for the GreenLightPA project. These templates provide the foundation for automating prior authorization workflows, integrating with LangChain services, and managing healthcare data processing.

## 📚 Template Categories

### 🏥 Healthcare Data Processing
- [**FHIR Document Ingestion**](#fhir-document-ingestion)
- [**Clinical Data Validation**](#clinical-data-validation)
- [**Patient Data Sync**](#patient-data-sync)

### 🤖 AI Service Integration
- [**LangChain NLP Processing**](#langchain-nlp-processing)
- [**Code Extraction Workflow**](#code-extraction-workflow)
- [**Policy RAG Query**](#policy-rag-query)

### 📋 Prior Authorization Workflows
- [**PA Request Processing**](#pa-request-processing)
- [**Multi-Payer Submission**](#multi-payer-submission)
- [**Status Tracking & Updates**](#status-tracking-updates)

### 🔄 Administrative Workflows
- [**Policy Document Scraping**](#policy-document-scraping)
- [**Audit Log Management**](#audit-log-management)
- [**Error Handling & Retry**](#error-handling-retry)

---

## 🏥 Healthcare Data Processing Templates

### **FHIR Document Ingestion**

**Purpose**: Automatically ingest FHIR documents from EHR systems and prepare them for AI processing.

**Trigger**: Webhook from EHR system or scheduled polling

**Workflow Steps**:
```json
{
  "name": "FHIR Document Ingestion",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "fhir-ingestion",
        "httpMethod": "POST",
        "responseMode": "responseNode"
      }
    },
    {
      "name": "Validate FHIR Bundle",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Validate FHIR bundle structure\nconst bundle = $input.first().json;\n\nif (!bundle.resourceType || bundle.resourceType !== 'Bundle') {\n  throw new Error('Invalid FHIR Bundle');\n}\n\n// Extract patient ID and encounter ID\nconst patientId = bundle.entry.find(e => e.resource.resourceType === 'Patient')?.resource.id;\nconst encounterId = bundle.entry.find(e => e.resource.resourceType === 'Encounter')?.resource.id;\n\nreturn {\n  bundle,\n  patientId,\n  encounterId,\n  timestamp: new Date().toISOString()\n};"
      }
    },
    {
      "name": "Store FHIR Bundle",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "fhir_bundles",
        "columns": "patient_id, encounter_id, bundle_data, created_at",
        "values": "={{$node['Validate FHIR Bundle'].json.patientId}}, ={{$node['Validate FHIR Bundle'].json.encounterId}}, ={{JSON.stringify($node['Validate FHIR Bundle'].json.bundle)}}, ={{$node['Validate FHIR Bundle'].json.timestamp}}"
      }
    },
    {
      "name": "Trigger LangChain Processing",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/process-fhir",
        "bodyParameters": {
          "parameters": [
            {
              "name": "bundle_id",
              "value": "={{$node['Store FHIR Bundle'].json.insertId}}"
            },
            {
              "name": "patient_id",
              "value": "={{$node['Validate FHIR Bundle'].json.patientId}}"
            }
          ]
        }
      }
    },
    {
      "name": "Success Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "status": 200,
        "body": {
          "status": "success",
          "bundle_id": "={{$node['Store FHIR Bundle'].json.insertId}}",
          "message": "FHIR bundle processed successfully"
        }
      }
    }
  ],
  "connections": {
    "Webhook Trigger": {
      "main": [["Validate FHIR Bundle"]]
    },
    "Validate FHIR Bundle": {
      "main": [["Store FHIR Bundle"]]
    },
    "Store FHIR Bundle": {
      "main": [["Trigger LangChain Processing"]]
    },
    "Trigger LangChain Processing": {
      "main": [["Success Response"]]
    }
  }
}
```

**Configuration Variables**:
- `FHIR_VALIDATION_ENDPOINT`: External FHIR validation service
- `LANGCHAIN_SERVICE_URL`: LangChain processing service URL
- `DATABASE_CONNECTION`: PostgreSQL connection string

---

### **Clinical Data Validation**

**Purpose**: Validate clinical data quality and completeness before processing.

**Workflow Steps**:
```json
{
  "name": "Clinical Data Validation",
  "nodes": [
    {
      "name": "Data Quality Check",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const clinicalData = $input.first().json;\nconst validationResults = {\n  hasPatientId: !!clinicalData.patientId,\n  hasEncounterText: !!clinicalData.encounterText && clinicalData.encounterText.length > 10,\n  hasValidDate: !!clinicalData.encounterDate && !isNaN(new Date(clinicalData.encounterDate)),\n  hasProviderInfo: !!clinicalData.providerId\n};\n\nconst isValid = Object.values(validationResults).every(v => v);\n\nreturn {\n  ...clinicalData,\n  validation: validationResults,\n  isValid,\n  validatedAt: new Date().toISOString()\n};"
      }
    },
    {
      "name": "Route Valid Data",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$node['Data Quality Check'].json.isValid}}",
              "operation": "equal",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Process Valid Data",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/process-clinical-data",
        "body": "={{JSON.stringify($node['Data Quality Check'].json)}}"
      }
    },
    {
      "name": "Handle Invalid Data",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const data = $input.first().json;\nconst errors = [];\n\nif (!data.validation.hasPatientId) errors.push('Missing patient ID');\nif (!data.validation.hasEncounterText) errors.push('Missing or insufficient encounter text');\nif (!data.validation.hasValidDate) errors.push('Invalid encounter date');\nif (!data.validation.hasProviderInfo) errors.push('Missing provider information');\n\nreturn {\n  status: 'validation_failed',\n  errors,\n  originalData: data\n};"
      }
    }
  ]
}
```

---

## 🤖 AI Service Integration Templates

### **LangChain NLP Processing**

**Purpose**: Orchestrate LangChain AI services for clinical document processing.

**Workflow Steps**:
```json
{
  "name": "LangChain NLP Processing",
  "nodes": [
    {
      "name": "Prepare Document",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const input = $input.first().json;\n\n// Prepare document for LangChain processing\nconst document = {\n  text: input.clinicalText,\n  metadata: {\n    patientId: input.patientId,\n    encounterId: input.encounterId,\n    documentType: input.documentType || 'clinical_note',\n    processedAt: new Date().toISOString()\n  }\n};\n\nreturn document;"
      }
    },
    {
      "name": "Extract Clinical Codes",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/langchain/extract-codes",
        "body": "={{JSON.stringify($node['Prepare Document'].json)}}",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer {{$env.LANGCHAIN_API_TOKEN}}"
        }
      }
    },
    {
      "name": "Validate Extracted Codes",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const codes = $input.first().json;\n\n// Validate extracted codes\nconst validatedCodes = {\n  icd10_codes: codes.icd10_codes.filter(c => c.confidence > 0.7),\n  cpt_codes: codes.cpt_codes.filter(c => c.confidence > 0.7),\n  hcpcs_codes: codes.hcpcs_codes.filter(c => c.confidence > 0.7),\n  ndc_codes: codes.ndc_codes.filter(c => c.confidence > 0.7),\n  snomed_codes: codes.snomed_codes.filter(c => c.confidence > 0.7)\n};\n\n// Calculate overall confidence\nconst allCodes = [...validatedCodes.icd10_codes, ...validatedCodes.cpt_codes, ...validatedCodes.hcpcs_codes];\nconst avgConfidence = allCodes.length > 0 ? allCodes.reduce((sum, c) => sum + c.confidence, 0) / allCodes.length : 0;\n\nreturn {\n  ...validatedCodes,\n  overall_confidence: avgConfidence,\n  total_codes_extracted: allCodes.length\n};"
      }
    },
    {
      "name": "Store Extraction Results",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "code_extractions",
        "columns": "patient_id, encounter_id, extracted_codes, confidence_score, created_at",
        "values": "={{$node['Prepare Document'].json.metadata.patientId}}, ={{$node['Prepare Document'].json.metadata.encounterId}}, ={{JSON.stringify($node['Validate Extracted Codes'].json)}}, ={{$node['Validate Extracted Codes'].json.overall_confidence}}, NOW()"
      }
    }
  ]
}
```

---

### **Policy RAG Query**

**Purpose**: Query policy documents using RAG for medical necessity determination.

**Workflow Steps**:
```json
{
  "name": "Policy RAG Query",
  "nodes": [
    {
      "name": "Build Policy Query",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const input = $input.first().json;\n\n// Build comprehensive query for policy RAG\nconst query = {\n  patient_context: {\n    age: input.patient.age,\n    gender: input.patient.gender,\n    medical_history: input.patient.medicalHistory\n  },\n  clinical_context: {\n    primary_diagnosis: input.codes.icd10_codes[0]?.code,\n    procedures: input.codes.cpt_codes.map(c => c.code),\n    medications: input.codes.ndc_codes.map(c => c.code)\n  },\n  payer_context: {\n    payer_id: input.payer.id,\n    plan_type: input.payer.planType,\n    prior_auth_required: true\n  },\n  query_text: `Medical necessity evaluation for ${input.codes.icd10_codes.map(c => c.description).join(', ')} with procedures ${input.codes.cpt_codes.map(c => c.description).join(', ')}`\n};\n\nreturn query;"
      }
    },
    {
      "name": "Query Policy RAG",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/langchain/policy-rag",
        "body": "={{JSON.stringify($node['Build Policy Query'].json)}}",
        "timeout": 30000
      }
    },
    {
      "name": "Process RAG Response",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const ragResponse = $input.first().json;\n\n// Process and structure the RAG response\nconst processedResponse = {\n  medical_necessity_decision: ragResponse.decision || 'REVIEW_REQUIRED',\n  confidence_score: ragResponse.confidence || 0.5,\n  supporting_policies: ragResponse.source_documents || [],\n  reasoning: ragResponse.reasoning || 'Unable to determine medical necessity',\n  requirements_met: ragResponse.requirements_met || [],\n  missing_requirements: ragResponse.missing_requirements || [],\n  next_steps: ragResponse.next_steps || ['Manual review required'],\n  processed_at: new Date().toISOString()\n};\n\nreturn processedResponse;"
      }
    }
  ]
}
```

---

## 📋 Prior Authorization Workflows

### **PA Request Processing**

**Purpose**: Complete end-to-end prior authorization request processing.

**Workflow Steps**:
```json
{
  "name": "PA Request Processing",
  "nodes": [
    {
      "name": "Initialize PA Request",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "prior_auth_requests",
        "columns": "patient_id, provider_id, payer_id, status, request_data, created_at",
        "values": "={{$json.patientId}}, ={{$json.providerId}}, ={{$json.payerId}}, 'PROCESSING', ={{JSON.stringify($json)}}, NOW()"
      }
    },
    {
      "name": "Process Clinical Document",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "langchain-nlp-processing",
        "data": {
          "clinicalText": "={{$json.clinicalDocument}}",
          "patientId": "={{$json.patientId}}",
          "encounterId": "={{$json.encounterId}}"
        }
      }
    },
    {
      "name": "Query Policy Requirements",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "policy-rag-query",
        "data": {
          "codes": "={{$node['Process Clinical Document'].json.extractedCodes}}",
          "payer": "={{$json.payer}}",
          "patient": "={{$json.patient}}"
        }
      }
    },
    {
      "name": "Generate PA Packet",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/generate-pa-packet",
        "body": "={{\n  JSON.stringify({\n    request_id: $node['Initialize PA Request'].json.insertId,\n    extracted_codes: $node['Process Clinical Document'].json,\n    policy_analysis: $node['Query Policy Requirements'].json,\n    clinical_document: $json.clinicalDocument\n  })\n}}"
      }
    },
    {
      "name": "Route for Submission",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "values": {
          "string": [
            {
              "value": "={{$json.payer.submissionMethod}}"
            }
          ]
        },
        "options": [
          {
            "value": "API",
            "outputIndex": 0
          },
          {
            "value": "FAX",
            "outputIndex": 1
          },
          {
            "value": "PORTAL",
            "outputIndex": 2
          }
        ]
      }
    }
  ]
}
```

---

### **Multi-Payer Submission**

**Purpose**: Submit prior authorization to different payers using appropriate channels.

**API Submission Branch**:
```json
{
  "name": "API Submission",
  "nodes": [
    {
      "name": "Format X12 278",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const paPacket = $input.first().json;\n\n// Format data for X12 278 transmission\nconst x12_278 = {\n  transaction_set: 'HC',\n  submitter: paPacket.provider,\n  receiver: paPacket.payer,\n  patient: paPacket.patient,\n  services: paPacket.services,\n  supporting_docs: paPacket.supportingDocuments\n};\n\nreturn { x12_278, original_packet: paPacket };"
      }
    },
    {
      "name": "Submit to Change Healthcare",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://api.changehealthcare.com/medical-network/prior-authorization/v1/278",
        "headers": {
          "Authorization": "Bearer {{$env.CHANGE_HEALTHCARE_TOKEN}}",
          "Content-Type": "application/json"
        },
        "body": "={{JSON.stringify($node['Format X12 278'].json.x12_278)}}"
      }
    },
    {
      "name": "Update PA Status",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "update",
        "table": "prior_auth_requests",
        "where": "id = {{$node['Format X12 278'].json.original_packet.request_id}}",
        "columns": "status, submission_reference, submitted_at",
        "values": "'SUBMITTED', '{{$node['Submit to Change Healthcare'].json.reference_id}}', NOW()"
      }
    }
  ]
}
```

---

## 🔄 Administrative Workflows

### **Policy Document Scraping**

**Purpose**: Automatically scrape and update payer policy documents.

**Workflow Steps**:
```json
{
  "name": "Policy Document Scraping",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 2 * * *"
            }
          ]
        }
      }
    },
    {
      "name": "Get Payer List",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "select",
        "table": "payers",
        "where": "active = true AND policy_scraping_enabled = true"
      }
    },
    {
      "name": "Scrape Payer Policies",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const payers = $input.all();\nconst scrapingTasks = [];\n\nfor (const payer of payers) {\n  if (payer.json.policy_url) {\n    scrapingTasks.push({\n      payer_id: payer.json.id,\n      payer_name: payer.json.name,\n      policy_url: payer.json.policy_url,\n      last_updated: payer.json.policy_last_updated\n    });\n  }\n}\n\nreturn scrapingTasks;"
      }
    },
    {
      "name": "Process Each Payer",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1
      }
    },
    {
      "name": "Download Policy Document",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "={{$json.policy_url}}",
        "timeout": 60000
      }
    },
    {
      "name": "Process with LangChain",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://fastapi:8000/api/v1/langchain/ingest-policy",
        "body": "={{\n  JSON.stringify({\n    payer_id: $json.payer_id,\n    payer_name: $json.payer_name,\n    policy_content: $node['Download Policy Document'].json,\n    source_url: $json.policy_url\n  })\n}}"
      }
    }
  ]
}
```

---

## 🛠️ Workflow Best Practices

### **Error Handling Pattern**
```json
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "const error = $input.first().json;\n\n// Standard error handling\nconst errorLog = {\n  workflow_id: $workflow.id,\n  node_name: $node.name,\n  error_message: error.message || 'Unknown error',\n  error_stack: error.stack,\n  input_data: $input.first().json,\n  timestamp: new Date().toISOString(),\n  severity: error.code ? 'WARNING' : 'ERROR'\n};\n\n// Log to monitoring system\nconsole.error('Workflow Error:', errorLog);\n\nreturn errorLog;"
  }
}
```

### **Retry Logic Pattern**
```json
{
  "name": "Retry Handler",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "const attempt = $executionData.attempt || 1;\nconst maxAttempts = 3;\nconst retryDelay = Math.pow(2, attempt) * 1000; // Exponential backoff\n\nif (attempt <= maxAttempts) {\n  // Wait before retry\n  await new Promise(resolve => setTimeout(resolve, retryDelay));\n  \n  return {\n    ....$input.first().json,\n    retry_attempt: attempt + 1,\n    retry_delay: retryDelay\n  };\n} else {\n  throw new Error(`Max retry attempts (${maxAttempts}) exceeded`);\n}"
  }
}
```

### **Configuration Management**
```json
{
  "name": "Load Configuration",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "// Centralized configuration loading\nconst config = {\n  langchain: {\n    base_url: $env.LANGCHAIN_SERVICE_URL || 'http://fastapi:8000',\n    timeout: parseInt($env.LANGCHAIN_TIMEOUT) || 30000,\n    retry_attempts: parseInt($env.LANGCHAIN_RETRIES) || 3\n  },\n  database: {\n    connection_string: $env.DATABASE_URL,\n    pool_size: parseInt($env.DB_POOL_SIZE) || 10\n  },\n  monitoring: {\n    enabled: $env.MONITORING_ENABLED === 'true',\n    log_level: $env.LOG_LEVEL || 'INFO'\n  }\n};\n\nreturn config;"
  }
}
```

## 📊 Monitoring & Analytics

### **Workflow Performance Tracking**
- Execution time monitoring
- Success/failure rate tracking
- Resource utilization metrics
- Error pattern analysis

### **Healthcare-Specific Metrics**
- PA processing time
- Approval rate by payer
- Code extraction accuracy
- Policy match relevance

## 🔐 Security Considerations

### **Data Handling**
- PHI encryption in transit and at rest
- Audit logging for all healthcare data access
- HIPAA-compliant data retention policies

### **API Security**
- JWT token validation
- Rate limiting on external API calls
- Secure credential storage in N8n

---

*These templates provide a foundation for building robust, HIPAA-compliant workflows that integrate seamlessly with the LangChain AI services while maintaining the flexibility and visual management capabilities of N8n.* 