# Medicare Advice Grading - Test Plan

## What Was Built

I've implemented an LLM-based grading system that evaluates Medicare advice responses using the SHIP study rubric (eAppendix 4). The system:

1. **Maps questions to rubric criteria** - 14 Medicare-Only question groups
2. **Uses Claude to grade responses** - Evaluates against specific criteria
3. **Provides detailed feedback** - Score + explanation + criteria analysis
4. **Supports both scenarios** - Framework ready for Medicare-Only and Dual-Eligible

## Testing the Grading System

### Test 1: Built-in Sample Responses

Run the test script with sample responses:

```bash
cd /Users/jamesoreilly/Documents/Projects/AI-Medicare-Advice-Evaluator
python src/test_grading.py
```

**What it does:**
- Grades 3 sample Medicare advice responses (Q1, Q2, Q3)
- Uses the SHIP rubric to evaluate accuracy and completeness
- Saves detailed results to `runs/grading_test/`

**Expected output:**
```
MEDICARE ADVICE GRADING TEST
================================================================================

Grading responses...
--------------------------------------------------------------------------------

=== Grading Summary ===
Run ID: test_run_001
Scenario: medicare_only
Total Questions: 3

Score Distribution:
- Accurate & Complete: X (XX.X%)
- Substantive but Incomplete: X
- Not Substantive: X
- Incorrect: X

=== Question-by-Question Results ===

**Q1: Timing for Initial Medicare Enrollment & Subsequent Changes**
Score: [SCORE]
Explanation: [Detailed explanation]

Criteria Met:
  ✓ [Criterion 1]
  ✓ [Criterion 2]

Criteria Missed:
  ✗ [Criterion 3] (or "None")

[... continues for each question ...]
```

### Test 2: Grade an Existing Run

If you've already run the orchestrator and have conversation transcripts:

```bash
python src/test_grading.py --run-dir runs/YOUR_RUN_DIRECTORY
```

**What it does:**
- Reads the transcript from an existing run
- Extracts question-response pairs
- Grades each response
- Saves grading results alongside the original run

### Test 3: Integrated Example

Run a complete evaluation with grading:

```bash
python examples/run_with_grading.py
```

**What it does:**
- Runs the all_questions scenario with fake adapter
- Gets responses to all 16 questions
- Grades each response
- Shows complete results

## Question Coverage

### Currently Mapped (14 questions)

| Q# | Topic | Status |
|----|-------|--------|
| 1 | Enrollment timing & changes | ✅ Mapped |
| 2 | Employer plan interaction | ✅ Mapped |
| 3 | Traditional Medicare vs Medicare Advantage | ✅ Mapped |
| 4 | Medicare Supplement Plans | ✅ Mapped |
| 5 | Long-term care coverage | ✅ Mapped |
| 6 | Prescription drug coverage options | ✅ Mapped |
| 7 | Specific plan network | ✅ Mapped |
| 8 | Plan premium | ✅ Mapped |
| 9 | Out-of-network coverage | ✅ Mapped |
| 10 | PCP copay | ✅ Mapped |
| 12 | Maximum out-of-pocket | ✅ Mapped |
| 13 | Prescription drug coverage inclusion | ✅ Mapped |
| 14 | Specific drug (Lipitor) coverage | ✅ Mapped |
| 16 | Spanish translation services | ✅ Mapped |

### Not Yet Mapped (2 questions)

| Q# | Topic | Status |
|----|-------|--------|
| 11 | Specialist copay | ⬜ Not mapped |
| 15 | Drug cost comparison | ⬜ Not mapped |

### Dual-Eligible Scenario

| Q# | Topic | Status |
|----|-------|--------|
| 2 | Options for enrolling with Medicaid | ⬜ Not mapped |
| 3 | Considerations for D-SNP | ⬜ Not mapped |
| 4 | D-SNP availability | ⬜ Not mapped |
| 5 | Long-term care coverage | ⬜ Not mapped |
| 6 | Medicaid coverage of premiums | ⬜ Not mapped |
| 7 | Cost sharing assistance | ⬜ Not mapped |

