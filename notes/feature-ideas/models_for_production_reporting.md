# Feature: [Name]

**Status:** exploring

---

## Problem

Goal of this doc is to determine which models to include for analysis and reporting about the quality of Medicare advice that AI models provide. Goal is to get responses the represent what a user would typically see. These will be the models that are popular rather than those used by AI power users. 

## Ideas

### Models to use

#### OpenAI
- GPT-5.2 is current default. But there are auto, instant, and thinking. Test each. (https://openrouter.ai/openai/gpt-5.2)
- GPT 5.2 Instant (https://openrouter.ai/openai/gpt-5.2-chat)
- GPT 5.2 Pro (https://openrouter.ai/openai/gpt-5.2-pro) (Expensive!!)

##### Google
- Gemini 3 Flash. Default for search results. (https://openrouter.ai/google/gemini-3-flash-preview)
https://blog.google/products-and-platforms/products/search/ai-mode-ai-overviews-updates/
- Gemini 3 Pro (https://openrouter.ai/google/gemini-3-pro-preview) (Expensive!!)

##### xAI
- Grok 4 (https://openrouter.ai/x-ai/grok-4 )
- Grok 4.1 Fast (https://openrouter.ai/x-ai/grok-4.1-fast)

#### Anthropic
- Sonnet 4.5 (https://openrouter.ai/anthropic/claude-sonnet-4.5) 
- Sonnet 3.5 (https://openrouter.ai/anthropic/claude-3.5-sonnet)

## User Impact

A variety of widely used models allows us to understand which model is performing the best according to the SHIP rubric. 

## Technical Considerations

None at this point

## Open Questions

None at this point

## References

Command line call:

# Run same scenario on different models via OpenRouter
for model in \
  "openai/gpt-5.2" \
  "google/gemini-3-flash-preview"; do

  python -m src run \
    --scenario scenarios/dual_eligible/all_questions.json \
    --target-model openrouter:$model \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --grade-model openrouter:anthropic/claude-3-haiku \
    --judges 1 \
    --run-id "test_dual_eligible_allquestions_GA-Candidate_GPT52-GEM3Flash_$(date +%Y%m%d%H%M)"

done

---

- GPT 5.2 Instant (https://openrouter.ai/openai/gpt-5.2-chat)
- GPT 5.2 Pro (https://openrouter.ai/openai/gpt-5.2-pro) (Expensive!!)

## Commands for running

### Command for GPT models

for model in \
  "openai/gpt-5.2-chat" \
  "openai/gpt-5.2-pro" \
  "openai/gpt-5.2"; do 

  python -m src run \
    --scenario scenarios/dual_eligible/all_questions.json \
    --target-model openrouter:$model \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --grade-model openrouter:anthropic/claude-3-haiku \
    --judges 1 \
    --run-id "test_dual_eligible_GA-Candidate_${safe_model}_$(date +%Y%m%d%H%M)"

done

### Command for Anthropic models

##### - Sonnet 4.5 (https://openrouter.ai/anthropic/claude-sonnet-4.5) 
##### - Sonnet 3.5 (https://openrouter.ai/anthropic/claude-3.5-sonnet)

for model in \
  "anthropic/claude-sonnet-4.5" \
  "anthropic/claude-3.5-sonnet"; do

  python -m src run \
    --scenario scenarios/dual_eligible/all_questions.json \
    --target-model openrouter:$model \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --grade-model openrouter:anthropic/claude-3-haiku \
    --judges 1 \
    --run-id "test_dual_eligible_allquestions_GA-Candidate_Anthropic_$(date +%Y%m%d%H%M)"

done

### Command for Google models

Gemini 3 Flash. Default for search results. (https://openrouter.ai/google/gemini-3-flash-preview)
Gemini 3 Pro (https://openrouter.ai/google/gemini-3-pro-preview) (Expensive!!)

for model in \
  "google/gemini-3-flash-preview" \
  "google/gemini-3-pro-preview"; do

  python -m src run \
    --scenario scenarios/dual_eligible/all_questions.json \
    --target-model openrouter:$model \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --grade-model openrouter:anthropic/claude-3-haiku \
    --judges 1 \
    --run-id "test_dual_eligible_allquestions_GA-Candidate_Google_$(date +%Y%m%d%H%M)"

done

### Command for xAI models

- Grok 4 (https://openrouter.ai/x-ai/grok-4 )
- Grok 4.1 Fast (https://openrouter.ai/x-ai/grok-4.1-fast)

for model in \
  "x-ai/grok-4" \
  "x-ai/grok-4.1-fast"; do

  python -m src run \
    --scenario scenarios/dual_eligible/all_questions.json \
    --target-model openrouter:$model \
    --agent-model openrouter:anthropic/claude-3-haiku \
    --grade-model openrouter:anthropic/claude-3-haiku \
    --judges 1 \
    --run-id "test_dual_eligible_allquestions_GA-Candidate_xAI_$(date +%Y%m%d%H%M)"

done

## Notes

### Scope

Leave old models out of scope. Interesting to see if models are improving or at some point crossed a threshold. But that's a secondary analysis. For now let's look at models like to be used currently (Feb 2026)

### Limitations

In real use scenarios like using ChatGPT.com or Google Search the AI tool may differ from OpenRouter models. 
- User context. The application will have user context from previous conversations and possibly other sources like Google profile.
- Context size. Large context can negatively impact performance. For now we will be starting with a new conversation without context.
- System Content. There may be system prompts guiding how the model responds. For example guiding against providing certain kinds of medical advice.
- Tools. The application can use tools like RAG to pull the latest information.

### [Date]
- Thought/discovery/update
