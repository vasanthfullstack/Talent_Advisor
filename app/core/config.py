"""Core configuration management for the application."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = "AI Talent Advisor"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # LLM Configuration
    openai_api_key: str = ""
    llm_model: str = "gpt-3.5-turbo"
    use_mock_llm: bool = True
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    use_mock_embeddings: bool = False
    
    # Vision Configuration
    use_mock_vision: bool = True
    vision_model: str = "gpt-4-vision-preview"
    
    # RAG Configuration
    rag_backend: str = "faiss"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 5
    
    # Paths
    student_profiles_path: str = "./student_profiles"
    data_path: str = "./data"
    faiss_index_path: str = "./data/faiss_index"
    metadata_path: str = "./data/metadata.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
