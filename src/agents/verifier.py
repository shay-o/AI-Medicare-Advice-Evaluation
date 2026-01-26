"""Verifier Agent - Judges claims against answer key"""

import json
from pathlib import Path
from typing import Any

from ..adapters.base import BaseLLMAdapter
from ..schemas import AnswerKey, Claim, Verdict, VerdictLabel, VerificationResult
from ..utils import extract_json_from_text


class VerifierAgent:
    """Verifies claims strictly against the provided answer key"""

    def __init__(
        self,
        adapter: BaseLLMAdapter,
        verifier_id: str = "V1",
        system_prompt_path: str | None = None,
    ):
        """
        Initialize the verifier agent.

        Args:
            adapter: LLM adapter to use for verification
            verifier_id: Unique identifier for this verifier instance
            system_prompt_path: Path to system prompt file (default: prompts/verifier_system.txt)
        """
        self.adapter = adapter
        self.verifier_id = verifier_id

        if system_prompt_path is None:
            system_prompt_path = "prompts/verifier_system.txt"

        self.system_prompt = self._load_system_prompt(system_prompt_path)

    def _load_system_prompt(self, path: str) -> str:
        """Load system prompt from file"""
        prompt_file = Path(path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"System prompt not found: {path}")
        return prompt_file.read_text()

    async def verify_claims(
        self,
        claims: list[Claim],
        answer_key: AnswerKey,
        seed: int = 42,
    ) -> VerificationResult:
        """
        Verify claims against the answer key.

        Args:
            claims: List of claims to verify
            answer_key: Ground truth answer key
            seed: Random seed for reproducibility

        Returns:
            VerificationResult with verdicts for each claim
        """
        # Build input
        user_input = {
            "claims": [claim.model_dump() for claim in claims],
            "answer_key": answer_key.model_dump(),
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Verify these claims against the answer key:\n\n{json.dumps(user_input, indent=2)}",
            },
        ]

        # Get response from LLM
        response = await self.adapter.generate(
            messages=messages,
            temperature=0.0,
            seed=seed if self.adapter.supports_seed() else None,
            max_tokens=4096,
        )

        # Parse JSON response (handles preamble/postamble text)
        try:
            result = extract_json_from_text(response.content)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse verifier response as JSON: {e}\n{response.content}")

        # Validate output structure
        if "verdicts" not in result:
            raise ValueError(f"Verifier output missing 'verdicts' key: {result}")

        # Convert to Pydantic models
        verdicts = []
        for verdict_data in result["verdicts"]:
            try:
                # Ensure label is valid
                if "label" in verdict_data:
                    verdict_data["label"] = VerdictLabel(verdict_data["label"])

                verdict = Verdict(**verdict_data)
                verdicts.append(verdict)
            except Exception as e:
                raise ValueError(f"Invalid verdict structure: {verdict_data}\nError: {e}")

        # Ensure we have a verdict for each claim
        claim_ids = {claim.claim_id for claim in claims}
        verdict_claim_ids = {verdict.claim_id for verdict in verdicts}

        if claim_ids != verdict_claim_ids:
            missing = claim_ids - verdict_claim_ids
            extra = verdict_claim_ids - claim_ids
            raise ValueError(
                f"Verdict/claim mismatch. Missing verdicts for: {missing}. Extra verdicts: {extra}"
            )

        return VerificationResult(
            verifier_id=self.verifier_id,
            verdicts=verdicts,
            verification_metadata={
                "model": self.adapter.get_model_identifier(),
                "num_verdicts": len(verdicts),
                "num_facts": len(answer_key.canonical_facts),
            },
        )
