# Feature Specification: Expand to Include All Questions in SHIP Study

**Feature Branch**: `003-ship-all-questions`
**Created**: 2026-02-02
**Status**: Draft
**Input**: GitHub Issue #3 - "Expand to include all questions in SHIP study"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medicare-Only Conceptual Questions (Priority: P1)

A researcher wants to evaluate AI models on all conceptual Medicare-only questions from the SHIP study, not just the TM vs MA comparison (Question #3). This enables comprehensive comparison to human counselor performance across enrollment, employer coverage, Medigap, long-term care, and Part D.

**Why this priority**: The SHIP study tested 13 questions in the Medicare-only scenario. Scenarios are now organized as scenarios/medicare_only/ and scenarios/dual_eligible/ with SHIP-MO-Qn and SHIP-DE-Qn IDs. Run with `--scenario medicare_only` to execute all Medicare-only questions.

**Independent Test**: Run evaluation with new scenario, verify scoring and report generation work. Compare AI results to SHIP Table 2 baseline data.

**Acceptance Scenarios**:

1. **Given** a new scenario (e.g., SHIP-001 Enrollment Timing), **When** the user runs `python -m src run --scenario scenarios/v1/scenario_001.json`, **Then** the evaluation completes and produces rubric scores
2. **Given** scenarios for SHIP questions 1, 2, 4, 5, 6 exist, **When** the user generates a report, **Then** results are grouped by scenario and comparable to SHIP study Table 2
3. **Given** each new scenario, **When** reviewed, **Then** it uses exact question wording from SHIP eAppendix 1 and scoring rubric from eAppendix 4

---

### User Story 2 - Dual-Eligible Scenario Questions (Priority: P2)

A researcher wants to evaluate AI models on dual-eligible questions from the SHIP study. The dual-eligible script (eAppendix 2) tests D-SNP knowledge, Medicaid coverage, and integrated care options.

**Why this priority**: Enables comparison to human counselor performance for dual eligibles (n=96 in study). Depends on having scenario infrastructure from User Story 1.

**Independent Test**: Run evaluation with dual-eligible scenario, verify persona and question flow match eAppendix 2.

**Acceptance Scenarios**:

1. **Given** dual-eligible scenarios exist, **When** the user runs an evaluation, **Then** the persona reflects dual-eligible beneficiary (Medicare + Medicaid eligible)
2. **Given** dual-eligible results, **When** the user generates a report, **Then** they can compare to SHIP Table 2 dual-eligible rows

---

### User Story 3 - Plan-Specific Lookup Questions (Priority: P3)

A researcher wants to evaluate AI models on plan-specific questions (e.g., "Is my doctor in network for Plan X?", "What is the premium for Plan Y?"). These require plan-specific data (Plan Finder, formulary, network directory).

**Why this priority**: Lower priority because they require additional infrastructure (mock plan data or API integration). SHIP study showed human counselors struggled most on these (26.1% accurate on PCP network question).

**Acceptance Scenarios**:

1. **Given** plan-specific scenarios exist, **When** the user runs an evaluation, **Then** the scenario includes plan/beneficiary-specific context (e.g., plan name, drug name, ZIP code)
2. **Given** plan-specific data is available, **When** scoring occurs, **Then** the answer key reflects the correct answer for the specific plan/beneficiary

---

### Edge Cases

- Questions 7-13 (Medicare-only) require selecting a specific MA plan, PCP, and location from the SHIP study methodology. The study used CMS Plan Compare and plan directories. We may need mock/sample plan data.
- Dual-eligible persona requires state-specific Medicaid rules; we may use a representative state (e.g., Florida) as in the Medicare-only scenario.
- Some questions have multiple sub-components (e.g., enrollment timing: when to enroll AND when changes can be made). Scoring must address both.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: New scenarios MUST use exact question wording from SHIP eAppendix 1 (Medicare-only) or eAppendix 2 (Dual-eligible)
- **FR-002**: New scenarios MUST use scoring rubrics from SHIP eAppendix 4 with canonical facts for each question
- **FR-003**: Each scenario MUST have a unique scenario_id (e.g., SHIP-001, SHIP-003, SHIP-004) matching the SHIP question numbering where applicable
- **FR-004**: Scenarios MUST follow the existing JSON schema (persona, scripted_turns, answer_key, scoring_rubric)
- **FR-005**: Report generator MUST support displaying results for new scenarios (existing --scenario filter and grouping already support this)
- **FR-006**: SHIP baseline data in reports SHOULD be extended for new scenarios when published baseline data exists in SHIP Table 2

### Key Entities

- **SHIP Medicare-Only Script**: eAppendix 1 - 13+ questions for beneficiaries without Medicaid
- **SHIP Dual-Eligible Script**: eAppendix 2 - 6+ questions for beneficiaries with Medicaid
- **SHIP Scoring Guide**: eAppendix 4 - Question groups with canonical facts and scoring criteria
- **Scenario JSON**: Existing schema in scenarios/v1/ - persona, scripted_turns, answer_key, scoring_rubric
- **Reference**: reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 3 new Medicare-only scenarios (beyond scenario_002) are implemented and evaluable
- **SC-002**: Each new scenario produces valid rubric scores (1-4) when run through the evaluation pipeline
- **SC-003**: Report generation includes new scenarios in output when present in runs
- **SC-004**: Documentation (SCENARIOS.md) is updated to describe new scenarios and their SHIP study mapping

## SHIP Study Question Mapping (from Table 2)

### Medicare-Only (n=88) - Current: scenario_002 = Q3

| Q | Topic | Baseline (1/2/3/4) | Complexity |
|---|-------|-------------------|------------|
| 1 | Timing for initial enrollment and subsequent changes | 57.1 / 33.2 / 7.1 / 2.7 | Both scenarios |
| 2 | Medicare enrollment and employer plan interaction | 62.5 / 22.7 / 3.4 / 11.4 | Conceptual |
| 3 | Differences between TM and MA | 5.7 / 88.6 / 5.7 / 0 | **DONE** (scenario_002) |
| 4 | Medicare supplement plan considerations | 3.4 / 88.6 / 6.8 / 1.1 | Conceptual |
| 5 | Long-term care coverage | 86.4 / 1.1 / 5.7 / 5.7 | Conceptual |
| 6 | Prescription drug coverage | 23.9 / 69.3 / 5.7 / 1.1 | Conceptual |
| 7 | Whether specific PCP in network for MA plan | 26.1 / 0 / 64.8 / 9.1 | Plan-specific |
| 8 | Premium for specific MA plan | 19.3 / 47.7 / 21.6 / 9.1 | Plan-specific |
| 9 | Whether MA plan allows out-of-network care | 61.4 / 15.9 / 14.8 / 4.5 | Plan-specific |
| 10 | In-network PCP copay | 48.9 / 6.8 / 26.1 / 14.8 | Plan-specific |
| 11 | Maximum out-of-pocket limit | 46.6 / 11.4 / 28.4 / 13.6 | Plan-specific |
| 12 | Whether MA plan includes Part D | 76.1 / 2.3 / 15.9 / 2.3 | Plan-specific |
| 13 | Whether MA plan covers Lipitor/generic | 45.5 / 17.0 / 31.8 / 3.4 | Plan-specific |

### Dual-Eligible (n=96)

| Q | Topic | Baseline (1/2/3/4) |
|---|-------|-------------------|
| 1 | Options for enrolling with full Medicaid | 24.0 / 47.9 / 19.8 / 8.3 |
| 2 | Considerations for D-SNP | 1.0 / 74.0 / 24.0 / 1.0 |
| 3 | D-SNP availability in area | 68.8 / 9.4 / 16.7 / 5.2 |
| 4 | Coverage for long-term care | 10.4 / 59.4 / 9.4 / 20.8 |
| 5 | Medicaid coverage of Medicare costs | 65.6 / 10.4 / 18.8 / 4.2 |
| 6 | Medicare cost sharing assistance | 27.1 / 46.9 / 17.7 / 8.3 |
