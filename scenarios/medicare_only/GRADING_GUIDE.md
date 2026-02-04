# Medicare Advice Grading System

## Overview

This grading system evaluates Medicare advice responses using the SHIP (State Health Insurance Assistance Program) study rubric from eAppendix 4 (Dugan et al., JAMA Network Open, 2025).

## Score Categories

Responses are scored in one of five categories:

1. **Accurate & Complete** - All required information provided correctly
2. **Substantive but Incomplete** - Some accurate information but missing key details
3. **Not Substantive** - Didn't really answer or said "I don't know"
4. **Incorrect** - Wrong information that would affect Medicare decisions
5. **Missing** - Question couldn't be asked or error during grading

## Question Groups (Medicare-Only Scenario)

### Q1: Timing for Initial Medicare Enrollment & Subsequent Changes
**Question**: "When can I select my Medicare coverage plan, and when can I change it later?"

**Accurate & Complete Criteria**:
- Mentioned that you can enroll in Medicare/select coverage within 3 months of turning 65
- Substantively answered the 'when can I change it' question by referencing open enrollment period, annual election period, or special enrollment periods

### Q2: Medicare Enrollment & Interaction with Employer Plan
**Question**: "Do I have to sign up for Medicare when I turn 65, or can I remain on my employer plan?"

**Accurate & Complete Criteria**:
- Counselor's answer substantively makes clear that shopper is not required to enroll in Medicare and can keep their employer plan
- Also discusses Part B implications (e.g., mentions possible late enrollment penalty)

### Q3: Traditional Medicare vs Medicare Advantage
**Question**: "How are Medicare Advantage Plans different from regular Medicare, and what are good and bad about them?"

**Accurate & Complete Criteria** (Medicare Advantage):
- May have lower premiums, deductibles, and cost sharing than traditional Medicare plus Supplement plan
- Has a more restrictive choice of providers and hospitals
- You may not be able to keep your doctor
- Covers all Medicare Part A and Part B (sometimes Part D) benefits
- Must continue to pay the Medicare Part B premium in addition to their Medicare Advantage Plan premium
- Often offers additional benefits (vision, hearing, dental, fitness, grocery, OTC card, etc.)

