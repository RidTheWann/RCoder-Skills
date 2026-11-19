# Installer security review — 2026-11-19

Scope: repository installers and launcher provisioning code in `scripts/install.sh`, `scripts/install.ps1`, `scripts/rcoder.mjs`, and `launcher/RCoder.ps1`, plus the package builder in `scripts/package`. This is a source review with local simulations; it is not a penetration test. No active scanning or exploitation was performed.

## Method

Targeted reads of the path-construction, extraction, backup, restore, PATH, and cleanup paths, corroborated by the existing installer simulations (`scripts/test-installers.sh`, `scripts/test-installers.ps1`, `scripts/test-node-installer.mjs`) and the repository's selected security checks in `scripts/validate-all`.

## Verified controls

| Area | Finding | Evidence |
|---|---|---|
| Path traversal | All three installers constrain the destination to the selected project/user base. Node `assertSafePath` rejects `..`, absolute, and out-of-scope relatives; PowerShell `Assert-Safe` uses a `$prefix` comparison and rejects reparse points; POSIX `check_links` requires the target to be under the base. | `scripts/rcoder.mjs:136`, `scripts/install.ps1:40`, `scripts/install.sh:38` |
| Symlink / reparse points | Node walks each segment with `lstatSync` and refuses links; PowerShell checks `FileAttributes::ReparsePoint` on each existing segment; POSIX checks `[ -L ]` per segment. Shell profiles that are symlinks are skipped before PATH edits. | `scripts/rcoder.mjs:142`, `scripts/install.ps1:47`, `scripts/install.sh:38`, `scripts/rcoder.mjs:298` |
| Archive extraction | The installers do not extract archives: they copy the canonical `skills/rcoder` directory into a staged destination. No `tar`/`Expand-Archive` untrusted-input path exists in the installer code. The distributed ZIPs are build artifacts with published SHA-256 sums. | `scripts/install.sh`, `scripts/install.ps1:77`, `dist/SHA256SUMS` |
| Backup / restore | Before replacing an existing install, the active folder is moved to a timestamped backup. Uninstall restores the newest `install-*` backup. PowerShell rolls back the saved install on error; Node uses staged application updates. | `scripts/install.ps1:62`, `scripts/install.ps1:78`, `scripts/rcoder.mjs:252` |
| Temporary cleanup | POSIX uses a stage directory with a `trap cleanup EXIT HUP INT TERM`; PowerShell removes the stage in a `finally`-style `catch` and restores the backup. | `scripts/install.sh:54`, `scripts/install.ps1:87` |
| Command injection | PATH registration constructs PowerShell and shell strings with explicit single-quote escaping (`psLiteral`, `shellQuote`, fish quoting). No unquoted interpolation of user-controlled paths into a shell command was found. No `iex`/`Invoke-Expression` occurs in the repository installer scripts. | `scripts/rcoder.mjs:270`, `scripts/rcoder.mjs:278`, `scripts/rcoder.mjs:288` |
| PATH modification scope | Windows writes only the User PATH via `[Environment]::SetEnvironmentVariable`, deduplicating case-insensitively. POSIX appends a marker-guarded line once per profile and supports fish. Failure to update PATH is warned, not silently ignored. | `scripts/rcoder.mjs:278`, `scripts/rcoder.mjs:288` |
| Idempotence | `Same-Tree` byte comparison (PowerShell) and equivalent Node/POSIX checks skip unchanged installs, preventing needless overwrite and duplicate backups. | `scripts/install.ps1:71`, `scripts/rcoder.mjs:182` |
| Download integrity | The repository installers perform no network download; the documented `irm ... | iex` and `npx github:` entry points fetch code through TLS/Git outside these files. Package artifacts are checksummed in `dist/SHA256SUMS`. | `scripts/package`, `dist/SHA256SUMS` |

## Residual risks / NOT VERIFIED

1. **POSIX case-pattern quoting.** The generated `case ":$PATH:" in *":<binRoot>:"*)` test embeds the unquoted `binRoot` in a pattern. A path containing `:` or shell glob characters could match incorrectly. No such path was observed in the tested fixtures. Minimum action: use a quoting-safe membership test (e.g., a small helper or `case` with escaped metacharacters) if arbitrary home-directory names must be supported.
2. **`irm | iex` bootstrap.** The user-facing one-liner executes remotely fetched PowerShell without a published checksum. This is inherent to the documented method, not a repository-script defect; verify the source URL over TLS and pin a released tag in security-sensitive deployments.
3. **Real-platform restore failure.** Backup/restore rollback is simulated; reparse-point and locked-file behavior on a live Windows profile was not executed here. Minimum action: run the matrix on a clean Windows 5.1 and 7 profile with an intentionally locked destination.
4. **PowerShell 5.1 locally.** Only PowerShell 7.6.10 is available in this environment; 5.1 is covered by hosted CI, not by local execution.
5. **ZIP extraction by external hosts.** RCoder does not extract its ZIPs; host-side import safety was not tested (no authenticated host UI available).

## Conclusion

No high-severity issue was found in the reviewed installer code. The traversal, symlink, staging, backup, cleanup, and command-quoting controls are present and exercised by the existing simulations. The residual items above are bounded and explicitly NOT VERIFIED where live-platform evidence is missing.
