"""Mock adapter that returns JSON for agent tasks"""

import json
import re
import time
from typing import Any

from ..schemas import ModelResponse
from .base import BaseLLMAdapter


class MockAgentAdapter(BaseLLMAdapter):
    """
    Mock adapter that simulates agent LLM behavior by returning proper JSON.

    This is used for testing the orchestrator without real LLM API calls.
    It detects which agent is calling it based on the system prompt and returns
    appropriate mock JSON responses.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(model_name="mock-agent-v1.0", **kwargs)

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: int | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Generate mock JSON response based on agent type"""
        import asyncio

        await asyncio.sleep(0.05)  # Simulate latency

        start_time = time.time()

        # Detect which agent is calling based on system prompt
        system_prompt = messages[0].get("content", "") if messages else ""
        user_message = messages[-1].get("content", "") if len(messages) > 1 else ""

        # Determine agent type - check in specific order to avoid conflicts
        if "questioner" in system_prompt.lower():
            agent_type = "questioner"
            content = self._mock_questioner_response(messages)
        elif "verifier" in system_prompt.lower() or ("verifying" in system_prompt.lower() and "medicare" in system_prompt.lower()):
            agent_type = "verifier"
            content = self._mock_verifier_response(messages)
        elif "extractor" in system_prompt.lower() or "extracting claims" in system_prompt.lower():
            agent_type = "extractor"
            content = self._mock_extractor_response(messages)
        elif "scorer" in system_prompt.lower() or "score" in system_prompt.lower():
            agent_type = "scorer"
            content = self._mock_scorer_response(messages)
        elif "adjudicator" in system_prompt.lower():
            agent_type = "adjudicator"
            content = self._mock_adjudicator_response(messages)
        else:
            # Default fallback
            agent_type = "unknown"
            content = '{"error": "Unknown agent type"}'

        # Debug logging (can be removed later)
        if "error" in content:
            print(f"[MockAdapter] Detected agent: {agent_type}")
            print(f"[MockAdapter] System prompt preview: {system_prompt[:100]}...")

        latency_ms = int((time.time() - start_time) * 1000)

        return ModelResponse(
            content=content,
            model_identifier="mock-agent-v1.0",
            tokens_used={
                "prompt": len(str(messages)) // 4,
                "completion": len(content) // 4,
                "total": (len(str(messages)) + len(content)) // 4,
            },
            latency_ms=latency_ms,
            metadata={"is_mock": True},
        )

    def _mock_questioner_response(self, messages: list[dict[str, str]]) -> str:
        """Mock questioner returning questions"""
        return json.dumps(
            {
                "turns": [
                    {
                        "turn_id": "Q1",
                        "user_message": "I'm trying to decide between Original Medicare and Medicare Advantage. What's the difference?",
                    }
                ]
            }
        )

    def _mock_extractor_response(self, messages: list[dict[str, str]]) -> str:
        """Mock extractor returning claims"""
        # Extract the actual response text from the user message
        user_message = messages[-1].get("content", "") if messages else ""

        try:
            json_start = user_message.find('{')
            if json_start != -1:
                json_str = user_message[json_start:]
                data = json.loads(json_str)
                response_text = data.get("response_text", "")
            else:
                response_text = user_message
        except:
            response_text = user_message

        # Simple rule-based claim extraction
        claims = []
        claim_id = 1

        # Look for bullet points and sentences
        sentences = re.split(r'[.\n]', response_text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue

            # Skip formatting markers
            if sentence.startswith("**") or sentence.startswith("-"):
                sentence = re.sub(r'\*\*|^-\s*', '', sentence).strip()

            if sentence:
                claims.append(
                    {
                        "claim_id": f"C{claim_id}",
                        "text": sentence,
                        "claim_type": "factual",
                        "confidence": "high",
                        "verifiable": True,
                        "quote_spans": [],
                        "is_hedged": any(
                            word in sentence.lower()
                            for word in ["may", "might", "often", "usually", "generally"]
                        ),
                        "context_dependent": False,
                    }
                )
                claim_id += 1

        return json.dumps({"claims": claims[:15]})  # Limit to 15 claims

    def _mock_verifier_response(self, messages: list[dict[str, str]]) -> str:
        """Mock verifier returning verdicts"""
        user_message = messages[-1].get("content", "") if messages else ""

        try:
            # Find JSON in the user message - it should be after a colon or newline
            lines = user_message.split('\n')
            json_str = None

            # Try to find the line that starts with {
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('{'):
                    # Join from this line to the end
                    json_str = '\n'.join(lines[i:])
                    break

            if not json_str:
                # Fallback: find first {
                json_start = user_message.find('{')
                if json_start != -1:
                    json_str = user_message[json_start:]

            if not json_str:
                return json.dumps({"verdicts": []})

            data = json.loads(json_str)
            claims = data.get("claims", [])
            answer_key = data.get("answer_key", {})

            if not claims:
                return json.dumps({"verdicts": []})

        except Exception as e:
            return json.dumps({"verdicts": []})

        verdicts = []
        canonical_facts = {f["fact_id"]: f for f in answer_key.get("canonical_facts", [])}

        for claim in claims:
            claim_text_lower = claim.get("text", "").lower()

            # Simple keyword matching to determine verdict
            label = "NOT_IN_KEY"
            evidence = []
            severity = "none"

            # Check for key Medicare concepts
            if "original medicare" in claim_text_lower and "part" in claim_text_lower:
                label = "SUPPORTED"
                evidence = ["F1"]
            elif "part a" in claim_text_lower and "hospital" in claim_text_lower:
                label = "SUPPORTED"
                evidence = ["F2"]
            elif "part b" in claim_text_lower and ("doctor" in claim_text_lower or "outpatient" in claim_text_lower):
                label = "SUPPORTED"
                evidence = ["F3"]
            elif "medicare advantage" in claim_text_lower or "part c" in claim_text_lower:
                if "network" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F8"]
                elif "private" in claim_text_lower or "insurance" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F4", "F5"]
                else:
                    label = "SUPPORTED"
                    evidence = ["F5"]
            elif "prescription" in claim_text_lower or "drug" in claim_text_lower or "part d" in claim_text_lower:
                if "advantage" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F6"]
                elif "original medicare" in claim_text_lower or "does not include" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F7"]
            elif "out-of-pocket" in claim_text_lower or "maximum" in claim_text_lower:
                if "advantage" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F10"]
                elif "original medicare" in claim_text_lower and "does not" in claim_text_lower:
                    label = "SUPPORTED"
                    evidence = ["F11"]
            elif "medigap" in claim_text_lower:
                label = "SUPPORTED"
                evidence = ["F11"]
            elif "any doctor" in claim_text_lower or "any provider" in claim_text_lower:
                label = "SUPPORTED"
                evidence = ["F9"]

            verdicts.append(
                {
                    "claim_id": claim.get("claim_id"),
                    "label": label,
                    "evidence": evidence,
                    "severity": severity,
                    "notes": f"Mock verification based on keyword matching",
                }
            )

        return json.dumps({"verdicts": verdicts})

    def _mock_scorer_response(self, messages: list[dict[str, str]]) -> str:
        """Mock scorer (not typically needed - scorer is rule-based)"""
        return json.dumps(
            {
                "ship_classification": "accurate_complete",
                "completeness_percentage": 0.85,
                "accuracy_percentage": 0.95,
                "missing_required_points": [],
                "error_categories": [],
                "harm_categories": [],
                "justification": "Mock scoring result",
            }
        )

    def _mock_adjudicator_response(self, messages: list[dict[str, str]]) -> str:
        """Mock adjudicator (not typically needed - adjudicator is rule-based)"""
        return json.dumps(
            {
                "needs_manual_review": False,
                "disagreement_percentage": 0.05,
                "adjudication_notes": "Mock adjudication",
            }
        )

    def get_model_identifier(self) -> str:
        return "mock-agent-v1.0"

    def supports_seed(self) -> bool:
        return True
