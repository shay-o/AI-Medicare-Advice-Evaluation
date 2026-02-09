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
- GPT 5.2 Instant (https://openrouter.ai/openai/gpt-5.2-pro) (Expensive!!)

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

None at this point
---

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
