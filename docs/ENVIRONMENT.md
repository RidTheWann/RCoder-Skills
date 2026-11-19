# Environment and capability record

This record separates observed runtime facts from capabilities that could not be established. It is a snapshot for the primary development environment, not a claim about every model or host. Update it by re-running the probes, not by inference.

## Probe log — 2026-11-18 (Termux development shell)

| Probe | Observed result | Status |
|---|---|---|
| `git status --short` | Clean working tree | VERIFIED |
| `git branch --show-current` | `main` (before feature branch creation) | VERIFIED |
| `git rev-parse HEAD` | `bd108ed115fdfea6d336785c167d27cea25bd419` | VERIFIED |
| `opencode --version` | `command not found` | VERIFIED (absent from PATH in this shell) |
| `node --version` | `v24.22.3` | VERIFIED |
| `npm --version` | `12.2.3` | VERIFIED |
| `python3 --version` | `Python 3.14.10` | VERIFIED |
| `git --version` | `git version 2.56.1` | VERIFIED |
| `bash --version` | `5.3.15(1)-release (aarch64-unknown-linux-gnu)` | VERIFIED |
| `uname -a` | `Linux localhost 6.1.164-JetKernel-Venus ... aarch64` | VERIFIED |
| `python3 scripts/validate-all` | 644 checks, PASS | VERIFIED |
| `python3 scripts/test-context-snapshot.py` | PASS | VERIFIED |
| `node --check scripts/rcoder.mjs` | Exit 0 | VERIFIED |
| `python3 scripts/test-score-eval.py` | PASS, perfect/mixed/ablation scoring and four rejection paths | VERIFIED |
| `python3 scripts/test-rsaver.py` | PASS, reduction, verbatim evidence, recovery, verification, dedupe economics | VERIFIED |
| `python3 scripts/rsaver.py compact <node-installer log> --max-lines 60 --json` | Relative estimate 293 to 144, saved 51.19%, critical lines preserved, omitted ranges recoverable | VERIFIED (relative estimate only) |
| `python3 scripts/score-eval.py --predictions <synthetic> --strict` | 24 TP / 18 TN / 0 FP / 0 FN; 19/19 scenarios PASS | VERIFIED (synthetic fixture only) |
| `command -v opencode` | `command not found` | VERIFIED |
| `~/.config/opencode/package.json` | Declares `@opencode-ai/plugin` 1.19.6 | VERIFIED (file read) |
| Installed `@opencode-ai/plugin/package.json` | Version 1.19.6; depends on `@opencode-ai/sdk` 1.19.6 | VERIFIED (file read) |
| `~/.config/opencode/opencode.jsonc` | Contains only `$schema: https://opencode.ai/config.json` | VERIFIED (file read) |
| `command -v gh`, `command -v pwsh`, `command -v powershell` | All not found | VERIFIED |

## Active agent — observable capabilities

Observed in-session tool surface: shell command execution, structured file read, file write, exact file edit, glob file search, regex content search, task delegation to subagents, a to-do state tool, web search, and web fetch. Parallel tool invocation is available and was used for independent read-only probes. File reading can return image and PDF attachments. Working directory is the workspace root; a pre-approved temporary directory exists outside the workspace.

Not established in this environment: context window size, exact reasoning-mode implementation, reliable subagent output quality, web-access policy in other hosts, native OpenCode skill discovery, multimodal input from the user, long-task continuity mechanisms, and the selected model's internal architecture. All of these remain `UNKNOWN` and must not be described as capabilities.

OpenCode plugin/SDK packages at version 1.19.6 exist in the configuration directory, so the historical version is now supported by local package evidence rather than a screenshot alone. The absence of the CLI means its version command, configuration schema behavior at runtime, and skill-discovery behavior remain unverified. No version-specific OpenCode configuration syntax is applied on the basis of the package version alone. The absence of `gh` and PowerShell prevents hosted CI and Windows verification from this shell.

## Model note

The session identifies the active model as Hy4 Flash Free (OpenCode). No claim about its architecture, training, context capacity, or tool-calling reliability is made here. Behavioral evaluation methodology is defined in `model-adaptation.md`; a recorded ablation for this model remains `NOT VERIFIED` until one is executed and retained under `evals/results.md`.

## Reusable discovery procedure

For any new session or host, follow the capability-discovery checklist in `skills/rcoder/references/model-adaptation.md`, record only observable evidence here, and mark anything else `UNKNOWN`. Do not ask a model to guess its own internals. See `docs/COMPATIBILITY.md` for host evidence tiers and installation constraints.
