"""LLM Provider Adapters"""

from .base import BaseLLMAdapter, ModelResponse
from .fake_adapter import FakeAdapter
from .mock_agent_adapter import MockAgentAdapter

# Real adapters - imported on demand to avoid missing dependency errors
# from .openai_adapter import OpenAIAdapter
# from .anthropic_adapter import AnthropicAdapter
# from .google_adapter import GoogleAdapter
# from .xai_adapter import XAIAdapter

__all__ = [
    "BaseLLMAdapter",
    "ModelResponse",
    "FakeAdapter",
    "MockAgentAdapter",
]
