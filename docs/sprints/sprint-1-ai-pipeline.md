# Sprint 1: Core AI Pipeline (4 weeks)

## 🎯 Sprint Overview

**Duration**: 4 weeks  
**Team Focus**: LangChain NLP extraction, ChromaDB setup, basic RAG implementation  
**Sprint Goal**: Build the core AI processing pipeline that can extract clinical codes from healthcare documents and perform basic policy matching with ≥90% recall.

## 📋 Sprint Objectives

### Primary Goals
1. **Clinical NLP Pipeline**: Extract ICD-10, CPT, HCPCS, SNOMED, NDC codes from clinical documents
2. **Document Processing**: FHIR document intake and text preprocessing
3. **Embedding & Vector Storage**: ChromaDB setup with medical document embeddings
4. **Basic RAG Engine**: Policy document ingestion and similarity search
5. **LangChain Integration**: Structured chains for document analysis
6. **Evaluation Framework**: Metrics and testing for AI accuracy

### Success Criteria
- [ ] Clinical code extraction achieves ≥90% recall on test dataset
- [ ] Vector similarity search returns relevant policy documents
- [ ] End-to-end document processing pipeline is functional
- [ ] LangSmith observability is tracking all AI operations
- [ ] Performance meets <5s latency requirement for document processing

## 🏗️ AI Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Processing Pipeline                      │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   FHIR      │───▶│  Document   │───▶│    Text Chunking    │  │
│  │  Ingestion  │    │ Extraction  │    │   & Preprocessing   │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                  │              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Clinical  │◀───│  LangChain  │◀───│     Embedding       │  │
│  │Code Extract │    │    NLP      │    │    Generation       │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                  │              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Policy    │───▶│  Vector     │◀───│     ChromaDB        │  │
│  │   Matching  │    │  Search     │    │   Vector Store      │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Detailed Task Breakdown

### **Task 1: FHIR Document Processing**
**Estimated Effort**: 3 days  
**Assignee**: AI Engineer + Backend Engineer  

#### Subtasks
- [ ] Implement FHIR R4 document loaders for clinical notes
- [ ] Parse Encounter and DocumentReference resources
- [ ] Extract clinical narrative text from FHIR bundles
- [ ] Handle different document formats (CDA, plain text)
- [ ] Implement error handling for malformed FHIR data

#### Implementation
```python
# app/services/fhir_processor.py
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document
from fhir.resources.encounter import Encounter
from fhir.resources.documentreference import DocumentReference

class FHIRDocumentLoader(BaseLoader):
    """Custom LangChain loader for FHIR documents"""
    
    def __init__(self, fhir_bundle: dict):
        self.fhir_bundle = fhir_bundle
    
    def load(self) -> List[Document]:
        """Extract documents from FHIR bundle"""
        documents = []
        
        for entry in self.fhir_bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "DocumentReference":
                doc_ref = DocumentReference(**resource)
                text_content = self._extract_text_content(doc_ref)
                
                documents.append(Document(
                    page_content=text_content,
                    metadata={
                        "resource_type": resource_type,
                        "document_id": doc_ref.id,
                        "patient_id": self._extract_patient_id(doc_ref),
                        "created_date": str(doc_ref.date),
                        "document_type": doc_ref.type.coding[0].display if doc_ref.type else None
                    }
                ))
        
        return documents
    
    def _extract_text_content(self, doc_ref: DocumentReference) -> str:
        """Extract text content from document reference"""
        if doc_ref.content:
            for content in doc_ref.content:
                if content.attachment and content.attachment.data:
                    # Handle base64 encoded content
                    import base64
                    return base64.b64decode(content.attachment.data).decode('utf-8')
        return ""
```

#### Acceptance Criteria
- Can process FHIR R4 Encounter and DocumentReference resources
- Extracts clinical narrative text correctly
- Handles multiple document formats
- Preserves metadata for downstream processing

---

### **Task 2: Clinical Code Extraction with LangChain**
**Estimated Effort**: 5 days  
**Assignee**: AI Engineer  

