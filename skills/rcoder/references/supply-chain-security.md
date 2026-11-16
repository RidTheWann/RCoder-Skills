# Software supply-chain and dependency security

## Activate when
Dependencies, package managers, CI actions, plugins, model/tool downloads, release artifacts, SBOMs, or provenance.

## Mental model
Registries, maintainers, build actions, transitive dependencies, artifacts, and update channels are all trust boundaries.

## Procedure
1. Inventory direct/transitive dependencies, lockfiles, registries, CI actions, plugins, generated code, and downloaded binaries.
2. Check provenance, maintainer trust, signatures/checksums, ownership changes, typosquatting, and dependency confusion.
3. Pin dependencies using the existing lock strategy; review transitive changes and lifecycle scripts.
4. Generate/inspect SBOM and license inventory where appropriate; distinguish advisories from exploitability in context.
5. Protect build credentials, isolate build jobs, use least-privilege tokens, and produce traceable artifacts.
6. Define patch SLAs, exception owners/expiry, update cadence, rollback, and compromised-dependency response.

## Quality checklist
- [ ] Dependency changes are intentional and reviewed.
- [ ] Artifacts have traceable provenance.
- [ ] CI credentials are least-privileged.
- [ ] Exceptions have owner, rationale, and expiry.

## Anti-patterns
- Blindly updating all dependencies to latest.
- Ignoring lifecycle/postinstall scripts.
- Treating lockfiles as proof of trust.

## Verification
Run lockfile checks, SCA, secret scans, provenance/signature checks, license review, and reproducible builds.

## Output format
Report dependency delta, advisories, exploitability context, provenance, licenses, remediation, and exceptions.
