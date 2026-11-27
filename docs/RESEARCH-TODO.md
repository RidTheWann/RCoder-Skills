# Outstanding verification (reconciled 2026-11-19)

These are environment-dependent checks, not claims that implementation is complete. Earlier duplicate benchmark tasks (formerly rows 13, 18, 21, and 24) are consolidated into one item below.

| Item | Status / blocker | Required evidence |
|---|---|---|
| Live ablation completion (historical control) | VERIFIED: 61/61 cases in both arms with `openrouter/tencent/hy4-flash`; `--strict` scorer exit 0; see `evals/runs/hy4-flash-openrouter-2026-11-19/` | Immutable; never re-run in place. |
| Live ablation after v1.13 routing changes | PARTIAL, VERIFIED: control v1.11.0 vs treatment v1.13 on 12 comparable positive triggers; specialist F1 0.368 -> 0.476, trigger F1 0.957 -> 0.857; see `evals/runs/v113-live-free-2026-11-19/` | Free-tier probe timed out after the run. Rerun the full 42 triggers and 19 scenarios on an authorized runtime when quota is available. |
| Scenario rubric scoring | VERIFIED: 19/19 scenarios per arm scored by a same-model judge from bounded transcripts; WITH 6/19 pass, WITHOUT 4/19 pass | Use a different judge model in a future run to measure and reduce same-model bias. |
| Specialist selection quality | IMPROVED INSTRUCTIONS, LIVE SIGNAL VERIFIED ON A SMALL SAMPLE: v1.13 selection gate and composition rules; free-tier control/treatment specialist F1 0.368 -> 0.476, empty sets 7/12 -> 5/12 | Confirm on the full frozen dataset with an authorized provider and held-out cases; do not treat the small sample as significant. |
| Independent judge | IMPLEMENTED, NOT VERIFIED: `--judge-model`, arm blinding, non-destructive judged output, full response retention | Run with a separate authorized judge model and compare against same-model judgments. |
| GitHub Actions (v1.12.0) | VERIFIED historically: PR #9 run `44515483533` PASS on Linux and Windows | Historical record only; v1.13 PR run status is recorded in `docs/V1.13-DELIVERY.md`. |
| Official `skills-ref` | VERIFIED: `skills-ref` 0.1.5 (pinned via npx cache) reported `Valid skill: skills/rcoder`, exit 0. The package shebang needed direct `node <dist/cli.js>` invocation on Termux because `/usr/bin/env` is absent. | Re-run on a conventional host with `npx skills-ref validate skills/rcoder`; no open action for this environment. |
| Windows `irm` bootstrap | Syntax checks do not execute a real HTTPS bootstrap in a clean profile | Run the exact `irm` command on PowerShell 5.1 and 7; verify PATH, launcher, Project/User install, update, dry-run, and restore. Only PowerShell 7 is locally observable here. |
| Node/npm clean install | CI package checks do not replace a clean networked install | Run `npx -y github:RidTheWann/RCoder-Skills` on a clean system with Node, npm, and Git. |
| Host-native discovery (all hosts) | VERIFIED for OpenCode 1.19.6 only; NOT VERIFIED for the other 19 hosts | Verify discovery and invocation in each host application; update `docs/COMPATIBILITY.md` per host. |
| OpenCode RScan adapter runtime | VERIFIED on 1.19.6: plugin loads, hook fires, scanner runs, and the injected menu was quoted verbatim by the answering agent in two independent sessions. The separate dual V2/V1 RCoder plugin was observed on 2.4.2 (`docs/OPENCODE-V2-ADAPTER.md`); it must not be used on V1. | No action for V1; any new V2 claim still needs observation on the exact V2 build. |
| Installer security review | Documented in `docs/INSTALLER-SECURITY-REVIEW.md` | Independently reproduce any open findings listed there on real Windows/POSIX profiles. |
| TRAE path | Community documented | Verify project `.trae/skills` and user `~/.trae/skills` in the current TRAE release. |
| Specialist quality (semantic) | Mechanically VERIFIED: 59 references, 13 headings each, substantive section bodies, no unfilled placeholders; deep semantic review sampled, not exhaustive | Score scenario prompts for the deepened programming, security, and RE modules against each module's Verification section. |
| ZIP import | No authenticated product UI in build environment | Import generated skill/plugin ZIPs into supported hosts and perform a low-risk activation test. |
| `rg` absent in this shell | OpenCode glob/grep/skill tools report `ripgrep execution failed` in both arms | Provide a working ripgrep on PATH in a clean benchmark host and rerun the ablation. The tool probe now offers ordered fallback and version detection for this case. |
| v1.13 expanded and multilingual live runs | NOT VERIFIED: datasets and harness support exist (`--triggers`, `--scenarios`), but the free-tier probe timed out before these runs | Run expanded and multilingual datasets as separate experiments on an authorized runtime; never merge them with the frozen control. |

Native discovery and model activation must not be inferred from successful file-copy simulations. Do not describe the partial benchmark as complete.
