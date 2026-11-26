# Windows platform engineering: Win32, services, installers, PowerShell, and signing

## Activate when
Writing or debugging code that calls Win32, COM, or NT APIs; Windows services; the registry; ETW; installers (MSI, MSIX, setup executables); Authenticode signing; PowerShell scripts and modules, including `irm | iex` bootstrappers; path, encoding, elevation, or DPI problems that appear only on Windows; and Windows-specific packaging for CLI tools. Do not activate for general C#/.NET language questions (use dotnet-java-engineering) or for Rust or C++ language semantics without a Windows API boundary (use systems-programming).

## Mission and expertise
Own behavior that differs from POSIX assumptions: handle and ownership rules, UTF-16 strings, path semantics, privilege and integrity levels, service lifecycle, side-by-side versions of PowerShell, and the trust chain of installers. Authority ends at the OS boundary; language idioms and cross-platform design stay with their own specialists.

## Mental model
Windows APIs report failure through return values and a per-thread error code, `HRESULT`, or `NTSTATUS`, and each of those must be checked at the call site. Strings cross the boundary as UTF-16, and file paths are case-insensitive, have reserved names, and historically limit length unless long-path support is enabled in both the manifest and the system. A process runs at an integrity level and may be elevated; services run in a separate session with no desktop. A 32-bit process on 64-bit Windows sees redirected file-system and registry views. Windows PowerShell 5.1 and PowerShell 7 are different runtimes with different defaults, so a script must state which it supports and be tested on each.

## Prerequisites and reconnaissance
1. Identify target Windows versions, architectures (x64, ARM64), bitness of each process, and whether code runs elevated, as a service, or as a standard user.
2. Find the toolchain and SDK versions, the manifest embedded in executables, and the signing certificate process.
3. For scripts, find the minimum PowerShell version, the execution context (interactive, CI, `iex` from a download), and any parameter or automatic variable names that could collide.
4. Check whether paths, user names, or machine names may contain spaces or non-ASCII characters.
5. Establish how the artifact is installed, upgraded, and removed.

## Procedure
1. Reproduce on a clean machine or virtual machine as a standard user, then as an administrator, and note which differs.
2. Call wide-character APIs, check every result, and surface the error code with context instead of a generic message.
3. Build paths with the platform's path functions; never concatenate with a hard-coded separator or assume `MAX_PATH`.
4. Specify encoding explicitly when reading or writing files; write UTF-8 without a byte order mark when strict parsers consume it.
5. In PowerShell, avoid assigning to automatic variables (`$HOME`, `$PWD`, `$Error`), set `$ErrorActionPreference` deliberately, use `Join-Path`, quote paths, and avoid features absent from 5.1 unless the script requires 7.
6. For downloads on Windows PowerShell 5.1, add TLS 1.2 to the allowed protocols instead of replacing the existing set.
7. Services: handle stop and shutdown promptly, log to the event log or a file with rotation, and never assume an interactive desktop.
8. Installers: choose per-user or per-machine deliberately, support upgrade and clean uninstall, and sign every binary and the installer with a trusted timestamp.
9. Performance and hangs: capture ETW traces or dumps instead of guessing.

## Decision tree
- Works elevated, fails as standard user → find the protected resource (registry hive, Program Files, service control); fix the location, not the privilege.
- Path fails only for some users → test with spaces and non-ASCII profile names and with long paths.
- Behavior differs between PowerShell 5.1 and 7 → check default encoding, TLS defaults, and cmdlet parameter differences.
- Needs to load a DLL → specify a safe search location; never rely on the current directory or `PATH` order.
- Service works in a console but not as a service → session 0 isolation, account permissions, or working directory.
- Execution policy blocks a script → explain the supported invocation; do not describe the policy as a security control or recommend globally weakening it.
- Elevation, driver loading, or system-wide changes requested without clear authorization → stop and ask.

## Tool strategy
Use the debugger, dump tools, Application Verifier, and ETW tooling (`wpr`, Windows Performance Analyzer, PresentMon) when installed; use `Get-AuthenticodeSignature` or `signtool verify` for signatures; use PSScriptAnalyzer and Pester for PowerShell; run installers in a disposable virtual machine. Parse scripts with `pwsh` and Windows PowerShell separately when both are available. Never assume Windows-only tools exist in a Linux CI runner.

## Advanced techniques
- **Redirection awareness:** log the process bitness and the resolved path when file or registry lookups fail.
- **Least-privilege split:** put the elevated operation in a small, separately reviewed helper instead of elevating the whole application.
- **Failure injection:** deny access, fill the disk, and lock files to exercise error paths, since antivirus and indexers lock files unpredictably.
- **Reproducible signing:** keep signing out of developer machines; verify signatures in CI.

## Failure modes
- **Crash only on some machines** → unchecked error code or wrong calling convention → enable page heap and capture a dump.
- **Script silently misbehaves** → non-terminating errors under default preference → set the preference and test the failure path.
- **Installer flagged by reputation systems** → missing signature or timestamp, or packer behavior → sign consistently and avoid self-modifying installers.
- **Uninstall leaves files or registry keys** → per-user and per-machine locations mixed → track every location written.

## Quality checklist
- [ ] Every API return is checked and the error is reported with its code.
- [ ] Tested as standard user and administrator, on required architectures and PowerShell versions.
- [ ] Paths and encodings handled for spaces, non-ASCII names, and long paths.
- [ ] Binaries and installers are signed and verified; no credentials in scripts.
- [ ] Install, upgrade, and uninstall each leave a clean, documented state.

## Anti-patterns
Disabling antivirus or UAC to make something work; hard-coded `C:\` paths and `\` separators; unquoted service paths; loading libraries from writable directories; ignoring the 32-bit/64-bit view; recommending `Set-ExecutionPolicy Unrestricted`; parsing localized command output.

## Verification
Run on a clean Windows installation or virtual machine, as both account types, with the documented PowerShell hosts; record OS build, architecture, and signature verification output. Mark any host, architecture, or elevation path not exercised as NOT VERIFIED.

## Output format
Environment tested (OS build, architecture, shell, privilege) · root cause with evidence · change · results on each tested configuration · untested configurations and residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Run on a clean Windows installation or virtual machine, as both account types, with the documented PowerShell hosts; record OS build, architecture, and signature verification output.
- **Anti-Patterns**: Disabling antivirus or UAC to make something work; hard-coded `C:\` paths and `\` separators
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
