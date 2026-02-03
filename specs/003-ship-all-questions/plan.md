# Implementation Plan: Expand to Include All SHIP Study Questions

**Branch**: `003-ship-all-questions` | **Date**: 2026-02-02 | **Spec**: [spec.md](./spec.md)

## Summary

Add new evaluation scenarios corresponding to all questions in the SHIP mystery-shopper study (Dugan et al. 2025). Currently only Question #3 (TM vs MA comparison) exists as scenario_002. This plan adds scenarios for the remaining Medicare-only conceptual questions first (Q1, Q2, Q4, Q5, Q6), then dual-eligible questions, with plan-specific questions (Q7-Q13) as a later phase requiring additional infrastructure.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Existing evaluation pipeline (orchestrator, agents, schemas)
**Reference**: reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf (eAppendix 1, 2, 4)
**Existing Pattern**: scenario_002.json structure

## Phased Approach

### Phase 1: Medicare-Only Conceptual Questions (P1)

Add 5 new scenarios. Exact wording and canonical facts from SHIP eAppendix 1 and 4.

| Scenario ID | SHIP Q | Topic | Notes |
|-------------|--------|-------|-------|
| SHIP-001 | 1 | Timing for initial enrollment and subsequent changes | Both scenarios; 2 components: enroll timing + change periods |
| SHIP-002 | 2 | Medicare enrollment and employer plan interaction | Medicare-only |
| SHIP-003 | 3 | TM vs MA differences | **Exists** - scenario_002 (rename or keep) |
| SHIP-004 | 4 | Medicare supplement (Medigap) considerations | Medicare-only |
| SHIP-005 | 5 | Long-term care coverage | Medicare-only |
| SHIP-006 | 6 | Prescription drug coverage (Part D) | Medicare-only |

**Note**: scenario_002 uses scenario_id "SHIP-002" but maps to SHIP Q3. We may keep SHIP-002 for backward compatibility and use SHIP-003 for the TM/MA scenario in new numbering, or keep current IDs. Recommendation: Keep scenario_002 as SHIP-002 (TM vs MA). Add SHIP-001, SHIP-004, SHIP-005, SHIP-006 for Q1, Q4, Q5, Q6. Add SHIP-003 for Q2 (employer plan) - but that would conflict. Better: use SHIP-001, SHIP-002 (existing), SHIP-004, SHIP-005, SHIP-006. For Q2 (employer), use SHIP-002B or similar. Actually the simplest is to number by SHIP question: SHIP-Q1, SHIP-Q2, etc. Or keep SHIP-002 for Q3 and use SHIP-001, SHIP-004, SHIP-005, SHIP-006 for the others. Skip SHIP-003 to avoid confusion with scenario_002. So: SHIP-001 (enrollment), SHIP-004 (Medigap), SHIP-005 (LTC), SHIP-006 (Part D). For Q2 (employer) we need SHIP-002 - but that's taken. Use SHIP-002B or SHIP-Q2. I'll use SHIP-001, SHIP-002 (existing Q3), SHIP-004, SHIP-005, SHIP-006. Add SHIP-003 for employer plan - no, that reuses 3. Let me use: SHIP-001 (Q1), SHIP-002 (Q3 existing), SHIP-004 (Q4), SHIP-005 (Q5), SHIP-006 (Q6). For Q2 we need a new file - call it SHIP-002B or scenario_003.json with id SHIP-Q2. To minimize confusion: scenario_001 = synthetic, scenario_002 = SHIP Q3. New: scenario_003 = SHIP Q1, scenario_004 = SHIP Q4, etc. Use scenario_id that matches: SHIP-001, SHIP-002 (existing), SHIP-004, SHIP-005, SHIP-006. For Q2 (employer): SHIP-002B is odd. Use SHIP-003 for Q2 - the number in scenario_id doesn't have to match file number. So: SHIP-001 (Q1), SHIP-002 (Q3), SHIP-003 (Q2), SHIP-004 (Q4), SHIP-005 (Q5), SHIP-006 (Q6).

### Phase 2: Dual-Eligible Questions (P2)

Add 6 scenarios with dual-eligible persona. New persona: Medicare + Medicaid eligible.

### Phase 3: Plan-Specific Questions (P3)

Requires mock plan data or Plan Finder integration. Deferred.

## Project Structure

```
scenarios/v1/
├── scenario_001.json   # Existing - synthetic
├── scenario_002.json  # Existing - SHIP Q3 (TM vs MA)
├── scenario_003.json  # NEW - SHIP Q1 (Enrollment timing)
├── scenario_004.json  # NEW - SHIP Q4 (Medigap)
├── scenario_005.json  # NEW - SHIP Q5 (Long-term care)
└── scenario_006.json  # NEW - SHIP Q6 (Part D)
```

## Implementation Notes

- Each new scenario follows scenario_002.json structure exactly
- Persona can reuse Medicare-only persona from scenario_002 for Q1, Q4, Q5, Q6 (same beneficiary profile)
- Q2 (employer plan) uses same persona - they have employer coverage
- Answer key canonical_facts must be extracted from eAppendix 4
- report_utils.py get_baseline_data() may need extension for new scenario IDs when baseline exists in SHIP Table 2
