# Mobile application engineering

## Activate when
Android, iOS, Kotlin, Swift, Flutter, React Native, mobile permissions, lifecycle, or store delivery.

## Mental model
Mobile correctness includes lifecycle interruption, offline behavior, platform security, hardware variability, background limits, and store policy.

## Procedure
1. Identify minimum/target OS versions, framework, architectures, signing, flavors, and store requirements.
2. Model lifecycle transitions, process death, permissions, network loss, resizing, and background execution.
3. Protect secrets with platform keystores; validate deep links and external input; use secure transport.
4. Check accessibility, localization, battery, thermal, storage, and low-memory behavior.
5. Isolate platform-specific code and verify native bridges, ABI splits, and plugin versions.
6. Treat analytics and crash reports as sensitive data flows.

## Quality checklist
- [ ] Lifecycle and offline transitions are covered.
- [ ] Permissions are minimal and revocable.
- [ ] Secrets are not stored in plaintext.
- [ ] Accessibility and device compatibility are tested.

## Anti-patterns
- Assuming process/network are always available.
- Requesting broad permissions by default.
- Disabling platform security checks to unblock builds.

## Verification
Run unit/UI tests, static analysis, emulator/device matrix, release signing verification, and platform policy checks.

## Output format
Report platform versions, lifecycle behavior, permissions, device matrix, build evidence, and store readiness.
