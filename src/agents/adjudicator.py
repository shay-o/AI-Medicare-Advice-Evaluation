"""Adjudicator Agent - Resolves disagreements between verifiers"""

from collections import Counter
from typing import Any

from ..schemas import (
    AnswerKey,
    AdjudicationResult,
    Claim,
    ScoreResult,
    Verdict,
    VerdictLabel,
    VerificationResult,
)
from .scorer import ScorerAgent


class AdjudicatorAgent:
    """Resolves disagreements between multiple verifier instances"""

    def __init__(self, scorer: ScorerAgent, disagreement_threshold: float = 0.20):
        """
        Initialize the adjudicator agent.

        Args:
            scorer: Scorer agent to compute final scores
            disagreement_threshold: Max disagreement rate before manual review (default: 0.20)
        """
        self.scorer = scorer
        self.disagreement_threshold = disagreement_threshold

    async def adjudicate(
        self,
        claims: list[Claim],
        verifications: list[VerificationResult],
        answer_key: AnswerKey,
        scoring_rubric: dict[str, Any] | None = None,
        seed: int = 42,
    ) -> AdjudicationResult:
        """
        Adjudicate between multiple verifier results.

        Args:
            claims: List of extracted claims
            verifications: List of verification results from different verifiers
            answer_key: Ground truth answer key
            scoring_rubric: Optional scenario-specific scoring rubric
            seed: Random seed for scorer

        Returns:
            AdjudicationResult with final verdicts and scores
        """
        if not verifications:
            raise ValueError("No verifications provided for adjudication")

        if len(verifications) == 1:
            # Single verifier - no adjudication needed
            return AdjudicationResult(
                final_claims=claims,
                final_verdicts=verifications[0].verdicts,
                final_scores=await self.scorer.score_trial(
                    claims, verifications[0].verdicts, answer_key, scoring_rubric, seed
                ),
                needs_manual_review=False,
                disagreement_percentage=0.0,
                adjudication_notes="Single verifier - no adjudication required.",
            )

        # Resolve verdicts across multiple verifiers
        final_verdicts, disagreement_info = self._resolve_verdicts(claims, verifications)

        # Calculate disagreement percentage
        disagreement_percentage = disagreement_info["disagreement_count"] / len(claims)

        # Determine if manual review is needed
        needs_manual_review = self._needs_manual_review(
            disagreement_percentage, disagreement_info
        )

        # Compute final scores
        final_scores = await self.scorer.score_trial(claims, final_verdicts, answer_key, scoring_rubric, seed)

        # Generate adjudication notes
        adjudication_notes = self._generate_notes(
            len(verifications), disagreement_percentage, disagreement_info
        )

        return AdjudicationResult(
            final_claims=claims,
            final_verdicts=final_verdicts,
            final_scores=final_scores,
            needs_manual_review=needs_manual_review,
            disagreement_percentage=disagreement_percentage,
            adjudication_notes=adjudication_notes,
        )

    def _resolve_verdicts(
        self, claims: list[Claim], verifications: list[VerificationResult]
    ) -> tuple[list[Verdict], dict[str, Any]]:
        """
        Resolve verdicts using majority vote.

        Returns:
            Tuple of (final_verdicts, disagreement_info)
        """
        # Build verdict map: claim_id -> list of verdicts
        verdict_map: dict[str, list[Verdict]] = {claim.claim_id: [] for claim in claims}

        for verification in verifications:
            for verdict in verification.verdicts:
                if verdict.claim_id in verdict_map:
                    verdict_map[verdict.claim_id].append(verdict)

        final_verdicts = []
        disagreement_count = 0
        total_disagreement_claims = []
        critical_disagreements = []

        for claim in claims:
            verdicts_for_claim = verdict_map[claim.claim_id]

            if not verdicts_for_claim:
                raise ValueError(f"No verdicts found for claim {claim.claim_id}")

            # Check for unanimous agreement
            labels = [v.label for v in verdicts_for_claim]
            label_counts = Counter(labels)
            most_common_label, count = label_counts.most_common(1)[0]

            # Check if unanimous
            is_unanimous = count == len(verdicts_for_claim)

            if not is_unanimous:
                disagreement_count += 1
                total_disagreement_claims.append(claim.claim_id)

            # Check for critical disagreement (CONTRADICTED vs SUPPORTED)
            has_critical_disagreement = (
                VerdictLabel.CONTRADICTED in labels and VerdictLabel.SUPPORTED in labels
            )

            if has_critical_disagreement:
                critical_disagreements.append(
                    {
                        "claim_id": claim.claim_id,
                        "labels": [label.value for label in labels],
                    }
                )

            # Use majority vote for label
            winning_label = most_common_label

            # For CONTRADICTED verdicts, use HIGHEST severity
            if winning_label == VerdictLabel.CONTRADICTED:
                severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}
                severities = [
                    v.severity for v in verdicts_for_claim if v.label == VerdictLabel.CONTRADICTED
                ]
                winning_severity = max(severities, key=lambda s: severity_order.get(s, 0))
            else:
                winning_severity = "none"

            # Aggregate evidence from all verifiers that agreed with winning label
            evidence = []
            notes_parts = []

            for verdict in verdicts_for_claim:
                if verdict.label == winning_label:
                    evidence.extend(verdict.evidence)
                    if verdict.notes:
                        notes_parts.append(verdict.notes)

            # Remove duplicate evidence
            evidence = list(set(evidence))

            # Combine notes
            combined_notes = " | ".join(notes_parts) if notes_parts else ""

            # Add disagreement info to notes if not unanimous
            if not is_unanimous:
                label_summary = ", ".join(f"{label.value}:{count}" for label, count in label_counts.items())
                combined_notes = (
                    f"[Disagreement: {label_summary}] {combined_notes}".strip()
                )

            final_verdicts.append(
                Verdict(
                    claim_id=claim.claim_id,
                    label=winning_label,
                    evidence=evidence,
                    severity=winning_severity,
                    notes=combined_notes,
                )
            )

        disagreement_info = {
            "disagreement_count": disagreement_count,
            "disagreement_claims": total_disagreement_claims,
            "critical_disagreements": critical_disagreements,
        }

        return final_verdicts, disagreement_info

    def _needs_manual_review(
        self, disagreement_percentage: float, disagreement_info: dict[str, Any]
    ) -> bool:
        """Determine if manual review is needed"""

        # High overall disagreement
        if disagreement_percentage > self.disagreement_threshold:
            return True

        # Any critical disagreements (CONTRADICTED vs SUPPORTED)
        if disagreement_info["critical_disagreements"]:
            return True

        return False

    def _generate_notes(
        self,
        num_verifiers: int,
        disagreement_percentage: float,
        disagreement_info: dict[str, Any],
    ) -> str:
        """Generate human-readable adjudication notes"""

        parts = [f"Adjudicated across {num_verifiers} verifiers."]

        parts.append(f"Disagreement rate: {disagreement_percentage:.1%}.")

        if disagreement_percentage <= 0.10:
            parts.append("Strong consensus across verifiers.")
        elif disagreement_percentage <= self.disagreement_threshold:
            parts.append("Moderate consensus - majority vote applied.")
        else:
            parts.append("High disagreement - flagged for manual review.")

        if disagreement_info["critical_disagreements"]:
            critical_claims = [
                d["claim_id"] for d in disagreement_info["critical_disagreements"]
            ]
            parts.append(
                f"Critical disagreements (CONTRADICTED vs SUPPORTED) on claims: "
                f"{', '.join(critical_claims)}."
            )

        if disagreement_info["disagreement_claims"]:
            parts.append(
                f"Total claims with disagreement: "
                f"{len(disagreement_info['disagreement_claims'])}."
            )

        return " ".join(parts)
