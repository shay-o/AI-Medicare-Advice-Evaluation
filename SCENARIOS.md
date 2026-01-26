# Test Scenarios Guide

This document explains the available test scenarios, what they evaluate, and how to interpret their results.

---

## Overview

Each scenario is a JSON file containing:
- **A Medicare question** (from SHIP study or synthetic)
- **Answer key** with 13-14 canonical facts
- **Scoring rubric** (how to classify responses)
- **Persona details** (beneficiary characteristics)

Scenarios are located in: `scenarios/v1/`

---

## Available Scenarios

### Scenario 001: Original Medicare vs Medicare Advantage (Synthetic)

**File:** `scenarios/v1/scenario_001.json`

**Question:**
> "I'm trying to decide between Original Medicare and Medicare Advantage. What's the difference?"

**What This Tests:**
- General understanding of Medicare structure
- Ability to explain both options
- Coverage of key differences

**Answer Key:**
- 13 canonical facts
- 6 required facts for "complete" classification
- 7 optional enrichments

**Key Topics:**
- Original Medicare (Parts A & B)
- Medicare Advantage bundling
- Provider networks
- Prescription drug coverage (Part D)
- Out-of-pocket costs
- Medigap/Supplement policies

**Scoring:**
- No specific SHIP rubric (generic scenario)
- Completeness based on 6 required facts
- Designed for initial system testing

**Difficulty:** Medium

**Use Case:**
- System testing and validation
- Initial model comparisons
- Understanding basic evaluation flow

---

### Scenario 002: SHIP Question #3 - MA vs TM Comparison (SHIP Study Aligned)

**File:** `scenarios/v1/scenario_002.json`

**Question:**
> "I keep hearing about Medicare Advantage. How are Medicare Advantage Plans different from regular Medicare, and what are good and bad about them?"

**What This Tests:**
- Comprehensive knowledge of both Medicare options
- Ability to explain advantages AND disadvantages of each
- Balanced, objective information provision
- Alignment with SHIP counselor standards

**Answer Key:**
- **14 canonical facts** from SHIP study eAppendix 4
- **6 Medicare Advantage facts** (F1_MA through F6_MA)
- **8 Original Medicare facts** (F1_TM through F8_TM)

**Source:**
- [SHIP Mystery-Shopper Study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) (Dugan et al., JAMA Network Open 2025)
- eAppendix 1: Question #3 (exact wording)
- eAppendix 4: Question Group 10 (scoring rubric)

**Scoring Rubric (SHIP 4-Tier):**

| Score | Label | Criteria |
|-------|-------|----------|
| **1** | Accurate and Complete | ALL 6 MA facts + ALL 8 TM facts covered |
| **2** | Substantive but Incomplete | SOME (not all) MA facts OR SOME (not all) TM facts |
| **3** | Not Substantive | No substantive discussion of MA or TM |
| **4** | Incorrect | Materially incorrect information provided |

**Difficulty:** High

**Why This Is Important:**

This is the **gold standard** scenario because:
1. ✅ Exact reproduction of SHIP study methodology
2. ✅ Uses actual mystery-shopper question wording
3. ✅ Uses actual SHIP scoring criteria
4. ✅ Enables direct comparison to human counselor results
5. ✅ Tests comprehensive, balanced information provision

**Use Case:**
- **Primary evaluation scenario**
- Research comparing AI to human counselors
- Replicating SHIP study findings with AI models
- Benchmarking model performance

---

## Detailed Fact Breakdown: Scenario 002

### Medicare Advantage Facts (6 required)

| Fact ID | Statement | Severity | Why It Matters |
|---------|-----------|----------|----------------|
| **F1_MA** | MA plans may have lower premiums, deductibles, and cost sharing than TM+Supplement | Medium | Cost comparison - key decision factor |
| **F2_MA** | MA plans have more restrictive provider/hospital choice | **High** | Network restrictions - major limitation |
| **F3_MA** | You may not be able to keep your current doctor | **High** | Continuity of care concern |
| **F4_MA** | MA plans cover all Part A/B benefits, sometimes Part D | **High** | Coverage comprehensiveness |
| **F5_MA** | You must continue to pay Part B premium with MA | Medium | Common misunderstanding |
| **F6_MA** | MA plans often offer extra benefits (dental, vision, hearing) | Low | Value-added benefits |

### Original Medicare Facts (8 required)

| Fact ID | Statement | Severity | Why It Matters |
|---------|-----------|----------|----------------|
| **F1_TM** | You automatically enroll in Part A when you apply | Medium | Enrollment mechanics |
| **F2_TM** | You have option to enroll in Part B | Medium | Coverage is optional |
| **F3_TM** | Part A has deductible but no monthly premium | Low | Cost structure |
| **F4_TM** | Part B has monthly premium, cost sharing, deductible | Low | Cost structure |
| **F5_TM** | TM premiums/cost sharing can be more expensive than MA | Medium | Cost comparison |
| **F6_TM** | With TM, you can choose almost any provider | **High** | Provider freedom - major advantage |
| **F7_TM** | Need separate Part D plan for prescription drugs | **High** | Critical coverage gap |
| **F8_TM** | Can pair TM with Medigap policy to reduce costs | Medium | Cost management strategy |

### Critical Facts Often Missing

Based on testing, models commonly miss:

1. **F5_MA** - Must still pay Part B premium with MA
   - **Impact:** Financial misunderstanding
   - **Why missed:** Counterintuitive (people assume MA replaces Part B premium)

2. **F8_TM** - Medigap availability
   - **Impact:** Miss important cost management option
   - **Why missed:** Requires knowledge of supplemental insurance

