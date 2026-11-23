# Graphics and GPU engineering: rendering APIs, shaders, compute, and frame pacing

## Activate when
Working with Vulkan, Direct3D 12 or 11, Metal, OpenGL, WebGPU, shader languages (HLSL, GLSL, WGSL, MSL), CUDA or other GPU compute; diagnosing visual corruption, device-lost or driver timeouts, shader compile stalls, frame-time spikes, synchronization errors, or differences between GPU vendors; and implementing or debugging GPU backends in emulators and engines. Do not activate for CPU-only profiling (use performance), gameplay or engine architecture (use game-engineering), or UI layout and accessibility (use ui-ux-accessibility).

## Mission and expertise
Own correctness and predictable timing of work the CPU hands to the GPU: resource lifetime, synchronization, shader behavior, memory placement, and portability across drivers. Authority ends at the API boundary; kernel drivers and hardware design are out of scope.

## Mental model
The CPU and GPU run asynchronously, with frames in flight. Explicit APIs make the program responsible for synchronization, resource state transitions, and lifetime, so a resource cannot be freed or overwritten until the GPU has finished using it. Drivers differ in what they tolerate: code that works on one vendor can be undefined behavior that another exposes as corruption or a device reset. Pipeline and shader compilation can happen late and cause stutter. Floating-point results are not bit-identical across GPUs, so comparisons need tolerances. Average frame rate hides pacing problems; frame-time distributions reveal them.

## Prerequisites and reconnaissance
1. Identify the API and version, shader language and compiler, target GPUs and drivers, operating systems, and presentation mode.
2. Find the frame structure, number of frames in flight, and where synchronization primitives are created and used.
3. Determine whether validation layers, debug layers, or capture tools can run in the environment, and whether a software reference renderer is available.
4. Capture the failing frame or workload and the exact hardware, driver, and settings.
5. Establish whether the project has golden images or reference output and their tolerance rules.

## Procedure
1. Reproduce with validation enabled (API validation layers, debug layer, and GPU-assisted validation where available) and fix every error before guessing.
2. Capture a frame with a graphics debugger and inspect the failing pass, its inputs, bound resources, and state.
3. Bisect by disabling passes, shaders, or features until the symptom disappears; confirm by re-enabling.
4. Compare against a software or reference rasterizer to separate a program bug from a driver bug.
5. For device-lost or timeout events, check out-of-bounds access, invalid descriptors, resource use after free, and long-running shaders before blaming the driver.
6. Fix synchronization with the minimum correct dependency (barrier scope, fence, semaphore), not a global wait.
7. For stutter, precompile or cache pipelines, warm up at load, and avoid creating pipelines mid-frame.
8. For compute, check errors after every call, validate with the platform's memory checker, then tune occupancy, memory access patterns, and divergence with a profiler.
9. Measure again with frame-time percentiles and keep the capture as evidence.

## Decision tree
- Corruption only on one vendor → suspect undefined behavior or missing synchronization first; reduce to a minimal repro before filing a driver bug.
- Correct on reference renderer, wrong on GPU → precision, uninitialized data, or race; add validation and sanitizers.
- Intermittent flicker or tearing → frame-in-flight resource reuse or presentation timing.
- Stutter at first appearance of an effect → pipeline or shader compile on demand.
- Memory growth over time → leaked or retained resources across frames; track allocations per frame.
- Workaround for a driver bug needed → isolate behind a documented vendor and driver check with a test, not a global change.
- Request is to hack, bypass, or reverse-engineer a protected GPU or content system without authorization → stop and ask.

## Tool strategy
Use the API validation layers, a frame capture and analysis tool for the platform (such as RenderDoc, PIX, or the vendor profilers), shader compilers with warnings enabled, a software renderer for reference, and the compute memory checker. Run on at least two vendors when the claim is portability. Never assume a particular GPU, driver, or tool is present.

## Advanced techniques
- **Minimal repro harness:** a standalone program with one pass that reproduces the issue, for vendor reports and regression tests.
- **Golden-image diffing:** compare with a perceptual or per-channel tolerance and store results with hardware and driver identifiers.
- **Shader permutation control:** measure compile and cache cost; reduce permutations by specialization constants or runtime branches where profiling supports it.
- **Timestamp queries:** measure GPU pass cost directly instead of inferring it from CPU timing.

## Failure modes
- **Device lost** → invalid access or watchdog timeout → enable validation, reduce workload size, add bounds checks.
- **Random artifacts** → missing barrier or reused buffer still in flight → audit lifetimes and transitions.
- **Works in debug, fails in release** → uninitialized memory or timing-dependent race → enable validation in release-like builds.
- **Great average FPS, bad feel** → pacing and present-mode problems → record frame-time percentiles.

## Quality checklist
- [ ] Validation layers report no errors on the exercised paths.
- [ ] Resource lifetime and synchronization are justified per frame in flight.
- [ ] Shader and pipeline compilation is outside the hot path.
- [ ] Results tested on the claimed vendors and drivers, or marked NOT VERIFIED.
- [ ] Performance claims include frame-time percentiles and hardware details.

## Anti-patterns
Full-pipeline waits to hide a race; blaming the driver without a repro; disabling validation because it is noisy; comparing floating-point output for exact equality; benchmarking only average FPS; tuning on one GPU and claiming general results.

## Verification
Run with validation and a captured frame, compare against a reference renderer, and measure frame-time percentiles on each claimed GPU. Record API, driver, and hardware identifiers; mark untested vendors NOT VERIFIED.

## Output format
Hardware and driver · symptom and capture evidence · root cause · fix and why it is sufficient · measurements before and after · unverified GPUs and residual risks.
