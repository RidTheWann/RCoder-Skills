# Context drift and re-anchoring research

This document records evidence about why long contexts cause drift and which mitigations are supported by published work. It makes no claim about a specific model's architecture or immunity.

## What drifts and why

- **Positional attention bias.** Relevant information at the beginning or end of a long input is used more reliably than the same information in the middle; the performance curve is U-shaped. This was measured in multi-document QA and key-value retrieval (Liu et al., 2023) and independently linked to an intrinsic U-shaped attention bias (Found in the Middle, 2024; Attention Basin, ACL 2026).
- **Context rot.** Anthropic describes context as a finite attention budget: as tokens accumulate, recall precision and long-range reasoning degrade before any hard window limit. The effect is a gradient, not a cliff, and is described across models rather than as an advantage unique to one product.
- **Structural anchors are load-bearing.** When KV eviction removes boundary tokens (system instruction, question delimiter, turn boundaries, attention sink), models enter degenerate repetition loops rather than merely answering slightly worse; protecting both ends restores most quality (Protection Is Nearly All You Need, 2026).
- **Relative position instructions are weak.** Asking a model to "focus on the middle" generally does little; absolute identifiers (document IDs) can help in some models. Explicit IDs are more reliable than positional prose (Attention Instruction, 2024).
- **Compaction can manufacture errors.** An analysis of 667 summaries found that reasoning entries (decisions, open TODOs) were frequently unsupported by environment outputs; 83% of failed runs traced to an action carrying out a specific summary entry, often a rewritten constraint or invented deliverable (Source-Judged Compaction, 2026). A summary is a hypothesis until each entry is tied to a source.
- **Proactive, structured checkpoints beat waiting for overflow.** AutoCompact and CORAL report that compacting at a resolved stage boundary, preserving verified facts plus task progress and an explicit next action, improves task success and reduces input tokens. Anthropic's long-running-agent guidance similarly uses a progress file and incremental clean-state sessions.

## Why Claude may appear to hold up better

Anthropic documents concrete practices in Claude Code: compaction that preserves architectural decisions, unresolved bugs, and implementation details; tool-result clearing; structured memory; subagents with fresh context; and re-injection of project rules, skill descriptions, Git status, and the five most recently modified files after compaction. These are observable engineering controls, not evidence of inherent immunity. Attribution of any observed robustness to a specific model architecture is **INFERRED** and not established by these sources.

## Mitigations RSaver implements

1. **Dual-end restatement.** Place the objective and the top hard constraints at both the start and end of the next request. This targets primacy and recency positions while leaving the middle for working material.
2. **Explicit IDs.** Name items `[OBJECTIVE-1]`, `[CONSTRAINT-1]`, `[FACT-1]`, `[DECISION-1]`, `[UNRESOLVED-1]`, `[NEXT-ACTION]` so follow-up instructions can reference an ID rather than a position.
3. **Bounded repetition.** Repeat only hard constraints and the objective. Repeating everything removes the priority signal; very short prompts gain nothing from duplication.
4. **Source discipline.** Keep verified facts separate from inferred decisions and unresolved hypotheses; never let a compaction block turn an unverified hypothesis into a stated fact.
5. **Drift signals, not diagnoses.** Detect objective/constraint absence from the recent window, repeated identical commands, and completion claims coexisting with open unknowns. These are deterministic text signals, not introspection.

## Limits

Re-anchoring cannot repair a genuinely wrong plan, restore missing evidence, or force a model to follow a constraint. It is a prompt-structuring intervention whose benefit must be measured with the RCoder ablation protocol. Do not claim an improvement without transcript evidence.

## Sources

- Liu et al., "Lost in the Middle": https://arxiv.org/abs/2307.03172
- "Found in the Middle": https://arxiv.org/abs/2406.16008
- "Attention Instruction": https://arxiv.org/abs/2406.17095
- "Attention Basin": https://aclanthology.org/2026.acl-long.1198/
- Anthropic, "Effective context engineering for AI agents": https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- Anthropic, "Effective harnesses for long-running agents": https://www.anthropic.com/research/effective-harnesses-for-long-running-agents
- Claude Code, "Explore the context window": https://code.claude.com/docs/en/context-window
- "Source-Judged Compaction": https://arxiv.org/html/2610.20927v1
- "AutoCompact": https://arxiv.org/abs/2610.02163
- CORAL: https://arxiv.org/abs/2610.40350v1
- "Protection Is (Nearly) All You Need": https://arxiv.org/html/2605.18053
