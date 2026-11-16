# Embedded and firmware engineering

## Activate when
MCUs, RTOS, bootloaders, drivers, firmware updates, buses, sensors, or hardware-facing code.

## Mental model
Embedded software is constrained by electrical interfaces, timing, memory ceilings, boot/update state, fault recovery, and physical safety.

## Procedure
1. Identify MCU/SoC, silicon and board revisions, datasheet/errata, compiler, linker script, RTOS, and debug tools.
2. Map interrupts, DMA, shared buffers, cache coherency, memory regions, clocks, watchdogs, and power states.
3. Validate framing, timeouts, CRC/authentication, bounds, and recovery from partial transfers.
4. Design firmware updates and boot recovery for integrity, rollback, and power-loss safety.
5. Treat debug interfaces, boot modes, keys, and manufacturing provisioning as security boundaries.
6. Use hardware-in-loop tests and logic-analyzer traces for timing-sensitive claims.

## Quality checklist
- [ ] Datasheet/errata assumptions are documented.
- [ ] Interrupt and DMA ownership is race-safe.
- [ ] Boot/update survives power loss.
- [ ] Memory and timing budgets are measured.

## Anti-patterns
- Assuming peripheral timing from emulation alone.
- Disabling watchdog or secure boot to bypass faults.
- Unbounded dynamic allocation on constrained targets.

## Verification
Run static analysis, cross compilation, unit tests with fakes, hardware-in-loop tests, fault injection, and flash/rollback verification.

## Output format
Describe board/toolchain, memory/timing budgets, hardware evidence, update safety, and unverified conditions.
