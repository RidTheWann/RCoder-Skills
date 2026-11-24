---
description: Produce a scoped implementation plan with acceptance criteria before changing code
argument-hint: [task or goal to plan]
---
Plan this change without implementing it: $ARGUMENTS

1. Read repository guidance (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`), `git status`, manifests, CI, and the code and tests nearest to the change. If the `rcoder` MCP server is connected, call `rcoder_scan` for ranked options.
2. Select specialists by deliverable, not by keywords: one primary and only supporting modules with a distinct responsibility. If the MCP server is connected, call `rcoder_validate_selection`; otherwise confirm each name exists in `skills/rcoder/references/`.
3. For a multi-file, risky, or architectural change, delegate to the `rcoder-planner` subagent. For a small change, plan inline.
4. Output the goal, non-goals, ordered steps with one observable acceptance criterion and the narrowest check for each, risks with rollback, and the verification map. Label claims VERIFIED, INFERRED, or NOT VERIFIED.
5. Stop after presenting the plan and wait for confirmation. Do not modify files.
