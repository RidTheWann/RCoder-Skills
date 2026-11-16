# S06 — Security review

## Fixture
An authenticated upload endpoint accepts a client-supplied path and optional URL. The service stores files and fetches URLs to import remote content.

## Task
Threat-model the boundary, trace inputs to filesystem/network sinks, inspect authorization and sensitive logging, rank findings, and propose mitigations with negative tests.

## Required evidence
- Assets, actors, entry points, trust boundaries and attacker goals.
- Path traversal, SSRF, input bounds, authorization and redirect handling assessed.
- Findings include trigger, impact, severity and source location/evidence.
- Mitigation and test for the actual trust boundary.
