# RCoder architecture

## Product boundary

RCoder is a portable Agent Skill package and installer/terminal manager. It is not a model, runtime, sandbox, permission system, or guarantee that a host model will select a skill. It coordinates only capabilities exposed by the active host.

## Layers

1. **Discovery and activation:** compact `skills/rcoder/SKILL.md` metadata supplies task-routing information.
2. **Core protocol:** instruction precedence and Intake → Recon → Plan → Implement → Verify → Report.
3. **Specialists:** focused references for programming languages, product engineering, cybersecurity, reverse engineering, and token efficiency; load only what is relevant.
4. **Runtime and tool adaptation:** observable capability discovery, adaptive execution profiles, and subagent strategy in `references/model-adaptation.md`; never treat a skill file as an installed tool.
5. **Deterministic helpers:** read-only stack detector and bounded metadata-only context snapshot.
6. **Extension and templates:** reusable templates under `assets/templates/` (including the 13-section specialist template and context capsule); project-specific rules under `.rcoder/`.
7. **Adapters and distribution:** Claude/Agent Plugin manifests, portable Agent Plugins manifest with Codex compatibility metadata, Node/npm CLI, PowerShell `irm` bootstrap, offline installers, terminal manager, and ZIP packages. Host evidence tiers live in `docs/COMPATIBILITY.md`; observed runtime capabilities in `docs/ENVIRONMENT.md`.

8. **Agent interface:** optional read-only stdio MCP server (`skills/rcoder/scripts/rcoder_mcp.py`) exposing the deterministic helpers, specialist lookup, and a routing-selection validator; Claude Code plugin slash commands and least-privilege subagents. Documented in `docs/MCP.md`. The server is launched by a host, never by installation.

## Runtime flow

```text
Request
  -> task boundary, instruction precedence, and authorization
  -> repository status and bounded reconnaissance
  -> discover observable host capabilities and select an execution profile
   -> select relevant engineering/security/reverse-engineering specialists
   -> plan with observable acceptance criteria
  -> implement the smallest correct change
  -> targeted verification and adversarial diff review
  -> evidence-based report and context capsule when needed
```

## Token and context policy

- Progressive disclosure: load only relevant references; keep the router compact.
- Bounded snapshots list paths and Git state but do not read source contents.
- Prefer exact symbol searches, bounded line ranges, focused diffs, and relevant test output.
- Maintain a compact ledger and context capsule on long tasks.
- Deduplicate tool calls; parallelize independent read-only work and serialize writes.
- Delegate only independent tasks with explicit file scopes and acceptance criteria.
- Never weaken authorization, provenance, regression, or data-integrity checks to reduce tokens.

## Installer and launcher flow

```text
PowerShell irm bootstrap (Windows) ----+
                                       +--> canonical skill + targets.json
Node/npm GitHub package ---------------+
       -> install selected native skill root
       -> register global command RCoder
       -> interactive target/scope/action manager
```

The PowerShell bootstrap provisions a Windows-native `RCoder.cmd` shim that calls the bundled `launcher/RCoder.ps1`; Node.js is not needed for the Windows `irm` route. The Node/npm installer provisions a POSIX wrapper or Windows shim as appropriate.

## Target registry

`targets.json` records stable target IDs, labels, and Project/User discovery roots. The Node manager and PowerShell terminal manager read it. The PowerShell bootstrap retrieves it from the same HTTPS archive. POSIX and offline PowerShell adapters have explicit path maps, checked by CI.

Multiple selections are deduplicated by resolved destination so hosts sharing a standard discovery root receive one physical copy.

## Invariants

- User and project instructions outrank RCoder defaults.
- Core skill metadata is portable and vendor-neutral.
- Canonical skill source is `skills/rcoder/`.
- Installs are scoped, idempotent, backed up, and reversible.
- Installers reject symlink/reparse-point traversal in destination paths.
- Bootstrap downloads are HTTPS-only and temporary; no downloaded second-stage installer is executed.
- Security testing and dynamic binary analysis require explicit authorization and isolated environments.
- Static checks do not impersonate native host activation or live model evaluation.
- The MCP server is read-only, dependency-free, root-confined, shell-free, network-free, and bounded in time and output; it never grants authorization.
- No hook is installed or shipped by default; automatic session-start behavior is opt-in.

## Distribution

Package version is synchronized across `package.json`, plugin manifests, skill metadata, changelog, and package builder. The npm `files` list includes the target catalog and PowerShell manager required by the global launcher.
