# Medicare Advice Grading System

## Overview

This grading system evaluates Medicare counseling responses using the SHIP (State Health Insurance Assistance Program) study rubric from the JAMA Network Open study (Dugan et al., 2025, eAppendix 4).

## What I've Built

### 1. Rubric Mapping (`src/grading_rubric.py`)

Maps all 20 question groups from the SHIP study to structured scoring criteria:
- **14 Medicare-Only question groups** (Q1-Q16, excluding Q11, Q15)
- **6 scoring categories** per question
- Detailed criteria for each score level

Each question group includes:
- Question topic and text
- Criteria for "Accurate & Complete"
- Criteria for "Substantive but Incomplete"
- Criteria for "Not Substantive"
- Criteria for "Incorrect"

### 2. LLM-Based Grader (`src/grader.py`)

Uses Claude API to evaluate responses against the rubric:

```python
from src.grader import MedicareAdviceGrader

grader = MedicareAdviceGrader()

# Grade a single response
score = grader.grade_response(
    question_number=1,
    question_text="When can I select my Medicare coverage plan?",
    response_text="You can select within 3 months...",
    scenario="medicare_only"
)

# Grade an entire run
run_score = grader.grade_run(
    run_id="my_run",
    questions_and_responses=[...],
    scenario="medicare_only"
)
```

**Output includes**:
- Score category for each question
- Detailed explanation of scoring decision
- List of criteria met
- List of criteria missed
- Overall accuracy rate

### 3. Testing & Examples

#### Test Script (`src/test_grading.py`)

```bash
# Test with built-in sample responses
python src/test_grading.py

# Grade an existing run
python src/test_grading.py --run-dir runs/RUN_20250204_123456
```

#### Example Integration (`examples/run_with_grading.py`)

```bash
# Run scenario and grade results
python examples/run_with_grading.py
```

### 4. Documentation

- `scenarios/medicare_only/GRADING_GUIDE.md` - Detailed rubric documentation
- `GRADING_SYSTEM_README.md` - This file

## Quick Start

### Installation

Make sure you have the required dependencies:

```bash
pip install anthropic pydantic
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### Run Grading Test

```bash
cd /Users/jamesoreilly/Documents/Projects/AI-Medicare-Advice-Evaluator
python src/test_grading.py
```

This will:
1. Grade 3 sample Medicare advice responses
2. Display detailed grading results
3. Save results to `runs/grading_test/grading_results_*.json`

### Grade an Existing Run

If you've already run the orchestrator and have results in the `runs/` directory:

```bash
python src/test_grading.py --run-dir runs/YOUR_RUN_DIR
```

## Score Categories

### 1. Accurate & Complete (Best)
All required information provided correctly. This is the target score.

### 2. Substantive but Incomplete
Some accurate information but missing key details. Common for complex questions where part of the answer is correct.

### 3. Not Substantive
Didn't really answer the question or said "I don't know".

### 4. Incorrect
Wrong information that would materially affect a Medicare enrollee's decision. Most serious issue.

### 5. Missing
Question couldn't be asked or error during grading.

## Mapped Questions

### Both Scenarios
- **Q1**: Enrollment timing & changes
- **Q16/Q8**: Spanish translation services

### Medicare-Only Scenario
- **Q2**: Employer plan interaction
- **Q3**: Traditional Medicare vs Medicare Advantage
- **Q4**: Medicare Supplement Plans
- **Q5**: Long-term care coverage
- **Q6**: Prescription drug coverage options
- **Q7**: Specific plan network
- **Q8**: Plan premium
- **Q9**: Out-of-network coverage
- **Q10**: PCP copay
- **Q12**: Maximum out-of-pocket
- **Q13**: Prescription drug coverage inclusion
- **Q14**: Specific drug (Lipitor) coverage

### Not Yet Mapped
- **Q11**: Specialist copay
- **Q15**: Drug cost comparison
- **Dual-Eligible scenario questions** (Q2-Q7)

## Example Output

```
=== Grading Summary ===
Run ID: test_run_001
Scenario: medicare_only
Total Questions: 3

Score Distribution:
- Accurate & Complete: 2 (66.7%)
- Substantive but Incomplete: 1
- Not Substantive: 0
- Incorrect: 0

=== Question-by-Question Results ===

**Q1: Timing for Initial Medicare Enrollment & Subsequent Changes**
Score: ACCURATE_COMPLETE
Explanation: The response comprehensively addresses both parts...

Criteria Met:
  ✓ Mentioned that you can enroll in Medicare/select coverage within 3 months of turning 65
  ✓ Substantively answered the 'when can I change it' question...

Criteria Missed:
  (None)
```

## Integration with Orchestrator

The grading system is designed to work alongside (not replace) the existing orchestrator:

**Current Orchestrator**: Uses claim extraction → verification → scoring
**New Grading System**: Direct rubric-based evaluation of responses

Both can be run on the same conversations to compare approaches.

## Advantages of LLM-Based Grading

1. **Flexible**: Understands substance over exact wording
2. **Detailed**: Provides explanations and identifies specific gaps
3. **Scalable**: Can grade unlimited responses
4. **Consistent**: Uses same rubric criteria for all evaluations

## Limitations

1. **API Cost**: Each grading call uses Claude API (though relatively cheap with Sonnet)
2. **Requires API Key**: Need Anthropic API access
3. **Not Instant**: Takes a few seconds per question
4. **Needs Review Cases Skipped**: Original rubric includes manual review for edge cases

## Future Enhancements

1. ✅ **Medicare-Only scenario** (14 question groups)
2. ⬜ **Dual-Eligible scenario** (6 additional question groups)
3. ⬜ **Specialist copay question** (Q11)
4. ⬜ **Drug cost comparison question** (Q15)
5. ⬜ **Confidence scores** for grading decisions
6. ⬜ **Inter-rater reliability** checks
7. ⬜ **Batch grading** for efficiency
8. ⬜ **Web report generation** with grading results

## Files Created

```
src/
  grading_rubric.py       # Rubric mapping and criteria
  grader.py               # LLM-based grading engine
  test_grading.py         # Test script

examples/
  run_with_grading.py     # Complete evaluation + grading example

scenarios/medicare_only/
  GRADING_GUIDE.md        # Detailed rubric documentation

GRADING_SYSTEM_README.md  # This file
```

## Reference

Based on:
- Dugan K, Peterson I, Dorneo A, Garrido MM. **Accuracy of Medicare information provided by State Health Insurance Assistance Programs.** _JAMA Netw Open._ 2025;8(4):e252834. doi:10.1001/jamanetworkopen.2025.2834
- Supplemental eAppendix 4: Scoring Guide

## Questions or Issues?

The grading system is ready to use for Medicare-Only scenarios. For dual-eligible scenarios or additional question mapping, the rubric structure is in place and can be extended following the same pattern.
