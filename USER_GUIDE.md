# User Guide - AI Medicare Evaluation Harness

**For researchers and evaluators unfamiliar with the codebase**

This guide explains how to run evaluations, test multiple models, and interpret results.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Scenarios](#understanding-scenarios)
3. [Running Single Evaluations](#running-single-evaluations)
4. [Running Multi-Model Comparisons](#running-multi-model-comparisons)
5. [Using OpenRouter](#using-openrouter)
6. [Interpreting Results](#interpreting-results)
7. [Cost Management](#cost-management)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- An API key from OpenRouter, OpenAI, Anthropic, or Google

### Installation

```bash
# Clone or download the repository
cd AI-Medicare-Advice-Evaluator

# Install with OpenRouter support (recommended - one key for all models)
pip install -e ".[openrouter]"

# OR install with specific provider
pip install -e ".[openai]"      # OpenAI only
pip install -e ".[anthropic]"   # Anthropic only
pip install -e ".[all]"         # All providers
```

### Set Up API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# For OpenRouter (recommended):
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env

# For direct providers:
echo "OPENAI_API_KEY=sk-your_openai_key" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-your_key" >> .env
```

### First Test Run (No API Key Required)

```bash
# Test with fake adapter to verify installation
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target fake:perfect \
  --judges 2
```

If this completes successfully, you're ready to evaluate real models!

---

## Understanding Scenarios

Scenarios are test cases based on the SHIP mystery-shopper study. Each scenario:
- Contains a specific Medicare question
- Has an answer key with 14+ canonical facts
- Uses SHIP study scoring rubrics
- Tests different aspects of Medicare knowledge

### Available Scenarios

See [SCENARIOS.md](SCENARIOS.md) for detailed descriptions.

**Quick Reference:**

| Scenario | Question Topic | Facts | Difficulty |
|----------|---------------|-------|------------|
| **scenario_001.json** | General: Original Medicare vs Medicare Advantage | 13 facts | Medium |
| **scenario_002.json** | SHIP Q3: MA vs TM comparison with pros/cons | 14 facts | High |

**Recommendation:** Start with **scenario_002.json** - it's the most aligned with SHIP study methodology.

---

## Running Single Evaluations

### Basic Command Structure

```bash
python -m src run \
  --scenario scenarios/v1/SCENARIO_FILE.json \
  --target PROVIDER:MODEL_NAME \
  --agent-model PROVIDER:AGENT_MODEL \
  --judges NUMBER_OF_JUDGES
```

### Example: Evaluate GPT-4 on SHIP Question #3

```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

**What this does:**
1. Asks GPT-4-turbo the SHIP Question #3
2. Uses Claude Haiku to extract and verify claims
3. Runs 2 independent verifiers for reliability
4. Scores against SHIP rubric
5. Saves results to `runs/TIMESTAMP/`

### Command Options

| Option | Description | Example | Default |
|--------|-------------|---------|---------|
| `--scenario` | Path to scenario JSON file | `scenarios/v1/scenario_002.json` | Required |
| `--target` | Model to evaluate | `openrouter:openai/gpt-4-turbo` | Required |
| `--agent-model` | Model for evaluation agents | `openrouter:anthropic/claude-3-haiku` | `fake:perfect` |
| `--judges` | Number of independent verifiers | `2` | `2` |
| `--seed` | Random seed for reproducibility | `42` | `42` |
| `--output-dir` | Where to save results | `runs` | `runs` |

### Cost-Saving Tips

**Use cheaper models for agents:**
```bash
# Target: GPT-4 (expensive)
# Agents: Claude Haiku (cheap)
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 1  # Use 1 judge instead of 2 to save costs
```

**Use mock agents (FREE but less accurate):**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --judges 2
# Agents default to fake:perfect (no API calls)
```

---

## Running Multi-Model Comparisons

### Method 1: Shell Script (Recommended)

Create a file `compare_models.sh`:

```bash
#!/bin/bash

# Test scenario
SCENARIO="scenarios/v1/scenario_002.json"

# Agent model (same for all tests for consistency)
AGENT_MODEL="openrouter:anthropic/claude-3-haiku"

# Models to test
MODELS=(
  "openrouter:openai/gpt-4-turbo"
  "openrouter:openai/gpt-4o"
  "openrouter:anthropic/claude-3-5-sonnet"
  "openrouter:google/gemini-pro-1.5"
  "openrouter:meta-llama/llama-3.1-70b-instruct"
)

# Run evaluation for each model
for MODEL in "${MODELS[@]}"; do
  echo "========================================="
  echo "Evaluating: $MODEL"
  echo "========================================="

  python -m src run \
    --scenario "$SCENARIO" \
    --target "$MODEL" \
    --agent-model "$AGENT_MODEL" \
    --judges 2

  # Small delay to avoid rate limits
  sleep 2
done

echo ""
echo "All evaluations complete!"
echo "Results saved in runs/"
```

Run it:
```bash
chmod +x compare_models.sh
./compare_models.sh
```

### Method 2: Manual Sequential Runs

```bash
# Run each model one at a time
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2

python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:anthropic/claude-3-5-sonnet \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2

python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:google/gemini-pro-1.5 \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

### Comparing Results

After running multiple models, compare them:

```bash
# View all results
for run in runs/*/results.jsonl; do
  echo "=== $run ==="
  cat "$run" | python -m json.tool | grep -A 3 '"target":'
  cat "$run" | python -m json.tool | grep -A 5 '"final_scores":'
  echo ""
done
```

Or create a comparison script `compare_results.sh`:

```bash
#!/bin/bash

echo "Model Comparison - SHIP Question #3"
echo "===================================="
printf "%-40s %-10s %-15s %-10s %-10s\n" "Model" "Score" "Label" "Complete" "Accuracy"
echo "------------------------------------------------------------------------------------"

for run in runs/*/results.jsonl; do
  MODEL=$(cat "$run" | python -m json.tool | grep '"model_version"' | head -1 | cut -d'"' -f4)
  SCORE=$(cat "$run" | python -m json.tool | grep '"rubric_score"' | head -1 | awk '{print $2}' | tr -d ',')
  LABEL=$(cat "$run" | python -m json.tool | grep '"rubric_label"' | head -1 | cut -d'"' -f4)
  COMPLETE=$(cat "$run" | python -m json.tool | grep '"completeness_percentage"' | head -1 | awk '{print $2}' | tr -d ',')
  ACCURACY=$(cat "$run" | python -m json.tool | grep '"accuracy_percentage"' | head -1 | awk '{print $2}' | tr -d ',')

  COMPLETE_PCT=$(echo "$COMPLETE * 100" | bc -l | xargs printf "%.1f%%")
  ACCURACY_PCT=$(echo "$ACCURACY * 100" | bc -l | xargs printf "%.1f%%")

  printf "%-40s %-10s %-15s %-10s %-10s\n" "$MODEL" "$SCORE" "$LABEL" "$COMPLETE_PCT" "$ACCURACY_PCT"
done
```

---

## Using OpenRouter

### Why OpenRouter?

**Benefits:**
- ✅ One API key for 100+ models
- ✅ Single bill across all providers
- ✅ Access to models without direct API (Llama, Mistral, etc.)
- ✅ Easy cost comparison
- ✅ Automatic fallbacks if model unavailable

### Setup

1. Get API key: [openrouter.ai/keys](https://openrouter.ai/keys)
2. Add to `.env`:
   ```bash
   echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env
   ```

### Model Name Format

OpenRouter uses: `provider/model-name`

**Popular models:**

```bash
# OpenAI Models
--target openrouter:openai/gpt-4-turbo
--target openrouter:openai/gpt-4o
--target openrouter:openai/gpt-3.5-turbo

# Anthropic Claude
--target openrouter:anthropic/claude-3-5-sonnet
--target openrouter:anthropic/claude-3-opus
--target openrouter:anthropic/claude-3-haiku

# Google Gemini
--target openrouter:google/gemini-pro-1.5
--target openrouter:google/gemini-flash-1.5

# Meta Llama
--target openrouter:meta-llama/llama-3.1-70b-instruct
--target openrouter:meta-llama/llama-3.1-405b-instruct

# Mistral
--target openrouter:mistralai/mistral-large
--target openrouter:mistralai/mixtral-8x7b-instruct
```

See full list: [openrouter.ai/models](https://openrouter.ai/models)

### Example: Test 5 Models via OpenRouter

```bash
# All using single OpenRouter API key
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:openai/gpt-4-turbo --judges 2
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:anthropic/claude-3-5-sonnet --judges 2
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:google/gemini-pro-1.5 --judges 2
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:meta-llama/llama-3.1-70b-instruct --judges 2
python -m src run --scenario scenarios/v1/scenario_002.json --target openrouter:mistralai/mistral-large --judges 2
```

---

## Interpreting Results

### Console Output

When evaluation completes, you'll see:

```
======================================================================
EVALUATION SUMMARY
======================================================================
Trial ID:          4af33dd6
Scenario:          SHIP Medicare-Only Question #3
Target Model:      openai/gpt-4-turbo
Classification:    Substantive but Incomplete (Score 2)
Completeness:      71.4%
Accuracy:          100.0%
Claims Extracted:  20
Verifiers:         2
Flags:
  - Refusal:       False
  - Hallucinated:  False
  - References:    False

Justification:
  Classified as Substantive but Incomplete (Score 2).
  Response covered 10 facts (71% of required points).
  Missing required facts: F1_TM, F2_TM, F5_MA, F8_TM.
======================================================================
```

### Understanding the Scores

#### SHIP Rubric (Scenario 002)

| Score | Label | Meaning |
|-------|-------|---------|
| **1** | Accurate and Complete | Covered ALL 14 required facts (6 MA + 8 TM) |
| **2** | Substantive but Incomplete | Covered SOME facts from both categories but not all |
| **3** | Not Substantive | Did not substantively discuss the topic |
| **4** | Incorrect | Provided materially incorrect information |

#### Key Metrics

**Completeness (%)** - What portion of required facts were covered
- 100% = All facts covered
- 71% = Most facts covered (like above example)
- 50% = Half the facts covered
- <30% = Insufficient coverage

**Accuracy (%)** - What portion of claims were correct
- 100% = No incorrect information
- 94% = Minor inaccuracies
- <90% = Significant errors

**Good Result Example:**
- Score: 1 (Accurate and Complete)
- Completeness: 100%
- Accuracy: 100%

**Common Result Example:**
- Score: 2 (Substantive but Incomplete)
- Completeness: 60-80%
- Accuracy: 100%

**Poor Result Example:**
- Score: 3 (Not Substantive)
- Completeness: <30%
- Accuracy: N/A

### Viewing Detailed Results

Results are saved in `runs/TIMESTAMP/`:

```bash
# Latest run
ls -t runs/ | head -1

# View full results JSON
cat runs/20260126_190421/results.jsonl | python -m json.tool | less

# View just the conversation
cat runs/20260126_190421/transcripts/*.json | python -m json.tool | less

# View which facts were covered
cat runs/20260126_190421/results.jsonl | python -m json.tool | grep -A 20 '"final_scores"'
```

### Understanding Missing Facts

The justification shows which facts were missing:

```
Missing required facts: F1_TM, F2_TM, F5_MA, F8_TM
```

Look these up in the scenario file to see what was omitted:

```bash
grep -A 5 '"fact_id": "F5_MA"' scenarios/v1/scenario_002.json
```

Output:
```json
"fact_id": "F5_MA",
"statement": "With a Medicare Advantage plan, you must continue to pay the Medicare Part B premium in addition to the Medicare Advantage Plan premium.",
"severity_if_wrong": "medium"
```

This tells you **what the model failed to mention** - a common and important detail.

---

## Cost Management

### Estimated Costs (per evaluation)

**With OpenRouter (typical pricing):**

| Component | Model | Cost per Call | Calls | Total |
|-----------|-------|---------------|-------|-------|
| Target Model | GPT-4-turbo | ~$0.02 | 1 | ~$0.02 |
| Extractor | Claude Haiku | ~$0.01 | 1 | ~$0.01 |
| Verifier 1 | Claude Haiku | ~$0.03 | 1 | ~$0.03 |
| Verifier 2 | Claude Haiku | ~$0.03 | 1 | ~$0.03 |
| **Total** | | | | **~$0.09** |

**Testing 5 models:** ~$0.45 total

### Cost Optimization Strategies

**1. Use cheaper agent models:**
```bash
# Use Claude Haiku for agents (very cheap)
--agent-model openrouter:anthropic/claude-3-haiku
```

**2. Reduce number of judges:**
```bash
# Use 1 judge instead of 2 (50% cost savings on verification)
--judges 1
```

**3. Use mock agents (FREE but less accurate):**
```bash
# Agents use fake adapter (no API calls)
# Only pay for target model
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --judges 2
# Cost: ~$0.02 per run
```

**4. Test with cheaper target models first:**
```bash
# Test with GPT-3.5-turbo or Gemini Flash first
--target openrouter:openai/gpt-3.5-turbo      # ~$0.001 per call
--target openrouter:google/gemini-flash-1.5    # ~$0.0001 per call
```

### Monitoring Costs

Check OpenRouter dashboard: [openrouter.ai/activity](https://openrouter.ai/activity)

---

## Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error:**
```
ValueError: OpenRouter API key not provided
```

**Solution:**
```bash
# Check .env file
grep OPENROUTER_API_KEY .env

# If missing, add it
echo "OPENROUTER_API_KEY=sk-or-your_key" >> .env
```

#### 2. Model Not Found

**Error:**
```
RuntimeError: OpenRouter API error: Model not found
```

**Solution:**
- Check model name format at [openrouter.ai/models](https://openrouter.ai/models)
- Use exact format: `provider/model-name`
- Example: `anthropic/claude-3-5-sonnet` NOT `claude-3-5-sonnet`

#### 3. Rate Limit Exceeded

**Error:**
```
RuntimeError: OpenRouter rate limit exceeded
```

**Solution:**
- Add delays between runs: `sleep 5`
- Reduce number of judges: `--judges 1`
- Check your OpenRouter limits/credits

#### 4. Scenario File Not Found

**Error:**
```
FileNotFoundError: scenarios/v1/scenario_003.json
```

**Solution:**
```bash
# List available scenarios
ls scenarios/v1/

# Use an existing scenario
--scenario scenarios/v1/scenario_002.json
```

#### 5. JSON Parsing Errors

If you see JSON parsing errors with real LLM agents, this was fixed in the recent update. Make sure you have the latest code.

### Getting Help

1. Check existing documentation:
   - [SCENARIOS.md](SCENARIOS.md) - Scenario details
   - [OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md) - OpenRouter specifics
   - [SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md) - Scoring rubric

2. Check logs:
   ```bash
   # View latest run
   cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool
   ```

3. Test with fake adapter first:
   ```bash
   # Verify system works without API calls
   python -m src run \
     --scenario scenarios/v1/scenario_002.json \
     --target fake:perfect \
     --judges 2
   ```

---

## Next Steps

1. **Run your first evaluation** with fake adapter
2. **Set up OpenRouter** API key
3. **Test one model** on scenario_002
4. **Compare 3-5 models** using the comparison script
5. **Interpret results** using SHIP rubric
6. **Document findings** for your research

---

## Quick Reference Card

```bash
# Basic evaluation
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2

# View results
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores

# List available scenarios
ls scenarios/v1/

# Check OpenRouter models
open https://openrouter.ai/models

# View cost
open https://openrouter.ai/activity
```

---

**For more details:**
- Scenarios: [SCENARIOS.md](SCENARIOS.md)
- OpenRouter: [OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)
- Architecture: [README.md](README.md)
