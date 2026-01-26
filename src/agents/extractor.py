"""Claim Extractor Agent - Converts responses into atomic claims"""

import json
from pathlib import Path
from typing import Any

from ..adapters.base import BaseLLMAdapter
from ..schemas import Claim, ClaimExtractionResult, ClaimType
from ..utils import extract_json_from_text


class ExtractorAgent:
    """Extracts atomic, verifiable claims from AI responses"""

    def __init__(self, adapter: BaseLLMAdapter, system_prompt_path: str | None = None):
        """
        Initialize the extractor agent.

        Args:
            adapter: LLM adapter to use for extraction
            system_prompt_path: Path to system prompt file (default: prompts/extractor_system.txt)
        """
        self.adapter = adapter

        if system_prompt_path is None:
            system_prompt_path = "prompts/extractor_system.txt"

        self.system_prompt = self._load_system_prompt(system_prompt_path)

    def _load_system_prompt(self, path: str) -> str:
        """Load system prompt from file"""
        prompt_file = Path(path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"System prompt not found: {path}")
        return prompt_file.read_text()

    async def extract_claims(
        self,
        response_text: str,
        conversation_context: list[str] | None = None,
        seed: int = 42,
    ) -> ClaimExtractionResult:
        """
        Extract claims from a response.

        Args:
            response_text: The AI model's response to analyze
            conversation_context: Optional previous turns for context
            seed: Random seed for reproducibility

        Returns:
            ClaimExtractionResult with list of extracted claims
        """
        # Build input
        user_input = {
            "response_text": response_text,
            "conversation_context": conversation_context or [],
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Extract claims from this response:\n\n{json.dumps(user_input, indent=2)}",
            },
        ]

        # Get response from LLM
        response = await self.adapter.generate(
            messages=messages,
            temperature=0.0,
            seed=seed if self.adapter.supports_seed() else None,
            max_tokens=4096,  # Extraction can be verbose
        )

        # Parse JSON response (handles preamble/postamble text)
        try:
            result = extract_json_from_text(response.content)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse extractor response as JSON: {e}\n{response.content}")

        # Validate and convert to Pydantic models
        if "claims" not in result:
            raise ValueError(f"Extractor output missing 'claims' key: {result}")

        claims = []
        for claim_data in result["claims"]:
            try:
                # Ensure claim_type is valid
                if "claim_type" in claim_data:
                    claim_data["claim_type"] = ClaimType(claim_data["claim_type"])

                claim = Claim(**claim_data)
                claims.append(claim)
            except Exception as e:
                raise ValueError(f"Invalid claim structure: {claim_data}\nError: {e}")

        return ClaimExtractionResult(
            claims=claims,
            extraction_metadata={
                "model": self.adapter.get_model_identifier(),
                "num_claims": len(claims),
                "response_length": len(response_text),
            },
        )
