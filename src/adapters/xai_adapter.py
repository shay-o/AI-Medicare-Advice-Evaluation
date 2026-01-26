"""xAI adapter for Grok models"""

import os
import time
from typing import Any

try:
    from openai import AsyncOpenAI  # xAI uses OpenAI-compatible API
    from openai import OpenAIError, APIError, RateLimitError, APIConnectionError
except ImportError:
    raise ImportError(
        "OpenAI SDK not installed (required for xAI). Install with: pip install openai>=1.0.0"
    )

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class XAIAdapter(BaseLLMAdapter):
    """Adapter for xAI Grok models"""

    # xAI uses OpenAI-compatible API
    XAI_BASE_URL = "https://api.x.ai/v1"

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize xAI adapter.

        Args:
            model_name: Model name (e.g., 'grok-beta', 'grok-2')
            api_key: xAI API key (default: from XAI_API_KEY env var)
            base_url: Optional custom base URL (default: https://api.x.ai/v1)
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "xAI API key not provided. Set XAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize async client with xAI base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url or self.XAI_BASE_URL,
        )
        self._model_version: str | None = None

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response using xAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            seed: Random seed (check xAI docs for support)
            **kwargs: Additional xAI-specific parameters

        Returns:
            ModelResponse with content and metadata
        """
        start_time = time.time()

        # Build request parameters (OpenAI-compatible)
        request_params: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Add seed if provided (check xAI docs for availability)
        if seed is not None:
            request_params["seed"] = seed

        try:
            # Make API call with retries
            response = await self._call_with_retry(request_params)

            # Extract content
            content = response.choices[0].message.content or ""

            # Track model version if available
            if hasattr(response, "model"):
                self._model_version = response.model

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract token usage
            tokens_used = {}
            if hasattr(response, "usage") and response.usage:
                tokens_used = {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                }

            return ModelResponse(
                content=content,
                model_identifier=self.get_model_identifier(),
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "system_fingerprint": getattr(response, "system_fingerprint", None),
                },
            )

        except RateLimitError as e:
            raise RuntimeError(f"xAI rate limit exceeded: {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"xAI API connection error: {e}")
        except APIError as e:
            raise RuntimeError(f"xAI API error: {e}")
        except OpenAIError as e:
            raise RuntimeError(f"xAI error: {e}")

    async def _call_with_retry(
        self,
        request_params: dict[str, Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Call xAI API with exponential backoff retry logic.

        Args:
            request_params: Parameters for chat.completions.create()
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            OpenAI-compatible ChatCompletion response
        """
        import asyncio

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.chat.completions.create(**request_params)
                return response

            except (RateLimitError, APIConnectionError) as e:
                last_exception = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = initial_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

            except (APIError, OpenAIError):
                # Don't retry on other API errors
                raise

        # If we get here, all retries failed
        raise last_exception or RuntimeError("xAI API call failed")

    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            Model identifier string (e.g., 'grok-2')
        """
        return self._model_version or self.model_name

    def supports_seed(self) -> bool:
        """
        Check if this model supports deterministic seeding.

        Returns:
            Check xAI documentation for current seed support
        """
        # Conservative default - check xAI docs for actual support
        return False

    async def close(self) -> None:
        """Close the xAI client"""
        await self.client.close()
