"""Fake adapter for testing with canned responses"""

import time
from typing import Any

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class FakeAdapter(BaseLLMAdapter):
    """Fake adapter that returns canned responses for testing"""

    # Predefined responses for testing
    CANNED_RESPONSES = {
        "perfect": """Medicare has two main options:

1. **Original Medicare (Parts A & B)**
   - Part A covers hospital stays, skilled nursing facility care, hospice, and some home health care
   - Part B covers doctor visits, outpatient care, medical equipment, and preventive services
   - You can see any provider that accepts Medicare
   - You'll need separate Part D for prescription drug coverage
   - Consider a Medigap policy to cover out-of-pocket costs

2. **Medicare Advantage (Part C)**
   - Private insurance that bundles Parts A, B, and usually D
   - Often includes extra benefits like dental, vision, and hearing
   - Uses provider networks - you may need to use in-network doctors
   - Has a yearly out-of-pocket maximum for cost protection
   - May require referrals to see specialists

You can compare specific plans at Medicare.gov or call 1-800-MEDICARE for personalized help.""",
        "incomplete": """Medicare Advantage and Original Medicare are different types of coverage.

Original Medicare is the traditional government program with Part A for hospitals and Part B for doctors.

Medicare Advantage is sold by private insurance companies and includes hospital and doctor coverage, and often prescription drugs too.

You should compare plans to see which works best for you.""",
        "incorrect": """Medicare Advantage is always better than Original Medicare because it has lower costs and better coverage. You should definitely switch to Medicare Advantage. All doctors accept Medicare Advantage plans, so you won't have any issues with networks. You don't need to worry about anything else.""",
        "refusal": """I appreciate your question about Medicare options. However, Medicare enrollment decisions can be complex and depend on your specific health needs, financial situation, and location.

I'd recommend speaking with a licensed Medicare advisor or contacting your State Health Insurance Assistance Program (SHIP) at 1-800-MEDICARE for personalized guidance. They can help you understand which option is best for your situation.

Is there any general information about Medicare that I can help clarify?""",
    }

    def __init__(self, response_type: str = "perfect", **kwargs: Any):
        """
        Initialize fake adapter.

        Args:
            response_type: One of 'perfect', 'incomplete', 'incorrect', 'refusal'
            **kwargs: Ignored
        """
        super().__init__(model_name=f"fake:{response_type}", **kwargs)
        if response_type not in self.CANNED_RESPONSES:
            raise ValueError(
                f"Invalid response_type '{response_type}'. "
                f"Must be one of: {list(self.CANNED_RESPONSES.keys())}"
            )
        self.response_type = response_type

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Return a canned response"""
        start_time = time.time()

        # Simulate processing time
        await self._simulate_latency()

        content = self.CANNED_RESPONSES[self.response_type]

        latency_ms = int((time.time() - start_time) * 1000)

        # Rough token estimation (4 chars per token)
        prompt_tokens = sum(len(m.get("content", "")) for m in messages) // 4
        completion_tokens = len(content) // 4

        return ModelResponse(
            content=content,
            model_identifier=f"fake-v1.0-{self.response_type}",
            tokens_used={
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": prompt_tokens + completion_tokens,
            },
            latency_ms=latency_ms,
            metadata={
                "response_type": self.response_type,
                "is_fake": True,
                "message_count": len(messages),
            },
        )

    def get_model_identifier(self) -> str:
        """Return fake model identifier"""
        return f"fake-v1.0-{self.response_type}"

    def supports_seed(self) -> bool:
        """Fake adapter is always deterministic"""
        return True

    async def _simulate_latency(self) -> None:
        """Simulate realistic API latency"""
        import asyncio

        await asyncio.sleep(0.1)  # 100ms fake latency
