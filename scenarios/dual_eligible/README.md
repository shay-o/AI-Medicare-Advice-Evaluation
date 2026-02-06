# Dual-Eligible Scenario Files

This directory contains scenarios for testing AI Medicare advice for dual-eligible beneficiaries (those eligible for both Medicare and Medicaid).

## Source

Based on the SHIP (State Health Insurance Assistance Program) mystery-shopper study:
- **Study**: Dugan K et al. "Accuracy of Medicare information provided by State Health Insurance Assistance Programs." JAMA Network Open. 2025;8(4):e252834
- **Script**: eAppendix 2 - Dual-Eligible Scenario
- **Sample**: n=96 human counselors tested

## Persona

**Default persona** (can be customized):
- Age: 66
- Location: Los Angeles, CA (Los Angeles County)
- Coverage: Medicare Parts A & B + Full Medicaid (Medi-Cal in California)
- Situation: Dual-eligible beneficiary exploring coverage options
- PCP: Dr. Sarah Chen

## Available Scenario Files

### Complete Question Set

**File**: `all_questions.json`
- **Scenario ID**: SHIP-DE-ALL
- **Questions**: 8 questions (Q1-Q8) in sequence
- **Use**: Complete evaluation matching SHIP study protocol

### Individual Question Files

| File | Question | Topic | SHIP Baseline |
|------|----------|-------|---------------|
| `q02_medicaid_enrollment_options.json` | Q2 | Medicare enrollment options with full Medicaid | 24.0% accurate |
| `q03_dsnp_considerations.json` | Q3 | Considerations for D-SNP enrollment | **1.0% accurate** |
| `q05_longterm_care.json` | Q5 | Long-term care coverage | 10.4% accurate |

**Note**: Additional individual files can be created as needed for testing specific questions.

## Questions Overview

### Q1: Enrollment Timing & Changes
Same as Medicare-Only Q1, but in dual-eligible context.

### Q2: Medicare Enrollment Options with Full Medicaid
- Tests knowledge of D-SNP vs Original Medicare options
- Understanding of how Medicaid integrates with Medicare
- Baseline: 24.0% accurate-complete

### Q3: D-SNP Enrollment Considerations ⚠️
- **Most difficult question in entire SHIP study**
- Baseline: Only 1.0% accurate-complete
- Tests comprehensive knowledge of:
  - D-SNP benefits and limitations
  - Network restrictions
  - Care coordination
  - Medicaid integration

### Q4: D-SNP Availability
- Tests ability to direct beneficiaries to plan finder tools
- Geographic availability varies by county
- Baseline: 68.8% accurate-complete

### Q5: Long-Term Care Coverage
- Tests knowledge of Medicare vs Medicaid coverage for LTC
- Role of D-SNPs in coordinating LTC services
- State-specific Medicaid rules
- Baseline: 10.4% accurate-complete

### Q6: Medicaid Coverage of Medicare Costs
- Medicare Savings Programs (QMB, SLMB, QI)
- Premium and cost-sharing assistance
- Baseline: 65.6% accurate-complete

### Q7: Cost-Sharing Assistance Programs
- Programs for those not eligible for full Medicaid
- Extra Help/Low-Income Subsidy
- Income and asset limits
- Baseline: 27.1% accurate-complete

### Q8: Spanish Translation Services
Same as Medicare-Only Q16.

## Key Differences from Medicare-Only

1. **Beneficiary Profile**: Dual-eligible (Medicare + Medicaid)
2. **Plan Type Focus**: D-SNP (Dual Special Needs Plans)
3. **Cost Sharing**: Medicaid covers most Medicare cost-sharing
4. **Integration**: Coordinated care between Medicare and Medicaid
5. **State Variation**: Medicaid rules vary significantly by state

## Usage

### Run All Questions
```bash
python -m src.orchestrator run \
  --scenario scenarios/dual_eligible/all_questions.json \
  --target-model anthropic:claude-3-5-sonnet-20241022 \
  --grade
```

### Run Single Question
```bash
python -m src.orchestrator run \
  --scenario scenarios/dual_eligible/q03_dsnp_considerations.json \
  --target-model anthropic:claude-3-5-sonnet-20241022
```

### Using Scenario Name Shortcut
```bash
python -m src.orchestrator run \
  --scenario dual_eligible \
  --target-model openrouter:anthropic/claude-3-haiku
```

## Grading Status

**Current Status**: Grading rubric not yet implemented

To implement grading for dual-eligible questions:
1. Extract canonical facts from SHIP eAppendix 4
2. Define question groups in `src/grading_rubric.py`
3. Map each question to appropriate scoring criteria
4. Test with `--grade` flag

See: `GRADING_SYSTEM_README.md` for grading implementation details.

## Plan Information

Currently, plan information (D-SNP details) is **not included** in these scenarios per SHIP study fidelity.

To add D-SNP plan information for testing plan-specific questions:
1. Add `plan_information` field to scenario JSON
2. Include D-SNP details (name, type, premium, benefits)
3. See `PLAN_INFORMATION_GUIDE.md` for schema and examples

## State-Specific Considerations

**California (Medi-Cal)** was chosen as the default state because:
- Large dual-eligible population
- Well-established D-SNP market
- Comprehensive Medi-Cal benefits
- Active integration programs (Cal MediConnect)

To use a different state:
- Edit `persona.location`
- Update state-specific Medicaid program names
- Adjust answer keys for state variations

## SHIP Study Fidelity

Per project principles in `CLAUDE.md`:
- Questions match SHIP eAppendix 2 exactly
- Opening statement matches study protocol
- No system prompts or extra context provided to AI
- Tests AI as typical user would interact with it

## Next Steps

1. **Add individual scenario files** for Q1, Q4, Q6, Q7, Q8
2. **Implement grading rubric** for all 8 questions
3. **Create answer keys** with canonical facts from SHIP study
4. **Add D-SNP plan information** (optional)
5. **Test with multiple models** and compare to SHIP baselines
6. **Document results** and update this README

## Resources

- SHIP Study PDF: `/reference_material/jamanetwopen-e252834-s001_Medicare_Test_Scenarios.pdf`
- Grading Guide: `GRADING_SYSTEM_README.md`
- Plan Information: `PLAN_INFORMATION_GUIDE.md`
- Project Principles: `CLAUDE.md`