#### Subtasks
- [ ] Design prompt templates for medical code extraction
- [ ] Implement structured output parsing for medical codes
- [ ] Create LangChain chains for different code types
- [ ] Add validation for extracted codes using external APIs
- [ ] Implement confidence scoring for extractions

#### Medical Code Extraction Chain
```python
# app/services/clinical_extraction_service.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import List, Optional

class ExtractedCodes(BaseModel):
    """Structured output for extracted medical codes"""
    icd10_codes: List[dict]  # [{"code": "Z51.1", "description": "Chemotherapy", "confidence": 0.95}]
    cpt_codes: List[dict]    # [{"code": "99213", "description": "Office visit", "confidence": 0.90}]
    hcpcs_codes: List[dict]  # [{"code": "J9999", "description": "Drug injection", "confidence": 0.85}]
    ndc_codes: List[dict]    # [{"code": "12345-678-90", "description": "Medication", "confidence": 0.80}]
    snomed_codes: List[dict] # [{"code": "182840001", "description": "Drug therapy", "confidence": 0.88}]

class ClinicalExtractionService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0  # Deterministic for code extraction
        )
        self.parser = PydanticOutputParser(pydantic_object=ExtractedCodes)
        self.chain = self._create_extraction_chain()
    
    def _create_extraction_chain(self) -> LLMChain:
        """Create LangChain for medical code extraction"""
        template = """
        You are a medical coding expert. Extract all relevant medical codes from the following clinical document.
        
        For each code found, provide:
        1. The exact code
        2. A brief description
        3. A confidence score (0.0 to 1.0)
        
        Focus on these code types:
        - ICD-10 (diagnosis codes): Format like Z51.1, C78.9, etc.
        - CPT (procedure codes): Format like 99213, 36415, etc.
        - HCPCS (supply/service codes): Format like J9999, A4633, etc.
        - NDC (drug codes): Format like 12345-678-90
        - SNOMED CT (clinical terms): Numeric codes
        
        Clinical Document:
        {clinical_text}
        
        {format_instructions}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["clinical_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        return LLMChain(llm=self.llm, prompt=prompt, output_parser=self.parser)
    
    async def extract_codes(self, clinical_text: str) -> ExtractedCodes:
        """Extract medical codes from clinical text"""
        try:
            result = await self.chain.arun(clinical_text=clinical_text)
            return result
        except Exception as e:
            logger.error(f"Code extraction failed: {e}")
            return ExtractedCodes(
                icd10_codes=[], cpt_codes=[], hcpcs_codes=[],
                ndc_codes=[], snomed_codes=[]
            )
    
    async def validate_codes(self, extracted_codes: ExtractedCodes) -> ExtractedCodes:
        """Validate extracted codes against external APIs"""
        # Implement validation against CMS APIs, SNOMED APIs, etc.
        # This is a placeholder for external validation
        return extracted_codes
```

#### Advanced Extraction Techniques
```python
# Enhanced extraction with medical context
class MedicalContextExtractor:
    def __init__(self):
        self.context_chain = self._create_context_chain()
    
    def _create_context_chain(self) -> LLMChain:
        """Extract medical context for better code accuracy"""
        template = """
        Analyze this clinical document and provide context for medical coding:
        
        1. Patient Demographics: Age, gender, relevant history
        2. Chief Complaint: Primary reason for visit
        3. Diagnoses: Primary and secondary diagnoses
        4. Procedures: Any procedures performed or planned
        5. Medications: Current medications and new prescriptions
        6. Medical Necessity: Clinical reasoning for treatments
        
        Clinical Document:
        {clinical_text}
        
        Provide structured analysis:
        """
        return LLMChain(
            llm=self.llm,
            prompt=PromptTemplate.from_template(template)
        )
```

#### Acceptance Criteria
- Extracts medical codes with ≥90% recall on test dataset
- Provides confidence scores for each extracted code
- Handles various clinical document formats
- Validates codes against external sources where possible

