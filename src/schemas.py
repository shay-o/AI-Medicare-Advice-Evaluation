"""Core data schemas for AI Medicare Evaluation Harness"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ============================================================================
# Scenario and Answer Key Schemas
# ============================================================================


class CanonicalFact(BaseModel):
    """A single verifiable fact from the answer key"""

    fact_id: str = Field(..., description="Unique identifier (e.g., 'F1')")
    statement: str = Field(..., description="The factual statement")
    rationale: str = Field(..., description="Why this is true")
    source: str = Field(..., description="Authoritative source reference")
    severity_if_wrong: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Potential harm if this fact is wrong or omitted"
    )


class AnswerKey(BaseModel):
    """Ground truth for evaluating a scenario"""

    canonical_facts: list[CanonicalFact] = Field(
        ..., description="All verifiable facts for this scenario"
    )
    required_points: list[str] = Field(
        ..., description="Fact IDs that must be covered for completeness"
    )
    optional_enrichments: list[str] = Field(
        default_factory=list, description="Fact IDs that improve but aren't required"
    )
    disallowed_claims: list[str] = Field(
        default_factory=list,
        description="Statements that should never be made (e.g., hallucinated specifics)",
    )
    acceptable_referrals: list[str] = Field(
        default_factory=list,
        description="Valid redirects to other resources (e.g., 'Contact plan directly')",
    )


class Persona(BaseModel):
    """Beneficiary persona for the scenario"""

    age: int
    location: str
    current_coverage: str
    situation: str = Field(..., description="Brief description of their circumstances")
    primary_care_physician: str | None = Field(None, description="Name of their PCP for network verification questions")


class ScriptedTurn(BaseModel):
    """A single turn in the conversation script"""

    turn_id: str
    user_message: str
    expected_topics: list[str] = Field(
        default_factory=list, description="Topics that should be addressed"
    )
    conditional_next: dict[str, str] = Field(
        default_factory=dict,
        description="Map of response patterns to next turn_id for branching",
    )


class TemporalValidity(BaseModel):
    """Time bounds for when scenario facts are valid"""

    valid_from: date
    valid_until: date
    notes: str = Field(default="", description="Notes about temporal constraints")


class TargetParameters(BaseModel):
    """Parameters for the target LLM being evaluated"""

    temperature: float = 0.0
    max_tokens: int = 2048
    top_p: float = 1.0
    seed: int | None = None


class DrugCoverage(BaseModel):
    """Drug coverage information for a specific medication"""

    drug_name: str = Field(..., description="Name of the medication")
    is_covered: bool = Field(..., description="Whether the drug is covered")
    tier: int | None = Field(None, description="Formulary tier (1-5)")
    copay: float | None = Field(None, description="Copay amount for this drug")
    prior_authorization_required: bool = Field(default=False)
    quantity_limits: str | None = Field(None, description="Any quantity restrictions")


class PlanInformation(BaseModel):
    """Medicare Advantage plan details for answer key and question substitution.

    NOTE: This information is used ONLY for:
    1. Substituting plan name in questions (e.g., replace [plan name] with actual name)
    2. Answer key verification (what the correct answers should be)

    IMPORTANT: Per SHIP study fidelity, this information is NOT provided to the target
    model as context. The model must respond based on its own knowledge, just as in
    the original study.
    """

    plan_name: str = Field(..., description="Full plan name (e.g., 'Humana Gold Plus HMO')")
    plan_type: Literal["HMO", "PPO", "PFFS", "SNP"] = Field(..., description="Plan type")
    contract_number: str | None = Field(None, description="CMS contract number")
    service_area: str | None = Field(None, description="Geographic service area")

    # Cost information
    monthly_premium: float = Field(..., description="Plan premium (not including Part B)")
    part_b_premium: float | None = Field(None, description="Part B premium for reference")
    deductible: float | None = Field(None, description="Annual deductible")
    max_out_of_pocket: float | None = Field(None, description="Maximum annual out-of-pocket")

    # Provider network and copays
    primary_care_copay: float | None = Field(None, description="In-network PCP visit copay")
    specialist_copay: float | None = Field(None, description="In-network specialist copay")
    out_of_network_allowed: bool = Field(..., description="Whether out-of-network care is allowed")
    out_of_network_primary_care_copay: float | None = Field(None, description="OON PCP copay if applicable")
    out_of_network_specialist_copay: float | None = Field(None, description="OON specialist copay if applicable")

    # Additional coverage
    includes_drug_coverage: bool = Field(..., description="Whether Part D is included")
    drug_formulary: list[DrugCoverage] | None = Field(None, description="Covered medications")
    additional_benefits: list[str] | None = Field(None, description="Extra benefits (dental, vision, etc.)")

    # Other details
    requires_referrals: bool | None = Field(None, description="Whether referrals needed for specialists")
    available_in_service_area: bool = Field(default=True, description="Whether plan is available")


class Scenario(BaseModel):
    """Complete test scenario with persona, questions, and answer key"""

    scenario_id: str
    title: str
    effective_date: date = Field(..., description="When this scenario is valid")
    persona: Persona
    scripted_turns: list[ScriptedTurn]
    variation_knobs: dict[str, Any] = Field(
        default_factory=dict, description="Parameters for generating variations"
    )
    answer_key: AnswerKey | None = None
    plan_information: PlanInformation | None = Field(
        None,
        description="Medicare plan details for question substitution and answer verification. "
        "NOT provided to target model per SHIP study fidelity."
    )
    scoring_rubric: dict[str, Any] | None = Field(
        None, description="Scenario-specific scoring rubric (e.g., SHIP 4-tier classification)"
    )
    rubric_version: str = Field(default="1.0")
    temporal_validity: TemporalValidity | None = None
    target_parameters: TargetParameters = Field(default_factory=TargetParameters)


# ============================================================================
# Conversation and Model Response Schemas
# ============================================================================


class ConversationTurn(BaseModel):
    """A single turn in the conversation with the target model"""

    turn_id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelResponse(BaseModel):
    """Response from an LLM adapter"""

    content: str
    model_identifier: str = Field(..., description="Full model version string")
    tokens_used: dict[str, int] = Field(
        default_factory=dict, description="Token counts: prompt, completion, total"
    )
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Claim Extraction Schemas
# ============================================================================


class ClaimType(str, Enum):
    """Types of claims that can be extracted"""

    FACTUAL = "factual"
    PROCEDURAL = "procedural"  # How to do something
    TEMPORAL = "temporal"  # Time-bound information
    CONDITIONAL = "conditional"  # If-then statements
    REFERRAL = "referral"  # Directing to another resource


class Claim(BaseModel):
    """An atomic, verifiable claim extracted from a response"""

    claim_id: str
    text: str = Field(..., description="The claim in plain language")
    claim_type: ClaimType
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Extractor's confidence this is a distinct claim"
    )
    verifiable: bool = Field(
        ..., description="Whether this can be checked against answer key"
    )
    quote_spans: list[dict[str, int]] = Field(
        default_factory=list, description="Character spans in original response"
    )
    is_hedged: bool = Field(
        default=False, description="Contains qualifiers like 'may', 'might', 'generally'"
    )
    context_dependent: bool = Field(
        default=False, description="Meaning depends on prior conversation context"
    )


class ClaimExtractionResult(BaseModel):
    """Output from the claim extractor agent"""

    claims: list[Claim]
    extraction_metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Verification Schemas
# ============================================================================


class VerdictLabel(str, Enum):
    """Possible verdicts for a claim"""

    SUPPORTED = "SUPPORTED"  # Explicitly supported by answer key
    CONTRADICTED = "CONTRADICTED"  # Contradicts answer key
    NOT_IN_KEY = "NOT_IN_KEY"  # Not covered by answer key
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"  # Missing important nuance


class Verdict(BaseModel):
    """A verifier's judgment of a single claim"""

    claim_id: str
    label: VerdictLabel
    evidence: list[str] = Field(
        default_factory=list, description="Fact IDs from answer key that support verdict"
    )
    severity: Literal["none", "low", "medium", "high", "critical"] = Field(
        default="none", description="Harm risk if label is CONTRADICTED"
    )
    notes: str = Field(default="", description="Explanation of the verdict")


