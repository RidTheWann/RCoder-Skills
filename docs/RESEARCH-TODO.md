# Outstanding verification

These are environment-dependent checks, not claims that implementation is complete.

| Item | Blocker | Required evidence |
|---|---|---|
| GitHub Actions | v1.3.0 feature branch has not completed CI | Inspect Linux and Windows job logs; require all jobs green before merge. |
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
| OpenCode CLI discovery | `opencode` is absent from PATH in the Termux development shell | Install or locate the CLI, record its exact version, verify skill discovery and configuration syntax against that version, then update `docs/COMPATIBILITY.md` and `docs/ENVIRONMENT.md`. |
| Deepened specialist behavior | Static validation checks structure, not behavioral quality | Run scenario prompts for the deepened programming, security, and reverse-engineering modules and score against their Verification sections. |

Native discovery and model activation must not be inferred from successful file-copy simulations.
