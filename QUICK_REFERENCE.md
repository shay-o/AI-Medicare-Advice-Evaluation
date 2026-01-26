# Quick Reference Card

**For fast access to common commands and information**

---

## Installation

```bash
# Install with OpenRouter support (recommended)
pip install -e ".[openrouter]"

# Set up API key
cp .env.example .env
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env
```

---

## Basic Commands

### Test Installation
```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target fake:perfect \
  --judges 2
```

### Evaluate One Model
```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

### Compare Multiple Models
```bash
chmod +x compare_models.sh
./compare_models.sh
```

---

## Common Models

### OpenRouter Format: `openrouter:provider/model-name`

```bash
# OpenAI
--target openrouter:openai/gpt-4-turbo
--target openrouter:openai/gpt-4o
--target openrouter:openai/gpt-3.5-turbo

# Anthropic
--target openrouter:anthropic/claude-3-5-sonnet
--target openrouter:anthropic/claude-3-opus
--target openrouter:anthropic/claude-3-haiku

# Google
--target openrouter:google/gemini-pro-1.5
--target openrouter:google/gemini-flash-1.5

# Meta
--target openrouter:meta-llama/llama-3.1-70b-instruct
--target openrouter:meta-llama/llama-3.1-405b-instruct

# Mistral
--target openrouter:mistralai/mistral-large
--target openrouter:mistralai/mixtral-8x7b-instruct
```

Find more: [openrouter.ai/models](https://openrouter.ai/models)

---

## Available Scenarios

```bash
# List scenarios
ls scenarios/v1/

# Scenario 001: General MA vs TM (synthetic)
--scenario scenarios/v1/scenario_001.json

# Scenario 002: SHIP Question #3 (research-grade)
--scenario scenarios/v1/scenario_002.json
```

Details: [SCENARIOS.md](SCENARIOS.md)

---

## Viewing Results

### Latest Run
```bash
# View summary
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores

# View full results
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | less

# View conversation
cat runs/$(ls -t runs/ | head -1)/transcripts/*.json | python -m json.tool | less
```

### All Runs
```bash
# List all runs
ls -lt runs/

# Compare scores across runs
for run in runs/*/results.jsonl; do
  echo "=== $run ==="
  cat "$run" | python -m json.tool | grep -A 5 '"final_scores":'
  echo ""
done
```

---

## Understanding Scores (SHIP Rubric)

| Score | Label | Meaning |
|-------|-------|---------|
| **1** | Accurate and Complete | All 14 facts covered |
| **2** | Substantive but Incomplete | Most facts covered (typical) |
| **3** | Not Substantive | Insufficient coverage |
| **4** | Incorrect | Materially wrong information |

**Good result:** Score 1-2, Completeness >70%, Accuracy 100%

**Typical result:** Score 2, Completeness 60-80%, Accuracy 100%

**Poor result:** Score 3-4, Completeness <60%, Accuracy <100%

---

## Cost Management

### Typical Costs (per evaluation)
- GPT-4 target + Claude Haiku agents: ~$0.09
- 5 model comparison: ~$0.45

### Save Money
```bash
# Use 1 judge instead of 2
--judges 1

# Use cheaper target models
--target openrouter:openai/gpt-3.5-turbo
--target openrouter:google/gemini-flash-1.5

# Use mock agents (free, less accurate)
# Omit --agent-model flag, defaults to fake:perfect
```

### Check Spending
[openrouter.ai/activity](https://openrouter.ai/activity)

---

## Troubleshooting

### API Key Error
```bash
# Check .env exists
cat .env

# Add key if missing
echo "OPENROUTER_API_KEY=sk-or-your_key" >> .env
```

### Model Not Found
- Check model name at [openrouter.ai/models](https://openrouter.ai/models)
- Use format: `openrouter:provider/model-name`

### Rate Limit
- Add delays: `sleep 5` between runs
- Reduce judges: `--judges 1`

### Scenario Not Found
```bash
# List available scenarios
ls scenarios/v1/
```

---

## Full Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete usage guide
- **[SCENARIOS.md](SCENARIOS.md)** - Scenario explanations
- **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)** - OpenRouter details
- **[README.md](README.md)** - Project overview

---

## Example Workflow

```bash
# 1. Test installation
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target fake:perfect \
  --judges 2

# 2. Evaluate one model
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2

# 3. View results
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores

# 4. Compare multiple models
./compare_models.sh

# 5. Check costs
open https://openrouter.ai/activity
```

---

## Command Options Reference

| Option | Description | Example | Default |
|--------|-------------|---------|---------|
| `--scenario` | Test scenario file | `scenarios/v1/scenario_002.json` | Required |
| `--target` | Model to evaluate | `openrouter:openai/gpt-4-turbo` | Required |
| `--agent-model` | Model for agents | `openrouter:anthropic/claude-3-haiku` | `fake:perfect` |
| `--judges` | Number of verifiers | `2` | `2` |
| `--seed` | Random seed | `42` | `42` |
| `--output-dir` | Results directory | `runs` | `runs` |

---

**For detailed explanations, see [USER_GUIDE.md](USER_GUIDE.md)**
