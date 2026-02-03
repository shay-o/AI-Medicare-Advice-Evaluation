# Test Scenarios

Scenarios are organized to match the SHIP study structure (Dugan et al. 2025).

## Directory Structure

```
scenarios/
├── medicare_only/     # Medicare-only script (eAppendix 1, n=88)
│   ├── q01_enrollment_timing.json   # SHIP-MO-Q1
│   └── q03_tm_vs_ma.json             # SHIP-MO-Q3
├── dual_eligible/     # Dual-eligible script (eAppendix 2, n=96)
│   └── (questions to be added)
└── v1/                # Legacy/synthetic scenarios
    └── scenario_001.json   # synthetic-tm-vs-ma (system testing)
```

## Running Evaluations

**Run all Medicare-only questions:**
```bash
python -m src run --scenario medicare_only --target openai:gpt-4-turbo
```

**Run all dual-eligible questions:**
```bash
python -m src run --scenario dual_eligible --target openai:gpt-4-turbo
```

**Run a single question:**
```bash
python -m src run --scenario scenarios/medicare_only/q03_tm_vs_ma.json --target openai:gpt-4-turbo
```

## Scenario ID Naming

- **SHIP-MO-Qn**: Medicare-only, Question n (e.g., SHIP-MO-Q1, SHIP-MO-Q3)
- **SHIP-DE-Qn**: Dual-eligible, Question n (e.g., SHIP-DE-Q1)
- **synthetic-***: Non-SHIP scenarios for system testing

## SHIP Study Alignment

Results structure matches SHIP Table 2:
- Medicare-only: n=88 human counselors
- Dual-eligible: n=96 human counselors
- Baseline data in report_utils.py maps scenario_id to SHIP study percentages
