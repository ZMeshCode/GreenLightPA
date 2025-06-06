"""
Synthetic data generation and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging

from app.core.database import get_database
from app.services.synthetic_pipeline import SyntheticDataPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate")
async def generate_synthetic_data(
    background_tasks: BackgroundTasks,
    num_patients: int = 500,
    specialties: List[str] = ["oncology", "rheumatology"],
    db: AsyncSession = Depends(get_database)
):
    """
    Generate synthetic patient data using Synthea
    """
    try:
        pipeline = SyntheticDataPipeline(db)
        
        # Run pipeline in background
        background_tasks.add_task(
            pipeline.run_full_pipeline,
            num_patients=num_patients,
            specialties=specialties
        )
        
        return {
            "message": "Synthetic data generation started",
            "num_patients": num_patients,
            "specialties": specialties,
            "status": "in_progress"
        }
    except Exception as e:
        logger.error(f"Failed to start synthetic data generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_generation_status(db: AsyncSession = Depends(get_database)):
    """
    Get status of synthetic data generation
    """
    try:
        # Query database for current counts
        from sqlalchemy import text
        
        patients_result = await db.execute(text("SELECT COUNT(*) FROM synthetic_patients"))
        notes_result = await db.execute(text("SELECT COUNT(*) FROM clinical_notes"))
        
        patients_count = patients_result.scalar()
        notes_count = notes_result.scalar()
        
        return {
            "patients_generated": patients_count,
            "clinical_notes": notes_count,
            "status": "completed" if patients_count > 0 else "not_started"
        }
    except Exception as e:
        logger.error(f"Failed to get generation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patients")
async def list_synthetic_patients(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_database)
):
    """
    List synthetic patients
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT patient_id, created_at, 
                   (fhir_bundle->>'resourceType') as resource_type
            FROM synthetic_patients 
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, {"limit": limit, "offset": offset})
        patients = [dict(row._mapping) for row in result]
        
        return {
            "patients": patients,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes")
async def list_clinical_notes(
    specialty: str = None,
    prior_auth_only: bool = False,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_database)
):
    """
    List clinical notes with filtering options
    """
    try:
        from sqlalchemy import text
        
        where_conditions = []
        params = {"limit": limit, "offset": offset}
        
        if specialty:
            where_conditions.append("specialty = :specialty")
            params["specialty"] = specialty
            
        if prior_auth_only:
            where_conditions.append("prior_auth_required = true")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = text(f"""
            SELECT note_id, patient_id, specialty, prior_auth_required, 
                   prior_auth_status, created_at,
                   LEFT(deidentified_text, 200) as text_preview
            FROM clinical_notes 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, params)
        notes = [dict(row._mapping) for row in result]
        
        return {
            "notes": notes,
            "filters": {
                "specialty": specialty,
                "prior_auth_only": prior_auth_only
            },
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-policies")
async def search_similar_policies(
    query_text: str,
    specialty: str = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_database)
):
    """
    Search for similar policy chunks using vector similarity
    """
    try:
        from app.services.embedding_service import EmbeddingService
        from sqlalchemy import text
        
        embedding_service = EmbeddingService()
        query_embedding = embedding_service.embed_text(query_text)
        
        # Convert to PostgreSQL array format
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        params = {
            "query_embedding": embedding_str,
            "match_threshold": 0.7,
            "match_count": limit,
            "filter_specialty": specialty
        }
        
        query = text("""
            SELECT * FROM search_similar_policies(
                :query_embedding::vector,
                :match_threshold,
                :match_count,
                :filter_specialty
            )
        """)
        
        result = await db.execute(query, params)
        policies = [dict(row._mapping) for row in result]
        
        return {
            "query": query_text,
            "similar_policies": policies,
            "specialty_filter": specialty
        }
    except Exception as e:
        logger.error(f"Failed to search policies: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 