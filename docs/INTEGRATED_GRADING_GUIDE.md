# Integrated Grading Guide

## Overview

SHIP rubric grading runs automatically on every evaluation. There is no flag to enable it: `python -m src run` queries the target model and grades the responses in one pass.

Claim extraction and verification is the separate, opt-in step, enabled with `--verify-claims`.

## Single Command Workflow

```bash
python -m src run \
  --scenario medicare_only \
  --target-model fake:perfect
```

This command will:

1. Load all Medicare-Only questions
2. Run them against the target model
3. Save conversation transcripts
4. Grade responses using the SHIP rubric
5. Save all results

Add `--verify-claims` to additionally extract atomic claims, verify them against the scenario answer key, and adjudicate disagreements between judges.

## Quick Examples

### Example 1: Test with the fake adapter

```bash
python -m src run \
  --scenario scenarios/medicare_only/all_questions.json \
  --target-model fake:perfect \
  --run-id test_with_grading
```

**Output includes:**

```
[1/6] Generating questions...
  ✓ Generated 16 question(s)

[2/6] Querying target model...
  ✓ Received 32 turn(s)

[2.5/6] Grading responses using SHIP rubric...
  ✓ Graded 16 question(s)
  ✓ Accuracy: 87.5% (14/16 accurate & complete)

[continues...]
```

### Example 2: Grade real model responses

```bash
export ANTHROPIC_API_KEY=your_key_here

python -m src run \
  --scenario scenarios/medicare_only/all_questions.json \
  --target-model anthropic:claude-3-5-sonnet-20241022
```

### Example 3: Compare multiple models

```bash
python -m src run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --run-id comparison_perfect

python -m src run \
  --scenario medicare_only \
  --target-model fake:incomplete \
  --run-id comparison_incomplete
```

### Example 4: Use OpenRouter for grading

```bash
export OPENROUTER_API_KEY=your_key_here

python -m src run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade-model openrouter:anthropic/claude-3.5-sonnet
```

### Example 5: Add claim verification

```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target-model fake:perfect \
  --verify-claims \
  --judges 3
```

## What Gets Saved

```
runs/YOUR_RUN_ID/
├── run_metadata.json
├── results.jsonl
├── transcripts/
│   └── [trial_id]_transcript.json
└── intermediate/
    └── [trial_id]/
        ├── grading.json          ← SHIP rubric grading results
        ├── extraction.json       ← only with --verify-claims
        ├── verification_v1.json  ← only with --verify-claims
        ├── verification_v2.json  ← only with --verify-claims
        └── adjudication.json     ← only with --verify-claims
```

## Grading Results Format

The `grading.json` file contains:

```json
{
  "run_id": "abc123",
  "scenario": "medicare_only",
  "question_scores": [
    {
      "question_number": 1,
      "question_text": "When can I select my Medicare coverage plan?",
      "response_text": "[Full response]",
      "score": "accurate_complete",
      "explanation": "The response comprehensively addresses...",
      "group_id": "QG1",
      "group_name": "Timing for Initial Medicare Enrollment & Subsequent Changes",
      "criteria_met": [
        "Mentioned that you can enroll in Medicare/select coverage within 3 months of turning 65",
        "Substantively answered the 'when can I change it' question..."
      ],
      "criteria_missed": []
    }
  ]
}
```

The four rubric labels are `accurate_complete`, `substantive_incomplete`, `not_substantive`, and `incorrect`.

## Viewing Grading Results

### Option 1: Console output

Grading summary appears during execution:

```
[2.5/6] Grading responses using SHIP rubric...
  ✓ Graded 16 question(s)
  ✓ Accuracy: 87.5% (14/16 accurate & complete)
```

### Option 2: Read the JSON file

```bash
cat runs/YOUR_RUN_ID/intermediate/TRIAL_ID/grading.json | jq .
```

```bash
cat runs/YOUR_RUN_ID/intermediate/TRIAL_ID/grading.json | jq '{
  total: .question_scores | length,
  accurate_complete: [.question_scores[] | select(.score == "accurate_complete")] | length,
  substantive_incomplete: [.question_scores[] | select(.score == "substantive_incomplete")] | length,
  not_substantive: [.question_scores[] | select(.score == "not_substantive")] | length,
  incorrect: [.question_scores[] | select(.score == "incorrect")] | length
}'
```

### Option 3: Formatted report

```bash
python src/test_grading.py --run-dir runs/YOUR_RUN_ID
```

## Requirements

### API key for the grading model

- Default: `anthropic:claude-3-5-sonnet-20241022` (requires `ANTHROPIC_API_KEY`)
- OpenRouter: set `--grade-model openrouter:MODEL` (requires `OPENROUTER_API_KEY`)

```bash
export ANTHROPIC_API_KEY=your_key_here
# OR
export OPENROUTER_API_KEY=your_key_here
```

Because grading always runs, a grading model key is required even for `fake:` target models.

### Rubric coverage

All 20 SHIP question groups are mapped in `src/grading_rubric.py`, covering both scenarios:

- Medicare-Only: QG1, QG2, QG9–QG20
- Dual-Eligible: QG1, QG21–QG26

QG2 (the Spanish-translation question) is mapped but excluded from reported rubric aggregates, because the SHIP study recorded it yes/no rather than on the 4-point rubric. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

### Scenario ID convention

- Must contain "MO" for Medicare-Only
- Must contain "DE" for Dual-Eligible

## The Two Evaluation Methods

The system has two complementary evaluation approaches.

### Rubric-based (always on)

Evaluates overall response quality against the SHIP study rubric criteria, producing question-by-question scores with accuracy rates and explanations. This is what the published reports are built from.

### Claim-based (opt-in, `--verify-claims`)

Extracts specific atomic claims from responses, verifies each against the scenario answer key, and adjudicates disagreements between independent judges. Requires an `answer_key` in the scenario file.

```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target-model fake:perfect \
  --verify-claims
```

Running both gives a comprehensive assessment, and lets you compare claim-based against rubric-based scores.

## Performance Notes

### Grading speed

- Roughly 2-3 seconds per question with the Claude API
- 16 questions is roughly 30-45 seconds of grading

### API costs

- Around 500-1000 tokens per grading evaluation
- 16 questions is roughly $0.10-0.20 USD with Claude Sonnet
- Costs vary by the model chosen with `--grade-model`

## Troubleshooting

### "Grading system not available"

The `grader.py` module could not be imported. Check:

```bash
python -c "from src.grader import MedicareAdviceGrader"
```

### "grade_adapter is required for SHIP rubric grading"

No grading adapter could be constructed. Confirm the relevant API key is set, or pass `--grade-model` explicitly.

## See Also

- [GRADING_SYSTEM_README.md](GRADING_SYSTEM_README.md) - how the rubric mapping works
- [GRADING_INTEGRITY.md](GRADING_INTEGRITY.md) - known answer-key defect affecting the plan-specific questions
- [REPRODUCIBILITY.md](REPRODUCIBILITY.md) - how published figures are derived
