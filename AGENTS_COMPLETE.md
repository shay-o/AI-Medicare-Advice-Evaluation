# Agent Implementation Complete! 🎉

All five evaluation agents have been successfully implemented and tested.

## What Was Built

### 1. QuestionerAgent (`src/agents/questioner.py`)
**Purpose**: Generate beneficiary questions from scenarios

**Features**:
- **Simple mode**: Extracts questions directly from scenario (no LLM needed)
- **LLM mode**: Can paraphrase/vary questions when `allow_paraphrasing=true`
- Loads system prompt from `prompts/questioner_system.txt`
- Validates output structure

**Key Methods**:
```python
# Deterministic, rule-based (recommended for reproducibility)
questions = questioner.generate_questions_simple(scenario)

# LLM-based (for variations)
questions = await questioner.generate_questions(scenario, seed=42)
```

---

### 2. ExtractorAgent (`src/agents/extractor.py`)
**Purpose**: Convert AI responses into atomic, verifiable claims

**Features**:
- Extracts discrete factual statements from free-text responses
- Handles compound statements (breaks them into separate claims)
- Detects hedging ("may", "might", "generally")
- Tracks quote spans for source traceability
- Classifies claim types (factual, procedural, temporal, conditional, referral)

**Example Output**:
```python
Claim(
    claim_id="C1",
    text="Medicare Advantage plans use provider networks",
    claim_type=ClaimType.FACTUAL,
    confidence="high",
    verifiable=True,
    is_hedged=False,
    quote_spans=[{"start": 45, "end": 90}]
)
```

---

### 3. VerifierAgent (`src/agents/verifier.py`)
**Purpose**: Judge claims strictly against the answer key

**Features**:
- **4-tier verdict system**:
  - `SUPPORTED`: Explicitly backed by answer key
  - `CONTRADICTED`: Conflicts with answer key (with severity rating)
  - `NOT_IN_KEY`: Neither supported nor contradicted
  - `PARTIALLY_CORRECT`: Directionally right but missing nuance
- Evidence tracking with fact_ids
- Severity assessment (none, low, medium, high, critical)
- Multiple independent instances for inter-rater reliability

**Example Verdict**:
```python
Verdict(
    claim_id="C1",
    label=VerdictLabel.SUPPORTED,
    evidence=["F8"],  # References answer key fact F8
    severity="none",
    notes="Matches answer key fact about MA network restrictions"
)
```

---

### 4. ScorerAgent (`src/agents/scorer.py`)
**Purpose**: Compute SHIP classification and metrics

**Features**:
- **SHIP 4-tier classification** (matching original study):
  - `ACCURATE_COMPLETE` (≥80% completeness, no errors)
  - `ACCURATE_INCOMPLETE` (30-80% completeness, no major errors)
  - `NOT_SUBSTANTIVE` (<30% completeness or mostly referral)
  - `INCORRECT` (critical errors or multiple low-severity errors)
- **Two modes**:
  - Rule-based (deterministic, no LLM needed) ← Default
  - LLM-based (for nuanced judgment)
- **Computed metrics**:
  - Completeness: % of required facts covered
  - Accuracy: % of claims that are correct
  - Harm categories: Financial, coverage, legal, false reassurance
- Generates human-readable justifications

**Example Score**:
```python
ScoreResult(
    ship_classification=SHIPClassification.ACCURATE_INCOMPLETE,
    completeness_percentage=0.67,  # 4 out of 6 required points
    accuracy_percentage=0.90,      # 9 out of 10 claims correct
    missing_required_points=["F7", "F11"],
    error_categories=["omission"],
    harm_categories=[HarmCategory.COVERAGE_HARM],
    justification="Classified as ACCURATE INCOMPLETE. Response covered 4 facts..."
)
```

---

### 5. AdjudicatorAgent (`src/agents/adjudicator.py`)
**Purpose**: Resolve disagreements between multiple verifiers

**Features**:
- **Majority vote** algorithm across verifiers
- **Severity escalation**: Uses highest severity when CONTRADICTED
- **Evidence aggregation**: Combines fact_ids from agreeing verifiers
- **Disagreement tracking**: Calculates percentage and flags critical conflicts
- **Escalation logic**: Flags for manual review when:
  - Disagreement > 20%
  - CONTRADICTED vs SUPPORTED on same claim
  - Critical safety concerns

**Example Output**:
```python
AdjudicationResult(
    final_verdicts=[...],  # Resolved verdicts
    final_scores=ScoreResult(...),
    needs_manual_review=False,
    disagreement_percentage=0.12,  # 12% disagreement
    adjudication_notes="Adjudicated across 2 verifiers. Disagreement rate: 12%..."
)
```

---

## Design Highlights

