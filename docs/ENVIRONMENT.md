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

## Active agent — observable capabilities

Observed in-session tool surface: shell command execution, structured file read, file write, exact file edit, glob file search, regex content search, task delegation to subagents, a to-do state tool, web search, and web fetch. Parallel tool invocation is available and was used for independent read-only probes. File reading can return image and PDF attachments. Working directory is the workspace root; a pre-approved temporary directory exists outside the workspace.

Not established in this environment: context window size, exact reasoning-mode implementation, reliable subagent output quality, web-access policy in other hosts, native OpenCode skill discovery, multimodal input from the user, long-task continuity mechanisms, and the selected model's internal architecture. All of these remain `UNKNOWN` and must not be described as capabilities.

## Model note

The session identifies the active model as Hy4 Flash Free (OpenCode). No claim about its architecture, training, context capacity, or tool-calling reliability is made here. Behavioral evaluation methodology is defined in `model-adaptation.md`; a recorded ablation for this model remains `NOT VERIFIED` until one is executed and retained under `evals/results.md`.

## Reusable discovery procedure

For any new session or host, follow the capability-discovery checklist in `skills/rcoder/references/model-adaptation.md`, record only observable evidence here, and mark anything else `UNKNOWN`. Do not ask a model to guess its own internals. See `docs/COMPATIBILITY.md` for host evidence tiers and installation constraints.