---

### **Task 3: ChromaDB Vector Store Setup**
**Estimated Effort**: 2 days  
**Assignee**: AI Engineer  

#### Subtasks
- [ ] Configure ChromaDB for persistent storage
- [ ] Create collections for different document types
- [ ] Implement embedding generation for clinical documents
- [ ] Set up metadata filtering capabilities
- [ ] Create backup and recovery procedures

#### ChromaDB Configuration
```python
# app/services/vector_store_service.py
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any

class VectorStoreService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            dimensions=1536
        )
        self.client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collections = self._initialize_collections()
    
    def _initialize_collections(self) -> Dict[str, Chroma]:
        """Initialize different collections for various document types"""
        collections = {}
        
        # Clinical documents collection
        collections['clinical_docs'] = Chroma(
            client=self.client,
            collection_name="clinical_documents",
            embedding_function=self.embeddings
        )
        
        # Policy documents collection
        collections['policies'] = Chroma(
            client=self.client,
            collection_name="payer_policies",
            embedding_function=self.embeddings
        )
        
        # Medical knowledge base
        collections['medical_kb'] = Chroma(
            client=self.client,
            collection_name="medical_knowledge",
            embedding_function=self.embeddings
        )
        
        return collections
    
    async def add_clinical_document(self, document: Document) -> str:
        """Add clinical document to vector store"""
        doc_id = await self.collections['clinical_docs'].aadd_documents([document])
        return doc_id[0]
    
    async def add_policy_document(self, document: Document) -> str:
        """Add policy document to vector store"""
        doc_id = await self.collections['policies'].aadd_documents([document])
        return doc_id[0]
    
    async def similarity_search(
        self,
        query: str,
        collection_name: str,
        k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Document]:
        """Perform similarity search in specified collection"""
        collection = self.collections.get(collection_name)
        if not collection:
            raise ValueError(f"Collection {collection_name} not found")
        
        return await collection.asimilarity_search(
            query=query,
            k=k,
            filter=filter_dict
        )
```

#### Performance Optimization
```python
# Batch processing for large document sets
class BatchProcessor:
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.batch_size = 100
    
    async def process_document_batch(self, documents: List[Document], collection_name: str):
        """Process documents in batches for better performance"""
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            collection = self.vector_store.collections[collection_name]
            await collection.aadd_documents(batch)
            logger.info(f"Processed batch {i//self.batch_size + 1}/{len(documents)//self.batch_size + 1}")
```

#### Acceptance Criteria
- ChromaDB is configured with persistent storage
- Multiple collections are properly initialized
- Embedding generation is working efficiently
- Similarity search returns relevant documents

---

### **Task 4: Policy Document RAG Engine**
**Estimated Effort**: 4 days  
**Assignee**: AI Engineer  

#### Subtasks
- [ ] Implement policy document ingestion pipeline
- [ ] Create chunking strategy for policy documents
- [ ] Build RAG chain for policy matching
- [ ] Implement relevance scoring and filtering
- [ ] Create policy update and versioning system

