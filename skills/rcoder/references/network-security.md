# Network and protocol security

## Activate when
Network services, TLS, DNS, proxies, firewalls, VPNs, sockets, packet captures, or network exposure reviews.

## Mental model
A network design must account for identity, segmentation, parser safety, confidentiality, integrity, availability, and hostile peers.

## Procedure
1. Define authorized scope, assets, trust zones, interfaces, protocol versions, and expected traffic.
2. Review TLS validation, certificate lifecycle, hostname checks, mutual authentication, cipher policy, and downgrade resistance.
3. Validate DNS resolution, rebinding exposure, proxy behavior, redirects, egress restrictions, and metadata endpoints.
4. Check protocol parsers for bounds, state-machine confusion, fragmentation, replay, and resource exhaustion.
5. Review firewall/security-group rules, management-plane exposure, IPv6 parity, logging, and rate controls.
6. Keep active tests inside written scope and rate limits; use passive evidence or isolated labs when authorization is unclear.

## Quality checklist
- [ ] Scope and permitted methods are explicit.
- [ ] TLS verifies peer identity.
- [ ] Network zones and egress are least-privileged.
- [ ] Protocol parsing is bounded and fuzzable.

## Anti-patterns
- Scanning third-party/public IPs without written authorization.
- Disabling certificate validation to fix connectivity.
- Assuming IPv4 controls also cover IPv6.

## Verification
Use configuration review, protocol tests, authorized packet captures, certificate tests, and scoped non-disruptive validation.

## Output format
Describe topology, scope, exposure, protocol controls, evidence, and untested paths.
