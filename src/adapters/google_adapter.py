"""Google adapter for Gemini models"""

import os
import time
from typing import Any

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    from google.api_core import exceptions as google_exceptions
except ImportError:
    raise ImportError(
        "Google Generative AI SDK not installed. Install with: pip install google-generativeai>=0.3.0"
    )

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class GoogleAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini models"""

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize Google adapter.

        Args:
            model_name: Model name (e.g., 'gemini-1.5-pro', 'gemini-1.5-flash')
            api_key: Google API key (default: from GOOGLE_API_KEY env var)
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key not provided. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Configure API
        genai.configure(api_key=self.api_key)

        # Initialize model
        self.model = genai.GenerativeModel(self.model_name)

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Generate a response using Google Gemini API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            seed: Random seed (not officially supported, will be ignored)
            **kwargs: Additional Google-specific parameters

        Returns:
            ModelResponse with content and metadata
        """
        start_time = time.time()

        # Convert messages to Gemini format
        # Gemini uses 'user' and 'model' roles
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                # Use system message as system_instruction
                system_instruction = content
            elif role == "user":
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})

        # Recreate model with system instruction if needed
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name, system_instruction=system_instruction
            )
        else:
            model = self.model

        # Build generation config
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            **kwargs,
        )

        try:
            # Make API call with retries
            response = await self._call_with_retry(
                model, gemini_messages, generation_config
            )

            # Extract content
            content = response.text if hasattr(response, "text") else ""

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract token usage
            tokens_used = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used = {
                    "prompt": response.usage_metadata.prompt_token_count,
                    "completion": response.usage_metadata.candidates_token_count,
                    "total": response.usage_metadata.total_token_count,
                }

            # Extract finish reason
            finish_reason = None
            if (
                hasattr(response, "candidates")
                and response.candidates
                and hasattr(response.candidates[0], "finish_reason")
            ):
                finish_reason = str(response.candidates[0].finish_reason)

            return ModelResponse(
                content=content,
                model_identifier=self.get_model_identifier(),
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": finish_reason,
                },
            )

        except google_exceptions.ResourceExhausted as e:
            raise RuntimeError(f"Google API rate limit exceeded: {e}")
        except google_exceptions.GoogleAPIError as e:
            raise RuntimeError(f"Google API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Google error: {e}")

    async def _call_with_retry(
        self,
        model: Any,
        messages: list[dict[str, Any]],
        generation_config: GenerationConfig,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Call Google API with exponential backoff retry logic.

        Args:
            model: GenerativeModel instance
            messages: Formatted messages
            generation_config: Generation configuration
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry

        Returns:
            GenerateContentResponse
        """
        import asyncio

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Start chat if we have multiple messages
                if len(messages) > 1:
                    # Use chat mode for multi-turn conversations
                    chat = model.start_chat(history=messages[:-1])
                    response = await asyncio.to_thread(
                        chat.send_message,
                        messages[-1]["parts"][0],
                        generation_config=generation_config,
                    )
                else:
                    # Use generate_content for single messages
                    response = await asyncio.to_thread(
                        model.generate_content,
                        messages[0]["parts"][0],
                        generation_config=generation_config,
                    )

                return response

            except google_exceptions.ResourceExhausted as e:
                last_exception = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = initial_delay * (2**attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise

            except google_exceptions.GoogleAPIError:
                # Don't retry on other API errors
                raise

        # If we get here, all retries failed
        raise last_exception or RuntimeError("Google API call failed")

    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            Model identifier string (e.g., 'gemini-1.5-pro')
        """
        return self.model_name

    def supports_seed(self) -> bool:
        """
        Check if this model supports deterministic seeding.

        Returns:
            False - Google Gemini does not officially support seed parameter
        """
        return False

    async def close(self) -> None:
        """Close the Google client (no-op, client is stateless)"""
        pass
