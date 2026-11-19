# Outstanding verification (reconciled 2026-11-19)

These are environment-dependent checks, not claims that implementation is complete. Earlier duplicate benchmark tasks (formerly rows 13, 18, 21, and 24) are consolidated into one item below.

| Item | Status / blocker | Required evidence |
|---|---|---|
| Live ablation completion | PARTIAL: 30/42 WITH-arm triggers valid; WITHOUT arm 0/61; provider free-usage limit reached | Rerun `scripts/run-benchmark.py` with quota or an authorized provider until both arms complete, then score with `--strict --json` and retain artifacts. |
| Scenario rubric scoring | NOT VERIFIED: 0/19 scenarios completed before quota exhaustion | Complete scenario runs and score each of the 4 objective rubric items from retained transcripts/test evidence. |
| Specialist selection quality | VERIFIED WEAKNESS on 18 WITH-arm positives: exact-match 1/18, F1 0.426 | Improve routing guidance, then rerun the full ablation to detect regression or improvement. |
| GitHub Actions (v1.11.0) | Feature-branch run pending | Observe the PR run URL and job conclusions on both Linux and Windows; record the exact commit. v1.10.0 main CI run `44491687529` is green (historical baseline). |
| Official `skills-ref` | VERIFIED: `skills-ref` 0.1.5 (pinned via npx cache) reported `Valid skill: skills/rcoder`, exit 0. The package shebang needed direct `node <dist/cli.js>` invocation on Termux because `/usr/bin/env` is absent. | Re-run on a conventional host with `npx skills-ref validate skills/rcoder`; no open action for this environment. |
| Windows `irm` bootstrap | Syntax checks do not execute a real HTTPS bootstrap in a clean profile | Run the exact `irm` command on PowerShell 5.1 and 7; verify PATH, launcher, Project/User install, update, dry-run, and restore. Only PowerShell 7 is locally observable here. |
| Node/npm clean install | CI package checks do not replace a clean networked install | Run `npx -y github:RidTheWann/RCoder-Skills` on a clean system with Node, npm, and Git. |
| Host-native discovery (all hosts) | VERIFIED for OpenCode 1.19.6 only; NOT VERIFIED for the other 19 hosts | Verify discovery and invocation in each host application; update `docs/COMPATIBILITY.md` per host. |
| OpenCode RScan adapter runtime | Plugin load, hook firing, and scanner execution VERIFIED on 1.19.6; final-menu visibility in the answering agent NOT VERIFIED after quota exhaustion | Re-run with available quota; confirm one injection per session and a fresh scan in a second session. V2 adapter is syntax-checked only and must not be used on V1. |
| Installer security review | Documented in `docs/INSTALLER-SECURITY-REVIEW.md` | Independently reproduce any open findings listed there on real Windows/POSIX profiles. |
| TRAE path | Community documented | Verify project `.trae/skills` and user `~/.trae/skills` in the current TRAE release. |
| Specialist quality (semantic) | Mechanically VERIFIED: 59 references, 13 headings each, substantive section bodies, no unfilled placeholders; deep semantic review sampled, not exhaustive | Score scenario prompts for the deepened programming, security, and RE modules against each module's Verification section. |
| ZIP import | No authenticated product UI in build environment | Import generated skill/plugin ZIPs into supported hosts and perform a low-risk activation test. |
| `rg` absent in this shell | OpenCode glob/grep/skill tools report `ripgrep execution failed` in both arms | Provide a working ripgrep on PATH in a clean benchmark host and rerun the ablation. |

Native discovery and model activation must not be inferred from successful file-copy simulations. Do not describe the partial benchmark as complete.
