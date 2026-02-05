# Plan Information Feature

## Quick Reference: Substitutable Variables

| Placeholder | Set In | Field Path | Example |
|------------|--------|------------|---------|
| `[plan name]` | plan_information | `plan_information.plan_name` | Humana Gold Plus HMO |
| `[doctor name]` | persona | `persona.primary_care_physician` | Dr. Maria Rodriguez |
| `[service area]` | plan_information | `plan_information.service_area` | Miami-Dade County, FL |

**Note:** Both `[placeholder]` and `{placeholder}` formats are supported.

## Overview

This feature allows you to include specific Medicare Advantage plan details in your scenarios for testing plan-specific questions (Q7-Q14 in the SHIP study).

## SHIP Study Fidelity

**IMPORTANT:** Per SHIP study methodology, plan information is used ONLY for:
1. **Question substitution** - Replace `[plan name]` with actual plan name
2. **Answer key verification** - Define correct answers for grading

**Plan details are NOT provided to the target AI model as context.** The model must respond based on its own knowledge, just as in the original SHIP study. This maintains fair evaluation conditions.

## How It Works

### 1. Add Plan Information to Scenario

Add a `plan_information` field to your scenario JSON:

```json
{
  "scenario_id": "SHIP-MO-PLAN-TEST",
  "title": "Medicare-Only with Plan Details",
  "plan_information": {
    "plan_name": "Humana Gold Plus HMO",
    "plan_type": "HMO",
    "contract_number": "H1036-333",
    "service_area": "Miami-Dade County, FL",
    "monthly_premium": 25.0,
    "part_b_premium": 174.70,
    "deductible": 0.0,
    "max_out_of_pocket": 3400.0,
    "primary_care_copay": 10.0,
    "specialist_copay": 40.0,
    "out_of_network_allowed": false,
    "includes_drug_coverage": true,
    "drug_formulary": [
      {
        "drug_name": "Lipitor",
        "is_covered": true,
        "tier": 2,
        "copay": 15.0,
        "prior_authorization_required": false
      }
    ],
    "requires_referrals": true,
    "available_in_service_area": true
  },
  "scripted_turns": [
    {
      "turn_id": "Q8",
      "question_number": 8,
      "user_message": "What is the monthly premium for [plan name]?"
    }
  ]
}
```

### 2. Use Placeholders in Questions

## Supported Placeholders

The orchestrator automatically substitutes the following placeholders in questions:

| Placeholder | Set In | Source Field | Example Value |
|------------|--------|--------------|---------------|
| `[plan name]` or `{plan_name}` | `plan_information` | `plan_name` | "Humana Gold Plus HMO" |
| `[doctor name]` or `{doctor_name}` | `persona` | `primary_care_physician` | "Dr. Maria Rodriguez" |
| `[service area]` or `{service_area}` | `plan_information` | `service_area` | "Miami-Dade County, FL" |

### Setting Placeholder Values

**Plan Name:**
```json
{
  "plan_information": {
    "plan_name": "Humana Gold Plus HMO"
  }
}
```

**Doctor Name:**
```json
{
  "persona": {
    "primary_care_physician": "Dr. Maria Rodriguez"
  }
}
```

**Service Area:**
```json
{
  "plan_information": {
    "service_area": "Miami-Dade County, FL"
  }
}
```

### Using Placeholders in Questions

```json
"scripted_turns": [
  {
    "user_message": "What is the monthly premium for [plan name]?"
  },
  {
    "user_message": "Can you tell me if [doctor name] is in the network for [plan name]?"
  },
  {
    "user_message": "Is [plan name] available in [service area]?"
  }
]
```

### Questions Using Placeholders in SHIP Study

From `scenarios/medicare_only/all_questions.json`:

- **Q7**: `My friend told me about [plan name]. Can you tell me if [doctor name] is in the network there?`
- **Q8**: `What is the monthly premium for [plan name]?`
- **Q9**: `Would [plan name] let me go out of network?`
- **Q10**: `What is the copay for a primary care doctor visit for [plan name]?`
- **Q11**: `What is the copay to see a specialist for [plan name]?`
- **Q12**: `For [plan name], is there a limit on out-of-pocket costs I would have to pay each year?`
- **Q13**: `Does [plan name] include prescription drug coverage?`
- **Q14a**: `I take Lipitor. Is that covered by [plan name]?`
- **Q14b**: `Is a generic version of Lipitor covered? I would be willing to take that.`
- **Q15**: `How much would Lipitor be out of pocket vs. the generic version?`

### 3. Complete Example

Here's a complete scenario showing all placeholder usage:

