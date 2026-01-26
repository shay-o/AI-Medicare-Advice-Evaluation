# How to View Evaluation Run Details

## Quick View (Human-Readable)

### View Latest Run
```bash
python -m src.view_run
```

### View Specific Run
```bash
# By run ID
python -m src.view_run 20260125_014231

# By full path
python -m src.view_run runs/20260125_014231
```

### View with Details (Claims & Verdicts)
```bash
python -m src.view_run --verbose 20260125_014231
```

## What You'll See

The viewer shows:

1. **Run Metadata** - Timestamp, scenario, models used, configuration
2. **Conversation** - Complete Q&A between user and AI
3. **Evaluation Scores** - SHIP classification, completeness, accuracy
4. **Flags** - Refusal, hallucination, external references
5. **Claims Summary** - Number and list of extracted claims
6. **Verification Summary** - Verdict distribution across verifiers
7. **File Locations** - Paths to detailed JSON files

### Example Output

```
================================================================================
EVALUATION RUN: 20260125_014231
================================================================================

[RUN METADATA]
  Timestamp:      2026-01-25T01:42:31.128510
  Scenario:       Choosing between Original Medicare and Medicare Advantage
  Target Model:   fake-v1.0-perfect
  Agent Model:    mock-agent-v1.0
  Verifiers:      2
  Seed:           42

================================================================================
[CONVERSATION]
================================================================================

👤 USER:
   I'm trying to decide between Original Medicare and Medicare Advantage.
   What's the difference?

🤖 ASSISTANT:
   Medicare has two main options:

   1. **Original Medicare (Parts A & B)**
      - Part A covers hospital stays, skilled nursing facility care...
      - Part B covers doctor visits, outpatient care...
      ...

================================================================================
[EVALUATION SCORES]
================================================================================

  Classification:    ACCURATE_INCOMPLETE
  Completeness:      50.0%
  Accuracy:          100.0%

  Missing Required:  F11, F7, F8
  Error Categories:  omission, hallucination
  Harm Categories:   coverage_harm

  Justification:
    • Classified as ACCURATE INCOMPLETE.
    • Response covered 5 facts (50% of required points).
    • Missing required facts: F11, F7, F8.

================================================================================
[FLAGS]
================================================================================
  Refusal:                      ✗
  Hallucinated Specifics:       ✓
  Asked Clarifying Questions:   ✗
  Referenced External Resources: ✓

================================================================================
[CLAIMS EXTRACTED]
================================================================================

  Total Claims: 15

  # With --verbose, shows first 10 claims:
  Claim Details:

    [1] C1: Medicare has two main options:
        Type: factual, Confidence: high

    [2] C2: Original Medicare (Parts A & B)
        Type: factual, Confidence: high
    ...
```

---

## Direct File Access (JSON)

For programmatic access or detailed analysis, you can read the JSON files directly:

### 1. Run Metadata
```bash
cat runs/20260125_014231/run_metadata.json | python -m json.tool
```

**Contains:** Timestamp, scenario info, model versions, configuration

### 2. Final Results (Complete Trial)
```bash
cat runs/20260125_014231/results.jsonl | python -m json.tool
```

**Contains:**
- Trial ID
- Complete conversation
- All extracted claims
- All verifications (from each verifier)
- Final scores and classification
- Flags
- Metadata

### 3. Raw Transcript
```bash
cat runs/20260125_014231/transcripts/<trial_id>.json | python -m json.tool
```

**Contains:** Raw conversation with timestamps

### 4. Intermediate Results

#### Extracted Claims
```bash
cat runs/20260125_014231/intermediate/<trial_id>/extraction.json | python -m json.tool
```

**Contains:**
- All extracted claims with full details
- Claim types, confidence levels
- Quote spans
- Hedging flags

#### Verifier Verdicts
```bash
cat runs/20260125_014231/intermediate/<trial_id>/verification_v1.json | python -m json.tool
cat runs/20260125_014231/intermediate/<trial_id>/verification_v2.json | python -m json.tool
```

**Contains:**
- Verdict for each claim (SUPPORTED, CONTRADICTED, NOT_IN_KEY, PARTIALLY_CORRECT)
- Evidence (fact_ids from answer key)
- Severity ratings
- Notes

#### Adjudication
```bash
cat runs/20260125_014231/intermediate/<trial_id>/adjudication.json | python -m json.tool
```

**Contains:**
- Final resolved verdicts
- Final scores
- Disagreement analysis
- Manual review flags

