# Grading Rubric Audit Results

**Date:** 2026-02-07
**Scope:** Comprehensive audit of grading rubric against SHIP study eAppendix 4

---

## Executive Summary

✅ **Grading rubric is now aligned with SHIP study methodology**

### Issues Found and Fixed

1. **Q10 PCP Copay Mismatch** - FIXED ✅
   - Test plan had $10 copay but SHIP study expects $0
   - Updated `scenarios/medicare_only/all_questions.json` to `"primary_care_copay": 0.0`

2. **Q11 and Q15 Not Scored in SHIP Study** - DOCUMENTED ✅
   - Q11 (specialist copay) and Q15 (drug cost comparison) were intentionally not scored
   - Maintaining SHIP fidelity by NOT creating rubrics for these questions
   - Questions remain in script but won't be graded

---

## SHIP Study Scoring Coverage

### Scored Questions (20 Question Groups)

#### Both Scenarios (2)
- ✅ Q1: Timing for Initial Medicare Enrollment & Subsequent Changes
- ✅ Q8/Q16: Spanish Translation Services

#### Medicare-Only Scenario (12)
- ✅ Q2: Medicare Enrollment & Interaction with Employer Plan
- ✅ Q3: Traditional Medicare vs Medicare Advantage
- ✅ Q4: Medicare Supplement Plans
- ✅ Q5: Long-Term Care Coverage
- ✅ Q6: Prescription Drug Coverage Options
- ✅ Q7: Specific PCP in Network
- ✅ Q8: Plan Premium
- ✅ Q9: Out-of-Network Coverage
- ✅ Q10: PCP Copay (now fixed to expect $0)
- ✅ Q12: Maximum Out-of-Pocket
- ✅ Q13: Prescription Drug Coverage Inclusion
- ✅ Q14: Specific Drug (Lipitor) Coverage

#### Dual-Eligible Scenario (6)
- ✅ Q2: Medicare Enrollment Options with Medicaid
- ✅ Q3: D-SNP Enrollment Considerations
- ✅ Q4: D-SNP Availability
- ✅ Q5: Long-Term Care Coverage (split into Q5a/Q5b)
- ✅ Q6: Medicaid Coverage of Medicare Costs
- ✅ Q7: Medicare Cost-Sharing Assistance Programs

### Questions NOT Scored in SHIP Study

These questions appear in the script but were not graded:

#### Medicare-Only
- ❌ Q11: Specialist copay (questions 82-85 in questionnaire)
- ❌ Q15: Drug cost comparison (questions 93-94 in questionnaire)

**Rationale:** Questions 1-13 in the SHIP questionnaire (eAppendix 4, lines 25-37) are marked "Not scored". The SHIP researchers chose to ask these questions but not include them in their accuracy/completeness analysis.

---

## Rubric Quality Assessment

### ✅ Well-Aligned Question Groups

The following rubrics closely match SHIP study scoring criteria:

- **QG1 (Q1):** Enrollment timing - Two-part question properly mapped
- **QG2 (Q8/Q16):** Spanish translation - Binary question correctly simplified
- **QG9 (Q2):** Employer plan interaction - Captures both components
- **QG10 (Q3):** MA vs Traditional Medicare - Most detailed rubric (14 criteria)
- **QG11 (Q4):** Medicare Supplement - Comprehensive 7-point coverage
- **QG12 (Q5):** Long-term care - Properly captures Medicare vs other coverage nuance
- **QG13 (Q6):** Prescription drug coverage - Key decision points covered
- **QG16 (Q9):** Out-of-network - Distinguishes PPO vs HMO appropriately
- **QG18 (Q12):** Max out-of-pocket - Verification-based scoring
- **QG19 (Q13):** Drug coverage inclusion - General vs plan-specific knowledge
- **QG20 (Q14):** Lipitor coverage - Brand vs generic distinction

### ⚠️ Areas for Future Enhancement

These rubrics are correct but could be improved with additional detail:

1. **QG21-QG26 (Dual-Eligible Q2-Q7):** Have rubrics but lack detailed answer keys with canonical facts like Medicare-Only Q3
2. **QG22 (Q3) and QG26 (Q7):** Should specify explicit thresholds (e.g., "requires 5 of 7 criteria")
3. **QG25 (Q6):** Could clarify variation in Medicaid assistance by eligibility category

### 📊 Rubric Statistics

- **Total SHIP Question Groups:** 20
- **Medicare-Only Groups:** 12
- **Dual-Eligible Groups:** 6
- **Both Scenarios Groups:** 2
- **Mapped in grading_rubric.py:** 20/20 ✅
- **Questions with detailed answer keys:** 1 (Q3 MA vs TM)

---

## Changes Made

### Fixed Files

1. **`scenarios/medicare_only/all_questions.json`**
   - Changed `"primary_care_copay": 10.0` → `"primary_care_copay": 0.0`

2. **`scenarios/dual_eligible/all_questions.json`** (from previous corrections)
   - Q2: Fixed to exact SHIP wording
   - Q3: Fixed to exact SHIP wording
   - Q4: Fixed to exact SHIP wording
   - Q5: Split into Q5a and Q5b
   - Q6: Fixed to exact SHIP wording
   - Q7: Fixed to exact SHIP wording

3. **`src/grading_rubric.py`** (from previous corrections)
   - Updated all dual-eligible question group topics to match exact questions

---

## Validation Status

✅ **Medicare-Only Questions:** All 16 questions match SHIP study eAppendix 1 exactly
✅ **Dual-Eligible Questions:** All 8 questions match SHIP study eAppendix 2 exactly
✅ **Grading Rubrics:** All 20 SHIP-scored question groups properly mapped
✅ **Test Plan Data:** PCP copay now matches SHIP study expectation

---

## Recommendations

### Immediate (None Required)
All critical issues resolved. System ready for valid SHIP-aligned grading.

### Future Enhancements (Optional)
1. Create detailed answer keys for dual-eligible questions (similar to Q3 MA vs TM)
2. Add explicit scoring thresholds for multi-criteria questions
3. Consider whether to extend beyond SHIP study to score Q11/Q15 (document as extension, not SHIP replication)

---

## References

- **SHIP Study:** Dugan K et al. JAMA Network Open. 2025;8(4):e252834
- **eAppendix 1:** Medicare-Only scenario script (pages 4-5)
- **eAppendix 2:** Dual-Eligible scenario script (pages 7-8)
- **eAppendix 4:** Scoring guide (pages 21-40)
- **Source PDF:** `reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`
