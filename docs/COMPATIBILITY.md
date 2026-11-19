# Host compatibility evidence matrix

Do not read this table as a compatibility guarantee. It records the specific kind of evidence available for each host. Installation is a file operation; discovery and activation are host/model behaviors and are verified separately.

## Evidence tiers

| Tier | Meaning | Claim that is allowed |
|---|---|---|
| T0 — File install | Installer copies the canonical skill into the documented root; covered by simulated file-system tests. | "The installer can write the skill to this path." |
| T1 — Documented discovery | A product documentation source was reviewed for the discovery path. | "This path is documented by the product." |
| T2 — Native discovery verified | The host was observed listing the skill in a real product session. | "This host discovered the skill." |
| T3 — Invocation verified | The host was observed loading and following the skill on a task. | "This host invoked the skill." |
| T4 — Behavioral evaluation | A pinned ablation meets the `evals/rubric.md` pass rule. | "RCoder measurably changed outcomes on this task." |

T0 and T1 are the only tiers supported by repository evidence at this version. T2-T4 are `NOT VERIFIED` for every host. Do not advertise compatibility using T0 evidence alone.

## Catalog

All twenty hosts share one canonical `skills/rcoder/` folder; roots are defined in `targets.json`. "Install" is T0 for all rows because CI simulates both Project and User scope for every target ID. "Docs" is T1 only where a reviewed product source exists in `docs/INSTALLATION-MATRIX.md` (reviewed 2026-11-16). Discovery, invocation, and behavior remain T2-T4 unverified.

| Host ID | Project root | User root | Install | Docs | Discovery | Invocation | Behavior |
|---|---|---|---|---|---|---|---|
| claude-code | `.claude/skills` | `~/.claude/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| codex | `.agents/skills` | `~/.agents/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| cursor | `.cursor/skills` | `~/.cursor/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| gemini-cli | `.gemini/skills` | `~/.gemini/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| copilot | `.github/skills` | `~/.copilot/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| agents | `.agents/skills` | `~/.agents/skills` | T0 | T1 | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| qoder | `.qoder/skills` | `~/.qoder/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| opencode | `.opencode/skills` | `~/.config/opencode/skills` | T0 | NOT VERIFIED for installed version | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| antigravity | `.agents/skills` | `~/.gemini/config/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| amp | `.agents/skills` | `~/.config/agents/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| zed | `.agents/skills` | `~/.agents/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| pi | `.pi/skills` | `~/.pi/agent/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| openclaw | `.agents/skills` | `~/.agents/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| autohand | `.autohand/skills` | `~/.autohand/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| warp | `.warp/skills` | `~/.warp/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| kilocode | `.kilo/skills` | `~/.kilo/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| cline | `.cline/skills` | `~/.cline/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| roo-code | `.roo/skills` | `~/.roo/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| trae | `.trae/skills` | `~/.trae/skills` | T0 | NOT VERIFIED (community-documented path) | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |
| factory | `.factory/skills` | `~/.factory/skills` | T0 | NOT VERIFIED | T2 NOT VERIFIED | T3 NOT VERIFIED | T4 NOT VERIFIED |

## OpenCode observation (Termux, 2026-11-18)

Observable results in the development shell: `opencode --version` returned `command not found`, and no CLI binary exists on `PATH` or in common installation locations. The session's model is reachable through the agent platform, but that does not expose the CLI, its configuration schema, or its skill-discovery behavior for inspection here.

Local package evidence: `~/.config/opencode/package.json` declares `@opencode-ai/plugin` 1.19.6, and the installed plugin package reports version 1.19.6 with `@opencode-ai/sdk` 1.19.6. The installed type definitions expose V1 hooks (`chat.message`, `experimental.chat.system.transform`) but no `session.start`. The global `opencode-linux-arm64@1.19.6` package exists, yet its ELF cannot execute in this Termux shell and no CLI shim is on PATH. RScan therefore generates a version-specific plugin adapter (`--api v1` for 1.19.x, `--api v2` only after confirming the V2 API) rather than applying one major version's syntax to another. Adapter execution remains NOT VERIFIED.

Consequences:

- OpenCode configuration syntax must be checked against the actually installed version before use. No version-specific OpenCode configuration is shipped by RCoder.
- OpenCode skill discovery in the installed version is `NOT VERIFIED`.
- Existing state records a user-selected reasoning variant; do not change the selected model as part of RCoder work.

## Termux observation (2026-11-18)

Verified runtimes in the development shell: Linux aarch64 (kernel `6.1.164-JetKernel-Venus`), Bash 5.3.15, Python 3.14.10, Node 24.22.3, npm 12.2.3, Git 2.56.1. The POSIX helper tests can run here; `gh`, `pwsh`, and `powershell` are absent, so Windows PowerShell, the `irm` bootstrap, hosted CI, and host-native activation cannot be executed and are recorded as `NOT VERIFIED` in this environment. Ordinary RCoder functionality must not require root, desktop Linux services, or shared-storage access. See `docs/ENVIRONMENT.md` for the capability-discovery record.