class VerificationResult(BaseModel):
    """Output from a verifier agent"""

    verifier_id: str = Field(..., description="Unique ID for this verifier instance")
    verdicts: list[Verdict]
    verification_metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Scoring Schemas
# ============================================================================


class HarmCategory(str, Enum):
    """Types of potential harm"""

    FINANCIAL_HARM = "financial_harm"
    COVERAGE_HARM = "coverage_harm"
    LEGAL_HARM = "legal_harm"
    FALSE_REASSURANCE = "false_reassurance"


class ScoreResult(BaseModel):
    """Output from the scorer agent"""

    rubric_score: int | None = Field(
        None, description="Numeric score from scenario rubric (e.g., 1-4 for SHIP)"
    )
    rubric_label: str | None = Field(
        None, description="Human-readable label from rubric (e.g., 'Accurate and Complete')"
    )
    completeness_percentage: float = Field(
        ..., ge=0.0, le=1.0, description="% of required_points covered"
    )
    accuracy_percentage: float = Field(
        ..., ge=0.0, le=1.0, description="% of claims that are correct"
    )
    missing_required_points: list[str] = Field(default_factory=list)
    error_categories: list[str] = Field(default_factory=list)
    harm_categories: list[HarmCategory] = Field(default_factory=list)
    justification: str = Field(..., description="Explanation of the classification")


# ============================================================================
# Adjudication Schemas
# ============================================================================


class AdjudicationResult(BaseModel):
    """Output from the adjudicator agent"""

    final_claims: list[Claim]
    final_verdicts: list[Verdict]
    final_scores: ScoreResult
    needs_manual_review: bool = Field(
        default=False, description="Whether inter-verifier disagreement was too high"
    )
    disagreement_percentage: float = Field(
        default=0.0, description="% of claims with verifier disagreement"
    )
    adjudication_notes: str = Field(default="")


# ============================================================================
# Trial Result Schema
# ============================================================================


class TrialFlags(BaseModel):
    """Special conditions detected during the trial"""

    refusal: bool = Field(default=False, description="Model refused to answer")
    hallucinated_specifics: bool = Field(
        default=False, description="Made up specific details not in answer key"
    )
    asked_clarifying_questions: bool = Field(
        default=False, description="Model asked for more information"
    )
    referenced_external_resources: bool = Field(
        default=False, description="Directed user to official resources"
    )


class TargetModelInfo(BaseModel):
    """Information about the model being evaluated"""

    provider: str
    model_name: str
    model_version: str | None = None
    parameters: TargetParameters


class TrialResult(BaseModel):
    """Complete result of a single evaluation trial"""

    trial_id: str
    scenario_id: str
    target: TargetModelInfo
    conversation: list[ConversationTurn]
    claims: list[Claim]
    verifications: list[VerificationResult]
    final_scores: ScoreResult
    flags: TrialFlags
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
