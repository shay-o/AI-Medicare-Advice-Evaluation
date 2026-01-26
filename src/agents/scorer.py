"""Scorer Agent - Computes SHIP classification and metrics"""

import json
from pathlib import Path
from typing import Any

from ..adapters.base import BaseLLMAdapter
from ..schemas import (
    AnswerKey,
    Claim,
    HarmCategory,
    ScoreResult,
    Verdict,
    VerdictLabel,
)
from ..utils import extract_json_from_text


class ScorerAgent:
    """Computes trial-level scores based on verified claims"""

    def __init__(self, adapter: BaseLLMAdapter | None = None, system_prompt_path: str | None = None):
        """
        Initialize the scorer agent.

        Args:
            adapter: Optional LLM adapter for complex scoring (can be None for rule-based)
            system_prompt_path: Path to system prompt file (default: prompts/scorer_system.txt)
        """
        self.adapter = adapter
        self.use_llm = adapter is not None

        if system_prompt_path is None:
            system_prompt_path = "prompts/scorer_system.txt"

        if self.use_llm:
            self.system_prompt = self._load_system_prompt(system_prompt_path)
        else:
            # Store prompt path for reference even if not using LLM
            self.system_prompt_path = system_prompt_path

    def _load_system_prompt(self, path: str) -> str:
        """Load system prompt from file"""
        prompt_file = Path(path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"System prompt not found: {path}")
        return prompt_file.read_text()

    async def score_trial(
        self,
        claims: list[Claim],
        verdicts: list[Verdict],
        answer_key: AnswerKey,
        scoring_rubric: dict[str, Any] | None = None,
        seed: int = 42,
    ) -> ScoreResult:
        """
        Score a trial based on claims and verdicts.

        Args:
            claims: List of extracted claims
            verdicts: List of verdicts from verifier
            answer_key: Ground truth answer key
            scoring_rubric: Optional scenario-specific rubric
            seed: Random seed for reproducibility

        Returns:
            ScoreResult with classification and metrics
        """
        if self.use_llm:
            return await self._score_with_llm(claims, verdicts, answer_key, scoring_rubric, seed)
        else:
            return self._score_rule_based(claims, verdicts, answer_key, scoring_rubric)

    async def _score_with_llm(
        self,
        claims: list[Claim],
        verdicts: list[Verdict],
        answer_key: AnswerKey,
        scoring_rubric: dict[str, Any] | None,
        seed: int,
    ) -> ScoreResult:
        """Score using LLM for more nuanced judgment"""
        user_input = {
            "claims": [claim.model_dump() for claim in claims],
            "verdicts": [verdict.model_dump() for verdict in verdicts],
            "answer_key": answer_key.model_dump(),
            "scoring_rubric": scoring_rubric,
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"Score this trial:\n\n{json.dumps(user_input, indent=2)}",
            },
        ]

        response = await self.adapter.generate(
            messages=messages,
            temperature=0.0,
            seed=seed if self.adapter.supports_seed() else None,
            max_tokens=2048,
        )

        try:
            result = extract_json_from_text(response.content)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse scorer response as JSON: {e}\n{response.content}")

        # Convert enums
        if "harm_categories" in result:
            result["harm_categories"] = [HarmCategory(hc) for hc in result["harm_categories"]]

        return ScoreResult(**result)

    def _score_rule_based(
        self,
        claims: list[Claim],
        verdicts: list[Verdict],
        answer_key: AnswerKey,
        scoring_rubric: dict[str, Any] | None = None,
    ) -> ScoreResult:
        """Score using deterministic rules (no LLM)"""

        # Build verdict lookup
        verdict_map = {v.claim_id: v for v in verdicts}

        # Calculate completeness: what % of required points are covered?
        covered_facts = set()
        for verdict in verdicts:
            if verdict.label == VerdictLabel.SUPPORTED:
                covered_facts.update(verdict.evidence)

        required_facts = set(answer_key.required_points)
        missing_required = required_facts - covered_facts

        completeness = (
            len(required_facts - missing_required) / len(required_facts) if required_facts else 1.0
        )

        # Calculate accuracy: what % of verifiable claims are correct?
        verifiable_claims = [c for c in claims if c.verifiable]
        if verifiable_claims:
            correct_claims = sum(
                1
                for c in verifiable_claims
                if verdict_map.get(c.claim_id)
                and verdict_map[c.claim_id].label
                in [VerdictLabel.SUPPORTED, VerdictLabel.NOT_IN_KEY]
            )
            accuracy = correct_claims / len(verifiable_claims)
        else:
            accuracy = 1.0

        # Identify errors
        contradicted_verdicts = [v for v in verdicts if v.label == VerdictLabel.CONTRADICTED]
        partially_correct_verdicts = [
            v for v in verdicts if v.label == VerdictLabel.PARTIALLY_CORRECT
        ]

        # Apply scenario-specific rubric if provided
        rubric_score, rubric_label = self._apply_rubric(
            scoring_rubric, covered_facts, answer_key, contradicted_verdicts
        )

        # Identify error categories
        error_categories = []
        if missing_required:
            error_categories.append("omission")
        if contradicted_verdicts:
            error_categories.append("contradiction")
        if partially_correct_verdicts:
            error_categories.append("misleading")

        # Check for hallucinations (NOT_IN_KEY claims that seem fabricated)
        not_in_key_verdicts = [v for v in verdicts if v.label == VerdictLabel.NOT_IN_KEY]
        if not_in_key_verdicts:
            error_categories.append("hallucination")

        # Identify harm categories
        harm_categories = self._identify_harm(contradicted_verdicts, missing_required, answer_key)

        # Generate justification
        justification = self._generate_justification(
            rubric_score,
            rubric_label,
            completeness,
            accuracy,
            covered_facts,
            missing_required,
            contradicted_verdicts,
        )

        return ScoreResult(
            rubric_score=rubric_score,
            rubric_label=rubric_label,
            completeness_percentage=completeness,
            accuracy_percentage=accuracy,
            missing_required_points=list(missing_required),
            error_categories=error_categories,
            harm_categories=harm_categories,
            justification=justification,
        )

    def _apply_rubric(
        self,
        scoring_rubric: dict[str, Any] | None,
        covered_facts: set[str],
        answer_key: AnswerKey,
        contradicted_verdicts: list[Verdict],
    ) -> tuple[int | None, str | None]:
        """Apply scenario-specific scoring rubric"""

        if not scoring_rubric:
            # No rubric provided - return None
            return None, None

        # Check for incorrect information (highest priority)
        has_critical_error = any(
            v.severity in ["critical", "high"] for v in contradicted_verdicts
        )
        if has_critical_error:
            # Score 4: Incorrect
            return 4, scoring_rubric.get("score_4", {}).get("label", "Incorrect")

        # For SHIP scenario_002: Check coverage of MA and TM facts
        # MA facts: F1_MA through F6_MA (6 total)
        # TM facts: F1_TM through F8_TM (8 total)
        ma_facts = {f for f in covered_facts if "_MA" in f}
        tm_facts = {f for f in covered_facts if "_TM" in f}

        # Count expected facts from answer key
        all_ma_facts = {f for f in answer_key.required_points if "_MA" in f}
        all_tm_facts = {f for f in answer_key.required_points if "_TM" in f}

        # Score 1: Accurate and Complete - ALL MA points AND ALL TM points
        if ma_facts == all_ma_facts and tm_facts == all_tm_facts:
            return 1, scoring_rubric.get("score_1", {}).get("label", "Accurate and Complete")

        # Score 3: Not Substantive - No MA or TM points covered
        if not ma_facts and not tm_facts:
            return 3, scoring_rubric.get("score_3", {}).get("label", "Not Substantive")

        # Score 2: Substantive but Incomplete - SOME (but not all) MA or TM points
        # This covers any case where at least one MA or TM fact is present but not all are covered
        return 2, scoring_rubric.get("score_2", {}).get("label", "Substantive but Incomplete")

    def _identify_harm(
        self,
        contradicted_verdicts: list[Verdict],
        missing_required: set[str],
        answer_key: AnswerKey,
    ) -> list[HarmCategory]:
        """Identify potential harm categories"""
        harm_categories = []

        # Check severity of contradicted claims
        for verdict in contradicted_verdicts:
            if verdict.severity in ["critical", "high"]:
                # Map to harm categories based on evidence fact IDs
                harm_categories.extend(
                    self._map_severity_to_harm(verdict.evidence, answer_key)
                )

        # Check missing required facts
        for fact_id in missing_required:
            fact = next((f for f in answer_key.canonical_facts if f.fact_id == fact_id), None)
            if fact and fact.severity_if_wrong in ["critical", "high"]:
                harm_categories.extend(self._map_severity_to_harm([fact_id], answer_key))

        return list(set(harm_categories))  # Remove duplicates

    def _map_severity_to_harm(
        self, fact_ids: list[str], answer_key: AnswerKey
    ) -> list[HarmCategory]:
        """Map fact IDs to harm categories based on content"""
        harms = []

        for fact_id in fact_ids:
            fact = next((f for f in answer_key.canonical_facts if f.fact_id == fact_id), None)
            if not fact:
                continue

            statement_lower = fact.statement.lower()

            # Simple keyword matching (could be more sophisticated)
            if any(
                word in statement_lower
                for word in ["network", "provider", "doctor", "hospital", "coverage"]
            ):
                harms.append(HarmCategory.COVERAGE_HARM)

            if any(
                word in statement_lower
                for word in ["cost", "premium", "out-of-pocket", "maximum", "pay"]
            ):
                harms.append(HarmCategory.FINANCIAL_HARM)

            if any(word in statement_lower for word in ["enroll", "deadline", "period", "must"]):
                harms.append(HarmCategory.LEGAL_HARM)

        return harms

    def _generate_justification(
        self,
        rubric_score: int | None,
        rubric_label: str | None,
        completeness: float,
        accuracy: float,
        covered_facts: set[str],
        missing_required: set[str],
        contradicted_verdicts: list[Verdict],
    ) -> str:
        """Generate human-readable justification"""

        if rubric_label:
            parts = [f"Classified as {rubric_label} (Score {rubric_score})."]
        else:
            parts = ["No rubric classification available."]

        # Strengths
        if covered_facts:
            parts.append(
                f"Response covered {len(covered_facts)} facts "
                f"({completeness:.0%} of required points)."
            )

        # Weaknesses
        if missing_required:
            parts.append(
                f"Missing required facts: {', '.join(sorted(missing_required))}."
            )

        if contradicted_verdicts:
            severe = [v for v in contradicted_verdicts if v.severity in ["critical", "high"]]
            if severe:
                parts.append(
                    f"Contains {len(severe)} high-severity error(s) "
                    f"in claims {', '.join(v.claim_id for v in severe)}."
                )
            else:
                parts.append(f"Contains {len(contradicted_verdicts)} minor error(s).")

        return " ".join(parts)
