# Token economics: input, cached input, and output

This document records observable mechanics from provider documentation, not assumptions about any model's intelligence. Prices and minimums change; verify against the linked source before using a number in a decision.

## The four token categories

| Category | What it is | Typical usage field |
|---|---|---|
| Input tokens | Everything sent in the request: instructions, tool schemas, history, retrieved files, images, and framing tokens added by the API. | `input_tokens` (OpenAI Responses), `input_tokens` (Anthropic usage), `total_input_tokens` (Gemini Interactions) |
| Cached input read | A reusable prompt prefix whose key-value states were stored by an earlier request; billed at a discount. | `input_tokens_details.cached_tokens` (OpenAI), `cache_read_input_tokens` (Anthropic), `total_cached_tokens` (Gemini) |
| Cached input write | The first request that stores a prefix; billed at a write rate, not a surcharge on top of ordinary input. | `input_tokens_details.cache_write_tokens` (OpenAI), `cache_creation_input_tokens` (Anthropic) |
| Output tokens | Everything the model generates: visible text, tool calls, channel delimiters, and reasoning tokens. Reasoning is billed as output even when invisible. | `output_tokens` (OpenAI), `output_tokens` (Anthropic), `total_output_tokens` plus `total_thought_tokens` (Gemini) |

Total input with caching is not the same as the `input_tokens` field in every provider:

- Anthropic: `total_input = cache_read_input_tokens + cache_creation_input_tokens + input_tokens`, where `input_tokens` covers only content after the last breakpoint.
- OpenAI Responses: `input_tokens` is the full input total; `cached_tokens` and `cache_write_tokens` are subsets that must be priced separately, not added again.
- Gemini: `usage` reports `total_input_tokens`, `total_cached_tokens`, `total_thought_tokens`, `total_output_tokens`, and `total_tool_use_tokens`.

A plain-text tokenizer count is not the request count: message roles, separators, tool definitions, images, and files add tokens that local tokenizers do not see. Pre-flight exact counts should use the provider's counting endpoint with the assembled payload.

## Context-window arithmetic

A request succeeds only if generated tokens plus input fit the window:

```text
input_tokens + output_tokens + reasoning_tokens + hidden formatting <= context_window
```

Reserve output headroom before loading context. Provider guidance for reasoning models recommends reserving a substantial buffer (for example about 25,000 tokens when starting with GPT-5-class reasoning) and notes that hitting `max_output_tokens` can produce an `incomplete` response with no visible answer after input and reasoning were already billed. Output token counts include non-visible formatting tokens, so visible text length is not a safe budget proxy.

## How prompt caching works

Caching stores KV tensors for an unchanged prefix, not the text itself. On a later request the provider finds the longest matching cached prefix and reuses those states; new content after the prefix still must be processed.

- **Prefix order matters.** Anthropic caches in the order `tools`, `system`, `messages`. OpenAI and Gemini also require the entire rendered prefix to match. Put stable instructions, tool definitions, and reference material first; put volatile user content last.
- **Breakpoints.** A breakpoint marks the end of a cacheable prefix. Changing anything at or before it changes the cumulative hash and causes a miss. Multiple breakpoints allow sections that change at different rates to be cached independently.
- **Minimum prefix length.** Anthropic models require roughly 512 to 4,096 tokens depending on model; OpenAI states 1,024 tokens for GPT-5.6 and later (and varies earlier models); Gemini requires 2,048 to 6,144 depending on model. A prefix below the minimum is silently not cached.
- **TTL and writes.** Anthropic defaults to 5 minutes and offers 1 hour at a higher write rate. OpenAI offers 30 minutes and 12 hours for supported models. Gemini implicit entries expire within about 24 hours and explicit caches have their own TTL controls.
- **Reads refresh.** A cache hit refreshes a 5-minute entry at no extra write cost. An agent loop with short start-to-start gaps keeps a 5-minute cache warm indefinitely; a 1-hour TTL only pays off when the gap is longer.
- **Break-even.** With Anthropic-style rates (write 1.25x, read 0.1x), two requests break even for a 5-minute TTL and three for a 1-hour TTL (write 2x). With OpenAI-style rates (write 1.25x, read 0.1x), one write plus nine reads costs about 2.15x versus 10x uncached.
- **Measure.** Check hit rate from usage fields, not intent. OpenAI rounds earlier-model cached counts down to multiples of 128; Anthropic reports creation/read split explicitly.

## Why RSaver Gate separates three budgets

1. **Input budget** determines which context items may enter the request. Required items are never dropped; optional history is deferred first, then merely useful material. Deferred items keep a recovery pointer.
2. **Cache budget** is the contiguous static prefix. It is planned separately because a small prefix that fails the provider minimum earns no discount, and a dynamic item inserted into the prefix fragments it.
3. **Output and reasoning reserve** is removed from the window *before* the input budget is computed. Otherwise a request can fit on paper and still return `incomplete` with nothing visible.

RSaver does not grant or observe a provider's cache state; it plans a stable prefix and reports what should be eligible. Actual hits must be confirmed from usage fields.

## Sources

- OpenAI, "Counting tokens" and "Prompt caching": https://developers.openai.com/api/docs/guides/token-counting and https://developers.openai.com/api/docs/guides/prompt-caching
- OpenAI, "Reasoning models": https://developers.openai.com/api/docs/guides/reasoning
- OpenAI Python SDK usage types: https://github.com/openai/openai-python/blob/main/src/openai/types/responses/response_usage.py
- Anthropic, "Prompt caching": https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Google, "Context caching" and "Understand and count tokens": https://aistudio.google.com/docs/caching and https://ai.google.dev/gemini-api/docs/tokens
- OpenAI GPT-2 encoder and tiktoken encoding definitions: https://github.com/openai/gpt-2/blob/master/src/encoder.py and https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py
