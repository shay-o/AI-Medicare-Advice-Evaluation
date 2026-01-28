# AI Medicare Evaluation Harness

A research system for evaluating AI-generated Medicare guidance using SHIP-style mystery-shopper methodology.

## Purpose

This system reproduces the methodology of the [SHIP mystery-shopper study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/) to evaluate:

- **Accuracy** - Factual correctness of Medicare information
- **Completeness** - Coverage of required information points
- **Safety and harm risk** - Potential for harmful misinformation

This system evaluates responses, not intent, UX quality, tone, or persuasion.

---

## 📚 Documentation

**New to this project?**

👉 **Start with [USER_GUIDE.md](USER_GUIDE.md)** - step-by-step instructions for running tests

**Quick access:**
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command reference card (keep this open!)
- **[SCENARIOS.md](SCENARIOS.md)** - What each test scenario evaluates
- **[REPORTING_GUIDE.md](REPORTING_GUIDE.md)** - Generate SHIP-style accuracy tables
- **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)** - How to access 100+ models with one API key
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete documentation catalog

**For developers:**
- **[ADAPTERS_COMPLETE.md](ADAPTERS_COMPLETE.md)** - LLM adapter implementation
- **[ORCHESTRATOR_COMPLETE.md](ORCHESTRATOR_COMPLETE.md)** - Pipeline architecture
- **[AGENTS_COMPLETE.md](AGENTS_COMPLETE.md)** - Agent system details

---

## Architecture

The system uses strict role separation with five specialized agents:

1. **Questioner** - Generates beneficiary questions from scenarios
2. **Extractor** - Converts AI responses into atomic, verifiable claims
3. **Verifier** - Judges claims against answer keys (multiple independent instances)
4. **Scorer** - Computes accuracy and completeness metrics
5. **Adjudicator** - Resolves disagreements between verifiers

## Quick Start

### 1. Install

```bash
# Recommended: Install with OpenRouter support (one API key for 100+ models)
pip install -e ".[openrouter]"

# Or install with specific provider
pip install -e ".[openai]"      # OpenAI only
pip install -e ".[anthropic]"   # Anthropic only
pip install -e ".[all]"         # All providers
```

### 2. Set Up API Keys

```bash
# Copy example environment file
cp .env.example .env

# Add your OpenRouter API key (recommended)
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env

# Or add direct provider keys
echo "OPENAI_API_KEY=sk-your_key" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-your_key" >> .env
```

