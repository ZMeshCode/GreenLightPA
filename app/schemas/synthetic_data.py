"""
Pydantic Schemas for Synthetic Data Pipeline
Request and response models for API endpoints
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class GenerateSyntheticDataRequest(BaseModel):
    """Request model for generating synthetic data"""
    
    num_patients: int = Field(default=500, ge=1, le=10000, description="Number of patients to generate")
    specialties: List[str] = Field(default=["oncology", "rheumatology"], description="Medical specialties to focus on")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "num_patients": 500,
                "specialties": ["oncology", "rheumatology"]
            }
        }
    )


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status"""
    
    patients_generated: int = Field(description="Number of patients generated")
    clinical_notes: int = Field(description="Number of clinical notes processed")
    status: str = Field(description="Pipeline status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patients_generated": 500,
                "clinical_notes": 1250,
                "status": "completed"
            }
        }
    )


class ClinicalNoteResponse(BaseModel):
    """Response model for clinical note"""
    
    note_id: str = Field(description="Unique note identifier")
    patient_id: str = Field(description="Patient identifier")
    specialty: Optional[str] = Field(description="Medical specialty")
    prior_auth_required: bool = Field(description="Whether prior authorization is required")
    prior_auth_status: str = Field(description="Prior authorization status")
    text_preview: Optional[str] = Field(description="Preview of note text")
    created_at: datetime = Field(description="Creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "note_id": "note_12345",
                "patient_id": "patient_67890",
                "specialty": "oncology",
                "prior_auth_required": True,
                "prior_auth_status": "approved",
                "text_preview": "Patient presents with...",
                "created_at": "2024-01-01T10:30:00Z"
            }
        }
    )


class SyntheticPatientResponse(BaseModel):
    """Response model for synthetic patient"""
    
    patient_id: str = Field(description="Unique patient identifier")
    resource_type: Optional[str] = Field(description="FHIR resource type")
    created_at: datetime = Field(description="Creation timestamp")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "patient_id": "patient_67890",
                "resource_type": "Bundle",
                "created_at": "2024-01-01T10:30:00Z"
            }
        }
    )


class PolicySearchRequest(BaseModel):
    """Request model for policy search"""
    
    query_text: str = Field(description="Text to search for in policies")
    specialty: Optional[str] = Field(default=None, description="Filter by medical specialty")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query_text": "chemotherapy prior authorization requirements",
                "specialty": "oncology",
                "limit": 5
            }
        }
    )


class PolicyChunkResponse(BaseModel):
    """Response model for policy chunk"""
    
    id: int = Field(description="Chunk ID")
    payer_id: str = Field(description="Payer identifier")
    policy_id: str = Field(description="Policy identifier")
    specialty: Optional[str] = Field(description="Medical specialty")
    chunk_text: str = Field(description="Policy text chunk")
    similarity: Optional[float] = Field(description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "payer_id": "BCBS",
                "policy_id": "ONCO-001",
                "specialty": "oncology",
                "chunk_text": "Prior authorization required for chemotherapy...",
                "similarity": 0.85,
                "metadata": {"category": "chemotherapy"}
            }
        }
    )


class PolicySearchResponse(BaseModel):
    """Response model for policy search results"""
    
    query: str = Field(description="Original search query")
    similar_policies: List[PolicyChunkResponse] = Field(description="Similar policy chunks")
    specialty_filter: Optional[str] = Field(description="Applied specialty filter")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "chemotherapy prior authorization",
                "similar_policies": [],
                "specialty_filter": "oncology"
            }
        }
    )


class ListPatientsResponse(BaseModel):
    """Response model for listing patients"""
    
    patients: List[SyntheticPatientResponse] = Field(description="List of patients")
    limit: int = Field(description="Results limit")
    offset: int = Field(description="Results offset")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patients": [],
                "limit": 10,
                "offset": 0
            }
        }
    )


class ListNotesResponse(BaseModel):
    """Response model for listing clinical notes"""
    
    notes: List[ClinicalNoteResponse] = Field(description="List of clinical notes")
    filters: Dict[str, Any] = Field(description="Applied filters")
    limit: int = Field(description="Results limit")
    offset: int = Field(description="Results offset")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notes": [],
                "filters": {"specialty": "oncology", "prior_auth_only": True},
                "limit": 10,
                "offset": 0
            }
        }
    )


class PipelineRunResponse(BaseModel):
    """Response model for pipeline run tracking"""
    
    run_id: str = Field(description="Pipeline run identifier")
    status: str = Field(description="Current status")
    num_patients_requested: int = Field(description="Number of patients requested")
    num_patients_generated: int = Field(description="Number of patients generated")
    num_notes_processed: int = Field(description="Number of notes processed")
    num_notes_deidentified: int = Field(description="Number of notes de-identified")
    num_notes_embedded: int = Field(description="Number of notes embedded")
    specialties: List[str] = Field(description="Target specialties")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(description="Completion timestamp")
    duration_seconds: Optional[int] = Field(description="Duration in seconds")
    error_message: Optional[str] = Field(description="Error message if failed")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "run_id": "run_12345",
                "status": "completed",
                "num_patients_requested": 500,
                "num_patients_generated": 500,
                "num_notes_processed": 1250,
                "num_notes_deidentified": 1250,
                "num_notes_embedded": 1250,
                "specialties": ["oncology", "rheumatology"],
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:15:00Z",
                "duration_seconds": 900,
                "error_message": None
            }
        }
    )


class EmbeddingServiceInfoResponse(BaseModel):
    """Response model for embedding service information"""
    
    model_name: str = Field(description="Name of the embedding model")
    embedding_dimension: int = Field(description="Dimension of embeddings")
    max_sequence_length: Optional[str] = Field(description="Maximum sequence length")
    model_type: str = Field(description="Type of model")
    is_ready: bool = Field(description="Whether service is ready")
    cache_stats: Optional[Dict[str, Any]] = Field(description="Cache statistics")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "embedding_dimension": 384,
                "max_sequence_length": "512",
                "model_type": "SentenceTransformer",
                "is_ready": True,
                "cache_stats": {
                    "cached_embeddings": 1250,
                    "total_cache_size_mb": 15.2
                }
            }
        }
    ) 