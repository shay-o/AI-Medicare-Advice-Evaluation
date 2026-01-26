"""Anthropic adapter for Claude models"""

import os
import time
from typing import Any

try:
    from anthropic import AsyncAnthropic
    from anthropic import (
        AnthropicError,
        APIError,
        RateLimitError,
        APIConnectionError,
    )
except ImportError:
    raise ImportError(
        "Anthropic SDK not installed. Install with: pip install anthropic>=0.18.0"
    )

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class AnthropicAdapter(BaseLLMAdapter):
    """Adapter for Anthropic Claude models"""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Anthropic adapter.

        Args:
            model_name: Model name (e.g., 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229')
            api_key: Anthropic API key (default: from ANTHROPIC_API_KEY env var)
            base_url: Optional custom base URL
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize async client
        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = AsyncAnthropic(**client_kwargs)

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response using Anthropic API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            seed: Random seed (not supported by Anthropic, will be ignored)
            **kwargs: Additional Anthropic-specific parameters

        Returns:
            ModelResponse with content and metadata
        """
        start_time = time.time()

        # Convert messages to Anthropic format
        # Anthropic requires system messages to be separate
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.model_name,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        # Add system message if present
        if system_message:
            request_params["system"] = system_message

        try:
            # Make API call with retries
            response = await self._call_with_retry(request_params)

            # Extract content
            content = ""
            if response.content:
                # Claude returns content as a list of content blocks
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract token usage
            tokens_used = {}
            if hasattr(response, "usage") and response.usage:
                tokens_used = {
                    "prompt": response.usage.input_tokens,
                    "completion": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens,
                }

            return ModelResponse(
                content=content,
                model_identifier=self.get_model_identifier(),
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "stop_reason": response.stop_reason,
                    "model": response.model,
                },
            )

        except RateLimitError as e:
            raise RuntimeError(f"Anthropic rate limit exceeded: {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"Anthropic API connection error: {e}")
        except APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}")
        except AnthropicError as e:
            raise RuntimeError(f"Anthropic error: {e}")

    async def _call_with_retry(
        self,
        request_params: dict[str, Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Call Anthropic API with exponential backoff retry logic.

        Args:
            request_params: Parameters for messages.create()
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            Anthropic Message response
        """
        import asyncio

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.messages.create(**request_params)
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

            except (APIError, AnthropicError):
                # Don't retry on other API errors
                raise

        # If we get here, all retries failed
        raise last_exception or RuntimeError("Anthropic API call failed")

    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            Model identifier string (e.g., 'claude-3-5-sonnet-20241022')
        """
        # Anthropic model names already include version (e.g., claude-3-5-sonnet-20241022)
        return self.model_name

    def supports_seed(self) -> bool:
        """
        Check if this model supports deterministic seeding.

        Returns:
            False - Anthropic does not support seed parameter
        """
        return False

    async def close(self) -> None:
        """Close the Anthropic client"""
        await self.client.close()
