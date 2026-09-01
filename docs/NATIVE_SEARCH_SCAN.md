# Provider-hosted web search: what is actually available

Probed 2026-08-19 against OpenRouter, to establish empirically which models can use provider-hosted ("native") search, rather than relying on the docs' provider-level list. Raw results in `reference_material/native_search_capability.json`.

The goal is a tier that approximates consumer AI products: the model's own search, not retrieval we bolt on.

## Results

| Model | Plain | Native search | Citations | Status |
| --- | --- | --- | --- | --- |
| `openai/gpt-5.2` | $0.0042 | $0.0270 | 0 | Searches, no citations returned |
| `openai/gpt-5.2-pro` | $0.0508 | $0.2419 | 0 | Searches, no citations returned |
| `anthropic/claude-sonnet-4.5` | $0.0039 | $0.0456 | 2 | Searches, **real source URLs** |
| `google/gemini-3-flash-preview` | $0.0009 | varies | 0 to 4 | Searches inconsistently, opaque redirect URLs |
| `anthropic/claude-opus-4.1` | $0.0196 | unsupported | n/a | No native search |
| `perplexity/sonar-pro` | $0.0080 | unsupported | n/a | No native search plugin |
| `openai/gpt-5.2-chat` | n/a | n/a | n/a | **No endpoints** |
| `anthropic/claude-3.5-sonnet` | n/a | n/a | n/a | **No endpoints** |
| `google/gemini-3-pro-preview` | n/a | n/a | n/a | **No endpoints** |
| `x-ai/grok-4` | n/a | n/a | n/a | **Deprecated by xAI** |
| `x-ai/grok-4.1-fast` | n/a | n/a | n/a | **Deprecated by xAI** |

## Four things this changes

### 1. The original roster has largely decayed

Five of the eleven candidates are gone, including four of the nine models behind the published figures. The original comparison cannot be re-run, only re-graded. This is the snapshot principle arriving in practice rather than in theory.

### 2. Search invocation is non-deterministic

This is the most consequential finding. With native search enabled, **the model decides whether to search**, and that decision is not stable across identical calls.

On one model and one question at temperature 0, across roughly nine calls:

- Some calls searched: about $0.029 with 3 to 4 citations
- Most did not: about $0.0009 with 0 citations, essentially the no-search cost
- Six consecutive calls declined to search, then the very same question searched again

It is not caching: repeated identical questions searched while freshly-phrased ones did not, which is the opposite of a cache signature.

So "search enabled" is an intent, not a condition. A single run per model per question cannot tell you whether search helps, because it cannot tell you whether search happened. Any search-tier design needs replicates, and the realized search rate should be reported as a result rather than assumed.

There is a real research question hiding in this: **does the model know when it needs to look something up?** A model that answers a plan-specific question from memory when it could have searched is making an error of judgment, and this setup can measure that directly, because cost and citations reveal whether search fired.

### 3. Citation quality varies by provider, which matters for auditability

- `claude-sonnet-4.5` returns real, resolvable source URLs
- `gemini-3-flash` returns opaque `vertexaisearch.cloud.google.com/grounding-api-redirect/...` links
- `gpt-5.2` and `gpt-5.2-pro` bill for search but return **no citations at all**

For a project whose main asset is a traceable audit trail, a searched answer with no record of what was read is a weak artifact. Only Anthropic's models currently give a fully auditable search tier.

### 4. Cost is dominated by one model

`gpt-5.2-pro` costs $0.24 for a single search-enabled question, roughly 270 times `gemini-3-flash` unsearched and 5 times its own unsearched cost. A full scenario run on that model alone would be several dollars. It should be included deliberately or not at all, not by default.

## Implication for the tier design

Only three models currently support native search: `openai/gpt-5.2`, `openai/gpt-5.2-pro`, `anthropic/claude-sonnet-4.5`, with `gemini-3-flash` accepting the plugin but searching erratically.

That is a thin roster, and it is skewed: the only model with usable citations is Anthropic's. Two options, both honest:

1. **Native only**, accepting three or four models and stating that the roster was determined by capability rather than chosen.
2. **Native where available, Exa fallback elsewhere**, which widens the roster but mixes two different retrieval stacks in one condition, so the tier no longer cleanly represents "the product's own search".

Option 1 is the better fit for the stated goal of matching consumer products. Option 2 would need the engine recorded per run and reported alongside every figure.

## Method

Each model received the same plan-specific question, once plain and once with `plugins: [{"id": "web", "engine": "native", "max_results": 5}]`. Search was judged to have fired when cost rose materially over the plain baseline or citations were returned. Re-run with `scripts/scan_native_search.py`.
