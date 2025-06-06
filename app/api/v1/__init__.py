"""
API v1 router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import synthetic_data

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    synthetic_data.router,
    prefix="/synthetic",
    tags=["synthetic-data"]
) 