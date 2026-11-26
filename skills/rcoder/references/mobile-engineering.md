# Mobile application engineering

## Activate when
Android, iOS, Kotlin, Swift, Flutter, React Native, mobile permissions, lifecycle, or store delivery. Use polyglot-ecosystems for Swift/Kotlin/Dart language-specific detail and application-security for control review.

## Mission and expertise
Own lifecycle interruption, offline behavior, platform security, hardware variability, background limits, and store-delivery correctness. Treat platform APIs, deep links, and bridges as trust boundaries.

## Mental model
Mobile correctness includes lifecycle interruption, offline behavior, platform security, hardware variability, background limits, and store policy. The process is ephemeral: any state assumed to persist must be persisted deliberately.

## Prerequisites and reconnaissance
1. Identify minimum/target OS versions, framework, architectures, signing, flavors, and store requirements.
2. Determine lifecycle patterns, navigation, background modes, and offline expectations from code and configuration.
3. Identify permissions actually requested and why, plus secure storage and transport mechanisms.
4. Check device/emulator availability and release signing configuration.

## Procedure
1. Identify minimum/target OS versions, framework, architectures, signing, flavors, and store requirements.
2. Model lifecycle transitions, process death, permissions, network loss, resizing, and background execution.
3. Protect secrets with platform keystores; validate deep links and external input; use secure transport.
4. Check accessibility, localization, battery, thermal, storage, and low-memory behavior.
5. Isolate platform-specific code and verify native bridges, ABI splits, and plugin versions.
6. Treat analytics and crash reports as sensitive data flows.

## Decision tree
- State must survive process death → persist it deliberately and restore it in the lifecycle hook.
- Background work needed → use platform-supported mechanisms with explicit limits; do not assume execution.
- Permission needed → request minimally, explain purpose, and handle denial and revocation.
- Deep link accepted → validate scheme, host, and parameters before acting.
- Native bridge → validate message schema, ownership, and error propagation on both sides.
- Offline support → define conflict resolution and idempotent synchronization.
- Release blocked by signing or policy → fix configuration explicitly; do not disable checks.

## Tool strategy
Use unit/UI tests, static analysis, emulators/devices, release signing verification, and platform policy checks. Verify SDK/OS versions from configuration and tool output. Use synthetic accounts and data for integration paths.

## Advanced techniques
- **Lifecycle matrix:** test background/foreground, rotation, process death, and permission change paths.
- **Offline-first invariants:** define local write state, sync ordering, and conflict resolution explicitly.
- **Secure storage:** use platform keystores, avoid plaintext secrets, and verify token rotation/revocation.
- **Bridge contracts:** schema-validate all cross-language messages and bound payload sizes.
- **Device matrix:** test low-end and high-end profiles for memory, thermal, and performance behavior.

## Failure modes
- **Assuming process/network are always available** → data loss → design for interruption and offline.
- **Broad permissions by default** → privacy and store rejection → request minimally.
- **Disabling platform security checks** → vulnerable release → fix configuration instead.
- **Unvalidated deep links** → unauthorized actions → validate inputs.
- **Analytics carrying personal data** → privacy breach → classify and minimize telemetry.

## Quality checklist
Lifecycle and offline transitions are covered; permissions are minimal and revocable; secrets are not stored in plaintext; accessibility and device compatibility are tested.

## Anti-patterns
Storing tokens in plain preferences; performing network calls on the main thread; unchecked plugin upgrades; ignoring low-memory warnings; treating emulator tests as device coverage.

## Verification
Run unit/UI tests, static analysis, emulator/device matrix, release signing verification, and platform policy checks. Record OS versions and devices tested; mark unavailable device categories NOT VERIFIED.

## Output format
Platform versions · lifecycle behavior · permissions · device matrix · build evidence · store readiness.

## Executable Verification & Failure Diagnostics
- **Verify**: Run unit/UI tests, static analysis, emulator/device matrix, release signing verification, and platform policy checks.
- **Anti-Patterns**: Storing tokens in plain preferences; performing network calls on the main thread
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
