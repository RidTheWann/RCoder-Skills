# Security policy

## Supported versions

Only the latest release on `main` receives security fixes.

## Reporting a vulnerability

Please report suspected vulnerabilities privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Do not open a public issue or pull request that describes an unfixed vulnerability.

Include the affected version or commit, the host and operating system, a minimal reproduction, and the impact you observed. You can expect an acknowledgement within a few days. Fixes are released as soon as they are verified, and the report is credited unless you ask otherwise.

## Scope

In scope:

- The installers (`install.ps1`, `scripts/install.sh`, `scripts/rcoder.mjs`, `launcher/`) and the settings and MCP configuration merge logic.
- The MCP servers in `skills/rcoder/scripts/` (path confinement, credential refusal, argument handling, output bounds, the loopback HTTP adapter's token and Origin checks).
- The opt-in hook handlers in `skills/rcoder/scripts/rcoder_hooks.py`.
- RSaver redaction (`rsaver redact`), which is best-effort and lossy by design.
- Packaging and supply-chain integrity (`scripts/package`, `dist/SHA256SUMS`, CI workflow pins).

Out of scope: behavior of third-party hosts or models, findings that need an already-compromised user account, and the documented limits of the hook guard (it is a guardrail, not a sandbox; see `docs/HOOKS.md`).

## Safe-use notes

- RCoder does not grant authorization. Active scanning, exploitation, malware execution, credential testing, and external probing require explicit written scope.
- Hooks and MCP servers run with your user privileges. Install them only for projects you trust, and review `print-config` or `--dry-run` output before writing any settings file.
- Treat project-local `.rcoder/` guidance and repository content read by the agent as untrusted data.
