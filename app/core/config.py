"""
Application configuration management
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/greenlight",
        description="Database connection URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    
    # AI/ML Settings
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    
    # Synthea settings
    synthea_output_dir: str = Field(
        default="./data/synthea",
        description="Directory for Synthea output"
    )
    
    # Data processing
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings() 