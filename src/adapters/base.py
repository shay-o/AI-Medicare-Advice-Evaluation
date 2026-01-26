"""Base adapter interface for LLM providers"""

from abc import ABC, abstractmethod
from typing import Any

from ..schemas import ModelResponse


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM provider adapters"""

    def __init__(self, model_name: str, **kwargs: Any):
        """
        Initialize the adapter.

        Args:
            model_name: Name of the model to use (e.g., 'gpt-4.1', 'claude-3.5-sonnet')
            **kwargs: Provider-specific configuration (API keys, base URLs, etc.)
        """
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response from the model.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens in response
            seed: Random seed for reproducibility (if supported)
            **kwargs: Additional provider-specific parameters

        Returns:
            ModelResponse with content, metadata, and usage stats
        """
        pass

    @abstractmethod
    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            String like 'gpt-4.1-20250101' or 'claude-3.5-sonnet-20241022'
        """
        pass

    def supports_seed(self) -> bool:
        """
        Check if this provider/model supports deterministic seeding.

        Returns:
            True if seed parameter is supported
        """
        return False

    async def close(self) -> None:
        """Clean up resources (HTTP clients, etc.)"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_name='{self.model_name}')"
