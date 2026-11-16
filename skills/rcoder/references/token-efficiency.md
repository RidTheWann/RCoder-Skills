# Token-efficient engineering and context management

## Activate when
Any coding-agent workflow, large repository, expensive context, multi-agent task, or repeated tool use.

## Mental model
Optimize total engineering cost—not token count alone. Minimize sufficient context and tool activity while preserving correctness, auditability, and security.

## Procedure
1. Use progressive disclosure: read the router, then only directly relevant references. Never preload the entire skill library.
2. Run scripts/context_snapshot.py for a compact repository map on large or unfamiliar projects; inspect git status, manifests, and quality entry points before broad exploration.
3. Prefer exact symbol search, bounded line ranges, focused diffs, and relevant test output. Never dump all files or full logs by default.
4. Maintain one compact working ledger: goal, constraints, verified facts with paths/lines, assumptions, decisions, commands/results, changed files, risks, and next action.
5. Deduplicate reads and tool calls. Parallelize independent read-only reconnaissance; serialize writes and state-changing operations.
6. Summarize verbose output while preserving paths, line numbers, exact error snippets, status codes, and uncertainty. Never compress away security-critical evidence.
7. Delegate only independent bounded tasks with explicit inputs, outputs, file scopes, and acceptance criteria; prevent overlapping edits.
8. Use risk-based verification: narrow test first, expand proportionately, and state exactly which checks were skipped.
9. Before context compaction or handoff, update a concise state capsule from assets/templates/context-capsule-template.md; do not narrate the entire conversation.
10. Do not weaken authorization, source provenance, threat modeling, data integrity, regression coverage, or destructive-action safeguards to save tokens.

## Quality checklist
- [ ] Only relevant modules and source ranges are loaded.
- [ ] Tool outputs are bounded without losing critical evidence.
- [ ] A current state capsule exists for long tasks.
- [ ] Delegation is independent and non-overlapping.
- [ ] Security and correctness gates are preserved.

## Anti-patterns
- Reading the entire repository or logs without a question.
- Repeatedly printing status or re-reading unchanged files.
- Multiple agents editing the same files concurrently.
- Replacing exact test evidence with unsupported summaries.
- Shortening context until assumptions or safety constraints disappear.

## Verification
Compare final state against acceptance criteria and the working ledger; inspect the final diff and verify every reported command/result.

## Output format
Use a compact handoff: objective, decisions, changed files, verified commands/results, assumptions, risks, and next action.
