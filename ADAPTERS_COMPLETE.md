# LLM Adapters Complete! 🎉

All real LLM provider adapters are implemented and ready to use.

## Supported Providers

### 1. OpenAI (`openai_adapter.py` - 210 lines)
**Models:**
- `gpt-4-turbo` (recommended for agents)
- `gpt-4`
- `gpt-4o`
- `gpt-3.5-turbo-1106`
- Any OpenAI chat completion model

**Features:**
- ✓ Seed support (gpt-4-turbo, gpt-4o, gpt-3.5-turbo-1106+)
- ✓ Exponential backoff retry (3 attempts)
- ✓ Rate limit handling
- ✓ Token usage tracking
- ✓ Model version identification

**Installation:**
```bash
pip install openai>=1.0.0
# or
pip install -e ".[openai]"
```

**Setup:**
```bash
# Get API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-your_key_here"
```

**Usage:**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo \
  --judges 2
```

---

### 2. Anthropic (`anthropic_adapter.py` - 193 lines)
**Models:**
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

**Features:**
- ✓ System message handling (separate from chat messages)
- ✓ Exponential backoff retry (3 attempts)
- ✓ Rate limit handling
- ✓ Token usage tracking
- ✗ No seed support (Anthropic limitation)

**Installation:**
```bash
pip install anthropic>=0.18.0
# or
pip install -e ".[anthropic]"
```

**Setup:**
```bash
# Get API key from https://console.anthropic.com/settings/keys
export ANTHROPIC_API_KEY="sk-ant-your_key_here"
```

**Usage:**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target anthropic:claude-3-5-sonnet-20241022 \
  --judges 2
```

---

### 3. Google (`google_adapter.py` - 195 lines)
**Models:**
- `gemini-1.5-pro` (recommended)
- `gemini-1.5-flash`
- `gemini-1.5-pro-latest`

**Features:**
- ✓ System instruction support
- ✓ Multi-turn conversation handling
- ✓ Exponential backoff retry (3 attempts)
- ✓ Rate limit handling
- ✓ Token usage tracking
- ✗ No official seed support

**Installation:**
```bash
pip install google-generativeai>=0.3.0
# or
pip install -e ".[google]"
```

**Setup:**
```bash
# Get API key from https://aistudio.google.com/app/apikey
export GOOGLE_API_KEY="your_key_here"
```

**Usage:**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target google:gemini-1.5-pro \
  --judges 2
```

---

### 4. xAI / Grok (`xai_adapter.py` - 187 lines)
**Models:**
- `grok-beta`
- `grok-2`

**Features:**
- ✓ OpenAI-compatible API
- ✓ Exponential backoff retry (3 attempts)
- ✓ Rate limit handling
- ✓ Token usage tracking
- ? Seed support (check xAI docs)

**Installation:**
```bash
pip install openai>=1.0.0  # xAI uses OpenAI-compatible API
# or
pip install -e ".[xai]"
```

**Setup:**
```bash
# Get API key from https://console.x.ai
export XAI_API_KEY="your_key_here"
```

**Usage:**
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target xai:grok-beta \
  --judges 2
```

---

## Install All Providers

```bash
# Install all LLM provider dependencies at once
pip install -e ".[all]"

# Or individually
pip install -e ".[openai,anthropic,google,xai]"
```

## Quick Start

### 1. Install Dependencies
```bash
# Core + one provider
pip install -e ".[openai]"
```

### 2. Set Up API Keys
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
echo "OPENAI_API_KEY=sk-your_actual_key_here" >> .env
```

### 3. Run Evaluation
```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo \
  --judges 2
```

## Common Patterns

### Evaluating Target Model
```bash
# Evaluate GPT-4
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo

# Evaluate Claude
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target anthropic:claude-3-5-sonnet-20241022

# Evaluate Gemini
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target google:gemini-1.5-pro
```

### Using Real Agents
By default, agents use the mock adapter (no API calls). To use real LLMs for agents:

```bash
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo \
  --agent-model anthropic:claude-3-5-sonnet-20241022 \
  --judges 2
```

**Warning:** Using real LLMs for agents will make many API calls:
- 1 call for extraction (per response turn)
- N calls for verification (N = number of judges)
- Can be expensive! Use mock adapter for testing.

### Cost Optimization

```bash
# Use cheaper model for agents, expensive model for target
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo \
  --agent-model openai:gpt-3.5-turbo \
  --judges 2
