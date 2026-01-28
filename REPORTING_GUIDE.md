# Reporting Guide

**Generate SHIP-style accuracy tables from evaluation runs**

This guide explains how to generate accuracy reports that replicate [Table 2 from the SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/).

---

## Quick Start

### Basic Table (Group by Scenario)

**By default, incomplete runs (without rubric scores) are excluded:**

```bash
python scripts/generate_accuracy_table.py
```

**Output:**
```
Question/Scenario                                   Total      Score 1      Score 2      Score 3      Score 4
Test: MA vs TM Comparison                              4     1 (25.0%)     2 (50.0%)     1 (25.0%)     0 ( 0.0%)
```

Note: The "Incomplete" column is hidden by default since incomplete runs are excluded.

### Table by Model (Most Useful)

```bash
python scripts/generate_accuracy_table.py --by-model --include-baseline
```

**Output:**
```
Scenario / Model                                              Total      Score 1      Score 2      Score 3      Score 4

Test: MA vs TM Comparison (maps to SHIP Medicare scenario)
SHIP Baseline: TM vs MA differences (Medicare, n=88)             88     5 ( 5.7%)    77 (88.6%)     5 ( 5.7%)     0 ( 0.0%)
anthropic/claude-3-5-sonnet                                       1     0 ( 0.0%)     1 (100.0%)     0 ( 0.0%)     0 ( 0.0%)
openai/gpt-4-turbo                                                2     1 (50.0%)     1 (50.0%)     0 ( 0.0%)     0 ( 0.0%)
```

**Key improvements:**
- Baseline appears as a peer row (not indented) alongside models
- Easy to compare AI vs human performance
- Incomplete runs excluded by default for cleaner output

### Detailed Statistics

```bash
python scripts/generate_accuracy_table.py --detailed
```

**Includes:**
- Average completeness percentage
- Average accuracy percentage

---

## Understanding the Table

### Column Definitions

Based on the SHIP study rubric:

| Column | Score | Meaning |
|--------|-------|---------|
| **Score 1: Accurate & Complete** | 1 | All required facts covered correctly |
| **Score 2: Accurate but Incomplete** | 2 | Some facts covered, no major errors (typical result) |
| **Score 3: Not Substantive** | 3 | Insufficient coverage or "I don't know" |
| **Score 4: Incorrect** | 4 | Materially wrong information that could affect decisions |
| **Incomplete Data** | - | Runs that failed or did not produce a rubric score |

**Important:** Percentages for Scores 1-4 sum to 100% and exclude incomplete runs. Incomplete % is calculated from total runs (including incomplete).

### Reading the Results

**Default output (incomplete runs excluded):**
```
Test: MA vs TM Comparison                              4    1 (25.0%)    2 (50.0%)    1 (25.0%)    0 (0.0%)
SHIP Baseline: TM vs MA differences (Medicare, n=88)  88    5 ( 5.7%)   77 (88.6%)    5 ( 5.7%)    0 (0.0%)
```

**Interpretation:**
- **Total n = 4**: 4 completed evaluations (incomplete runs excluded by default)
- **Score 1: 1 (25.0%)**: 1 of 4 runs (25%) achieved perfect accuracy
- **Score 2: 2 (50.0%)**: 2 of 4 runs (50%) were substantive but incomplete
- **Score 3: 1 (25.0%)**: 1 of 4 runs (25%) did not provide substantive information
- **Score 4: 0 (0.0%)**: 0 of 4 runs provided incorrect information
- **Baseline row**: Shows human counselor performance (5.7% complete, 88.6% incomplete)

**Note:** Percentages for Scores 1-4 add to 100% (25% + 50% + 25% + 0% = 100%)

**With incomplete runs included (--include-incomplete):**
```
Test: MA vs TM Comparison    4/7    1 (25.0%)    2 (50.0%)    1 (25.0%)    0 (0.0%)    3 (42.9%)
```

**Additional column:**
- **Total n = 4/7**: 7 total evaluations, 4 completed with scores, 3 incomplete
- **Incomplete: 3 (42.9%)**: 3 of 7 total runs failed or had no score