```json
{
  "scenario_id": "SHIP-MO-ALL",
  "persona": {
    "age": 64,
    "location": "Miami, FL 33166 (Miami-Dade County)",
    "current_coverage": "Employer-based health coverage",
    "situation": "Turning 65 in 2 months...",
    "primary_care_physician": "Dr. Maria Rodriguez"
  },
  "plan_information": {
    "plan_name": "Humana Gold Plus HMO",
    "plan_type": "HMO",
    "service_area": "Miami-Dade County, FL",
    "monthly_premium": 25.0,
    "primary_care_copay": 10.0,
    "specialist_copay": 40.0,
    "max_out_of_pocket": 3400.0,
    "includes_drug_coverage": true
  },
  "scripted_turns": [
    {
      "user_message": "My friend told me about [plan name]. Can you tell me if [doctor name] is in the network there?"
    }
  ]
}
```

**After substitution:**
- `[plan name]` → `Humana Gold Plus HMO`
- `[doctor name]` → `Dr. Maria Rodriguez`

**Question becomes:**
"My friend told me about Humana Gold Plus HMO. Can you tell me if Dr. Maria Rodriguez is in the network there?"

### 4. Run the Evaluation

The orchestrator automatically substitutes placeholders:

```bash
python -m src.orchestrator run \
  --scenario scenarios/medicare_only/example_with_plan_info.json \
  --target-model anthropic:claude-3-5-sonnet-20241022
```

**What happens:**
1. Orchestrator loads scenario with plan information
2. Questions with `[plan name]` are substituted with "Humana Gold Plus HMO"
3. Target model receives: "What is the monthly premium for Humana Gold Plus HMO?"
4. Model responds based on its knowledge (may or may not know the answer)
5. Answer is verified against plan_information values

## Plan Information Schema

### Required Fields

- `plan_name` (string) - Full plan name
- `plan_type` (string) - One of: "HMO", "PPO", "PFFS", "SNP"
- `monthly_premium` (float) - Plan premium amount
- `out_of_network_allowed` (bool) - Whether OON care is allowed
- `includes_drug_coverage` (bool) - Whether Part D is included

### Optional Fields

- `contract_number` (string) - CMS contract number
- `service_area` (string) - Geographic coverage area
- `part_b_premium` (float) - Part B premium for reference
- `deductible` (float) - Annual deductible
- `max_out_of_pocket` (float) - Annual MOOP limit
- `primary_care_copay` (float) - PCP visit copay
- `specialist_copay` (float) - Specialist visit copay
- `out_of_network_primary_care_copay` (float) - OON PCP copay
- `out_of_network_specialist_copay` (float) - OON specialist copay
- `drug_formulary` (array) - List of covered drugs
- `additional_benefits` (array) - Extra benefits like dental, vision
- `requires_referrals` (bool) - Whether referrals needed
- `available_in_service_area` (bool) - Plan availability

### Drug Coverage Schema

```json
{
  "drug_name": "Lipitor",
  "is_covered": true,
  "tier": 2,
  "copay": 15.0,
  "prior_authorization_required": false,
  "quantity_limits": "30 day supply"
}
```

## Example Scenario

See: `scenarios/medicare_only/example_with_plan_info.json`

This demonstrates:
- Complete plan information for Humana Gold Plus HMO
- Questions 7-14 (plan-specific questions)
- Placeholder substitution
- Drug formulary information

## Testing

### Verify Schema Loading

```bash
python -c "
from src.schemas import Scenario
import json

with open('scenarios/medicare_only/example_with_plan_info.json') as f:
    scenario = Scenario(**json.load(f))

print(f'Plan: {scenario.plan_information.plan_name}')
print(f'Premium: \${scenario.plan_information.monthly_premium}')
"
```

### Test Substitution

```bash
python -m src.orchestrator run \
  --scenario scenarios/medicare_only/example_with_plan_info.json \
  --target-model fake:perfect
```

Check the transcript - questions should have "Humana Gold Plus HMO" instead of "[plan name]".

## Where to Find Real Plan Data

Plan information can be obtained from:

1. **Medicare.gov Plan Finder** - https://www.medicare.gov/plan-compare/
2. **CMS Plan Benefit Package (PBP) Files** - Detailed plan specifications
3. **Plan Summary of Benefits** - Documents provided by insurers
4. **Evidence of Coverage (EOC)** - Complete plan details

## Best Practices

### Do:
✓ Use real plan data from Medicare.gov when available
✓ Keep plan_information up to date with current year data
✓ Include all relevant fields for the questions you're testing
✓ Test with multiple plan types (HMO, PPO) to compare AI performance

### Don't:
✗ Provide plan details to the AI model via system prompts
✗ Add extra context that wasn't in the SHIP study
✗ Artificially help the AI by giving it plan information upfront
✗ Use fictitious plan data - use real Medicare plans

## Future Enhancements

Potential additions:
- Support for multiple plans in one scenario (comparison questions)
- Plan availability date ranges
- Network provider lists
- More detailed drug formulary with step therapy requirements
- Plan star ratings
