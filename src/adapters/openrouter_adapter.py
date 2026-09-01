"""OpenRouter adapter for unified access to multiple LLM providers"""

import os
import time
from typing import Any

try:
    from openai import AsyncOpenAI
    from openai import OpenAIError, APIError, RateLimitError, APIConnectionError
except ImportError:
    raise ImportError(
        "OpenAI SDK not installed (required for OpenRouter). Install with: pip install openai>=1.0.0"
    )

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class OpenRouterAdapter(BaseLLMAdapter):
    """
    Adapter for OpenRouter.ai - unified access to multiple LLM providers.

    OpenRouter provides access to models from OpenAI, Anthropic, Google, Meta, and more
    through a single API key and OpenAI-compatible interface.

    Model naming format: "provider/model-name"
    Examples:
        - "anthropic/claude-3.5-sonnet"
        - "openai/gpt-4-turbo"
        - "google/gemini-pro-1.5"
        - "meta-llama/llama-3.1-70b-instruct"
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        model_name: str,
        api_key: str | None = None,
        base_url: str | None = None,
        app_name: str | None = None,
        site_url: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize OpenRouter adapter.

        Args:
            model_name: Model identifier (e.g., 'anthropic/claude-3.5-sonnet', 'openai/gpt-4-turbo')
            api_key: OpenRouter API key (default: from OPENROUTER_API_KEY env var)
            base_url: Optional custom base URL (default: https://openrouter.ai/api/v1)
            app_name: Optional app name for OpenRouter dashboard
            site_url: Optional site URL for OpenRouter dashboard
            **kwargs: Additional configuration
        """
        super().__init__(model_name, **kwargs)

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable "
                "or pass api_key parameter. Get your key at: https://openrouter.ai/keys"
            )

        # Build headers for OpenRouter
        default_headers = {
            "HTTP-Referer": site_url or os.getenv("OPENROUTER_SITE_URL", ""),
            "X-Title": app_name or os.getenv("OPENROUTER_APP_NAME", "AI Medicare Evaluator"),
        }

        # Initialize async client with OpenRouter base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url or self.OPENROUTER_BASE_URL,
            default_headers=default_headers,
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
        Generate a response using OpenRouter API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            seed: Random seed (support depends on underlying model)
            **kwargs: Additional OpenRouter-specific parameters

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

        # Add seed if provided (support varies by model)
        if seed is not None:
            request_params["seed"] = seed

        # OpenRouter-specific: can pass transforms for fallback behavior
        # request_params["transforms"] = ["middle-out"]  # Optional

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
            cost_usd = None
            if hasattr(response, "usage") and response.usage:
                tokens_used = {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                }
                # OpenRouter reports the actual charge for the call. Preferred over
                # multiplying tokens by a local price table, which goes stale and has
                # to be maintained per model.
                cost_usd = getattr(response.usage, "cost", None)

            # OpenRouter provides additional metadata
            metadata = {
                "finish_reason": response.choices[0].finish_reason,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
            }

            if cost_usd is not None:
                metadata["cost_usd"] = cost_usd

            # Citations from provider-hosted web search, when the web plugin is on.
            # Stored because a search-enabled answer is only auditable if you can see
            # what it read, and because those results change over time.
            citations = self._extract_citations(response)
            if citations:
                metadata["citations"] = citations

            # Extract OpenRouter-specific metadata if available
            if hasattr(response, "id"):
                metadata["openrouter_id"] = response.id

            return ModelResponse(
                content=content,
                model_identifier=self.get_model_identifier(),
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata=metadata,
            )

        except RateLimitError as e:
            raise RuntimeError(f"OpenRouter rate limit exceeded: {e}")
        except APIConnectionError as e:
            raise RuntimeError(f"OpenRouter API connection error: {e}")
        except APIError as e:
            raise RuntimeError(f"OpenRouter API error: {e}")
        except OpenAIError as e:
            raise RuntimeError(f"OpenRouter error: {e}")

    @staticmethod
    def _extract_citations(response: Any) -> list[str]:
        """Pull web-search source URLs out of the raw response body.

        Reads the raw JSON rather than the parsed object because the OpenAI SDK
        discards OpenRouter's `annotations` field during parsing.
        """
        body = getattr(response, "_raw_body", None)
        if not isinstance(body, dict):
            return []
        try:
            annotations = body["choices"][0]["message"].get("annotations") or []
        except (KeyError, IndexError, TypeError):
            return []
        urls = []
        for a in annotations:
            if isinstance(a, dict) and a.get("type") == "url_citation":
                url = (a.get("url_citation") or {}).get("url")
                if url:
                    urls.append(url)
        return urls

    async def _call_with_retry(
        self,
        request_params: dict[str, Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> Any:
        """
        Call OpenRouter API with exponential backoff retry logic.

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
                # with_raw_response keeps the raw HTTP body reachable. The SDK's typed
                # ChatCompletion drops fields it does not know about, and OpenRouter's
                # web-search citations (message.annotations) are one of them: they are
                # absent from both the typed field and model_extra, but present in the
                # JSON. Parsing the body is the only way to keep them.
                raw = await self.client.chat.completions.with_raw_response.create(
                    **request_params
                )
                response = raw.parse()
                try:
                    response._raw_body = raw.http_response.json()
                except Exception:
                    response._raw_body = None
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
        raise last_exception or RuntimeError("OpenRouter API call failed")

    def get_model_identifier(self) -> str:
        """
        Get the full model version identifier.

        Returns:
            Model identifier string (e.g., 'anthropic/claude-3.5-sonnet')
        """
        return self._model_version or self.model_name

    def supports_seed(self) -> bool:
        """
        Check if this model supports deterministic seeding.

        Returns:
            Depends on underlying model - OpenAI models support seed,
            Anthropic models do not. Conservative default is False.
        """
        # Check if underlying model supports seed
        model_lower = self.model_name.lower()

        # OpenAI models support seed
        if "openai/" in model_lower and ("gpt-4" in model_lower or "gpt-3.5" in model_lower):
            return True

        # Most other providers don't officially support seed
        return False

    async def close(self) -> None:
        """Close the OpenRouter client"""
        await self.client.close()

    def __repr__(self) -> str:
        return f"OpenRouterAdapter(model_name='{self.model_name}')"