#### Policy RAG Implementation
```python
# app/services/policy_rag_service.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from typing import List, Dict

class PolicyRAGService:
    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        self.qa_chain = self._create_qa_chain()
    
    def _create_qa_chain(self) -> RetrievalQA:
        """Create RAG chain for policy question answering"""
        template = """
        You are a prior authorization policy expert. Use the following policy context to answer questions about medical necessity and coverage requirements.
        
        Context from Policy Documents:
        {context}
        
        Question: {question}
        
        Instructions:
        1. Provide a clear answer based only on the policy context
        2. Cite specific policy sections when possible
        3. If the context doesn't contain enough information, say so explicitly
        4. Focus on medical necessity criteria and coverage requirements
        
        Answer:
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        retriever = self.vector_store.collections['policies'].as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance
            search_kwargs={
                "k": 10,
                "fetch_k": 20,
                "lambda_mult": 0.5
            }
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
    
    async def ingest_policy_document(self, policy_text: str, metadata: Dict[str, Any]) -> List[str]:
        """Ingest and chunk policy document"""
        chunks = self.text_splitter.split_text(policy_text)
        
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        doc_ids = []
        for doc in documents:
            doc_id = await self.vector_store.add_policy_document(doc)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    async def check_medical_necessity(
        self,
        extracted_codes: ExtractedCodes,
        clinical_context: str,
        payer_id: str = None
    ) -> Dict[str, Any]:
        """Check medical necessity based on extracted codes and clinical context"""
        
        # Build query from extracted codes and context
        query = self._build_policy_query(extracted_codes, clinical_context)
        
        # Add payer filter if specified
        filter_dict = {"payer_id": payer_id} if payer_id else None
        
        # Query the RAG system
        result = await self.qa_chain.arun(
            query=query,
            filter=filter_dict
        )
        
        return {
            "medical_necessity_decision": self._parse_decision(result["result"]),
            "supporting_policies": result["source_documents"],
            "reasoning": result["result"],
            "confidence_score": self._calculate_confidence(result)
        }
    
    def _build_policy_query(self, codes: ExtractedCodes, context: str) -> str:
        """Build policy query from extracted codes and clinical context"""
        query_parts = []
        
        # Add diagnosis codes
        if codes.icd10_codes:
            diagnoses = [code["code"] for code in codes.icd10_codes]
            query_parts.append(f"Diagnoses: {', '.join(diagnoses)}")
        
        # Add procedure codes
        if codes.cpt_codes:
            procedures = [code["code"] for code in codes.cpt_codes]
            query_parts.append(f"Procedures: {', '.join(procedures)}")
        
        # Add clinical context
        query_parts.append(f"Clinical Context: {context}")
        
        return "\n".join(query_parts)
```

#### Policy Evaluation Chain
```python
class PolicyEvaluationChain:
    """Advanced policy evaluation with multi-step reasoning"""
    
    def __init__(self, policy_rag: PolicyRAGService):
        self.policy_rag = policy_rag
        self.evaluation_chain = self._create_evaluation_chain()
    
    def _create_evaluation_chain(self) -> LLMChain:
        """Create chain for step-by-step policy evaluation"""
        template = """
        Evaluate the medical necessity for prior authorization based on the following:
        
        Patient Information:
        - Diagnosis Codes: {icd10_codes}
        - Procedure Codes: {cpt_codes}
        - Clinical Context: {clinical_context}
        
        Policy Requirements:
        {policy_context}
        
        Step-by-step evaluation:
        1. Coverage Analysis: Is this service/procedure covered?
        2. Medical Necessity: Does the clinical context support medical necessity?
        3. Documentation Requirements: Are all required documents present?
        4. Prior Authorization Required: Is PA required for this case?
        
        Provide your analysis in this format:
        DECISION: [APPROVED/DENIED/ADDITIONAL_INFO_NEEDED]
        REASONING: [Detailed explanation]
        REQUIREMENTS: [Any missing requirements]
        CONFIDENCE: [0.0-1.0]
        """
        
        return LLMChain(
            llm=self.policy_rag.llm,
            prompt=PromptTemplate.from_template(template)
        )
```

#### Acceptance Criteria
- Policy documents are properly chunked and indexed
- RAG system returns relevant policy information
- Medical necessity evaluation provides clear decisions
- Source documents are properly cited

---

### **Task 5: LangSmith Observability Integration**
**Estimated Effort**: 2 days  
**Assignee**: AI Engineer + DevOps Engineer  

#### Subtasks
- [ ] Configure LangSmith tracing for all LangChain operations
- [ ] Set up evaluation datasets for AI accuracy testing
- [ ] Implement custom evaluation metrics
- [ ] Create dashboards for AI performance monitoring
- [ ] Set up alerting for AI accuracy degradation

