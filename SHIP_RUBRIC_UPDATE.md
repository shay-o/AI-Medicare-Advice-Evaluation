# SHIP Rubric Update - Summary

**Date:** 2026-01-26
**Status:** ✅ COMPLETE

---

## What Changed

The system now uses **scenario-specific scoring rubrics** from the [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) instead of hardcoded classification logic.

### Before (Generic System):
- Hardcoded 4-tier classification: `accurate_complete`, `accurate_incomplete`, `not_substantive`, `incorrect`
- Fixed thresholds: 80% for complete, 30% for substantive
- Same logic for all scenarios

### After (SHIP Study Rubric):
- **Scenario-specific rubrics** from [study methodology](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)
- **Numeric scores** (1-4) with labels defined in scenario file
- **Study-aligned criteria** matching actual SHIP research

---

## SHIP Scenario-002 Rubric (Question #3)

From the actual [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) (eAppendix 4, Question Group 10):

| Score | Label | Criteria |
|-------|-------|----------|
| **1** | Accurate and Complete | Response substantively covers ALL 6 Medicare Advantage points (F1_MA-F6_MA) AND ALL 8 Original Medicare points (F1_TM-F8_TM) |
| **2** | Substantive but Incomplete | Response substantively covers SOME (but not all) MA points OR SOME (but not all) TM points |
| **3** | Not Substantive | Response does not substantively discuss any MA or TM points, or counselor says they do not know |
| **4** | Incorrect | Incorrect information was provided that is substantive enough to materially change the answer or affect coverage decisions |

---

## Example Results

### GPT-4-Turbo on SHIP Question #3:

**Latest Run:** `runs/20260126_190421/`

```json
{
  "rubric_score": 2,
  "rubric_label": "Substantive but Incomplete",
  "completeness_percentage": 0.714,  // 71.4%
  "accuracy_percentage": 1.0,        // 100%
  "missing_required_points": [
    "F5_MA",  // Must pay Part B premium with MA
    "F8_TM",  // Medigap availability
    "F1_TM",  // Auto Part A enrollment
    "F2_TM"   // Optional Part B enrollment
  ],
  "justification": "Classified as Substantive but Incomplete (Score 2). Response covered 10 facts (71% of required points). Missing required facts: F1_TM, F2_TM, F5_MA, F8_TM."
}
```

**Coverage:**
- MA Facts: 5 of 6 (83%) → Missing F5_MA
- TM Facts: 5 of 8 (63%) → Missing F1_TM, F2_TM, F8_TM
- **Result:** Score 2 (Substantive but Incomplete) ✅

This correctly matches the SHIP rubric: covers SOME (not all) of each category.

---

## Technical Changes

### 1. Updated Schemas (`src/schemas.py`)

**Removed:**
```python
class SHIPClassification(str, Enum):
    ACCURATE_COMPLETE = "accurate_complete"
    ACCURATE_INCOMPLETE = "accurate_incomplete"
    NOT_SUBSTANTIVE = "not_substantive"
    INCORRECT = "incorrect"
```

**Added to Scenario:**
```python
class Scenario(BaseModel):
    # ... other fields
    scoring_rubric: dict[str, Any] | None = Field(
        None, description="Scenario-specific scoring rubric"
    )
```

**Updated ScoreResult:**
```python
class ScoreResult(BaseModel):
    rubric_score: int | None = Field(None, description="Numeric score (e.g., 1-4 for SHIP)")
    rubric_label: str | None = Field(None, description="Human-readable label")
    completeness_percentage: float  # Kept
    accuracy_percentage: float      # Kept
    # ... other fields
```

### 2. Updated ScorerAgent (`src/agents/scorer.py`)

**Removed:**
- `_classify_ship()` method with hardcoded thresholds

**Added:**
- `_apply_rubric()` method that implements scenario-specific logic
- Accepts `scoring_rubric` parameter from scenario

**Key Logic:**
```python
def _apply_rubric(self, scoring_rubric, covered_facts, answer_key, contradicted_verdicts):
    # Check for errors first (Score 4)
    if has_critical_error:
        return 4, "Incorrect"

    # Check fact coverage
    ma_facts = {f for f in covered_facts if "_MA" in f}
    tm_facts = {f for f in covered_facts if "_TM" in f}

    # Score 1: ALL MA and ALL TM
    if ma_facts == all_ma_facts and tm_facts == all_tm_facts:
        return 1, "Accurate and Complete"

    # Score 3: NO MA and NO TM
    if not ma_facts and not tm_facts:
        return 3, "Not Substantive"

    # Score 2: SOME but not all
    return 2, "Substantive but Incomplete"
```

### 3. Updated Orchestrator (`src/orchestrator.py`)