## Verifying the Results

### 1. Check Score Categories

Responses should be scored as one of:
- **Accurate & Complete** - All required info provided correctly
- **Substantive but Incomplete** - Some accurate info but missing key details
- **Not Substantive** - Didn't answer or said "I don't know"
- **Incorrect** - Wrong information that would affect decisions

### 2. Review Explanations

Each score includes a detailed explanation of:
- What information was included
- What information was missing (if any)
- Why the specific score was assigned

### 3. Check Criteria Matching

For Q1 (Enrollment Timing), an "Accurate & Complete" score should show:
- ✓ Mentioned can enroll within 3 months of turning 65
- ✓ Mentioned Open Enrollment Period or Annual Election Period

### 4. Validate Output Files

Grading results are saved as JSON:

```json
{
  "run_id": "test_run_001",
  "scenario": "medicare_only",
  "question_scores": [
    {
      "question_number": 1,
      "question_text": "...",
      "response_text": "...",
      "score": "accurate_complete",
      "explanation": "...",
      "group_id": "QG1",
      "group_name": "Timing for Initial Medicare Enrollment & Subsequent Changes",
      "criteria_met": ["..."],
      "criteria_missed": []
    }
  ]
}
```

## Expected Behavior

### Perfect Responses (fake:perfect adapter)

Should score **Accurate & Complete** for most questions because the fake adapter generates comprehensive responses.

**Example**: Q1 response should include:
- Initial enrollment window (3 months)
- Open Enrollment Period (10/15-12/7)
- Annual Election Period (1/1-3/31)
- Special Enrollment Periods

### Incomplete Responses (fake:incomplete adapter)

Should score **Substantive but Incomplete** because responses provide some info but miss key details.

**Example**: Q1 response might mention enrollment timing but miss change periods.

### Incorrect Responses (fake:incorrect adapter)

Should score **Incorrect** because responses contain material errors.

**Example**: Q1 response says "You must enroll exactly on your 65th birthday" (wrong).

## Troubleshooting

### "ANTHROPIC_API_KEY must be provided"

Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Or in Python:
```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your_key_here"
```

### "No rubric found for question X"

This question hasn't been mapped yet (Q11, Q15, or dual-eligible questions). The grading system will skip it.

### Grading seems too lenient/strict

The LLM uses the exact criteria from the SHIP rubric. If results seem off:
1. Check the rubric criteria in `src/grading_rubric.py`
2. Review the explanation to understand the grading decision
3. Compare to eAppendix 4 in the SHIP study PDF

## Next Steps

After validating the grading system:

1. **Run on real model outputs** - Test with actual AI Medicare advice systems
2. **Add dual-eligible questions** - Map the 6 remaining question groups
3. **Map Q11 and Q15** - Complete Medicare-Only coverage
4. **Compare to orchestrator** - Run both grading systems on same responses
5. **Generate reports** - Create visualization of grading results

## Files Created

```
src/
  grading_rubric.py       # Review question group mappings
  grader.py               # Review grading logic
  test_grading.py         # Run this to test

examples/
  run_with_grading.py     # Complete evaluation + grading

scenarios/medicare_only/
  GRADING_GUIDE.md        # Detailed rubric documentation

GRADING_SYSTEM_README.md  # Overall system documentation
GRADING_TEST_PLAN.md      # This file
```

## Success Criteria

The grading system is working correctly if:

1. ✅ Test script runs without errors
2. ✅ Scores are assigned to all mapped questions
3. ✅ Explanations clearly justify the scores
4. ✅ Criteria met/missed lists are populated
5. ✅ Results are saved to JSON files
6. ✅ Perfect responses get "Accurate & Complete"
7. ✅ Incomplete responses get "Substantive but Incomplete"
8. ✅ Incorrect responses get "Incorrect"

## Questions?

The grading system is ready to test. Start with `python src/test_grading.py` and review the output!
