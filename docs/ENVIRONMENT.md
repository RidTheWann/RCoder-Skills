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
| `python3 -m pip install tiktoken` / `tokenizers` | Failed to build wheels on Termux aarch64 / Python 3.14 | VERIFIED (environment limitation) |
| Public `r50k_base`, `cl100k_base`, `o200k_base` encoding files fetched over HTTPS | Used as a pure-Python BPE oracle for calibration | VERIFIED (research only) |
| Seven-sample calibration: aggregate absolute error vs oracle | `chars/4` ~15%, v1 ~13%, v2 generic ~13%, v2 o200k profile ~7.5% | VERIFIED for that fixture; NOT a benchmark |
| `python3 scripts/rsaver.py gate <synthetic-envelope> --json` | Required items kept, optional history deferred, cache prefix eligible, budget within window | VERIFIED (synthetic envelope only) |
| `python3 scripts/rsaver.py budget --window 100000 --output-reserve 4000 --reasoning-reserve 8000 --tool-schema 1000` | available_input 88000, item_budget 87000 | VERIFIED |
| `python3 scripts/rsaver.py drift <synthetic-transcript> --json` | objective/constraint absence, repeated command, and completion-with-unknowns signals detected | VERIFIED (synthetic fixture only) |
| `python3 scripts/rsaver.py anchor <synthetic-state> --json` | Dual-end block, explicit IDs, estimate within budget | VERIFIED (synthetic fixture only) |
| `python3 scripts/rscan.py scan --root . --format json` | Stacks, risk signals, ranked options; bounded sample | VERIFIED |
| `python3 scripts/rscan.py hooks preview --host claude-code|gemini-cli` | Valid `SessionStart` config payloads | VERIFIED (templates only; live host execution NOT VERIFIED) |
| `python3 scripts/rsaver.py pack <repeated-text> --json` / `unpack` | Estimate reduced ~93%, SHA-256 verified exact restoration | VERIFIED (synthetic fixture) |
| `python3 scripts/rsaver.py crosscheck --expect ... --diff ... --test-log ... --usage ... --json` | FAIL verdict with evidence lines; usage copied, billing unchanged | VERIFIED (synthetic fixture) |
| `python3 scripts/score-eval.py --predictions <synthetic> --strict` | 24 TP / 18 TN / 0 FP / 0 FN; 19/19 scenarios PASS | VERIFIED (synthetic fixture only) |
| `command -v opencode` | `command not found` | VERIFIED |
| `~/.config/opencode/package.json` | Declares `@opencode-ai/plugin` 1.19.6 | VERIFIED (file read) |
| Installed `@opencode-ai/plugin/package.json` | Version 1.19.6; depends on `@opencode-ai/sdk` 1.19.6 | VERIFIED (file read) |
| `npm ls -g` | `opencode-linux-arm64@1.19.6` is installed globally, but no `opencode` shim is on PATH | VERIFIED |
| Direct execution of the bundled `opencode` ELF | Fails with `cannot execute: required file not found` on Termux | VERIFIED (environment limitation) |
| Installed plugin type definitions | 1.19.6 exposes V1 hooks including `chat.message` and `experimental.chat.system.transform`; no `session.start` | VERIFIED (file read) |
| `~/.config/opencode/opencode.jsonc` | Contains only `$schema: https://opencode.ai/config.json` | VERIFIED (file read) |
| `command -v gh`, `command -v pwsh`, `command -v powershell` | All not found | VERIFIED |

## Active agent — observable capabilities

Observed in-session tool surface: shell command execution, structured file read, file write, exact file edit, glob file search, regex content search, task delegation to subagents, a to-do state tool, web search, and web fetch. Parallel tool invocation is available and was used for independent read-only probes. File reading can return image and PDF attachments. Working directory is the workspace root; a pre-approved temporary directory exists outside the workspace.

Not established in this environment: context window size, exact reasoning-mode implementation, reliable subagent output quality, web-access policy in other hosts, native OpenCode skill discovery, multimodal input from the user, long-task continuity mechanisms, and the selected model's internal architecture. All of these remain `UNKNOWN` and must not be described as capabilities.