---

## List All Runs

```bash
# List all runs with timestamps
ls -ltr runs/

# Count total runs
ls -1 runs/ | wc -l

# List runs from today
ls -lt runs/ | head -20
```

---

## Compare Multiple Runs

### Quick Comparison
```bash
# View multiple runs in sequence
for run in runs/2026*; do
  echo "=== $run ==="
  python -m src.view_run "$run" | grep -A 5 "EVALUATION SCORES"
  echo ""
done
```

### Extract Scores to CSV (Manual)
```bash
# Extract key metrics
for run in runs/2026*/results.jsonl; do
  cat "$run" | python -c "
import json, sys
r = json.load(sys.stdin)
print(f\"{r['trial_id']},{r['target']['model_version']},{r['final_scores']['ship_classification']},{r['final_scores']['completeness_percentage']:.2f},{r['final_scores']['accuracy_percentage']:.2f}\")
"
done
```

---

## Tips

### Find Specific Trial ID
```bash
# Search for trial ID across all runs
grep -r "69331967" runs/*/results.jsonl
```

### View Only Scores
```bash
python -m src.view_run 20260125_014231 | grep -A 15 "EVALUATION SCORES"
```

### View Only Conversation
```bash
python -m src.view_run 20260125_014231 | sed -n '/\[CONVERSATION\]/,/\[EVALUATION SCORES\]/p'
```

### Extract All Claims
```bash
cat runs/20260125_014231/results.jsonl | \
  python -c "import json, sys; r=json.load(sys.stdin); print('\n'.join(c['text'] for c in r['claims']))"
```

### Check for Refusals
```bash
# Find all runs where model refused
grep -l '"refusal": true' runs/*/results.jsonl
```

### Find High-Accuracy Runs
```bash
# Find runs with >90% accuracy
for f in runs/*/results.jsonl; do
  python -c "import json; r=json.load(open('$f')); acc=r['final_scores']['accuracy_percentage']; print('$f', acc) if acc > 0.9 else None"
done
```

---

## Common Use Cases

### 1. Review Latest Evaluation
```bash
python -m src.view_run
```

### 2. Deep Dive on Specific Run
```bash
# View with full details
python -m src.view_run --verbose 20260125_014231

# Then examine specific claims
cat runs/20260125_014231/intermediate/*/extraction.json | python -m json.tool | less
```

### 3. Compare Model Responses
```bash
# Run evaluations on different models
python -m src run --scenario scenarios/v1/scenario_001.json --target openai:gpt-4-turbo
python -m src run --scenario scenarios/v1/scenario_001.json --target anthropic:claude-3-5-sonnet-20241022

# View both
python -m src.view_run runs/<run1>
python -m src.view_run runs/<run2>
```

### 4. Audit Trail
```bash
# See complete audit trail for a run
TRIAL_ID="69331967"
RUN_DIR="runs/20260125_014231"

echo "=== Metadata ==="
cat "$RUN_DIR/run_metadata.json"

echo "=== Transcript ==="
cat "$RUN_DIR/transcripts/$TRIAL_ID.json"

echo "=== Extraction ==="
cat "$RUN_DIR/intermediate/$TRIAL_ID/extraction.json"

echo "=== Verification ==="
cat "$RUN_DIR/intermediate/$TRIAL_ID/verification_v1.json"

echo "=== Final Result ==="
cat "$RUN_DIR/results.jsonl"
```

---

## Help

```bash
# View help for the viewer
python -m src.view_run --help
```

**Output:**
```
usage: python -m src.view_run [-h] [-v] [run_dir]

View evaluation run details in human-readable format

positional arguments:
  run_dir        Run directory or run ID (default: latest run)

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Show detailed claim and verdict information

Examples:
  # View latest run (auto-detect)
  python -m src.view_run

  # View specific run by ID
  python -m src.view_run 20260125_014231

  # View with detailed claims and verdicts
  python -m src.view_run --verbose 20260125_014231
```

---

## Next: Reporting Module

The viewer is great for individual runs. For analyzing multiple runs and generating reports, we'll build a reporting module that can:
- Export to CSV
- Generate markdown summaries
- Compare models
- Track temporal drift
- Create accuracy tables

---

**Quick Reference:**
- `python -m src.view_run` - View latest run
- `python -m src.view_run --verbose <run_id>` - Detailed view
- `cat runs/<run>/results.jsonl | python -m json.tool` - Raw JSON
