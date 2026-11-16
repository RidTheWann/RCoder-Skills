# RCoder architecture

## Product boundary
RCoder is an instruction package, not a runtime, model, sandbox, or permission system. It coordinates only capabilities exposed by the host agent.

## Layers
1. **Discovery:** `skills/rcoder/SKILL.md` frontmatter supplies compact activation metadata.
2. **Core protocol:** instruction precedence and Intake → Recon → Plan → Implement → Verify → Report.
3. **Experts:** focused `references/*.md` with decision procedures, checks, anti-patterns, verification, and output format; links are one level deep.
4. **Deterministic helper:** `scripts/detect_stack.py` is read-only and has no network calls.
5. **Extension:** reusable templates under `assets/templates/`; project-specific rules under `.rcoder/`.
6. **Adapters/distribution:** AGENTS/CLAUDE bootstrap files, Claude manifest, portable root Agent Plugins manifest plus Codex compatibility fallback, target installers, ZIP packages.

## Runtime flow
```text
Request -> task boundary and instruction precedence -> repo recon -> relevant modules
 -> proportional plan -> smallest correct implementation -> observable verification
 -> adversarial diff review -> evidence-based report
```

## Invariants
- User and project instructions outrank RCoder defaults.
- No model/vendor lock-in in core metadata or workflow.
- Stack detector is read-only; installers do not fetch remote code.
- Installation is scoped, reversible, and backed up.
- Static validation is never described as proof of live behavior.

## Distribution and extensions
`skills/rcoder/` is canonical. Installers copy it to native discovery paths. Plugin manifests reference the same skill folder. Add a specialist with `expert-module-template.md`, update router signal and evals, and keep project-only overrides in `.rcoder/`.
