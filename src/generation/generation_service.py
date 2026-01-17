"""Multi-provider generation service for LLM text generation."""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

import google.generativeai as genai
from openai import OpenAI

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("generation.service")


class BaseGenerationProvider(ABC):
    """Base class for generation providers."""
    
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        """Generate content from a prompt."""
        pass


class GeminiGenerationProvider(BaseGenerationProvider):
    """Google Gemini generation provider."""
    
    def __init__(self, api_key: str, model: str):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        logger.info(f"Initialized Gemini generation provider with model: {model}")
    
    def generate_content(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text


class OpenAIGenerationProvider(BaseGenerationProvider):
    """OpenAI generation provider."""
    
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        logger.info(f"Initialized OpenAI generation provider with model: {model}")
    
    def generate_content(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content or ""


class GenerationService:
    """Service for generating content using multiple providers with fallback."""

    def __init__(self):
        """Initialize the generation service."""
        self.provider = self._create_provider()
        self.fallback_providers = self._create_fallback_chain()
        logger.info("Initialized GenerationService")

    def _create_provider(self) -> BaseGenerationProvider:
        """Create the primary provider based on config."""
        # Default to same logic as embedding provider for simplicity, 
        # but using the generation model config
        provider_name = settings.embedding_provider.lower()
        
        if provider_name == "gemini":
            if not settings.google_api_key:
                raise ValueError("Google API key not configured")
            return GeminiGenerationProvider(
                api_key=settings.google_api_key,
                model=settings.gemini_generation_model
            )
        
        elif provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            return OpenAIGenerationProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_generation_model
            )
        
        elif provider_name == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OpenRouter API key not configured")
            return OpenAIGenerationProvider(
                api_key=settings.openrouter_api_key,
                model=settings.openrouter_generation_model,
                base_url="https://openrouter.ai/api/v1"
            )
        
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def _create_fallback_chain(self) -> List[BaseGenerationProvider]:
        """Create fallback providers."""
        fallbacks = []
        current_provider = settings.embedding_provider.lower()
        provider_order = ["gemini", "openai", "openrouter"]
        fallback_order = [p for p in provider_order if p != current_provider]
        
        for provider_name in fallback_order:
            try:
                if provider_name == "gemini" and settings.google_api_key:
                    fallbacks.append(GeminiGenerationProvider(
                        api_key=settings.google_api_key,
                        model=settings.gemini_generation_model
                    ))
                elif provider_name == "openai" and settings.openai_api_key:
                    fallbacks.append(OpenAIGenerationProvider(
                        api_key=settings.openai_api_key,
                        model=settings.openai_generation_model
                    ))
                elif provider_name == "openrouter" and settings.openrouter_api_key:
                    fallbacks.append(OpenAIGenerationProvider(
                        api_key=settings.openrouter_api_key,
                        model=settings.openrouter_generation_model,
                        base_url="https://openrouter.ai/api/v1"
                    ))
            except Exception as e:
                logger.warning(f"Could not create fallback generation provider {provider_name}: {e}")
        
        return fallbacks

    def generate_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a summary answer for the query based on search results."""
        if not results:
            return "No results found to summarize."

        # Prepare context from results
        context_parts = []
        for i, result in enumerate(results[:5], 1): # Top 5
            meta = result.get("metadata", {})
            name = meta.get("name", "Unknown")
            code = result.get("document", "")[:500] # Truncate long code
            context_parts.append(f"Result {i}: {name}\nCode:\n{code}\n")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
You are an expert code analyst.
User Query: "{query}"

Here are the relevant code snippets found in the codebase:
{context}

Please provide a concise summary (1 paragraph) answering the user's query based on these snippets. 
Focus on:
1. Which specific component handles the logic.
2. How it works high-level.
3. Any important validation or constraints mentioned in the code.

Do not just list the files. Synthesize the information.
"""
        return self._generate_with_fallback(prompt)

    def _generate_with_fallback(self, prompt: str) -> str:
        """Generate content handling fallbacks."""
        try:
            return self.provider.generate_content(prompt)
        except Exception as e:
            logger.warning(f"Generation failed with primary provider: {e}")
            for provider in self.fallback_providers:
                try:
                    res = provider.generate_content(prompt)
                    self.provider = provider # Switch to working provider
                    return res
                except Exception as ex:
                    logger.warning(f"Fallback generation failed: {ex}")
            
            return "Error: Could not generate summary due to provider failures."