---

## Command Options

### Filter to Specific Scenario

```bash
python scripts/generate_accuracy_table.py --scenario SHIP-002
```

### Include SHIP Study Baseline (Human Counselors)

Compare AI performance directly to human counselors from the original SHIP study:

```bash
python scripts/generate_accuracy_table.py --by-model --include-baseline
```

**Output:**
```
Scenario / Model                                              Total      Score 1      Score 2      Score 3      Score 4

Test: MA vs TM Comparison (maps to SHIP Medicare scenario)
SHIP Baseline: TM vs MA differences (Medicare, n=88)             88     5 ( 5.7%)    77 (88.6%)     5 ( 5.7%)     0 ( 0.0%)
anthropic/claude-3-5-sonnet                                       1     0 ( 0.0%)     1 (100.0%)     0 ( 0.0%)     0 ( 0.0%)
openai/gpt-4-turbo                                                2     1 (50.0%)     1 (50.0%)     0 ( 0.0%)     0 ( 0.0%)
```

The baseline appears as a peer row alongside models, making direct comparison easy.

### Include Incomplete Runs

By default, incomplete runs (without rubric scores) are excluded. To include them:

```bash
python scripts/generate_accuracy_table.py --include-incomplete
```

This adds an "Incomplete" column and shows the total as "scored/total" (e.g., "4/7").

### Custom Runs Directory

```bash
python scripts/generate_accuracy_table.py --runs-dir path/to/runs
```

### All Options Combined

```bash
python scripts/generate_accuracy_table.py \
  --by-model \
  --scenario SHIP-002 \
  --include-baseline \
  --detailed
```

---

## Common Use Cases

### 1. Compare AI Models to Human Baseline (Most Useful)

```bash
# Compare all AI models to human counselors (clean output, no incomplete runs)
python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002
```

This shows which AI models outperform human SHIP counselors and by how much. Incomplete runs are excluded by default for cleaner output.

### 2. Compare Multiple Models

```bash
# Run evaluations for multiple models
./compare_models.sh

# Generate comparison table with human baseline
python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002
```

### 3. Include Incomplete Runs in Analysis

```bash
# Show all runs including incomplete ones
python scripts/generate_accuracy_table.py --by-model --include-baseline --include-incomplete --scenario SHIP-002
```

Use this when you need to see failure rates or debug incomplete evaluations.

### 4. Track Model Performance Over Time

```bash
# Keep separate run directories
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:openai/gpt-4-turbo --output-dir runs/2026-01
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:openai/gpt-4-turbo --output-dir runs/2026-02

# Compare both time periods to baseline
python scripts/generate_accuracy_table.py --runs-dir runs/2026-01 --by-model --include-baseline
python scripts/generate_accuracy_table.py --runs-dir runs/2026-02 --by-model --include-baseline
```

### 5. Generate Report for Publication

```bash
# Generate all tables with baseline data (clean, no incomplete runs)
python scripts/generate_accuracy_table.py --by-model --include-baseline > reports/accuracy_by_model.txt
python scripts/generate_accuracy_table.py --include-baseline > reports/accuracy_by_scenario.txt
python scripts/generate_accuracy_table.py --detailed > reports/detailed_stats.txt
```

---

## Comparing to SHIP Study Results

### Understanding SHIP Study Scenarios

The SHIP study tested human counselors on **TWO main scenarios:**

1. **"Medicare"** = Medicare-only scenario (n=88)
   - Beneficiary without Medicaid
   - Questions about Traditional Medicare vs Medicare Advantage
   - Tests general Medicare knowledge

2. **"Dual"** = Dual-eligible scenario (n=96)
   - Beneficiary with both Medicare and Medicaid
   - Questions about D-SNPs (Dual Special Needs Plans)
   - Tests knowledge of integrated coverage

Each scenario included multiple questions testing different aspects of counselor knowledge.

### Direct Comparison with Baseline Data

**NEW:** You can now directly compare AI performance to human counselors using the `--include-baseline` flag:

