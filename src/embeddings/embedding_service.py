"""Multi-provider embedding service supporting OpenAI, Gemini, and OpenRouter."""

from typing import List
from abc import ABC, abstractmethod

import google.generativeai as genai
from openai import OpenAI

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("embeddings.service")


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers."""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        pass


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Google Gemini embedding provider."""
    
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]
    
    def get_dimension(self) -> int:
        return 768  # Gemini embedding-001 dimension


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._dimension = self._get_model_dimension(model)
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def get_dimension(self) -> int:
        return self._dimension
    
    def _get_model_dimension(self, model: str) -> int:
        """Get dimension based on model name."""
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(model, 1536)


class OpenRouterEmbeddingProvider(BaseEmbeddingProvider):
    """OpenRouter embedding provider."""
    
    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self._dimension = 1536  # Most OpenRouter models use 1536
        logger.info(f"Initialized OpenRouter provider with model: {model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def get_dimension(self) -> int:
        return self._dimension


class EmbeddingService:
    """Service for generating embeddings using multiple providers with automatic fallback."""

    def __init__(self):
        """Initialize the embedding service with configured provider and fallback chain."""
        self.provider = self._create_provider()
        self.fallback_providers = self._create_fallback_chain()
        logger.info(f"Initialized EmbeddingService with provider: {settings.embedding_provider}")
        if self.fallback_providers:
            logger.info(f"Fallback chain: {[p.__class__.__name__ for p in self.fallback_providers]}")

    def _create_provider(self) -> BaseEmbeddingProvider:
        """Create the appropriate embedding provider based on configuration."""
        provider_name = settings.embedding_provider.lower()
        
        if provider_name == "gemini":
            if not settings.google_api_key:
                raise ValueError("Google API key not configured")
            return GeminiEmbeddingProvider(
                api_key=settings.google_api_key,
                model=settings.gemini_embedding_model
            )
        
        elif provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIEmbeddingProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_embedding_model
            )
        
        elif provider_name == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OpenRouter API key not configured")
            return OpenRouterEmbeddingProvider(
                api_key=settings.openrouter_api_key,
                model=settings.openrouter_embedding_model
            )
        
        else:
            raise ValueError(f"Unknown embedding provider: {provider_name}")
    
    def _create_fallback_chain(self) -> List[BaseEmbeddingProvider]:
        """Create fallback providers in order: Gemini → OpenAI → OpenRouter."""
        fallbacks = []
        current_provider = settings.embedding_provider.lower()
        
        # Define fallback order
        provider_order = ["gemini", "openai", "openrouter"]
        
        # Remove current provider from fallback chain
        fallback_order = [p for p in provider_order if p != current_provider]
        
        # Create fallback providers
        for provider_name in fallback_order:
            try:
                if provider_name == "gemini" and settings.google_api_key:
                    fallbacks.append(GeminiEmbeddingProvider(
                        api_key=settings.google_api_key,
                        model=settings.gemini_embedding_model
                    ))
                elif provider_name == "openai" and settings.openai_api_key:
                    fallbacks.append(OpenAIEmbeddingProvider(
                        api_key=settings.openai_api_key,
                        model=settings.openai_embedding_model
                    ))
                elif provider_name == "openrouter" and settings.openrouter_api_key:
                    fallbacks.append(OpenRouterEmbeddingProvider(
                        api_key=settings.openrouter_api_key,
                        model=settings.openrouter_embedding_model
                    ))
            except Exception as e:
                logger.warning(f"Could not create fallback provider {provider_name}: {e}")
        
        return fallbacks

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text with automatic fallback.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        # Try primary provider
        try:
            return self.provider.generate_embedding(text)
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}")
            
            # Try fallback providers
            for i, fallback_provider in enumerate(self.fallback_providers):
                try:
                    logger.info(f"Trying fallback provider {i+1}: {fallback_provider.__class__.__name__}")
                    embedding = fallback_provider.generate_embedding(text)
                    logger.info(f"Successfully switched to {fallback_provider.__class__.__name__}")
                    # Update primary provider to the working one
                    self.provider = fallback_provider
                    return embedding
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider {i+1} failed: {fallback_error}")
                    continue
            
            # All providers failed
            logger.error("All embedding providers failed")
            raise Exception(f"All embedding providers failed. Last error: {e}")

    def generate_embeddings(self, text: str) -> List[float]:
        """Alias for generate_embedding to support legacy/incorrect calls.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.generate_embedding(text)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        batch_size = settings.batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            for text in batch:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Error in batch processing: {e}")
                    # Add zero vector as placeholder for failed embeddings
                    embeddings.append([0.0] * self.provider.get_dimension())

        return embeddings

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Embedding vector
        """
        # For OpenAI and OpenRouter, same method works for queries
        # For Gemini, we could use task_type="retrieval_query" but keeping it simple
        return self.generate_embedding(query)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from current provider."""
        return self.provider.get_dimension()
