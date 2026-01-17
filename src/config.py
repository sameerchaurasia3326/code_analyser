"""Configuration management using Pydantic settings."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Embedding Provider Configuration
    embedding_provider: str = Field(
        default="gemini",
        description="Embedding provider: 'gemini', 'openai', or 'openrouter'",
    )
    
    # Google Gemini API Configuration
    google_api_key: str = Field(default="", description="Google API key for Gemini")
    gemini_embedding_model: str = Field(
        default="models/embedding-001",
        description="Google embedding model to use",
    )
    
    # OpenAI API Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use",
    )
    
    # OpenRouter API Configuration
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        description="OpenRouter embedding model to use",
    )

    # Generative AI Configuration
    gemini_generation_model: str = Field(
        default="gemini-1.5-flash",
        description="Google Gemini model for generation",
    )
    openai_generation_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model for generation",
    )
    openrouter_generation_model: str = Field(
        default="openai/gpt-4o-mini",
        description="OpenRouter model for generation",
    )
    
    embedding_dimension: int = Field(
        default=1536,
        description="Dimension of embedding vectors (auto-set based on model)",
    )

    # Vector Database Configuration
    chroma_persist_directory: str = Field(
        default="./chroma_db",
        description="Directory to persist ChromaDB data",
    )
    chroma_collection_name: str = Field(
        default="code_embeddings",
        description="ChromaDB collection name",
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="text", description="Log format (json or text)")

    # Code Indexing Configuration
    max_chunk_size: int = Field(
        default=8000,
        description="Maximum size of code chunk in characters",
    )
    batch_size: int = Field(
        default=100,
        description="Batch size for embedding generation",
    )
    supported_extensions: str = Field(
        default=".py,.js,.ts,.java,.go,.cpp,.c,.h",
        description="Comma-separated list of supported file extensions",
    )

    # Search Configuration
    default_search_limit: int = Field(
        default=10,
        description="Default number of search results",
    )
    similarity_threshold: float = Field(
        default=0.3,
        description="Minimum similarity threshold for search results (0-1)",
    )
    
    # Statement-Level Chunking
    enable_statement_chunking: bool = Field(
        default=True,
        description="Enable extraction of individual statements"
    )
    max_statements_per_function: int = Field(
        default=20,
        description="Maximum statements to extract per function"
    )

    @property
    def supported_extensions_list(self) -> List[str]:
        """Get supported extensions as a list."""
        return [ext.strip() for ext in self.supported_extensions.split(",")]


# Global settings instance
settings = Settings()
