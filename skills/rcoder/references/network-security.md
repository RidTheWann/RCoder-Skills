# Network and protocol security

## Activate when
Network services, TLS, DNS, proxies, firewalls, VPNs, sockets, packet captures, or network exposure reviews. Use network modules in distributed-systems for delivery guarantees and security for authorization boundaries.

## Mission and expertise
Own network-exposure, TLS trust, segmentation, parser-safety, and active-testing-boundary correctness. Treat hostile peers and untrusted intermediate data as normal conditions.

## Mental model
A network design must account for identity, segmentation, parser safety, confidentiality, integrity, availability, and hostile peers. A reachable port is not automatically a vulnerability; reachability plus a reachable weakness plus impact is.

## Prerequisites and reconnaissance
1. Define authorized scope, assets, trust zones, interfaces, protocol versions, and expected traffic.
2. Determine whether active testing is permitted and under what rate limits and exclusions.
3. Identify certificate authorities, hostname validation, and renewal processes from configuration.
4. Confirm that packet-capture and analysis tools are permitted and available.

## Procedure
1. Define authorized scope, assets, trust zones, interfaces, protocol versions, and expected traffic.
2. Review TLS validation, certificate lifecycle, hostname checks, mutual authentication, cipher policy, and downgrade resistance.
3. Validate DNS resolution, rebinding exposure, proxy behavior, redirects, egress restrictions, and metadata endpoints.
4. Check protocol parsers for bounds, state-machine confusion, fragmentation, replay, and resource exhaustion.
5. Review firewall/security-group rules, management-plane exposure, IPv6 parity, logging, and rate controls.
6. Keep active tests inside written scope and rate limits; use passive evidence or isolated labs when authorization is unclear.

## Decision tree
- Active scan requested without scope → passive configuration review only and label active tests NOT VERIFIED.
- Certificate validation failing → fix the trust chain or hostname, never disable verification.
- Parser accepts unbounded lengths → bound input before allocation and fuzz the state machine.
- Management plane reachable broadly → restrict by identity and network, and add audit.
- IPv4 rules exist but IPv6 does not → implement equivalent controls and test both.
- Egress unrestricted → define an allowlist where feasible, especially for metadata endpoints.
- Traffic anomaly observed → correlate with logs and timeline before concluding compromise.

## Tool strategy
Use configuration review, protocol tests, authorized packet captures, certificate checks, parser fuzzing, and scoped non-disruptive validation. Verify tool versions and capture locations. Redact sensitive payloads from captures and reports.

## Advanced techniques
- **Exposure matrix:** list each listening service, its authentication, its authorized consumers, and its network zone.
- **Certificate validation tests:** cover expired, wrong-hostname, untrusted-CA, and downgrade cases.
- **Parser state testing:** drive unexpected sequences and fragmentation with synthetic inputs.
- **Egress validation:** verify that workloads cannot reach metadata or unintended external endpoints.
- **Dual-stack parity:** compare IPv4 and IPv6 controls and logging.

## Failure modes
- **Scanning third-party/public IPs without written authorization** → policy and legal harm → require scope.
- **Disabling certificate validation to fix connectivity** → MITM exposure → repair trust configuration.
- **Assuming IPv4 controls also cover IPv6** → exposed services → implement and test both.
- **Unbounded parser input** → resource exhaustion → bound and fuzz.
- **Capturing sensitive payloads** → privacy harm → redact at collection.

## Quality checklist
Scope and permitted methods are explicit; TLS verifies peer identity; network zones and egress are least-privileged; protocol parsing is bounded and fuzzable.

## Anti-patterns
Default-allow firewalls; plaintext management protocols; shared credentials across hosts; treating a clean port scan as proof of security; capturing full payloads containing personal data.

## Verification
Use configuration review, protocol tests, authorized packet captures, certificate tests, and scoped non-disruptive validation. Record exact scope and mark out-of-scope tests NOT VERIFIED.

## Output format
Topology · scope · exposure · protocol controls · evidence · untested paths.