```

## Adapter Architecture

### Common Features

All adapters implement:

1. **Exponential Backoff Retry**
   - 3 retry attempts
   - Delays: 1s, 2s, 4s
   - Only retries rate limits and connection errors

2. **Error Handling**
   - Rate limit errors → retry
   - Connection errors → retry
   - API errors → fail immediately
   - All errors wrapped in RuntimeError with clear messages

3. **Token Tracking**
   - Prompt tokens
   - Completion tokens
   - Total tokens
   - Returned in ModelResponse.tokens_used

4. **Latency Measurement**
   - Millisecond precision
   - Includes retry delays
   - Returned in ModelResponse.latency_ms

5. **Model Version Tracking**
   - Actual model identifier (e.g., "gpt-4-turbo-2024-04-09")
   - Returned in ModelResponse.model_identifier

### Provider-Specific Details

**OpenAI:**
- Native async client
- System messages in chat history
- Seed support on newer models

**Anthropic:**
- Native async client
- System message separate from chat
- No seed support (API limitation)

**Google:**
- Uses `asyncio.to_thread()` (sync API wrapped)
- System instruction separate from chat
- Multi-turn via chat.send_message()

**xAI:**
- Uses OpenAI SDK with custom base URL
- Fully OpenAI-compatible
- Check docs for seed support

## Testing Adapters

### Without API Calls (Mock)
```bash
# Use fake adapter - no costs
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target fake:perfect
```

### With API Calls (Real)
```bash
# Small test with real API
python -m src run \
  --scenario scenarios/v1/scenario_001.json \
  --target openai:gpt-4-turbo \
  --judges 1  # Use 1 judge to reduce costs
```

Expected costs per evaluation (approximate):
- **Target model call**: 1 call (~500-1000 tokens) = $0.01-0.03
- **Extractor call**: 1 call (~1000-2000 tokens) = $0.02-0.05
- **Verifier calls**: N calls (~2000 tokens each) = $0.04-0.10 per judge

**Total for 2 judges**: ~$0.10-0.20 per evaluation

## Error Messages

### Missing API Key
```
ValueError: OpenAI API key not provided. Set OPENAI_API_KEY environment
variable or pass api_key parameter.
```

**Fix:** Add API key to `.env` file or export as environment variable.

### Missing Dependency
```
RuntimeError: OpenAI adapter requires 'openai' package.
Install with: pip install openai>=1.0.0
```

**Fix:** Install the required package.

### Rate Limit
```
RuntimeError: OpenAI rate limit exceeded: Rate limit reached for requests
```

**Fix:**
- Wait a few seconds and retry
- Reduce concurrency (use fewer judges)
- Upgrade API tier

### Invalid Model
```
RuntimeError: OpenAI API error: The model 'gpt-5' does not exist
```

**Fix:** Use a valid model name from the provider's documentation.

## Recommended Models

### For Target Evaluation (Being Tested)
- **OpenAI**: `gpt-4-turbo` or `gpt-4o`
- **Anthropic**: `claude-3-5-sonnet-20241022`
- **Google**: `gemini-1.5-pro`
- **xAI**: `grok-beta`

### For Agent Tasks (If Not Using Mock)
- **Cost-effective**: `gpt-3.5-turbo-1106`, `claude-3-haiku-20240307`
- **Best quality**: `claude-3-5-sonnet-20241022`, `gpt-4-turbo`
- **Recommended**: Use mock adapter (free, fast)

## Implementation Details

### Files Created
- `src/adapters/openai_adapter.py` (210 lines)
- `src/adapters/anthropic_adapter.py` (193 lines)
- `src/adapters/google_adapter.py` (195 lines)
- `src/adapters/xai_adapter.py` (187 lines)

**Total**: 785 lines of production adapter code

### Code Quality
- ✓ Full type hints
- ✓ Comprehensive docstrings
- ✓ Error handling with retries
- ✓ Async/await throughout
- ✓ Clean abstraction (all extend BaseLLMAdapter)

### Testing
```bash
# Test with mock (no API calls)
python -m src run --scenario scenarios/v1/scenario_001.json --target fake:perfect

# Test with real API (requires API key)
python -m src run --scenario scenarios/v1/scenario_001.json --target openai:gpt-4-turbo
```

## Next Steps

With adapters complete, you can now:

1. **Run real evaluations** on any supported LLM
2. **Compare models** side-by-side
3. **Build reporting** to analyze results across models
4. **Create more scenarios** for comprehensive testing

## Example: Compare All Models

```bash
# Evaluate same scenario across all providers
for model in "openai:gpt-4-turbo" "anthropic:claude-3-5-sonnet-20241022" "google:gemini-1.5-pro"; do
  python -m src run \
    --scenario scenarios/v1/scenario_001.json \
    --target "$model" \
    --judges 2 \
    --run-id "comparison_$(date +%Y%m%d)"
done

# Results will be in runs/comparison_20260125/
```

---

**All LLM adapters are complete and ready for production use!** 🚀
