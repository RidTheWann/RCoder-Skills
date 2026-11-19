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
| opencode | `.opencode/skills` | `~/.config/opencode/skills` | T0 | T1 (verified 1.19.6 docs) | T2 VERIFIED (1.19.6) | T3 VERIFIED (1.19.6) | T4 PARTIAL (WITH arm only) |
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

## OpenCode observation (Termux, re-probed 2026-11-19)

`opencode` is not on `PATH`, and direct execution of the bundled ELF fails on Termux. The CLI runs when invoked through the installed glibc loader, which reported version `1.19.6`. Version-matched local evidence: `@opencode-ai/plugin` and `@opencode-ai/sdk` both report `1.19.6`; their type definitions expose V1 hooks (`chat.message`, `experimental.chat.system.transform`) and no `session.start`. Official V1 and V2 plugin contracts were reviewed; V2 (`Plugin.define`, `ctx.session.hook`) must not be applied to the installed V1 runtime, so the adapter requires an explicit `--api` choice.

With the loader-based CLI, native discovery from `.opencode/skills/rcoder/SKILL.md` was directly observed: the model invoked the `skill` tool with `name: "rcoder"`, read `SKILL.md`, and loaded specialist references. A separate probe plugin confirmed that `experimental.chat.system.transform` reaches model context and fires multiple times per session. The generated V1 RScan adapter loaded in the real CLI, ran the scanner, and the answering agent quoted the injected menu verbatim in two independent sessions, confirming end-to-end injection and per-session behavior. The V2 adapter is syntax-checked only and remains NOT VERIFIED at runtime.

Consequences:

- OpenCode 1.19.6 supports project-level skill discovery: T2 and T3 are VERIFIED for that exact version only.
- T4 has a partial WITH-arm result for hy4-flash-free; the controlled WITHOUT arm is NOT VERIFIED because the provider free-usage limit was exhausted.
- `rg` is absent; OpenCode glob/grep/skill tools report `ripgrep execution failed`. This affects both arms identically and is an environment limitation, not an RCoder failure.
- The user-selected reasoning variant was left unchanged; no model or provider configuration was modified.

## Termux observation (2026-11-18)

Verified runtimes in the development shell: Linux aarch64 (kernel `6.1.164-JetKernel-Venus`), Bash 5.3.15, Python 3.14.10, Node 24.22.3, npm 12.2.3, Git 2.56.1. The POSIX helper tests can run here; `gh`, `pwsh`, and `powershell` are absent, so Windows PowerShell, the `irm` bootstrap, hosted CI, and host-native activation cannot be executed and are recorded as `NOT VERIFIED` in this environment. Ordinary RCoder functionality must not require root, desktop Linux services, or shared-storage access. See `docs/ENVIRONMENT.md` for the capability-discovery record.
