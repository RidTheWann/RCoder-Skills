# Outstanding verification

These are environment-dependent checks, not claims that implementation is complete.

| Item | Blocker | Required evidence |
|---|---|---|
| GitHub Actions | Hosted CI for v1.10.0 has not been observed in this session | Check the PR run URL and job conclusions; record the exact commit before merge. Historical PRs #3, #4, and #5 are merged with green CI. |
| Official `skills-ref` | Validator is not installed in the build environment | Run the official validator against `skills/rcoder`; record version and output. |
| Windows `irm` bootstrap | Syntax checks do not execute a real HTTPS bootstrap in a clean profile | Run the exact `irm` command on PowerShell 5.1 and 7; verify PATH, launcher, Project/User install, update, dry-run, and restore. |
| Node/npm package | CI package checks do not replace a clean networked install | Run `npx -y github:RidTheWann/RCoder-Skills` on a clean system with Node, npm, and Git. |
| Host-native discovery | Path matrices are simulated | Verify skill discovery and invocation in all twenty host applications. |
| TRAE path | Current path convention is community documented | Verify project `.trae/skills` and user `~/.trae/skills` in the current TRAE release; update the catalog if native UI differs. |
| Live trigger/behavior | No controlled model runtime in CI | Run trigger prompts and scenarios with identical models/tools/permissions, with and without RCoder; score transcript and tests using `evals/rubric.md`. |
| Installer security review | Static checks cover selected patterns only | Independently review PATH updates, symlink handling, archive extraction, and backup/restore failure paths. |
| Reverse-engineering behavior | Static evaluation includes an RE scenario | Test on authorized fixture binaries; validate provenance, evidence-led hypotheses, isolation, and differential tests. |
| Context helper | Unit test covers bounded fixture output | Test representative large repos on Windows and POSIX; inspect path limits and symlink handling. |
| ZIP import | No authenticated product UI in build environment | Import the generated skill/plugin ZIP into supported hosts and perform a low-risk activation test. |
| Model ablation (Hy4 Flash Free) | No pinned with/without run has been executed | Run the identical suite with and without RCoder under the `evals/rubric.md` methodology; retain configuration and per-criterion scores in `evals/results.md`. |
| OpenCode CLI discovery | Package 1.19.6 is installed globally, but its ELF cannot execute on Termux and no CLI shim is on PATH | Run the CLI on a supported host, record its version, verify skill discovery, then update `docs/COMPATIBILITY.md` and `docs/ENVIRONMENT.md`. |
| OpenCode RScan adapter | V1 and V2 plugin templates are generated but never executed in a real OpenCode session | Install `rscan hooks adapter --host opencode` on the exact target version, confirm the menu is injected once per session, and record the outcome. |
| Live ablation with the new scorer | No model prediction run has been produced; the harness is verified only on synthetic fixtures | Produce with/without prediction files using `evals/ABLATION-PROTOCOL.md`, run `scripts/score-eval.py --strict`, and retain results in `evals/results.md`. |
| Deepened specialist behavior | Static validation checks structure, not behavioral quality | Run scenario prompts for the deepened programming, security, and reverse-engineering modules and score against their Verification sections. |
| Specialist quality gate | Validator enforces all 13 headings but cannot judge substance | Use model evaluation results and negative cases to audit each specialist's decision tree, sources, and verification contract. |
| Live benchmark execution | `docs/LIVE-BENCHMARK.md` defines the protocol but no run exists | Produce with/without prediction files and score with `scripts/score-eval.py --strict`; retain results in `evals/results.md`. |

Native discovery and model activation must not be inferred from successful file-copy simulations.
