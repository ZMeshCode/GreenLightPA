"""
Configuration settings for GreenLightPA
Supports hybrid N8n + LangChain architecture
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "GreenLightPA"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    
    # Vector Database
    vector_db_host: str = Field(default="localhost", env="VECTOR_DB_HOST")
    vector_db_port: int = Field(default=5432, env="VECTOR_DB_PORT")
    vector_db_name: str = Field(default="greenlightpa_vectors", env="VECTOR_DB_NAME")
    
    # AI/ML Configuration
    # LLM Provider Selection
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")  # openai, anthropic, or both
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    
    # Embedding model (independent of LLM choice)
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", 
        env="EMBEDDING_MODEL"
    )
    
    # LangChain Configuration
    langchain_tracing_v2: bool = Field(default=False, env="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com", 
        env="LANGCHAIN_ENDPOINT"
    )
    langchain_api_key: Optional[str] = Field(default=None, env="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="greenlightpa", env="LANGCHAIN_PROJECT")
    
    # N8n Workflow Configuration
    n8n_host: str = Field(default="localhost", env="N8N_HOST")
    n8n_port: int = Field(default=5678, env="N8N_PORT")
    n8n_webhook_url: str = Field(
        default="http://localhost:5678/webhook", 
        env="N8N_WEBHOOK_URL"
    )
    n8n_api_key: Optional[str] = Field(default=None, env="N8N_API_KEY")
    
    # ChromaDB Configuration
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    chroma_persist_directory: str = Field(
        default="./chroma_db", 
        env="CHROMA_PERSIST_DIRECTORY"
    )
    
    # Payer Integration APIs
    change_healthcare_api_key: Optional[str] = Field(
        default=None, 
        env="CHANGE_HEALTHCARE_API_KEY"
    )
    change_healthcare_endpoint: str = Field(
        default="https://api.changehealthcare.com", 
        env="CHANGE_HEALTHCARE_ENDPOINT"
    )
    
    # Twilio Configuration (for voicebot)
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    
    # Security
    jwt_secret_key: str = Field(env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, 
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    
    # Healthcare Standards
    fhir_version: str = Field(default="4.0.1", env="FHIR_VERSION")
    x12_version: str = Field(default="005010", env="X12_VERSION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings 