# SHIP Study Methodology Comparison

**Date:** January 24, 2026
**Reference:** Dugan K et al. JAMA Network Open. 2025;8(4):e252834
**Purpose:** Document differences between our AI evaluation implementation and the original SHIP mystery-shopper study methodology

---

## Executive Summary

Our current implementation captures the **spirit** of the SHIP study but differs in several **critical dimensions** that affect methodology validity. The most significant gap is the absence of **plan-specific lookup testing**, which distinguishes between "knowing about Medicare" and "being able to help someone make decisions."

**Key Finding:** scenario_001.json tests general knowledge breadth; scenario_002.json aligns with SHIP methodology for a single question; full SHIP alignment requires 16 sequential questions with plan-specific lookups.

---

## Comparison: scenario_001.json vs scenario_002.json vs SHIP Study

### Scenario Structure

| Dimension | scenario_001.json | scenario_002.json | SHIP Study (Full) |
|-----------|-------------------|-------------------|-------------------|
| **Number of questions** | 1 broad question | 1 specific question | 16 sequential questions |
| **Question source** | Synthetic | SHIP Question #3 (exact) | eAppendix 1 Questions #1-16 |
| **Topic coverage** | TM vs MA comparison | TM vs MA comparison | Comprehensive Medicare knowledge |
| **Persona specificity** | Generic (age, state) | Detailed (city/zip/county) | Very specific (actual plan/doctor) |
| **Expected response** | General knowledge | Both advantages AND disadvantages | Mix of general + specific lookups |

### Answer Key Structure

| Dimension | scenario_001.json | scenario_002.json | SHIP Study |
|-----------|-------------------|-------------------|------------|
| **Total canonical facts** | 13 facts | 14 facts (6 MA + 8 TM) | Varies by question |
| **Required for "complete"** | 6 facts | All 14 facts | All checklist items per question |
| **Scoring rubric** | Binary (required vs optional) | 4-level SHIP rubric | 4-level per question group |
| **Fact categories** | Mixed topics | Separated MA vs TM | Per question topic |

### Critical Differences

#### 1. **Question Progression** ❌ CRITICAL GAP

**SHIP Study:**
- 16 sequential questions that build on each other
- Questions #1-6: General knowledge (enrollment, plan types, coverage)
- Questions #7-15: Plan-specific lookups (network, costs, drugs)
- Question #16: Accessibility (translation services)

**Our Implementation:**
- scenario_001: Single broad question
- scenario_002: Single question (matches SHIP #3)
- ❌ **Missing:** Questions #1-2, #4-16

**Impact:** Cannot assess breadth of knowledge across multiple domains or ability to handle sequential questioning.

---

#### 2. **Persona Specificity & Lookup Requirements** ❌ CRITICAL GAP

**SHIP Study Persona Details:**
```
Location: Specific city, state, zip code, county (from shop confirmation)
Doctor: Actual doctor name (from shop confirmation)
Plan: Specific plan name (from shop confirmation) - e.g., "Humana Gold Plus H1036-178"
Medications: Lipitor 10mg daily
Income: $1,600/month (dual-eligible scenario)
```

**scenario_001.json:**
```json
{
  "age": 64,
  "location": "Florida",
  "current_coverage": "Employer-sponsored insurance",
  "situation": "Retiring soon, first time enrolling in Medicare"
}
```

**scenario_002.json:**
```json
{
  "age": 64,
  "location": {
    "city": "Miami",
    "state": "FL",
    "zip_code": "33166",
    "county": "Miami-Dade County"
  },
  "medications": ["Lipitor 10mg daily"],
  "primary_care_physician": "Generic - to be specified in plan-specific scenarios"
}
```

**Gap Analysis:**
- ✅ scenario_002 adds zip code (enables plan lookup)
- ❌ **Missing:** Specific plan name for Questions #7-15
- ❌ **Missing:** Specific doctor name for Question #7
- ❌ **Impact:** Cannot test Questions #7-15 which require actual Medicare.gov Plan Finder lookups

**Example SHIP Question #7 (Plan-Specific):**
> "My friend told me about [Humana Gold Plus H1036-178]. Can you tell me if [Dr. Maria Rodriguez] is in the network there?"

This requires:
1. Looking up the actual plan in Medicare.gov Plan Finder
2. Checking provider network for that specific plan
3. Verifying the specific doctor is listed

**Our Current Capability:** ❌ Cannot evaluate this dimension

---

#### 3. **Scoring Granularity** ❌ CRITICAL GAP

**SHIP Study Scoring:**
- 20 question groups scored independently
- Each group uses 4-level rubric:
  1. **Accurate and Complete** - All required elements present
  2. **Substantive but Incomplete** - Some required elements present
  3. **Not Substantive** - No meaningful answer or "I don't know"
  4. **Incorrect** - Wrong information that could affect decisions

**Example from Question Group 10 (SHIP eAppendix 4):**

```
Accurate and Complete if:
  - Question 55: mentions items 1 AND 2 AND 3 AND 4 AND 5 AND 6 (all MA points)
  - AND
  - Question 58: mentions items 1 AND 2 AND 3 AND 4 AND 5 AND 6 AND 7 AND 8 (all TM points)

Substantive but Incomplete if:
  - Question 55: mentions item 1 OR 2 OR 3 OR 4 OR 5 OR 6 (any MA point)
  - OR
  - Question 58: mentions item 1 OR 2 OR 3 OR 4 OR 5 OR 6 OR 7 OR 8 (any TM point)
```

**Our Implementation:**
- scenario_001: Overall response scored on fact coverage
- scenario_002: Includes SHIP rubric in `scoring_rubric` field
- ✅ scenario_002 aligns with SHIP for this question
- ❌ **Missing:** Per-question scoring for Questions #1-2, #4-16

---

#### 4. **Question Type Mix** ❌ CRITICAL GAP

**SHIP Study Question Types:**

| Question # | Type | Example | Requires Lookup? |
|------------|------|---------|------------------|
| #1 | General | When can I select/change Medicare coverage? | No |
| #2 | General | Do I have to sign up at 65 or stay on employer plan? | No |
| #3 | General | How is MA different from TM? Pros/cons? | No |
| #4 | General | What is Medigap? Cost? When to enroll? | No |
| #5 | General | Does TM/MA/Medigap cover long-term care? | No |
| #6 | General | Prescription drug options? How to choose? | No |
| #7 | **Specific** | Is [Dr. Smith] in [Plan X] network? | **Yes** |
| #8 | **Specific** | What is monthly premium for [Plan X]? | **Yes** |
| #9 | **Specific** | Does [Plan X] allow out-of-network? | **Yes** |
| #10 | **Specific** | PCP copay for [Plan X]? | **Yes** |
| #11 | **Specific** | Specialist copay for [Plan X]? | **Yes** |
| #12 | **Specific** | Out-of-pocket max for [Plan X]? | **Yes** |
| #13 | **Specific** | Does [Plan X] include drug coverage? | **Yes** |
| #14 | **Specific** | Is Lipitor covered by [Plan X]? Generic? | **Yes** |
| #15 | **Specific** | Cost of Lipitor vs generic in [Plan X]? | **Yes** |
| #16 | Accessibility | Spanish translation services available? | No |

**Our Implementation:**
- scenario_001: General knowledge only (similar to SHIP #3)
- scenario_002: General knowledge only (exact SHIP #3)
- ❌ **Missing:** All plan-specific lookup questions (#7-15)

**Impact:** We test "knowledge about Medicare" but not "ability to help someone make a decision"

---

## Implementation Gaps & Recommendations

### Gap 1: Multi-Turn Sequential Questioning

**Current State:** Single-turn evaluation
**SHIP Methodology:** 16-turn conversation with specific order
**Severity:** ❌ CRITICAL

**Recommendation:**
```
Create scenario_003.json: "SHIP Medicare-Only Full Sequence"
- Include all 16 questions from eAppendix 1
- Maintain strict question order
- Score each question independently (20 question groups)
```

**Implementation Changes Needed:**
1. Update `Scenario` schema to support multiple turns:
```python
class Scenario(BaseModel):
    scripted_turns: list[ScriptedTurn]  # Currently supports this ✅
```

2. Update `QuestionerAgent` to iterate through turns:
```python
# Already supported - just need multi-turn scenarios ✅
```

3. Update `ScorerAgent` to score per-turn:
```python
class TurnScore(BaseModel):
    turn_id: str
    score_level: Literal["accurate_complete", "substantive_incomplete", "not_substantive", "incorrect"]
    facts_covered: list[str]
    facts_missing: list[str]
    rationale: str

class TrialResult(BaseModel):
    turn_scores: list[TurnScore]  # Add this ✅
    overall_score: ScoreResult     # Keep this for summary
```

**Effort:** Medium (1-2 days) - Schema supports this, just need scoring logic update

---

### Gap 2: Plan-Specific Lookup Testing

**Current State:** Generic personas only
**SHIP Methodology:** Actual plan/doctor names requiring Medicare.gov lookups
**Severity:** ❌ CRITICAL

**Recommendation:**
```
Create scenario_004.json: "SHIP Plan-Specific Lookups (Questions #7-15)"
- Specific plan: "Humana Gold Plus H1036-178" (or current year equivalent)
- Specific doctor: "Dr. Maria Rodriguez" (fictional but verifiable via plan network)
- Zip code: 33166 (Miami-Dade County, FL)
- Include correct answers from Medicare.gov Plan Finder
```

**Example Answer Key for Question #7:**
```json
{
  "fact_id": "F7_NETWORK",
  "statement": "Dr. Maria Rodriguez is in the network for Humana Gold Plus H1036-178 in zip code 33166",
  "verification_source": "Medicare.gov Plan Finder, accessed 2024-01-15",
  "verification_url": "https://www.medicare.gov/plan-compare/",
  "correct_answer": "Yes, Dr. Maria Rodriguez is in network",
  "acceptable_answers": [
    "Yes, the doctor is in network",
    "Yes, but you should verify directly with the plan",
    "According to Medicare.gov, yes"
  ],
  "incorrect_answers": [
    "No, the doctor is not in network",
    "I don't have access to that information" (should offer to show how to look it up)
  ]
}
```

**Implementation Changes Needed:**
1. Add verification data to answer keys:
```python
class CanonicalFact(BaseModel):
    # ... existing fields ...
    verification_source: str | None = None
    verification_date: date | None = None
    correct_answer: str | None = None  # For lookup questions
    acceptable_answer_patterns: list[str] = []
    incorrect_answer_patterns: list[str] = []
```

2. Update `VerifierAgent` to handle lookup-based facts:
```python
# Need to distinguish between:
# - General knowledge facts (verify against statement)
# - Lookup facts (verify against correct_answer)
```

**Effort:** High (3-5 days) - Requires gathering 2024 plan data from Medicare.gov

---

### Gap 3: Per-Question Scoring with SHIP Rubric

**Current State:** Overall response scoring
**SHIP Methodology:** 20 question groups, each scored independently
**Severity:** ❌ CRITICAL

**Recommendation:**
```
Update ScorerAgent to implement per-question scoring:
- For each turn in multi-turn scenarios
- Apply the 4-level SHIP rubric
- Track completeness and accuracy separately
- Generate summary scores across all questions
```

**Implementation Changes Needed:**

1. Update scoring logic in `ScorerAgent`:
```python
def score_turn(
    self,
    turn: ScriptedTurn,
    response: str,
    verdicts: list[Verdict],
    answer_key: AnswerKey
) -> TurnScore:
    """
    Score a single question/turn using SHIP 4-level rubric.

    Returns:
        TurnScore with level:
        - "accurate_complete": All required facts covered correctly
        - "substantive_incomplete": Some required facts covered
        - "not_substantive": No meaningful answer
        - "incorrect": Wrong information that could affect decisions
    """
    # Count facts covered vs required for this turn
    turn_required_facts = turn.scoring_metadata.get("required_facts", [])
    facts_covered = [v for v in verdicts if v.label == "SUPPORTED"]

    if len(facts_covered) == len(turn_required_facts):
        return TurnScore(level="accurate_complete", ...)
    elif len(facts_covered) > 0:
        return TurnScore(level="substantive_incomplete", ...)
    elif has_incorrect_facts(verdicts):
        return TurnScore(level="incorrect", ...)
    else:
        return TurnScore(level="not_substantive", ...)
```

2. Update `ScoreResult` schema:
```python
class ScoreResult(BaseModel):
    classification: SHIPClassification
    turn_scores: list[TurnScore]  # Add per-turn scores
    overall_completeness: float
    overall_accuracy: float
    # ... existing fields ...
```

**Effort:** Medium (2-3 days) - Logic exists, needs refactoring

---

### Gap 4: Dual-Eligible Scenario

**Current State:** Medicare-only scenarios
**SHIP Methodology:** Separate dual-eligible scenario (8 questions)
**Severity:** 🟨 HIGH (not critical for initial validation)

**Recommendation:**
```
Create scenario_005.json: "SHIP Dual-Eligible Scenario"
- Based on eAppendix 2 (8 questions)
- Tests understanding of:
  - D-SNPs (Dual-Eligible Special Needs Plans)
  - Medicaid/Medicare coordination
  - Medicare Savings Programs (QMB, SLMB)
  - Extra Help for Part D
```

**Effort:** Medium (2-3 days) - Similar to Medicare-only but different topics

---

### Gap 5: Temporal Validity & Plan Data Currency

**Current State:** Static scenarios for 2024
**SHIP Methodology:** Year-specific plan data that changes annually
**Severity:** 🟨 HIGH

**Recommendation:**
1. Add year-specific plan data files:
```
reference_material/
  medicare_plans_2024/
    plan_H1036-178_details.json
    plan_H1036-178_network.json
    plan_H1036-178_formulary.json
```

2. Update scenarios to reference plan data version:
```json
{
  "temporal_validity": {
    "valid_from": "2024-01-01",
    "valid_until": "2024-12-31",
    "plan_data_source": "Medicare.gov Plan Finder 2024",
    "plan_data_accessed": "2024-01-15"
  }
}
```

**Effort:** High (ongoing) - Requires annual updates

---

## Acceptable Variations from SHIP Study

These differences are acceptable for AI evaluation and don't compromise methodology:

### 1. ✅ Single-Turn vs Multi-Turn Dialogue Flow

**SHIP Study:** Mystery shoppers have natural back-and-forth
**Our Implementation:** AI provides comprehensive single response
**Why Acceptable:** AIs can provide complete answers upfront; human counselors need iterative questioning

### 2. ✅ Opening Statement

**SHIP Study:** "I am turning 65 soon and will be eligible for Medicare. I would like help choosing my coverage. Can you help?"
**Our Implementation:** Context is implicit in question
**Why Acceptable:** Doesn't materially change information requirements

### 3. ✅ Questionnaire Complexity

**SHIP Study:** 100+ question survey filled by mystery shoppers
**Our Implementation:** Automated claim extraction and verification
**Why Acceptable:** Our ExtractorAgent + VerifierAgent replicate the scoring function

### 4. ✅ Test Setting

**SHIP Study:** Phone or face-to-face counseling
**Our Implementation:** Text-based AI evaluation
**Why Acceptable:** Different modality, same knowledge requirements

---

## Summary: Implementation Roadmap

### ✅ Completed
- [x] scenario_001.json - Synthetic broad comparison (baseline)
- [x] scenario_002.json - SHIP Question #3 exact reproduction
- [x] 4-level SHIP rubric documented in scenario_002

### 🚧 High Priority (Critical Gaps)
- [ ] **scenario_003.json** - Full SHIP Medicare-Only sequence (Questions #1-16)
  - 16 scripted turns
  - General knowledge only (Questions #1-6)
  - Accessibility question (Question #16)
  - Effort: 2-3 days

- [ ] **Per-question scoring in ScorerAgent**
  - Implement TurnScore
  - Apply 4-level rubric per turn
  - Aggregate turn scores to overall score
  - Effort: 2-3 days

- [ ] **scenario_004.json** - SHIP Plan-Specific Lookups (Questions #7-15)
  - Specific plan/doctor/location
  - Requires 2024 Medicare.gov plan data
  - Answer key with correct_answers from lookups
  - Effort: 3-5 days

### 🟨 Medium Priority (Important for Full Alignment)
- [ ] **scenario_005.json** - SHIP Dual-Eligible scenario
  - 8 questions from eAppendix 2
  - D-SNP, MSP, Extra Help topics
  - Effort: 2-3 days

- [ ] **Plan data collection system**
  - Scrape/download 2024 plan data from Medicare.gov
  - Structure for verification
  - Effort: 3-5 days

### 🟩 Lower Priority (Enhancements)
- [ ] Multi-turn conversation flow in orchestrator
- [ ] Temporal validity tracking & auto-updates
- [ ] Error recovery testing
- [ ] Multilingual capability testing

---

## Cost-Benefit Analysis

### High ROI Immediately:
1. **scenario_002.json** - ✅ Already completed, validates approach
2. **Per-question scoring** - Enables proper SHIP comparison
3. **scenario_003.json (general knowledge)** - No lookup data needed

### High ROI with Data Collection:
4. **scenario_004.json (plan lookups)** - Tests real-world capability
5. **Plan data collection** - Enables verification

### Future Work:
6. Dual-eligible scenario
7. Multi-turn flow
8. Temporal tracking

---

## Conclusion

**Current State Assessment:**
- ✅ Our implementation tests general Medicare knowledge effectively
- ✅ scenario_002.json aligns with SHIP methodology for Question #3
- ❌ Missing plan-specific lookup testing (Questions #7-15)
- ❌ Missing multi-question sequence (Questions #1-2, #4-16)
- ❌ Missing per-question scoring

**Validation:**
- For testing "Does AI know about Medicare?" → Current implementation is sufficient
- For testing "Can AI help someone enroll in Medicare?" → Need plan-specific scenarios

**Recommendation:**
1. Use scenario_002.json to validate current system works
2. Implement per-question scoring (2-3 days)
3. Create scenario_003.json for full general knowledge sequence (2-3 days)
4. Collect 2024 plan data and create scenario_004.json for lookup testing (3-5 days)

**Total effort for full SHIP alignment: 7-11 days**
