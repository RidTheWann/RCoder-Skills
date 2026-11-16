# RCoder build progress — 2026-11-17

## Release objective

Build v1.2.0 as a safe extension of v1.1.0. Preserve both installers, the Agent Skill format, plugin manifests, and existing engineering references.

## Implementation checklist

- [x] Audit the repository and preserve PowerShell `irm` and Node/npm installation methods.
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
- [ ] Merge only after required checks pass.

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

## Evidence boundary

CI validates static structure, packaging, and simulated file-system behavior. It does not prove that a host model autonomously selects RCoder; native discovery, live activation, and with/without-skill model evaluation remain separate verification tasks.
