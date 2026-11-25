# Repository agent instructions

For software-engineering work, read `skills/rcoder/SKILL.md` and load only relevant expert references. Precedence: explicit user instructions → repository conventions and automation (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING`, linters, tests, CI) → RCoder defaults. Never claim a check passed unless it was run and observed. Keep changes scoped, preserve behavior, and report evidence and residual risks. This file is the small bootstrap for agents that do not discover Agent Skills.

On an unfamiliar model or host, select an execution profile and discover observable capabilities using `skills/rcoder/references/model-adaptation.md` before choosing specialists. Mark unestablished capabilities UNKNOWN and host compatibility claims as NOT VERIFIED unless evidence exists in `docs/COMPATIBILITY.md`.

Outside this repository (user-scope installs, external projects, Git worktrees), `skills/rcoder/` does not exist in the working directory. Prefer connected `mcp__rcoder__*` tools, then helper scripts under the installed skill directory by absolute path, and never conclude RCoder is unavailable from a missing relative path. See "Tool execution and resolution priority" in `skills/rcoder/SKILL.md`.
