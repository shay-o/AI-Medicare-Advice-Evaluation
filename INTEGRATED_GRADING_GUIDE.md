# Integrated Grading - Quick Start Guide

## Overview

You can now run questions against AI models AND grade the responses in a single command using the `--grade` flag.

## Single Command Workflow

```bash
python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade
```

This single command will:
1. ✅ Load all Medicare-Only questions
2. ✅ Run them against the target model
3. ✅ Save conversation transcripts
4. ✅ Extract claims (existing workflow)
5. ✅ Verify claims (existing workflow)
6. ✅ **Grade responses using SHIP rubric** (NEW!)
7. ✅ Save all results

## Quick Examples

### Example 1: Test with Fake Adapter + Grading

```bash
# Fast test run with grading
python -m src.orchestrator run \
  --scenario scenarios/medicare_only/all_questions.json \
  --target-model fake:perfect \
  --grade \
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

[3/6] Extracting claims...
  ✓ Extracted 45 claim(s)

[continues...]
```

### Example 2: Grade Real Model Responses

```bash
# Run against Claude and grade
export ANTHROPIC_API_KEY=your_key_here

python -m src.orchestrator run \
  --scenario scenarios/medicare_only/all_questions.json \
  --target-model anthropic:claude-3-5-sonnet-20241022 \
  --grade
```

### Example 3: Compare Multiple Models

```bash
# Run the same questions against different models
python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade \
  --run-id comparison_perfect

python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:incomplete \
  --grade \
  --run-id comparison_incomplete
```

### Example 4: Use OpenRouter for Grading

```bash
# Grade using OpenRouter (requires OPENROUTER_API_KEY)
export OPENROUTER_API_KEY=your_key_here

python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade \
  --grade-model openrouter:anthropic/claude-3.5-sonnet
```

## What Gets Saved

With `--grade` enabled, your run directory includes:

```
runs/YOUR_RUN_ID/
├── run_metadata.json
├── results.jsonl
├── transcripts/
│   └── [trial_id]_transcript.json
└── intermediate/
    └── [trial_id]/
        ├── extraction.json
        ├── verification_v1.json
        ├── verification_v2.json
        ├── adjudication.json
        └── grading.json          ← NEW! SHIP rubric grading results
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
    },
    // ... more questions
  ]
}
```

## Viewing Grading Results

### Option 1: Check the Console Output

Grading summary appears during execution:
```
[2.5/6] Grading responses using SHIP rubric...
  ✓ Graded 16 question(s)
  ✓ Accuracy: 87.5% (14/16 accurate & complete)
```

### Option 2: Read the JSON File

```bash
# View grading results
cat runs/YOUR_RUN_ID/intermediate/TRIAL_ID/grading.json | jq .

# Get accuracy summary
cat runs/YOUR_RUN_ID/intermediate/TRIAL_ID/grading.json | jq '{
  total: .question_scores | length,
  accurate_complete: [.question_scores[] | select(.score == "accurate_complete")] | length,
  substantive_incomplete: [.question_scores[] | select(.score == "substantive_incomplete")] | length,
  not_substantive: [.question_scores[] | select(.score == "not_substantive")] | length,
  incorrect: [.question_scores[] | select(.score == "incorrect")] | length
}'
```

### Option 3: Use the Grading Test Script

```bash
# Generate formatted report from grading results
python src/test_grading.py --run-dir runs/YOUR_RUN_ID
```

## Requirements

### For Grading to Work

1. **API Key for grading model**:
   - Default: Uses `anthropic:claude-3-5-sonnet-20241022` (requires `ANTHROPIC_API_KEY`)
   - OpenRouter: Set `--grade-model openrouter:MODEL` (requires `OPENROUTER_API_KEY`)
   - Example:
     ```bash
     export ANTHROPIC_API_KEY=your_key_here
     # OR
     export OPENROUTER_API_KEY=your_key_here
     ```

2. **Questions must be mapped** in the rubric:
   - Medicare-Only: 14/16 questions mapped ✅
   - Dual-Eligible: 0/6 questions mapped ⬜

3. **Scenario ID convention**:
   - Must contain "MO" for Medicare-Only
   - Must contain "DE" for Dual-Eligible

## Without --grade Flag

If you don't use `--grade`, the orchestrator works exactly as before:
- No grading step
- No grading.json file
- No API key required for grading
- Only existing claim extraction/verification workflow

## Performance Notes

### Grading Speed

- **~2-3 seconds per question** with Claude API
- **16 questions ≈ 30-45 seconds** for grading
- Grading happens in parallel with other processing where possible

### API Costs

- Default uses `claude-3-5-sonnet-20241022` for grading
- ~500-1000 tokens per grading evaluation
- 16 questions ≈ $0.10-0.20 USD total with Claude Sonnet
- Costs vary by model chosen with `--grade-model`

## Comparison: Two Evaluation Methods

Your system now has **two complementary evaluation approaches**:

### Method 1: Claim-Based (Existing)
```bash
python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect
```
- Extracts specific claims from responses
- Verifies each claim against answer key
- Adjudicates disagreements
- Produces completeness/accuracy scores

### Method 2: Rubric-Based (New - with --grade)
```bash
python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade
```
- Evaluates overall response quality
- Uses SHIP study rubric criteria
- Provides question-by-question scores
- Produces accuracy rate and detailed explanations

### Both Together (Recommended!)
```bash
python -m src.orchestrator run \
  --scenario medicare_only \
  --target-model fake:perfect \
  --grade
```
- Runs BOTH evaluation methods
- Compare claim-based vs rubric-based scores
- Get comprehensive quality assessment
- Most complete evaluation

## Troubleshooting

### "Grading system not available"

The grader.py module couldn't be imported. Check:
```bash
python -c "from src.grader import MedicareAdviceGrader"
```

### "ANTHROPIC_API_KEY must be provided"

Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
# Then run again
```

### "No rubric found for question X"

This question isn't mapped yet (Q11, Q15, or dual-eligible questions). The grading will skip unmapped questions.

### Grading takes too long

- Normal: ~2-3 seconds per question
- If slower, check your internet connection
- Consider grading fewer questions initially

## Next Steps

1. **Try it out**: Run a test with `--grade`
2. **Compare methods**: Look at both claim-based and rubric-based scores
3. **Analyze differences**: See where the two methods agree/disagree
4. **Test real models**: Use with actual AI Medicare advice systems

## Examples Repository

See these files for more examples:
- `src/test_grading.py` - Standalone grading
- `examples/run_with_grading.py` - Programmatic usage
- `GRADING_SYSTEM_README.md` - Full grading documentation