```bash
python scripts/generate_accuracy_table.py --scenario SHIP-002 --include-baseline
```

**Output:**
```
Test: MA vs TM Comparison (maps to SHIP Medicare scenario)   4/7      1 (25.0%)     2 (50.0%)     1 (25.0%)     0 ( 0.0%)     3 (42.9%)
  └─ SHIP Baseline: TM vs MA differences (Medicare, n=88)     88     5 ( 5.7%)    77 (88.6%)     5 ( 5.7%)     0 ( 0.0%)     0 ( 0.0%)
```

This shows:
- **Top row**: Your AI test results
- **Bottom row**: SHIP study baseline (human counselors) from the **Medicare scenario**

### SHIP Study Baseline Performance

From [Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/), for the MA vs TM comparison question:

**Human counselor performance (Medicare scenario, n=88):**
- Accurate & Complete: 5.7%
- Accurate but Incomplete: 88.6%
- Not Substantive: 5.7%
- Incorrect: 0.0%

**Key insight:** Human counselors were highly consistent (88.6% substantive) but rarely provided complete answers (only 5.7%).

### Compare AI to Human Performance

Use the `--by-model` and `--include-baseline` flags together for the best comparison:

```bash
python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002
```

This shows:
1. The SHIP study baseline (human counselors) first
2. Each AI model's performance below it
3. Easy visual comparison between AI and human performance

**Key comparisons:**
- Are AI models achieving similar accuracy rates to humans?
- Are AI models more likely to be incomplete vs. incorrect?
- How do different AI models compare to each other and to humans?
- Which AI models outperform human counselors on specific metrics?

---

## Export Options

### Export to CSV

```bash
python scripts/generate_accuracy_table.py --format csv > results.csv
```

*(Not yet implemented - feature request)*

### Export to JSON

```bash
python scripts/generate_accuracy_table.py --format json > results.json
```

*(Not yet implemented - feature request)*

---

## Interpreting Completeness and Accuracy

### Completeness Percentage

**Formula:** `covered_facts / required_facts`

**Example:**
- Required facts: 14 (6 MA + 8 TM)
- Covered facts: 10
- Completeness: 71.4%

**Interpretation:**
- 100%: Model covered all required facts
- 70-99%: Model covered most facts (typical for Score 2)
- 50-69%: Model covered some facts (borderline Score 2/3)
- <50%: Insufficient coverage (likely Score 3)

### Accuracy Percentage

**Formula:** `correct_claims / verifiable_claims`

**Example:**
- Verifiable claims: 20
- Correct claims: 20
- Accuracy: 100%

**Interpretation:**
- 100%: No incorrect information
- 95-99%: Minor inaccuracies
- 90-94%: Some inaccuracies
- <90%: Significant errors (likely Score 4)

---

## Troubleshooting

### "No results found"

**Problem:** Script can't find any results.jsonl files

**Solutions:**
```bash
# Check runs directory exists
ls runs/

# Check results files exist
ls runs/*/results.jsonl

# Verify you're in the correct directory
pwd
# Should be: /path/to/AI-Medicare-Advice-Evaluator
```

### "All scores showing 0%"

**Problem:** Results don't have rubric scores

**Cause:** Scenario doesn't define a scoring_rubric

**Solution:**
- Only scenario_002.json (SHIP-002) has SHIP rubric defined
- Filter to SHIP-002: `--scenario SHIP-002`
- Or add rubric to other scenarios

### "Incomplete data showing"

**Problem:** Some results showing in "Incomplete Data" column

**Causes:**
1. Scenario doesn't have a rubric defined (scenario_001.json)
2. Evaluation failed or crashed mid-run
3. Agents couldn't parse the response

**Check:**
```bash
# View a specific result file
cat runs/TIMESTAMP/results.jsonl | python -m json.tool | grep rubric_score
```

**If `rubric_score: null`:**
- The scenario doesn't have a rubric defined
- Only SHIP-aligned scenarios (scenario_002.json) have rubrics
- Add `--scenario SHIP-002` to filter to scored runs only