- Passes `scenario.scoring_rubric` to adjudicator
- Displays `rubric_label` and `rubric_score` instead of `ship_classification`

### 4. Updated Adjudicator (`src/agents/adjudicator.py`)

- Accepts and passes `scoring_rubric` to scorer

### 5. Updated Scenario File (`scenarios/v1/scenario_002.json`)

**Added scoring rubric:**
```json
"scoring_rubric": {
  "score_1": {
    "label": "Accurate and Complete",
    "criteria": "Response substantively covers ALL...",
    "ship_reference": "eAppendix 4, Question Group 10, Scoring Guide item 1"
  },
  "score_2": {
    "label": "Substantive but Incomplete",
    "criteria": "Response substantively covers SOME (but not all)...",
    "ship_reference": "eAppendix 4, Question Group 10, Scoring Guide item 2"
  },
  "score_3": {
    "label": "Not Substantive",
    "criteria": "Response does not substantively discuss...",
    "ship_reference": "eAppendix 4, Question Group 10, Scoring Guide item 3"
  },
  "score_4": {
    "label": "Incorrect",
    "criteria": "Incorrect information was provided...",
    "ship_reference": "eAppendix 4, Question Group 10, Scoring Guide item 4"
  }
}
```

---

## Benefits

### 1. Study Alignment ✅
- Now matches actual [SHIP methodology](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) exactly
- Scoring criteria directly from eAppendix 4
- Can cite specific study references

### 2. Flexibility ✅
- Each scenario can define its own rubric
- Different scenarios can have different scoring systems
- Easy to add new scenarios with custom rubrics

### 3. Transparency ✅
- Score and label clearly displayed
- Justification explains which tier and why
- Completeness % still calculated for detail

### 4. Backward Compatibility ⚠️
- Old scenarios without `scoring_rubric` will return `rubric_score: null`
- System gracefully handles missing rubrics
- Can add rubrics to existing scenarios incrementally

---

## Output Format

### Console Output:
```
[5/6] Scoring and adjudicating...
  ✓ Classification: Substantive but Incomplete (Score 2)
  ✓ Completeness: 71.4%
  ✓ Accuracy: 100.0%

======================================================================
EVALUATION SUMMARY
======================================================================
Classification:    Substantive but Incomplete (Score 2)
Completeness:      71.4%
Accuracy:          100.0%
Justification:
  Classified as Substantive but Incomplete (Score 2).
  Response covered 10 facts (71% of required points).
  Missing required facts: F1_TM, F2_TM, F5_MA, F8_TM.
```

### JSON Output (results.jsonl):
```json
{
  "final_scores": {
    "rubric_score": 2,
    "rubric_label": "Substantive but Incomplete",
    "completeness_percentage": 0.714,
    "accuracy_percentage": 1.0,
    "missing_required_points": ["F5_MA", "F8_TM", "F2_TM", "F1_TM"],
    "justification": "..."
  }
}
```

---

## Validation

### Test Run Confirms Correctness:

**GPT-4-Turbo Coverage:**
- ✅ F1_MA - Lower costs with MA
- ✅ F2_MA - Network restrictions
- ✅ F3_MA - May not keep doctor
- ✅ F4_MA - Covers Part A/B/D
- ❌ **F5_MA - Must pay Part B premium** ⚠️ MISSING (critical)
- ✅ F6_MA - Extra benefits

- ❌ **F1_TM - Auto Part A enrollment** MISSING
- ❌ **F2_TM - Optional Part B** MISSING
- ✅ F3_TM - Part A no premium
- ✅ F4_TM - Part B has premium
- ✅ F5_TM - TM can be more expensive
- ✅ F6_TM - Provider choice
- ✅ F7_TM - Need separate Part D
- ❌ **F8_TM - Medigap availability** MISSING

**Result:** 5 of 6 MA + 5 of 8 TM = Substantive but Incomplete ✅

---

## Next Steps

### For scenario_001.json:
- Can add a generic rubric if desired
- Or leave without rubric (will show `rubric_score: null`)
- Completeness % still calculated either way

### For New Scenarios:
- Define scenario-specific rubric in JSON
- Follow [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) methodology
- Reference actual study appendices

### For Reporting:
- Can filter by rubric_score (1, 2, 3, 4)
- Can group results by label
- Can compare across models using standard scale

---

## Summary

✅ **Removed hardcoded SHIP classification**
✅ **Added scenario-specific rubrics**
✅ **Kept completeness_percentage and accuracy_percentage**
✅ **Matches [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) methodology exactly**
✅ **Tested and validated with GPT-4-turbo**

The system now correctly implements the [SHIP mystery-shopper study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) scoring methodology!