OpenCode plugin/SDK packages at version 1.19.6 exist locally, and the V1 plugin hook names were confirmed from the installed type definitions. Direct execution of the packaged ELF fails, but the CLI runs through the Termux glibc loader (`ld-linux-aarch64.so.1 --library-path <glibc/lib> <opencode-ELF>`). This unlocked live probing on 19 November 2026: `opencode run --format json` produced genuine hy4-flash-free responses and provider token fields; the `rcoder` skill was **natively discovered and invoked** from `.opencode/skills/rcoder/SKILL.md` (permission `skill pattern=rcoder`, `tool_use tool=skill name=rcoder`, direct `SKILL.md` read); and a probe plugin proved that `experimental.chat.system.transform` injects text into model context and fires twice per session. The RScan V1 adapter was generated, loaded by the real CLI, ran `rscan.py` successfully, and the answering agent quoted the injected menu verbatim in two independent sessions. With user-supplied OpenRouter credentials passed per process, the complete 61-case × 2-arm ablation was rerun on `openrouter/tencent/hy4-flash`; no credential was stored in any artifact. PowerShell 7.6.10 and `gh` are available locally; hosted CI results are recorded per run URL, not inferred.

## Probe log — 2026-11-19 (Termux development shell, re-probed)

| Probe | Observed result | Status |
|---|---|---|
| Baseline `git rev-parse HEAD` on `main` | `6472c7090e580317b9b26142422455aba5092c7c` (v1.10.0, PR #6) | VERIFIED |
| `gh pr list` / `gh run list` | PRs #1-#6 merged; latest main CI `44491687529` success | VERIFIED |
| `opencode` via glibc loader, `--version` | `1.19.6` | VERIFIED |
| `opencode run --model opencode/hy4-flash-free --format json` | Real JSON events, step_finish token counts | VERIFIED |
| Native skill discovery from `.opencode/skills/rcoder/` | `skill` tool invoked, SKILL.md read, references loaded | VERIFIED |
| RScan V1 plugin in real CLI | Plugin loaded, hook fired, `rscan.py` produced 887-char menu | VERIFIED (plugin/menu); end-to-end injection to final answer NOT VERIFIED |
| `command -v gh` / `pwsh --version` | `gh` 2.105.0; PowerShell 7.6.10 | VERIFIED |
| `command -v rg` | not found; OpenCode glob/grep/skill tools report `ripgrep execution failed` | VERIFIED (affects both benchmark arms equally) |
| Live ablation, WITH arm | 30/42 triggers valid before provider quota exhaustion | VERIFIED (partial) |
| Live ablation, WITHOUT arm | 0/61 cases (harness ordering + provider quota) | NOT VERIFIED |
| Provider free usage | `AI_APICallError: Free usage limit reached` | VERIFIED (external blocker) |

## Model note

The session identifies the active model as Hy4 Flash Free (OpenCode). No claim about its architecture, training, context capacity, or tool-calling reliability is made here. Behavioral evaluation methodology is defined in `model-adaptation.md`; a recorded ablation for this model remains `NOT VERIFIED` until one is executed and retained under `evals/results.md`.

## Probe log — 2026-11-19 (v1.13 development session, re-probed)

This section supersedes the earlier present-tense "opencode NOT AVAILABLE" observation, which remains true of the earlier development shell but is not a property of this session.

| Probe | Observed result | Status |
|---|---|---|
| `command -v opencode` | not found | VERIFIED |
| glibc loader `/data/data/com.termux/files/usr/glibc/lib/ld-linux-aarch64.so.1 --version` | GNU libc for Android/com.termux 2.44 | VERIFIED |
| `ld-linux-aarch64.so.1 --library-path /data/data/com.termux/files/usr/glibc/lib <opencode-ELF> --version` | `1.19.6`, exit 0 | VERIFIED |
| Free-tier live probe with `opencode/hy4-flash-free` | real `text` event and `step_finish` token block, exit 0 | VERIFIED |
| Bounded control/treatment ablation | 24 trigger IDs per arm; 12 positive IDs comparable after shared invalid exclusion | VERIFIED |
| Post-run free-tier probe | timeout (quota exhausted); no paid substitute used | VERIFIED |
| `command -v rg` | not found | VERIFIED |
| `gh auth status` | authenticated as `RidTheWann`, scopes `repo`, `workflow` | VERIFIED |

## Reusable discovery procedure

For any new session or host, follow the capability-discovery checklist in `skills/rcoder/references/model-adaptation.md`, record only observable evidence here, and mark anything else `UNKNOWN`. Do not ask a model to guess its own internals. See `docs/COMPATIBILITY.md` for host evidence tiers and installation constraints.