#### LangSmith Configuration
```python
# app/core/observability.py
import os
from langsmith import Client
from langchain.callbacks import LangChainTracer
from langchain.schema.runnable import RunnableConfig

class ObservabilityService:
    def __init__(self):
        self.client = Client(
            api_url=os.getenv("LANGCHAIN_ENDPOINT"),
            api_key=os.getenv("LANGCHAIN_API_KEY")
        )
        self.tracer = LangChainTracer(
            project_name=os.getenv("LANGCHAIN_PROJECT", "greenlightpa")
        )
    
    def get_config(self, operation_name: str) -> RunnableConfig:
        """Get configuration for tracing specific operations"""
        return RunnableConfig(
            callbacks=[self.tracer],
            tags=[operation_name, "production"],
            metadata={
                "operation": operation_name,
                "version": "1.0.0"
            }
        )
    
    async def evaluate_extraction_accuracy(self, test_dataset: List[Dict]) -> Dict[str, float]:
        """Evaluate code extraction accuracy using LangSmith"""
        results = []
        
        for test_case in test_dataset:
            # Run extraction
            extracted = await self.extraction_service.extract_codes(
                test_case["clinical_text"]
            )
            
            # Compare with ground truth
            accuracy = self._calculate_accuracy(
                extracted, 
                test_case["expected_codes"]
            )
            
            results.append(accuracy)
        
        return {
            "mean_accuracy": sum(results) / len(results),
            "median_accuracy": sorted(results)[len(results) // 2],
            "min_accuracy": min(results),
            "max_accuracy": max(results)
        }
```

#### Acceptance Criteria
- All LangChain operations are traced in LangSmith
- Evaluation datasets are configured
- Performance dashboards are operational
- Accuracy monitoring is automated

---

## 🧪 Testing & Evaluation

### **Test Dataset Creation**
```python
# Create synthetic test dataset for evaluation
test_cases = [
    {
        "clinical_text": "Patient presents with Type 2 diabetes mellitus. Prescribed metformin 500mg twice daily. HbA1c 8.2%.",
        "expected_codes": {
            "icd10_codes": [{"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"}],
            "ndc_codes": [{"code": "0093-1074-01", "description": "Metformin 500mg"}]
        }
    },
    # Add more test cases...
]
```

### **Evaluation Metrics**
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Code Extraction Recall | ≥90% | Compare extracted vs. ground truth codes |
| Code Extraction Precision | ≥85% | Accuracy of extracted codes |
| Policy Retrieval Relevance | ≥80% | Manual evaluation of retrieved policies |
| End-to-End Latency | <5s | Time from document input to code output |
| System Availability | ≥99% | Uptime monitoring |

## 📊 Sprint Deliverables

### **Code Deliverables**
- [ ] FHIR document processing service
- [ ] Clinical code extraction service with LangChain
- [ ] ChromaDB vector store configuration
- [ ] Policy RAG engine implementation
- [ ] LangSmith observability integration
- [ ] Comprehensive test suite

### **Documentation Deliverables**
- [ ] API documentation for all services
- [ ] LangChain prompt templates documentation
- [ ] Vector store management guide
- [ ] Performance optimization guide
- [ ] Troubleshooting guide

### **Evaluation Results**
- [ ] Code extraction accuracy report
- [ ] Policy retrieval performance analysis
- [ ] System latency benchmarks
- [ ] LangSmith evaluation dashboard

## 🔄 Sprint Retrospective

### **Technical Debt to Address**
- [ ] Optimize embedding generation for large documents
- [ ] Implement caching for frequently accessed policies
- [ ] Add fallback mechanisms for AI service failures
- [ ] Improve error handling and logging

### **Next Sprint Preparation**
- [ ] Identify N8n integration points
- [ ] Plan workflow orchestration patterns
- [ ] Design API interfaces for N8n communication
- [ ] Prepare policy document sources for next sprint

---

**Sprint 1 Success Metrics**: By sprint end, the system should process a clinical document, extract medical codes with ≥90% accuracy, and return relevant policy information in under 5 seconds. 