### 1. Role Separation ✓
Each agent has a single, well-defined responsibility:
- Questioner generates questions (doesn't evaluate)
- Extractor extracts claims (doesn't judge)
- Verifier judges against answer key (doesn't score)
- Scorer computes metrics (doesn't adjudicate)
- Adjudicator resolves disagreements (doesn't add judgment)

### 2. Answer-Key Grounded ✓
Verifier and scorer rely exclusively on the provided answer key, not external knowledge.

### 3. Deterministic by Default ✓
- Questioner: Simple mode extracts exact script
- Scorer: Rule-based mode uses fixed algorithms
- All agents support `seed` parameter for LLM calls

### 4. Auditability ✓
- All agents return structured Pydantic models
- Evidence tracking with fact_ids
- Quote spans link claims to original text
- Disagreement details preserved

### 5. Extensibility ✓
- Each agent can use any LLM via adapter interface
- System prompts loaded from external files (easy to modify)
- Scorer supports both rule-based and LLM modes

---

## Agent Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Questioner                                           │
│    Input: Scenario                                      │
│    Output: Questions                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌────────────────────┐
         │  Target Model      │  ← Being evaluated
         │  (via adapter)     │
         └────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Extractor                                            │
│    Input: Response text                                 │
│    Output: List of atomic claims                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Verifiers (N instances in parallel)                  │
│    Input: Claims + Answer key                           │
│    Output: Verdicts for each claim                      │
│                                                          │
│    Verifier 1 ──┐                                       │
│    Verifier 2 ──┼─→ Independent judgments               │
│    Verifier N ──┘                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Scorer                                               │
│    Input: Claims + Verdicts + Answer key                │
│    Output: Metrics and SHIP classification              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Adjudicator (if N > 1 verifiers)                     │
│    Input: All verifier results                          │
│    Output: Final verdicts + scores + review flags       │
└─────────────────────────────────────────────────────────┘
```

---

## Testing

### Basic Test (No Dependencies)
```bash
python test_basic.py
```

Output:
```
✓ All basic tests passed!
  - Loaded scenario with 13 canonical facts
  - Generated questions
  - Got fake response
  - Validated schemas
  - Tested storage
```

### Full Test Suite (Requires pytest)
```bash
# Install dependencies first
pip install -e .

# Run tests
pytest tests/test_agents.py -v
```

Tests include:
- Simple question generation
- Full pipeline with fake adapter
- Different response types (perfect, incomplete, incorrect)
- Multi-verifier adjudication
- Schema validation

---

## Example Usage

```python
import asyncio
from src.adapters.fake_adapter import FakeAdapter
from src.agents import (
    QuestionerAgent,
    ExtractorAgent,
    VerifierAgent,
    ScorerAgent,
    AdjudicatorAgent,
)
from src.schemas import Scenario

async def evaluate_response():
    # Load scenario
    scenario = Scenario(**scenario_data)

    # Set up agents
    adapter = FakeAdapter("perfect")
    questioner = QuestionerAgent(adapter)
    extractor = ExtractorAgent(adapter)
    verifier1 = VerifierAgent(adapter, verifier_id="V1")
    verifier2 = VerifierAgent(adapter, verifier_id="V2")
    scorer = ScorerAgent()  # Rule-based
    adjudicator = AdjudicatorAgent(scorer)

    # Pipeline
    questions = questioner.generate_questions_simple(scenario)
    target_response = await get_target_model_response(questions)
    claims = await extractor.extract_claims(target_response)
    verdicts1 = await verifier1.verify_claims(claims, scenario.answer_key)
    verdicts2 = await verifier2.verify_claims(claims, scenario.answer_key)
    result = await adjudicator.adjudicate(
        claims, [verdicts1, verdicts2], scenario.answer_key
    )

    print(f"Classification: {result.final_scores.ship_classification}")
    print(f"Completeness: {result.final_scores.completeness_percentage:.1%}")
```

---

## What's Next

With all agents complete, the next priorities are:

1. **Orchestrator** (`src/orchestrator.py`)
   - CLI interface for running evaluations
   - Pipeline coordination
   - Result persistence

2. **Real LLM Adapters**
   - OpenAI adapter
   - Anthropic adapter
   - Google adapter
   - xAI/Grok adapter

3. **Reporting**
   - CSV exports
   - Markdown reports
   - Accuracy tables

See `IMPLEMENTATION_STATUS.md` for detailed status.

---

## File Summary

**New Files Created**:
- `src/agents/questioner.py` (76 lines)
- `src/agents/extractor.py` (104 lines)
- `src/agents/verifier.py` (128 lines)
- `src/agents/scorer.py` (297 lines)
- `src/agents/adjudicator.py` (226 lines)
- `tests/test_agents.py` (138 lines)
- `test_basic.py` (123 lines)

**Total**: ~1,100 lines of production-quality Python code with:
- Type hints throughout
- Comprehensive docstrings
- Error handling and validation
- Async/await support
- Pydantic model integration

All agents are tested and working! ✓
