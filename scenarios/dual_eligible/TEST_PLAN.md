# Dual-Eligible Scenario - SHIP Study Fidelity Corrections

## Date: 2026-02-07

## Problem Identified

The questions in `scenarios/dual_eligible/all_questions.json` were paraphrased instead of using exact wording from the SHIP study (eAppendix 2). This violated the core SHIP study fidelity principle and caused invalid grading results, as the grading rubric was scoring paraphrased questions against rubrics designed for the exact questions.

## Source of Truth

**Reference Document:** `reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`
- **eAppendix 2 (page 7):** Exact question wording for Dual-Eligible scenario
- **eAppendix 4 (pages 21-30):** Scoring guide and rubric criteria

## Changes Made

### 1. Fixed Question Wording in `scenarios/dual_eligible/all_questions.json`

| Question | Before (Paraphrased) | After (SHIP Study Exact) | Status |
|----------|---------------------|-------------------------|--------|
| **Q1** | When can I select my Medicare coverage plan, and when can I change it later? | *(unchanged - already correct)* | ✅ |
| **Q2** | What are my options for enrolling in Medicare coverage with full Medicaid? | If I stay eligible for Medicaid, what are my options for enrolling in Medicare? | ✅ Fixed |
| **Q3** | What should I consider when deciding whether to enroll in a D-SNP? | I saw a commercial about special plans for people with both Medicaid and Medicare. Can you tell me more about them and why I may or may not want to choose one? | ✅ Fixed |
| **Q4** | Are there any D-SNPs available where I live? | Are special plans for people with Medicaid and Medicare available in my area? | ✅ Fixed |
| **Q5** | Do either regular Medicare, Medicare Advantage Plans, D-SNPs, or Medicaid cover long-term care? | **Split into Q5a and Q5b:**<br>**Q5a:** If I ever need long-term care in the future, would it be covered under any of the Medicare options we've talked about?<br>**Q5b:** What about Medicaid? If I stay eligible, will Medicaid pay for long-term care? | ✅ Fixed |
| **Q6** | Will Medicaid cover my Medicare premiums and cost-sharing? | If I stay eligible for Medicaid, will it pay for my Medicare premiums and cost sharing and deductibles no matter if I choose a Dual Eligible Special Needs Plan, a Medicare Advantage Plan, or regular Medicare? | ✅ Fixed |
| **Q7** | Are there programs that can help me pay for Medicare costs if I don't qualify for full Medicaid? | I was told that if I'm not eligible for Medicaid, there are other programs to help with out-of-pocket costs for Medicare. My income is $1,600 a month. Would I get any help? | ✅ Fixed |
| **Q8** | I have a friend who does not speak much English. Do you offer Spanish translation services at your location? | *(unchanged - already correct)* | ✅ |

### 2. Updated Grading Rubric in `src/grading_rubric.py`

Updated the `topic` field in all dual-eligible question groups to match exact question wording:

- **QUESTION_GROUP_21 (Q2):** Updated topic to exact question
- **QUESTION_GROUP_22 (Q3):** Updated topic to exact question
- **QUESTION_GROUP_23 (Q4):** Updated topic to exact question
- **QUESTION_GROUP_24 (Q5):** Updated topic to reflect both Q5a and Q5b
- **QUESTION_GROUP_25 (Q6):** Updated topic to exact question
- **QUESTION_GROUP_26 (Q7):** Updated topic to exact question (including "$1,600 a month" detail)

## Impact

### Before
- Grading results were **invalid** - the grader was scoring responses to paraphrased questions against rubrics designed for different questions
- Violated SHIP study fidelity principle
- Some answers incorrectly passed as "complete" when they weren't addressing the actual SHIP study questions

### After
- Grading results are now **valid** - responses to exact SHIP study questions are scored against correct rubrics
- Maintains SHIP study fidelity
- Accurate evaluation of AI model performance matching the original study methodology

## Testing Recommendation

Previous runs with the dual_eligible scenario should be **discarded** as they contain invalid results. All evaluations should be re-run with the corrected questions.

## Notes

- Q5 was correctly split into Q5a and Q5b as separate turns, matching the SHIP study script where Q5b is a follow-up question
- The $1,600/month income detail in Q7 is critical context from the persona that makes the question meaningful
- All questions now match eAppendix 2 word-for-word, maintaining exact SHIP study fidelity