Get OpenRouter API key at: [openrouter.ai/keys](https://openrouter.ai/keys)

### 3. Test Installation (No API Key Required)

```bash
# Verify system works with fake adapter
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target fake:perfect \
  --judges 2
```

### 4. Run Your First Evaluation

```bash
# Evaluate GPT-4 on SHIP Question #3
python -m src run \
  --scenario scenarios/v1/scenario_002.json \
  --target openrouter:openai/gpt-4-turbo \
  --agent-model openrouter:anthropic/claude-3-haiku \
  --judges 2
```

### 5. View Results

```bash
# View latest results
cat runs/$(ls -t runs/ | head -1)/results.jsonl | python -m json.tool | grep -A 10 final_scores

# Generate SHIP-style accuracy table (clean, incomplete runs excluded by default)
python scripts/generate_accuracy_table.py

# Compare AI performance to human counselors from the SHIP study (most useful)
python scripts/generate_accuracy_table.py --by-model --include-baseline --scenario SHIP-002
```

**Key features:**
- Baseline appears as a peer row alongside AI models for easy comparison
- Incomplete runs (without rubric scores) are excluded by default for cleaner output
- Use `--include-incomplete` to show incomplete runs when needed

**For detailed instructions, see [USER_GUIDE.md](USER_GUIDE.md) and [REPORTING_GUIDE.md](REPORTING_GUIDE.md)**

## Supported AI Providers

### OpenRouter (Recommended)

**One API key for 100+ models**

Access all major AI models through a single API:
- OpenAI: `gpt-4-turbo`, `gpt-4o`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet`, `claude-3-opus`, `claude-3-haiku`
- Google: `gemini-pro-1.5`, `gemini-flash-1.5`
- Meta: `llama-3.1-70b-instruct`, `llama-3.1-405b-instruct`
- Mistral: `mistral-large`, `mixtral-8x7b-instruct`
- And 100+ more models

**Benefits:**
- ✅ Single API key and billing
- ✅ Easy model comparison
- ✅ Unified cost tracking
- ✅ Access to models without direct API

**Usage:**
```bash
--target openrouter:openai/gpt-4-turbo
--target openrouter:anthropic/claude-3-5-sonnet
--target openrouter:google/gemini-pro-1.5
```

See full guide: **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)**

### Direct Provider Access

You can also use direct provider APIs:
- **OpenAI** - `--target openai:gpt-4-turbo`
- **Anthropic** - `--target anthropic:claude-3-5-sonnet-20241022`
- **Google** - `--target google:gemini-1.5-pro`
- **xAI** - `--target xai:grok-beta`

### Testing (No API Key)

- **Fake** - `--target fake:perfect` (no API calls, for testing)

## Project Structure

```
ai-medicare-eval/
├── scenarios/          # Test scenarios with answer keys
├── prompts/           # System prompts for each agent
├── src/               # Core implementation
│   ├── adapters/      # LLM provider integrations
│   └── agents/        # Evaluation agents
└── runs/              # Evaluation results (auto-generated)
```

## Key Design Principles

1. **Strict role separation** - Questioner ≠ Responder ≠ Judge
2. **Answer-key grounded** - Judges rely only on provided answer keys
3. **Deterministic by default** - Fixed seeds, prompts, and parameters
4. **Full auditability** - Raw transcripts and judge outputs stored verbatim
5. **Snapshot-based evaluation** - Results are time-, model-, and prompt-specific

## Ethics and Framing

⚠️ **This system is for research purposes only.**

This tool evaluates AI-generated information quality. It does not provide medical, legal, or insurance advice. Results should not be used to make healthcare decisions.

## What This Enables

- Replication of SHIP-style accuracy tables
- Model-to-model comparison under identical prompts
- Prompt sensitivity analysis
- Longitudinal drift detection
- Audit-ready evaluation artifacts

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run basic functionality test (no external deps)
python test_basic.py

# Test full pipeline with mock agents
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target fake:perfect \
  --judges 2
```

## Documentation

### For Researchers & Evaluators

- **[USER_GUIDE.md](USER_GUIDE.md)** - How to run evaluations and compare models
- **[SCENARIOS.md](SCENARIOS.md)** - Test scenarios and what they evaluate
- **[OPENROUTER_GUIDE.md](OPENROUTER_GUIDE.md)** - Using OpenRouter for model access
- **[SHIP_RUBRIC_UPDATE.md](SHIP_RUBRIC_UPDATE.md)** - Understanding SHIP scoring methodology

### For Developers

- **[ADAPTERS_COMPLETE.md](ADAPTERS_COMPLETE.md)** - LLM adapter implementation
- **[ORCHESTRATOR_COMPLETE.md](ORCHESTRATOR_COMPLETE.md)** - Pipeline architecture
- **[AGENTS_COMPLETE.md](AGENTS_COMPLETE.md)** - Agent system details
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Project status and roadmap
- **[METHODOLOGY_COMPARISON.md](METHODOLOGY_COMPARISON.md)** - System vs SHIP study comparison

## License

[To be determined]

## References

Based on methodology from:

**Dugan K, et al.** "Evaluating State Health Insurance Assistance Program (SHIP) Counselor Responses." *JAMA Network Open*. 2025;8(4):e252834.

- PubMed Central: [PMC11962663](https://pmc.ncbi.nlm.nih.gov/articles/PMC11962663/)
- DOI: [10.1001/jamanetworkopen.2025.2834](https://doi.org/10.1001/jamanetworkopen.2025.2834)
