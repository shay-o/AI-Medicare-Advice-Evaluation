# Getting Started - First Evaluation in 10 Minutes

**Complete checklist for running your first AI Medicare evaluation**

Follow these steps exactly to go from zero to your first results.

---

## ✅ Step 1: Install (2 minutes)

```bash
# Navigate to project directory
cd AI-Medicare-Advice-Evaluator

# Install with OpenRouter support
pip install -e ".[openrouter]"
```

**Verify installation:**
```bash
python -m src run --help
```

You should see usage information. If you get an error, check that Python 3.11+ is installed.

---

## ✅ Step 2: Test Without API Key (2 minutes)

Let's verify everything works using the fake adapter (no API calls):

```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target fake:perfect \
  --judges 2
```

**Expected output:**
```
======================================================================
Starting Trial: xxxxxxxx
...
[6/6] Finalizing results...
  ✓ Saved results to: runs/TIMESTAMP/results.jsonl

Trial Complete!
```

**If this works, your installation is correct!** ✅

**If you get errors:**
- Check Python version: `python --version` (need 3.11+)
- Reinstall: `pip install -e ".[openrouter]"`

---

## ✅ Step 3: Get OpenRouter API Key (3 minutes)

OpenRouter gives you access to 100+ AI models with one API key.

1. **Visit:** [openrouter.ai/keys](https://openrouter.ai/keys)
2. **Sign up** (free account)
3. **Create API key** (click "Create Key")
4. **Copy the key** (starts with `sk-or-...`)

**Add $5-10 credits** to your account (optional but recommended for testing)

---

## ✅ Step 4: Configure API Key (1 minute)

```bash
# Copy example file
cp .env.example .env

# Add your API key
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env
```

**Verify it's set:**
```bash
cat .env
```

You should see your API key.

---

## ✅ Step 5: Run First Real Evaluation (2 minutes)

Now let's evaluate a real AI model!

```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

**What this does:**
1. Asks GPT-4-turbo the [SHIP](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) Medicare Question #3
2. Uses Claude Haiku to verify the response
3. Scores it against the SHIP study rubric
4. Saves results to `runs/`

**This will take ~90 seconds and cost ~$0.09**

**Expected output:**
```
======================================================================
EVALUATION SUMMARY
======================================================================
Classification:    Substantive but Incomplete (Score 2)
Completeness:      71.4%
Accuracy:          100.0%
Claims Extracted:  20
Verifiers:         2
```

**Congratulations! You just evaluated your first AI model!** 🎉

---

## ✅ Step 6: View Results (1 minute)

```bash
# View summary
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores

# View full conversation
cat runs/$(ls -t runs/ | head -1)/transcripts/*.json | python -m json.tool | less
```

**Key results to look for:**

```json
{
  "rubric_score": 2,
  "rubric_label": "Substantive but Incomplete",
  "completeness_percentage": 0.714,
  "accuracy_percentage": 1.0,
  "missing_required_points": ["F5_MA", "F8_TM", "F1_TM", "F2_TM"]
}
```

**What this means:**
- **Score 2** = Good but not complete (typical for AI models)
- **71.4% complete** = Covered 10 of 14 required facts
- **100% accurate** = No incorrect information
- **Missing 4 facts** = Omitted some important details

---

## ✅ Step 7: Understanding the Score

### [SHIP Rubric](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) Explained:

| Score | What It Means | Your Action |
|-------|---------------|-------------|
| **1** | Perfect - all facts covered | ✅ Model passed with flying colors |
| **2** | Good - most facts covered | ✅ Typical result, acceptable |
| **3** | Poor - insufficient coverage | ⚠️ Model needs improvement |
| **4** | Failed - incorrect information | ❌ Model is unreliable |

**Your result (Score 2) means:**
- Model provided substantive, accurate information
- Covered most (71%) of the required facts
- Missing some details but no errors
- **This is a typical and acceptable result**

---

## ✅ Step 8: What to Try Next

### Option A: Test Another Model

```bash
# Try Claude Sonnet
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:anthropic/claude-3-5-sonnet \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

### Option B: Compare Multiple Models

```bash
# Use the comparison script
./compare_models.sh
```

This will test 5 models and generate a comparison table.

### Option C: Try Different Scenario

```bash
# Test with scenario_001 (simpler)
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

---

## 🎯 Quick Reference for Daily Use

### Test One Model
```bash
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:MODEL_NAME \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

### View Latest Results
```bash
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores
```

### Compare Models
```bash
./compare_models.sh
```

### Check Costs
[openrouter.ai/activity](https://openrouter.ai/activity)

---

## 🆘 Troubleshooting

### "API key not found"
```bash
# Check .env exists
cat .env

# If missing, add it
echo "OPENROUTER_API_KEY=sk-or-your_key" >> .env
```

### "Model not found"
- Check model name at [openrouter.ai/models](https://openrouter.ai/models)
- Must use format: `openrouter:provider/model-name`
- Example: `openrouter:openai/gpt-4-turbo`

### "Rate limit exceeded"
- Add delay between runs: `sleep 5`
- Or reduce judges: `--judges 1`

### "Command not found: python"
```bash
# Try python3 instead
python3 -m src run ...
```

---

## 📚 What to Read Next

Now that you've run your first evaluation:

1. **[SCENARIOS.md](SCENARIOS.md)** - Understand what scenario_002 tests (10 min read)
2. **[USER_GUIDE.md](USER_GUIDE.md)** - Learn advanced features (15 min read)
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Keep this open for quick commands
4. **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)** - Explore 100+ available models

---

## 💡 Tips for Success

### Cost Management
- Use Claude Haiku for agents (cheap and accurate)
- Use 1 judge for testing: `--judges 1`
- Test with fake adapter first: `--target fake:perfect`

### Good Practices
- Always test with `fake:perfect` before using real API
- Run scenario_002 for research-grade results (aligned with [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/))
- Keep QUICK_REFERENCE.md open while working
- Check costs regularly at openrouter.ai/activity

### Common Patterns
```bash
# Quick test (free)
--target fake:perfect

# Real evaluation (cheap)
--target openrouter:anthropic/claude-3-haiku --judges 1

# High quality (moderate cost)
--target openrouter:openai/gpt-4-turbo --judges 2

# Premium (expensive)
--target openrouter:anthropic/claude-3-opus --judges 2
```

---

## ✨ Success Checklist

- ✅ Installed system
- ✅ Tested with fake adapter
- ✅ Got OpenRouter API key
- ✅ Configured .env file
- ✅ Ran first evaluation
- ✅ Viewed results
- ✅ Understand the score
- ✅ Ready for more testing!

**You're now ready to evaluate AI models on Medicare questions!** 🎉

---

## 🚀 Next Steps

Pick one:

**A. Research Mode** - Compare models systematically
```bash
./compare_models.sh
```

**B. Deep Dive Mode** - Learn the [SHIP study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) methodology
- Read [SCENARIOS.md](SCENARIOS.md)
- Read [SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md)

**C. Developer Mode** - Understand the system
- Read [AGENTS_COMPLETE.md](AGENTS_COMPLETE.md)
- Read [ORCHESTRATOR_COMPLETE.md](ORCHESTRATOR_COMPLETE.md)

---

**Questions?** Check [USER_GUIDE.md](USER_GUIDE.md) Troubleshooting section or [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete guide catalog.

**Happy evaluating!** 🔬