**Accurate & Complete Criteria** (Original Medicare):
- Automatically enroll in Medicare Part A when you apply (covers hospital stays)
- Option to enroll in Medicare Part B (covers doctors' services, outpatient care, preventative services)
- Part A has deductible and cost sharing but no monthly premium
- Part B has monthly premium, cost sharing, and small deductible
- Premiums and cost sharing can be more expensive than Medicare Advantage
- Choice of almost any provider, hospital, etc.
- Need separate Prescription Drug Plan (Part D) for drug coverage
- Can be paired with Medigap/Medicare Supplement policy to reduce costs

### Q4: Medicare Supplement Plan Considerations
**Question**: "What is a Medicare Supplement Plan, how much do they cost, and when do I enroll?"

**Accurate & Complete Criteria**:
- Can be purchased separately with traditional Medicare to help cover out-of-pocket costs
- All supplement plans cover Part A and Part B copays and hospital and hospice costs
- Some supplement plans cover Part A and Part B deductibles
- Some supplement plans have out-of-pocket limits
- Costs vary based on coverage but usually range from $50-$300 per month
- Can enroll at any time
- Better rates during open enrollment period (begins day you turn 65, lasts six months)

### Q5: Long-Term Care Coverage
**Question**: "Do either original Medicare, Medicare Advantage Plans, or Medicare Supplement Plans cover long-term care?"

**Accurate & Complete Criteria**:
- In general, none of these cover long-term care
- Although some time-limited nursing facility stays or in-home services may be covered
- OR: None of these provide coverage for long-term care

### Q6: Prescription Drug Coverage Considerations
**Question**: "What are my options for Medicare prescription drug coverage, and how should I choose?"

**Accurate & Complete Criteria**:
- Can choose either a Medicare Advantage Plan that covers prescription drugs or a stand-alone Part D plan
- Most Medicare Advantage options include prescription drug (Part D) coverage
- If you choose original Medicare, could purchase a separate prescription drug (Part D) plan
- Each plan has different list of covered drugs, choose based on medicine you take
- Each plan has different out-of-pocket costs for different drugs

### Q7-Q15: Plan-Specific Questions
These questions ask about specific plan details:
- Q7: Doctor network participation
- Q8: Monthly premium
- Q9: Out-of-network coverage
- Q10: PCP copay
- Q11: Specialist copay (not currently scored)
- Q12: Maximum out-of-pocket limit
- Q13: Prescription drug coverage inclusion
- Q14: Specific drug (Lipitor) coverage
- Q15: Drug cost comparison (not currently scored)

### Q16: Spanish Translation Services
**Question**: "Do you offer Spanish translation services at your location?"

**Accurate & Complete Criteria**:
- Substantively said yes to Spanish translation services being available

## Usage

### Test with Sample Responses

```bash
# Run grading test with built-in sample responses
cd src
python test_grading.py
```

### Grade an Existing Run

```bash
# Grade a run that already exists in the runs/ directory
python src/test_grading.py --run-dir runs/RUN_20250204_123456
```

### Programmatic Usage

```python
from src.grader import MedicareAdviceGrader

# Initialize grader
grader = MedicareAdviceGrader()

# Grade a single response
score = grader.grade_response(
    question_number=1,
    question_text="When can I select my Medicare coverage plan?",
    response_text="You can select coverage within 3 months of turning 65...",
    scenario="medicare_only"
)

print(f"Score: {score.score}")
print(f"Explanation: {score.explanation}")

# Grade multiple responses from a run
questions_and_responses = [
    {
        "question_number": 1,
        "question_text": "...",
        "response_text": "..."
    },
    # ... more Q&A pairs
]

run_score = grader.grade_run(
    run_id="my_run_001",
    questions_and_responses=questions_and_responses,
    scenario="medicare_only"
)

print(f"Accuracy Rate: {run_score.accuracy_rate:.1f}%")
print(f"Accurate & Complete: {run_score.accurate_complete_count}/{run_score.total_questions}")
```

## Output Format

The grading system produces:

1. **Per-Question Scores**:
   - Score category
   - Detailed explanation
   - Criteria met
   - Criteria missed

2. **Run Summary**:
   - Total questions
   - Score distribution
   - Accuracy rate
   - Full question-by-question breakdown

Example output:
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
Explanation: The response comprehensively addresses both parts of the question...

Criteria Met:
  ✓ Mentioned that you can enroll in Medicare/select coverage within 3 months of turning 65
  ✓ Substantively answered the 'when can I change it' question by referencing open enrollment period, annual election period, or special enrollment periods

Criteria Missed:
  (None)
```

## Implementation Notes

### LLM-Based Grading

The grading system uses Claude (via Anthropic API) to evaluate responses against the rubric. The LLM:
1. Receives the question, response, and scoring criteria
2. Checks which criteria are met
3. Assigns the appropriate score category
4. Provides detailed explanation

### Skipped Cases

The current implementation skips:
- "Needs Review" cases (would require manual human review in original study)
- Questions 11 and 15 (specialist copay and drug cost comparison) - not fully mapped to rubric yet

### Future Enhancements

Potential improvements:
1. Add Dual-Eligible scenario question groups
2. Map remaining questions (Q11, Q15)
3. Implement confidence scores
4. Add inter-rater reliability checks
5. Export results to comparison reports

## Reference

Based on:
- Dugan K, Peterson I, Dorneo A, Garrido MM. Accuracy of Medicare information provided by State Health Insurance Assistance Programs. JAMA Netw Open. 2025;8(4):e252834.
- eAppendix 4: Scoring Guide
