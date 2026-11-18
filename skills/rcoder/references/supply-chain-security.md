# Software supply-chain and dependency security

## Activate when
Dependencies, package managers, CI actions, plugins, model/tool downloads, release artifacts, SBOMs, or provenance. Do not activate for application logic bugs (use coding) or for a broad build failure (use build-toolchain-engineering, loading this module for dependency-specific risk).

## Mission and expertise
Treat registries, maintainers, build actions, transitive dependencies, artifacts, and update channels as trust boundaries. Own dependency-delta review, provenance and integrity verification, credential exposure analysis in builds, and compromised-dependency response planning.

## Mental model
Registries, maintainers, build actions, transitive dependencies, artifacts, and update channels are all trust boundaries. A lockfile pins versions; it does not prove trust. An advisory indicates possible exposure; exploitability depends on the code path and configuration actually used.

## Prerequisites and reconnaissance
1. Inventory direct/transitive dependencies, lockfiles, registries, CI actions, plugins, generated code, and downloaded binaries.
2. Determine who controls each registry or feed and whether namespace ownership can be confused.
3. Identify build credentials, signing keys, and network egress available to build jobs.
4. Confirm the project's update, exception, and patch policy before recommending changes.

## Procedure
1. Inventory direct/transitive dependencies, lockfiles, registries, CI actions, plugins, generated code, and downloaded binaries.
2. Check provenance, maintainer trust, signatures/checksums, ownership changes, typosquatting, and dependency confusion.
3. Pin dependencies using the existing lock strategy; review transitive changes and lifecycle scripts.
4. Generate/inspect SBOM and license inventory where appropriate; distinguish advisories from exploitability in context.
5. Protect build credentials, isolate build jobs, use least-privilege tokens, and produce traceable artifacts.
6. Define patch SLAs, exception owners/expiry, update cadence, rollback, and compromised-dependency response.

## Decision tree
- New dependency with no clear need → reject or replace with standard library.
- Package name resembles an internal package on a public registry → dependency-confusion risk; scope the registry explicitly.
- Version is unpinned or uses a moving tag → pin to a reviewed, immutable version.
- Lifecycle scripts run on install → review them before permitting the dependency.
- Advisory affects a dependency but the vulnerable code path is unused → Informational with evidence, not Confirmed exploitability.
- Advisory affects a reachable path → prioritize remediation and add a regression check.
- Build credential has write scope to a registry → reduce to least privilege and isolate the job.
- Provenance cannot be verified → Unverified Hypothesis; do not claim a clean supply chain.

## Tool strategy
Use lockfile diffing, dependency scanners, SBOM generators, checksum/signature verification, license inventories, and artifact inspectors. Verify each tool's own provenance. Prefer offline resolution from a reviewed cache where available. Never execute unreviewed install scripts on a developer host.

## Advanced techniques
- **Dependency-delta review:** inspect exactly what changed in a lockfile update, including transitive additions and lifecycle scripts.
- **Reachability-based triage:** map an advisory to the actual call path and configuration in this repository before rating impact.
- **Provenance attestation:** verify artifact origin through checksums, signatures, and build attestations where the project supports them.
- **Least-privilege builds:** separate read-only dependency fetch from publish credentials; avoid long-lived tokens.
- **Exception governance:** every accepted risk has an owner, rationale, expiry, and compensating control.
- **Compromised-dependency playbook:** define isolate, identify affected artifacts, rotate credentials, rebuild clean, and notify consumers.

## Failure modes
- **Blindly updating all dependencies to latest** → unreviewed changes → update intentionally with lockfile review.
- **Ignoring lifecycle/postinstall scripts** → code execution at install → review and pin before use.
- **Treating lockfiles as proof of trust** → false assurance → verify provenance separately.
- **Publishing artifacts with debug debris or secrets** → leakage → inspect artifact contents before release.
- **Overrating an unreachable advisory** → wasted effort → use reachability evidence and classify accordingly.

## Quality checklist
Dependency changes are intentional and reviewed; artifacts have traceable provenance; CI credentials are least-privileged; exceptions have owner, rationale, and expiry.

## Anti-patterns
`latest` tags in production builds; unverified curl-to-shell installers; shared publish credentials across jobs; ignoring license obligations; treating a clean SCA scan as proof of supply-chain safety.

## Verification
Run lockfile checks, SCA, secret scans, provenance/signature checks, license review, and reproducible builds. Record exact commands, versions, and results; mark unavailable checks NOT VERIFIED.

## Output format
Dependency delta · advisories with reachability context · provenance · licenses · remediation · exceptions · residual risk.
