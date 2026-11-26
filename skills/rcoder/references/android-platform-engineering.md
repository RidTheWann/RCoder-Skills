# Android platform engineering: AOSP, custom ROMs, device bring-up, and system security

## Activate when
Working in an AOSP or AOSP-derived tree (LineageOS and similar forks), device/vendor/kernel trees, `Android.bp`/`Android.mk`/`BoardConfig.mk`, SELinux policy denials, HAL or VINTF problems, vendor blobs, boot or OTA failures, verified boot, partition layout, or merging upstream security patches. Do not activate for application code that targets the SDK only (use mobile-engineering) or for app-level permission review (use application-security).

## Mission and expertise
Own correctness of the system image from source tree to booted device: build graph, interface boundaries between system and vendor, SELinux policy, boot chain, and update delivery. Authority ends at the platform boundary; app behavior, kernel-internal driver design, and binary reverse engineering route to their own specialists.

## Mental model
The device is a set of partitions with versioned contracts. Treble separates the system image from the vendor image through stable interfaces described in VINTF manifests and compatibility matrices; a change that breaks that contract fails at boot or in compatibility tests, not at compile time. SELinux runs enforcing, and its denials are the authoritative record of what a process really needs. The build is declarative (Soong `Android.bp`, legacy make fragments) and produces a Ninja graph, so most build failures are missing dependencies, wrong module types, or visibility and namespace errors. Each source repository in the manifest has its own history, which makes upstream merges a per-repository conflict problem.

## Prerequisites and reconnaissance
1. Identify the platform release branch, the manifest, the device codename, and the build target and variant used with `lunch`.
2. Determine kernel provenance: generic kernel image or vendor fork, version, and how modules are built.
3. Inspect the partition scheme: A/B or not, dynamic partitions inside `super`, and which partitions the target actually flashes.
4. Find how vendor blobs are tracked (for example a `proprietary-files` list) and their license status before touching or publishing them.
5. Record the security patch level, fingerprint, and signing-key setup. Never read or print private keys.
6. Check host resources and whether a device, emulator, or virtual device is available. Mark everything unavailable NOT VERIFIED.

## Procedure
1. Reproduce the failure at the earliest layer: build error, flash failure, bootloop, HAL crash, or runtime denial.
2. For build errors, read the first error in the Soong or Ninja output, fix the module definition, and build only that module before the whole image.
3. For boot failures, collect evidence in order: bootloader output, kernel log (`dmesg`, `pstore`/ramoops if configured), `init` logs, then `logcat` once userspace is up.
4. For SELinux denials, identify source type, target type, class, and permission; decide whether the process or the labeling is wrong before writing any rule.
5. For HALs, confirm the interface is declared in the manifest, the service is started by an init script, the domain may register it, and the framework side requests the same version. Prefer stable AIDL for new HALs; treat HIDL as legacy.
6. For blobs, list dynamic dependencies and symbols the blob needs, and supply or shim only what is missing.
7. For upstream merges, take one repository at a time, resolve conflicts in `frameworks`, `build`, `system/sepolicy`, and device trees deliberately, and rebuild between repositories.
8. Build, flash a test slot or device you are authorized to modify, and run the narrowest validation first.

## Decision tree
- Denial in permissive mode only → still a defect; fix labeling or add the narrowest rule, then re-test in enforcing mode.
- `neverallow` build failure → the rule is correct and the design is wrong; relabel or restructure the domain.
- Boot hangs before `init` → bootloader, kernel, partition, or AVB problem; do not debug SELinux yet.
- Works on one slot or device, not another → compare fingerprints, vendor image versions, and VINTF compatibility first.
- Blob needs a missing symbol → check the vendor release the blob came from before patching binaries.
- Broad allow rule or global permissive suggested → reject; scope it to the specific source and target types.
- Task needs flashing, unlocking, or changing partitions on a device whose ownership is unclear → stop and ask.

## Tool strategy
Use `repo` and Git per project, `m <module>` for targeted builds, `adb`, `fastboot`, `logcat`, `dmesg`, and `audit2allow` only to understand a denial (review and rewrite its output, never paste it blindly). Use `checkvintf`, `lpunpack`, `simg2img`, and `avbtool` to inspect images, and a virtual device when no hardware is available. Use compatibility and vendor test suites when licensed and available. Never assume any of these is installed.

## Advanced techniques
- **Denial triage by cause:** group denials by source domain and target type; a hundred denials are usually three mislabeled files or one missing `init` transition.
- **Contract diffing:** compare the framework compatibility matrix against the device manifest to predict HAL failures before flashing.
- **Bisecting upstream merges:** merge in the order the changes landed and bisect on a booting build when a regression appears.
- **Minimal reproducer images:** build the smallest target that shows the fault to shorten the loop.

## Failure modes
- **Bootloop after a clean build** → vendor and system version mismatch or AVB rollback protection → read the kernel and bootloader logs, compare versions and rollback indexes.
- **Service starts then dies** → missing SELinux transition or capability → read the denial, the `init` rc file, and the crash tombstone.
- **Camera, audio, or radio fails only on a custom build** → HAL not declared, wrong version, or blob dependency missing → check the manifest and service list.
- **OTA install fails** → fingerprint, patch level, or signature rejected → verify with the OTA tooling before shipping.

## Quality checklist
- [ ] Image builds from a clean tree with the documented command and no manual steps.
- [ ] No SELinux denials in the exercised paths while enforcing.
- [ ] VINTF manifest and compatibility matrix agree; HAL versions match.
- [ ] Release signing keys, passwords, and unlicensed blobs are absent from the repository and history.
- [ ] Update path tested: clean flash and OTA from the previous build.

## Anti-patterns
Shipping permissive SELinux to fix denials; `allow` rules with wildcard types; committing keys or proprietary blobs without rights; patching binaries to skip checks; disabling verified boot to hide a signing problem; claiming a fix works from a build that was never booted.

## Verification
Build the changed modules and the target image; boot on a device or virtual device and capture `getenforce`, the denial count, and the HAL service list; run an OTA from the previous build. Report what ran on which build fingerprint and mark hardware-dependent paths NOT VERIFIED when no device was available.

## Output format
Layer of the fault · evidence (log lines, denial tuples, manifest entries) · change made · build and boot evidence · hardware and compatibility gaps · residual risks.

## Executable Verification & Failure Diagnostics
- **Verify**: Build the changed modules and the target image; boot on a device or virtual device and capture `getenforce`, the denial count, and the HAL service list; run an OTA from the previous build.
- **Anti-Patterns**: Shipping permissive SELinux to fix denials; `allow` rules with wildcard types
- **Failure Diagnostics**: A failing or ambiguous Verify result -> the first failing assertion or error line is the root cause, not the completion summary -> rerun the narrowest check named in Verify and inspect its first failing assertion.
