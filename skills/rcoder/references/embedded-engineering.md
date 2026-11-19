# Embedded and firmware engineering

## Activate when
MCUs, RTOS, bootloaders, drivers, firmware updates, buses, sensors, or hardware-facing code. Use systems-programming for language-level memory/ABI rules and reverse-engineering for undocumented hardware behavior.

## Mission and expertise
Own hardware-interface, timing, memory-budget, boot/update, and safety correctness. Treat datasheets and errata as authoritative evidence and never infer peripheral timing from emulation alone.

## Mental model
Embedded software is constrained by electrical interfaces, timing, memory ceilings, boot/update state, fault recovery, and physical safety. Hardware evidence is required for timing and electrical claims; emulator results alone are insufficient.

## Prerequisites and reconnaissance
1. Identify MCU/SoC, silicon and board revisions, datasheet/errata, compiler, linker script, RTOS, and debug tools.
2. Determine memory regions, clock configuration, interrupt priorities, and boot flow from the actual project.
3. Identify how firmware is signed, delivered, and rolled back.
4. Check which hardware or hardware-in-loop setup is actually available before making timing claims.

## Procedure
1. Identify MCU/SoC, silicon and board revisions, datasheet/errata, compiler, linker script, RTOS, and debug tools.
2. Map interrupts, DMA, shared buffers, cache coherency, memory regions, clocks, watchdogs, and power states.
3. Validate framing, timeouts, CRC/authentication, bounds, and recovery from partial transfers.
4. Design firmware updates and boot recovery for integrity, rollback, and power-loss safety.
5. Treat debug interfaces, boot modes, keys, and manufacturing provisioning as security boundaries.
6. Use hardware-in-loop tests and logic-analyzer traces for timing-sensitive claims.

## Decision tree
- Shared buffer between interrupt and main context → declare volatile where appropriate and protect with correct synchronization; verify no torn access.
- Peripheral timing unknown → consult datasheet/errata and measure on hardware; do not guess.
- Protocol frame untrusted → validate bounds, length, CRC, and authentication before processing.
- Update interrupted by power loss → use redundant slots or a recovery bootloader with integrity checks.
- Debug interface enabled in release → treat as a security boundary and disable or protect it.
- Dynamic allocation on constrained target → prefer static allocation with measured worst-case bounds.
- Fault persists → use the watchdog deliberately and record the cause; do not disable it to hide the fault.

## Tool strategy
Use cross compilers, static analysis, link-map inspection, unit tests with hardware fakes, oscilloscope/logic-analyzer traces, and hardware-in-loop rigs. Verify toolchain versions and board revisions. Mark hardware-dependent claims NOT VERIFIED when the hardware is unavailable.

## Advanced techniques
- **Worst-case execution/budget analysis:** measure and bound interrupt latency and loop execution, not just averages.
- **Link-map audit:** verify memory placement, stack/heap margins, and section sizes against the target's limits.
- **Power-loss testing:** inject resets at each update stage and verify recovery.
- **Fault injection:** corrupt frames and storage deliberately to validate error handling.
- **Errata cross-check:** verify that known silicon issues are addressed for the exact board revision.

## Failure modes
- **Assuming peripheral timing from emulation alone** → hardware failures → measure on real hardware.
- **Disabling watchdog or secure boot to bypass faults** → unsafe product → fix the root cause.
- **Unbounded dynamic allocation** → fragmentation and exhaustion → bound or eliminate it.
- **Unvalidated protocol lengths** → memory corruption → bounds-check before use.
- **Unprotected debug/keys** → device compromise → secure provisioning and boot.

## Quality checklist
Datasheet/errata assumptions are documented; interrupt and DMA ownership is race-safe; boot/update survives power loss; memory and timing budgets are measured.

## Anti-patterns
Blocking in interrupt handlers; magic addresses without documentation; ignoring silicon errata; shipping debug credentials; treating a single board sample as representative.

## Verification
Run static analysis, cross compilation, unit tests with fakes, hardware-in-loop tests, fault injection, and flash/rollback verification. Record board revisions and tool versions; mark unavailable hardware tests NOT VERIFIED.

## Output format
Board/toolchain · memory/timing budgets · hardware evidence · update safety · unverified conditions.
