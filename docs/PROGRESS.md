# RCoder build progress — 2026-11-18

## Release objective

Build v1.3.0 as a safe extension of v1.2.0. Preserve both installers, the Agent Skill format, plugin manifests, the canonical skill directory, and all existing specialist capabilities while adding model adaptation and an evidence-based compatibility contract.

## Implementation checklist

- [x] Audit the repository and preserve PowerShell `irm` and Node/npm installation methods.
- [x] Normalize the evaluation contract across `evals/rubric.md`, `evals/results.md`, and `scripts/validate-all`.
- [x] Add model-adaptation capability discovery, adaptive execution profiles, and evaluation methodology.
- [x] Add a host compatibility evidence matrix and an environment/capability record.
- [x] Deepen core engineering, security, and reverse-engineering specialists without removing existing modules.
- [ ] Re-run the full local gate set and installer/packaging regressions for v1.3.0.
- [x] Add a global terminal manager invoked by typing `RCoder`.
- [x] Add multi-target and Project/User selection, shared-root deduplication, install/update, uninstall, backup, and restore.
- [x] Add a Windows-native PowerShell launcher independent of Node.js.
- [x] Add a Node/npm global launcher and include its runtime files in package metadata.
- [x] Expand the target catalog to twenty hosts.
- [x] Add programming, cybersecurity, reverse-engineering, and smart-contract specialists.
- [x] Add a read-only metadata-only context snapshot helper and context-capsule template.
- [x] Expand trigger evaluations to 42 prompts and behavioral scenarios to 14.
- [x] Run the Linux and Windows GitHub Actions matrix on the feature branch.
- [x] Inspect CI logs and fix the validator, Node test, POSIX test, and PowerShell launcher issues found during CI.
- [x] Merge PR #1 after all required checks passed; verify the resulting `main` commit with a post-merge CI run.

## Verification design

| Area | Required checks |
|---|---|
| Static structure | Skill frontmatter, specialist headings/line limits, links, manifests, versions, target registry, and selected security checks |
| Context helper | Metadata-only output, bounded paths/depth, dependency/build exclusions, and symlink handling |
| Node CLI | Syntax, help/list, 40 target/scope cases, dry-run, backup/restore, idempotence, launcher and interactive menu |
| POSIX adapter | 40 target/scope cases, dry-run, backup/restore, repeated install |
| PowerShell | Parse bootstrap and manager; 40 target/scope cases on Windows PowerShell 5.1 and PowerShell 7 |
| Packaging | `npm pack --dry-run --json`, reproducible ZIP packages, and checksums |
| Live activation | Separate native verification in each host; not inferred from file-copy tests |

## Verified CI evidence

- Workflow run: [43937693813](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43937693813) — **PASS** on both `ubuntu-latest` and `windows-latest` for commit `a19eed4f466d2231779a2c230a364ff773ad4554`.
- Static validator: 644 checks passed.
- Context snapshot regression and Node syntax check passed on both platforms.
- Node installer/launcher matrix: 20 hosts × 2 scopes passed on Linux and Windows, including launcher setup, idempotence, shared-root restore, legacy backup restore, and interactive-menu smoke test.
- npm package dry-run passed on both platforms.
- POSIX adapter: 20 hosts × 2 scopes passed on Linux.
- Windows PowerShell 5.1 and PowerShell 7: parser checks and 20 hosts × 2 scopes passed.
- Reproducible skill/plugin/source package build passed on Linux and Windows.

## Verified merge and CI evidence

- PR [#1](https://github.com/RidTheWann/RCoder-Skills/pull/1) was squash-merged on 2026-11-17 UTC as `7f7c88f2fce5b8b2754d9cc10c65cca69a23f5ed`.
- Post-merge workflow [43940645566](https://github.com/RidTheWann/RCoder-Skills/actions/runs/43940645566) — **PASS** on both `ubuntu-latest` and `windows-latest` for the exact `main` merge commit.
- The post-merge run revalidated static checks, context snapshot, Node/launcher matrix, npm package, POSIX matrix, Windows PowerShell 5.1 and 7 matrices, and reproducible package build.

## Evidence boundary

CI validates static structure, packaging, and simulated file-system behavior. It does not prove that a host model autonomously selects RCoder; native discovery, live activation, and with/without-skill model evaluation remain separate verification tasks.
