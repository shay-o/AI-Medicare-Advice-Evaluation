# Tasks: Expand to Include All SHIP Study Questions

**Input**: spec.md, plan.md
**Reference**: reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf

## Phase 1: Infrastructure

- [ ] T001 Update scorer to support generic SHIP rubric (when scenario lacks _MA/_TM facts) - use required_points coverage for Score 1/2/3
- [ ] T002 Add baseline data for new scenarios to report_utils.py get_baseline_data() when SHIP Table 2 data exists

## Phase 2: Medicare-Only Conceptual Scenarios

- [ ] T003 Create scenario_003.json - SHIP Q1: Timing for initial enrollment and subsequent changes
- [ ] T004 Create scenario_004.json - SHIP Q4: Medicare supplement (Medigap) considerations
- [ ] T005 Create scenario_005.json - SHIP Q5: Long-term care coverage
- [ ] T006 Create scenario_006.json - SHIP Q6: Prescription drug coverage (Part D)
- [ ] T007 Create scenario_007.json - SHIP Q2: Medicare enrollment and employer plan interaction

## Phase 3: Documentation and Verification

- [ ] T008 Update SCENARIOS.md with new scenario descriptions and SHIP mapping
- [ ] T009 Run evaluation with new scenario and verify scoring
- [ ] T010 Regenerate reports and verify new scenarios appear