**To investigate incomplete runs:**
```bash
# Find runs without scores
for run in runs/*/results.jsonl; do
  score=$(cat "$run" | python -m json.tool | grep '"rubric_score"' | head -1)
  if [[ $score == *"null"* ]]; then
    echo "Incomplete: $run"
    cat "$run" | python -m json.tool | grep '"scenario_id"'
  fi
done
```

---

## Advanced Usage

### Programmatic Access

```python
from pathlib import Path
import sys
sys.path.append('scripts')

from generate_accuracy_table import load_all_results, calculate_accuracy_stats, group_by_scenario

# Load results
results = load_all_results(Path("runs"))

# Group by scenario
grouped = group_by_scenario(results)

# Calculate stats
for scenario_id, scenario_results in grouped.items():
    stats = calculate_accuracy_stats(scenario_results)
    print(f"{scenario_id}: {stats['score_1_pct']:.1f}% complete")
```

### Custom Filtering

```python
# Filter to specific model
gpt4_results = [r for r in results if "gpt-4" in r.get("target", {}).get("model_name", "")]

# Filter to high accuracy
high_accuracy = [r for r in results if r.get("final_scores", {}).get("accuracy_percentage", 0) > 0.95]

# Filter by date
recent = [r for r in results if r.get("timestamp", "").startswith("2026-01-26")]
```

---

## Future Enhancements

Planned features:

- [x] Comparison to baseline (IMPLEMENTED: use `--include-baseline`)
- [ ] CSV export
- [ ] JSON export
- [ ] Statistical significance testing
- [ ] Confidence intervals
- [ ] Trend analysis over time
- [ ] Cost per accuracy tier
- [ ] HTML report generation

---

## Examples from Real Data

### Example 1: Single Model Evaluation

```bash
$ python scripts/generate_accuracy_table.py --scenario SHIP-002

SHIP Question #3: MA vs TM Comparison    4/7    1 (25.0%)    2 (50.0%)    1 (25.0%)    0 (0.0%)    3 (42.9%)
```

**Interpretation:**
- Tested 7 times total, 4 completed with scores
- 25% of scored runs achieved perfect accuracy (Score 1)
- 50% of scored runs were substantive but incomplete (Score 2)
- 25% of scored runs were not substantive (Score 3)
- 0% provided incorrect information (Score 4)
- 43% of all runs were incomplete (no score)

### Example 2: Multi-Model Comparison

```bash
$ python scripts/generate_accuracy_table.py --by-model --scenario SHIP-002

SHIP Question #3: MA vs TM Comparison
  anthropic/claude-3-5-sonnet     1      0 ( 0.0%)    1 (100.0%)    0 ( 0.0%)    0 ( 0.0%)    0 ( 0.0%)
  fake:perfect                 1/2      0 ( 0.0%)    0 ( 0.0%)    1 (100.0%)    0 ( 0.0%)    1 (50.0%)
  openai/gpt-4-turbo           2/4      1 (50.0%)    1 (50.0%)    0 ( 0.0%)    0 ( 0.0%)    2 (50.0%)
```

**Interpretation:**
- **Claude-3.5-sonnet**: 100% substantive but incomplete (1 run, all scored)
- **fake:perfect**: 100% not substantive (1 scored run), 50% incomplete (1 of 2 runs)
- **GPT-4-turbo**: 50% perfect, 50% incomplete (2 scored runs), 50% incomplete (2 of 4 runs)
- Need more data for statistical significance

---

## Reference

**Original SHIP Study Table 2:**
https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/table/zoi250151t2/

**Full study citation:**
Dugan K, et al. "Evaluating State Health Insurance Assistance Program (SHIP) Counselor Responses." *JAMA Network Open*. 2025;8(4):e252834.

---

**For more information:**
- [USER_GUIDE.md](USER_GUIDE.md) - Running evaluations
- [SCENARIOS.md](SCENARIOS.md) - Understanding test scenarios
- [SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md) - Scoring methodology
