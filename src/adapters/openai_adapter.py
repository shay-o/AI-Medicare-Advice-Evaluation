"""OpenAI adapter for GPT models"""

import os
import time
from typing import Any

try:
    from openai import AsyncOpenAI
    from openai import OpenAIError, APIError, RateLimitError, APIConnectionError
except ImportError:
    raise ImportError(
        "OpenAI SDK not installed. Install with: pip install openai>=1.0.0"
    )

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI GPT models"""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize OpenAI adapter.

        Args:
            model_name: Model name (e.g., 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo')
            api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
            base_url: Optional custom base URL
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize async client
        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**client_kwargs)
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
        Generate a response using OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            seed: Random seed for reproducibility (supported on some models)
            **kwargs: Additional OpenAI-specific parameters

        Returns:
            ModelResponse with content and metadata
        """
        start_time = time.time()

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Add seed if provided (supported on gpt-4-turbo and later)
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
            raise RuntimeError(f"OpenAI rate limit exceeded: {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"OpenAI API connection error: {e}")
        except APIError as e:
            raise RuntimeError(f"OpenAI API error: {e}")
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI error: {e}")

    async def _call_with_retry(
        self,
        request_params: dict[str, Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Call OpenAI API with exponential backoff retry logic.

        Args:
            request_params: Parameters for chat.completions.create()
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            OpenAI ChatCompletion response
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
        raise last_exception or RuntimeError("OpenAI API call failed")

    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            Model identifier string (e.g., 'gpt-4-turbo-2024-04-09')
        """
        # Return actual model version if we have it, otherwise return requested name
        return self._model_version or self.model_name

    def supports_seed(self) -> bool:
        """
        Check if this model supports deterministic seeding.

        Returns:
            True for gpt-4-turbo and gpt-3.5-turbo-1106 or later
        """
        # Seed support was added in:
        # - gpt-4-turbo (and variants)
        # - gpt-3.5-turbo-1106 and later
        # - gpt-4-0125-preview and later

        model_lower = self.model_name.lower()

        if "gpt-4-turbo" in model_lower:
            return True
        if "gpt-4o" in model_lower:
            return True
        if "gpt-3.5-turbo-1106" in model_lower:
            return True
        if "gpt-4-0125" in model_lower:
            return True

        # Conservative default
        return False

    async def close(self) -> None:
        """Close the OpenAI client"""
        await self.client.close()
