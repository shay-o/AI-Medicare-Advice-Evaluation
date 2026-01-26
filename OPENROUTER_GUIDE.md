# OpenRouter Integration Guide

OpenRouter.ai provides unified access to multiple LLM providers through a single API key and billing account. This is ideal for:
- Testing multiple models without managing multiple API keys
- Unified billing across providers
- Access to models that might not have direct API access
- Easy model comparison

## Setup

### 1. Get OpenRouter API Key

Visit [openrouter.ai/keys](https://openrouter.ai/keys) and create an API key.

### 2. Install Dependencies

```bash
pip install openai>=1.0.0
# or
pip install -e ".[openrouter]"
```

### 3. Configure API Key

```bash
# Add to .env file
echo "OPENROUTER_API_KEY=sk-or-your_key_here" >> .env

# Or export as environment variable
export OPENROUTER_API_KEY="sk-or-your_key_here"
```

### 4. Optional: App Identification

For dashboard analytics, you can set:

```bash
echo "OPENROUTER_APP_NAME=AI Medicare Evaluator" >> .env
echo "OPENROUTER_SITE_URL=https://your-site.com" >> .env
```

## Usage

### Basic Evaluation

```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:anthropic/claude-3.5-sonnet \
  --judges 2
```

### Model Name Format

OpenRouter uses the format: `provider/model-name`

**Popular Models:**

```bash
# Anthropic Claude
--target openrouter:anthropic/claude-3.5-sonnet
--target openrouter:anthropic/claude-3-opus
--target openrouter:anthropic/claude-3-haiku

# OpenAI GPT
--target openrouter:openai/gpt-4-turbo
--target openrouter:openai/gpt-4o
--target openrouter:openai/gpt-3.5-turbo

# Google Gemini
--target openrouter:google/gemini-pro-1.5
--target openrouter:google/gemini-flash-1.5

# Meta Llama
--target openrouter:meta-llama/llama-3.1-70b-instruct
--target openrouter:meta-llama/llama-3.1-405b-instruct

# Mistral
--target openrouter:mistralai/mistral-large
--target openrouter:mistralai/mixtral-8x7b-instruct

# And many more...
```

See [openrouter.ai/models](https://openrouter.ai/models) for the complete list.

## Examples

### Compare Multiple Models

```bash
# Run same scenario on different models via OpenRouter
for model in \
  "anthropic/claude-3.5-sonnet" \
  "openai/gpt-4-turbo" \
  "google/gemini-pro-1.5" \
  "meta-llama/llama-3.1-70b-instruct"; do

  python -m src run \
    --scenario scenarios/v1/scenario_001.json \
    --target openrouter:$model \
    --judges 2 \
    --run-id "comparison_$(date +%Y%m%d)"
done

# View results
for run in runs/comparison_*/; do
  python -m src.view_run "$run" | grep -A 5 "EVALUATION SCORES"
done
```

### Cost-Effective Testing

OpenRouter often has competitive pricing. Use cheaper models for testing:

```bash
# Use a more affordable model for testing
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:anthropic/claude-3-haiku \
  --judges 1  # Use fewer judges to save costs
```

### Mix Direct and OpenRouter Access

You can use direct provider adapters for some models and OpenRouter for others:

```bash
# Use direct OpenAI adapter (if you have OpenAI API key)
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo

# Use OpenRouter for Anthropic (single billing)
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:anthropic/claude-3.5-sonnet

# Use OpenRouter for models without direct API
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:meta-llama/llama-3.1-70b-instruct
```

## Benefits of OpenRouter

### 1. Single API Key
- No need to manage multiple provider accounts
- One key for OpenAI, Anthropic, Google, Meta, and more

### 2. Unified Billing
- Single invoice for all model usage
- Easy cost tracking across providers
- Simpler accounting

### 3. Access to More Models
- Models from providers without direct API access
- Community-hosted models
- Open-source models (Llama, Mistral, etc.)

### 4. Model Fallbacks
OpenRouter can automatically fall back to alternative models if primary is unavailable.

### 5. Usage Analytics
Dashboard shows usage across all models at [openrouter.ai/activity](https://openrouter.ai/activity).

## Cost Comparison

OpenRouter pricing is generally competitive with direct provider APIs. Check current prices at [openrouter.ai/models](https://openrouter.ai/models).

**Example costs (approximate):**
- Claude 3.5 Sonnet: ~$3/$15 per 1M tokens (input/output)
- GPT-4 Turbo: ~$10/$30 per 1M tokens
- Gemini 1.5 Pro: ~$1.25/$5 per 1M tokens
- Llama 3.1 70B: ~$0.50/$0.80 per 1M tokens

*(Prices vary - check OpenRouter for current rates)*

## Limitations

### 1. Seed Support
Not all models support deterministic seeding through OpenRouter. OpenAI models do, most others don't.

### 2. Rate Limits
OpenRouter has its own rate limits separate from direct provider APIs.

### 3. Slight Latency
May have slightly higher latency than direct API access due to routing.

### 4. Model Availability
Some brand-new models might not be available immediately on OpenRouter.

## When to Use Direct vs OpenRouter

### Use Direct Provider Adapters When:
- ✓ You need guaranteed seed support for determinism
- ✓ You need the absolute lowest latency
- ✓ You want direct relationship with provider
- ✓ You need access to brand-new models immediately
- ✓ You have existing provider credits/contracts

### Use OpenRouter When:
- ✓ You want unified billing across providers
- ✓ You want to test many different models easily
- ✓ You need access to models without direct API (Llama, Mistral, etc.)
- ✓ You prefer simpler API key management
- ✓ You want automatic fallback options
- ✓ Cost savings from OpenRouter's pricing

## Troubleshooting

### API Key Not Found
```
ValueError: OpenRouter API key not provided
```

**Solution:**
```bash
# Check if key is in .env
grep OPENROUTER_API_KEY .env

# Or export it
export OPENROUTER_API_KEY="sk-or-your_key"
```

### Invalid Model Name
```
RuntimeError: OpenRouter API error: Model not found
```

**Solution:** Check the model name format at [openrouter.ai/models](https://openrouter.ai/models). Use the exact format shown (e.g., `anthropic/claude-3.5-sonnet`).

### Rate Limit Exceeded
```
RuntimeError: OpenRouter rate limit exceeded
```

**Solution:**
- Wait a few seconds and retry
- Reduce concurrency (use fewer judges: `--judges 1`)
- Check your OpenRouter credits/limits

## Advanced: Custom Headers

You can customize OpenRouter headers for better analytics:

```python
from src.adapters.openrouter_adapter import OpenRouterAdapter

adapter = OpenRouterAdapter(
    model_name="anthropic/claude-3.5-sonnet",
    app_name="Medicare Evaluator v1.0",
    site_url="https://your-site.com",
)
```

## Resources

- **OpenRouter Dashboard:** [openrouter.ai](https://openrouter.ai)
- **API Keys:** [openrouter.ai/keys](https://openrouter.ai/keys)
- **Model List:** [openrouter.ai/models](https://openrouter.ai/models)
- **Pricing:** [openrouter.ai/models](https://openrouter.ai/models) (see individual model pages)
- **Documentation:** [openrouter.ai/docs](https://openrouter.ai/docs)

## Quick Reference

```bash
# Setup
export OPENROUTER_API_KEY="sk-or-your_key"

# Basic usage
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openrouter:anthropic/claude-3.5-sonnet

# Compare models
python -m src run --target openrouter:openai/gpt-4-turbo
python -m src run --target openrouter:anthropic/claude-3.5-sonnet
python -m src run --target openrouter:google/gemini-pro-1.5

# View results
python -m src.view_run
```

---

**OpenRouter gives you flexibility:** Use it for unified billing and easy model comparison, while keeping the option to use direct provider adapters when you need specific features or lowest latency.
