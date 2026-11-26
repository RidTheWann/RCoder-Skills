---
description: Build a checksummed context capsule and capture verified lessons before handoff or compaction
argument-hint: [current objective]
---
Prepare a compact, verifiable context handoff capsule for long-running or multi-agent work.

Objective requested by the user (may be empty): $ARGUMENTS

1. Capture current repository state using `rcoder_context_snapshot` (or `context_snapshot.py`) and check recent episodic lessons with `rcoder_recall`.
2. If verified fixes were completed in this session, record sanitized lessons with `rcoder_learn`.
3. Assemble a SHA-256 checksummed handoff capsule via `rcoder_handoff` separating verified facts, decisions, hard constraints, and open unknowns. Label unverified items NOT VERIFIED.