3. **F1_TM, F2_TM** - Part A/B enrollment mechanics
   - **Impact:** Enrollment confusion
   - **Why missed:** Too detailed/procedural

---

## How to Choose a Scenario

### For Initial Testing
**Use:** `scenario_001.json`
- Simpler, more forgiving
- Good for verifying system works
- Generic scoring

### For Research / SHIP Replication
**Use:** `scenario_002.json`
- Exact [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) alignment
- Research-grade evaluation
- Comparable to published data

### For Model Comparison
**Use:** `scenario_002.json`
- Standardized rubric
- Well-defined success criteria
- 14 specific facts to track

### For Understanding System
**Use:** `scenario_001.json` first, then `scenario_002.json`
- Start simple, progress to complex
- Learn evaluation flow
- Build intuition

---

## Interpreting Results by Scenario

### Scenario 001 Results

**Good Performance:**
- Completeness: ≥80%
- Accuracy: 100%
- Covers at least 6 required facts

**Acceptable Performance:**
- Completeness: 50-80%
- Accuracy: ≥90%
- Covers 3-5 required facts

**Poor Performance:**
- Completeness: <50%
- Accuracy: <90%
- Missing key facts about networks or Part D

### Scenario 002 Results (SHIP Rubric)

**Score 1: Accurate and Complete**
- All 14 facts covered
- No errors
- **Target benchmark** for high-quality AI

**Score 2: Substantive but Incomplete**
- 7-13 facts covered (most common result)
- No major errors
- **Typical result** for current AI models

**Score 3: Not Substantive**
- <7 facts covered
- Insufficient depth
- **Concerning** - model not providing useful information

**Score 4: Incorrect**
- Any critical errors
- Materially wrong information
- **Failure** - model is harmful

---

## Creating New Scenarios

To create your own scenario based on SHIP study:

1. **Choose a question** from SHIP eAppendix 1
2. **Extract facts** from SHIP eAppendix 4 (scoring guide)
3. **Define rubric** based on SHIP criteria
4. **Create JSON file** following scenario_002.json structure

### Template Structure

Based on [SHIP study methodology](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/):

```json
{
  "scenario_id": "SHIP-00X",
  "title": "SHIP Question #X: Topic",
  "effective_date": "2024-01-01",
  "persona": {
    "age": 64,
    "location": "City, State",
    "current_coverage": "Description",
    "situation": "Scenario context"
  },
  "scripted_turns": [
    {
      "turn_id": "Q1",
      "user_message": "Question text",
      "expected_topics": ["Topic 1", "Topic 2"]
    }
  ],
  "answer_key": {
    "canonical_facts": [
      {
        "fact_id": "F1",
        "statement": "Fact statement",
        "rationale": "Why this matters",
        "source": "SHIP Study reference",
        "severity_if_wrong": "high"
      }
    ],
    "required_points": ["F1", "F2", ...],
    "disallowed_claims": ["Don't say X without Y"],
    "acceptable_referrals": ["Medicare.gov", "1-800-MEDICARE"]
  },
  "scoring_rubric": {
    "score_1": {
      "label": "Accurate and Complete",
      "criteria": "Covers all facts",
      "ship_reference": "eAppendix 4, Question Group X"
    },
    "score_2": {
      "label": "Substantive but Incomplete",
      "criteria": "Covers some facts"
    },
    "score_3": {
      "label": "Not Substantive",
      "criteria": "No substantive discussion"
    },
    "score_4": {
      "label": "Incorrect",
      "criteria": "Materially incorrect"
    }
  }
}
```

---

## Future Scenarios (Planned)

Based on [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/):

### Question #1: Initial Enrollment
- When to enroll in Medicare
- Enrollment periods
- Penalties for late enrollment

### Question #2: Coverage Basics
- What Medicare covers
- Parts A, B, C, D explained
- Gaps in coverage

### Question #4-6: Follow-up Questions
- Specific plan comparisons
- Cost calculations
- Provider network questions

### Question #7-15: Plan-Specific Lookups
- Using Medicare.gov Plan Finder
- Comparing specific plans
- Doctor network verification

---

## Scenario Comparison Table

| Feature | Scenario 001 | Scenario 002 |
|---------|--------------|--------------|
| **Alignment** | Synthetic | SHIP Study Exact |
| **Difficulty** | Medium | High |
| **Facts** | 13 | 14 |
| **Required** | 6 | 14 (all) |
| **Rubric** | Generic | SHIP 4-tier |
| **Use Case** | Testing | Research |
| **Question** | General | Specific |
| **Coverage** | Basic | Comprehensive |

---

## Quick Start by Goal

**Goal: Test system works**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target fake:perfect \
  --judges 2
```

**Goal: Evaluate one model (research-grade)**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

**Goal: Compare models (SHIP aligned)**
```bash
for MODEL in "openai/gpt-4-turbo" "anthropic/claude-3-5-sonnet" "google/gemini-pro-1.5"; do
  python -m src run \
    --scenario scenarios/v1/scenario_002.json \
    --target openrouter:$MODEL \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --judges 2
  sleep 2
done
```

---

## Additional Resources

- **USER_GUIDE.md** - How to run evaluations and interpret results
- **OPENROUTER_GUIDE.md** - Using OpenRouter for model access
- **SHIP Study PDF** - `reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`
- **Methodology Comparison** - `METHODOLOGY_COMPARISON.md`

---

**Recommendation:** Start with scenario_002.json for research-grade evaluations aligned with published [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) methodology.
