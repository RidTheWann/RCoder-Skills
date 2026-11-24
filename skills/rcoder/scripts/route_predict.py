#!/usr/bin/env python3
"""Deterministic specialist-routing assistant (read-only, standard library only).

This helper does not decide the routing for a model; it proposes a small candidate
set with per-module evidence and an ordinal confidence, applies the cross-domain
composition rules documented in ``references/specialist-routing.md``, and refuses to
guess when the request carries no engineering signal. A model may override the
proposal with a stated reason.

Rules are derived from the product specification (the router tables in ``SKILL.md``
and the composition rules in ``specialist-routing.md``), not learned from the
evaluation prompts. Evaluation against ``evals/`` is a held-out check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCES = SKILL_DIR / "references"

HELPERS = {"verification", "rsaver", "rsaver-gate", "rsaver-anchor", "rsaver-crosscheck",
           "token-efficiency", "model-adaptation", "rscan"}
SECURITY_FAMILY = {
    "threat-modeling", "secure-code-review", "application-security", "penetration-testing",
    "cloud-container-security", "network-security", "identity-crypto-secrets",
    "cryptography-engineering", "supply-chain-security", "vulnerability-research",
    "incident-response-forensics", "malware-analysis", "binary-exploitation-defense",
    "smart-contract-security", "llm-agent-security",
}
SYSTEMS_LANGS = {"systems-programming"}

# --- signals: (regex, [modules], evidence label). Ordered by specificity. -------
# Patterns are matched case-insensitively against the request text. Only
# high-precision, product-documented triggers are listed; a partial match is not a
# routing decision, it is a candidate with visible evidence.
# Indonesian terms are included for common engineering actions because multilingual
# activation is part of the RCoder contract; identifiers are kept verbatim.

SIGNALS: list[tuple[str, list[str], str]] = [
    # Out-of-scope guard first: non-engineering deliverables.
    (r"\b(poem|haiku|limerick|wedding invitation|birthday invitation|logo|poster|"
     r"itinerary|travel (?:plan|guide)|holiday|restaurant recommendation|"
     r"weather forecast|horoscope|headline|news article|recipe|menu translation|"
     r"pythagorean theorem|(?:daftar|list )?belanja|itinerary wisata|kuliner lokal)\b",
     [], "out-of-scope: non-engineering deliverable"),
    (r"\btranslate this\b(?!\s+.{0,40}\b(?:code|prompt|regex|json|schema|error|stack))",
     [], "out-of-scope: language translation without a technical artifact"),

    # Indonesian equivalents of high-precision engineering signals.
    (r"\b(regressi|kesalahan|kegagalan|gagal|perbaiki|memperbaiki|mendiagnosis|"
     r"menganalisis|menginvestigasi)\b", ["debugging"], "Indonesian: debugging signal"),
    (r"\b(pengujian|tes|test suite|pengujian regression|menambahkan tes|"
     r"tes deterministik)\b", ["testing-qa"], "Indonesian: testing signal"),
    (r"\b(mengoptimalkan|optimasi|latensi|bottleneck|penggunaan token|"
     r"biaya konteks)\b", ["performance"], "Indonesian: performance/token signal"),
    (r"\b(konfigurasi|mengonfigurasi|plugin|marketplace|extension|"
     r"agent skill|komponen plugin)\b", ["agent-extensions-engineering"],
     "Indonesian: host extension signal"),

    # Security (base added by composition). Specific named areas first.
    (r"\b(solidity|reentrancy|smart contract|access-control.{0,20}vault|"
     r"accounting invariant)", ["smart-contract-security"], "smart-contract security"),
    (r"\b(prompt injection|tool poison|agent permission|untrusted tool output|"
     r"agentic .{0,20}(?:security|permission))", ["llm-agent-security"], "LLM/agent security"),
    (r"\b(malware|suspicious (?:pe|elf|binary|file)|defensive indicator|"
     r"isolated lab|triage a suspicious)", ["malware-analysis"], "defensive malware triage"),
    (r"\b(forensic|chain[- ]of[- ]custody|incident (?:timeline|response)|"
     r"acquisition note|evidence (?:timeline|hash))", ["incident-response-forensics"],
     "incident response / forensics"),
    (r"\b(penetration test|pentest|authorized .{0,25}(?:test|assessment|scope)|"
     r"written scope of work)", ["penetration-testing"], "authorized penetration testing"),
    (r"\b(terraform|kubernetes|k8s|helm chart|iam permission|networkpolicy|"
     r"container escape|privilege escalation.{0,25}container)", ["cloud-container-security"],
     "cloud/container/infrastructure security"),
    (r"\b(supply chain|dependency confusion|typosquat|sbom|provenance of (?:a )?package)",
     ["supply-chain-security"], "software supply-chain security"),
    (r"\b(ssrf|path traversal|sql injection|csrf|xxe|insecure deserialization|"
     r"upload endpoint|injection vulnerability)", ["application-security"], "application security"),
    (r"\b(threat model|trust boundary|attack surface|adversary|"
     r"modeling the threat)", ["threat-modeling"], "threat modeling"),
    (r"\b(keamanan|security (?:assessment|review|audit)|audit keamanan|"
     r"klasifikasi risiko|risiko keamanan)\b", ["secure-code-review"],
     "Indonesian/EN: security assessment signal"),
    (r"\b(secret|credential|api key|key rotation|token rotation|jwt|oauth|"
     r"key management|hsm)", ["identity-crypto-secrets"], "identity / crypto / secrets"),
    (r"\b(audit .{0,30}(?:endpoint|code|module|pull request|diff)|secure code review|"
     r"review .{0,25}for (?:security|vulnerabilit))", ["secure-code-review"], "secure code review"),
    (r"\b(tls|certificate|handshake|aes|rsa|hmac|encrypt(?:ion)? scheme|cipher suite)",
     ["cryptography-engineering"], "applied cryptography"),

    # Reverse engineering.
    (r"\b(undocumented (?:file|binary|save-file) format|infer .{0,20}format|"
     r"binary (?:packet|wire) format|file-format|reconstruct the .{0,20}format)",
     ["reverse-engineering-file-formats"], "binary file-format analysis"),
    (r"\b(ghidra|disassembl|decompil|reverse[- ]engineer|recover(?:ed)? function|"
     r"firmware image|crackme)", ["reverse-engineering"], "software reverse engineering"),

    # Agent/MCP platform.
    (r"\b(streamable http|stdio mcp|mcp (?:server|transport|client|endpoint)|"
     r"json-rpc|tools/list|opaque cursor|structuredcontent)", ["mcp-transport-engineering"],
     "MCP protocol/transport"),
    (r"\b(agent skill|slash command|marketplace manifest|plugin manifest|"
     r"plugin hooks|subagent|skill authoring)", ["agent-extensions-engineering"],
     "Agent Skills / host extensions"),

    # Observability / IaC / platform.
    (r"\b(?:slo|sli|prometheus|grafana|alert(?:ing)? rule|promql|on-call|"
     r"pager|dashboard .{0,20}metric)\b", ["observability-sre"], "observability / SRE"),
    (r"\b(terraform plan|opentofu|pulumi|cloudformation|ansible|helm|"
     r"iac|state drift|rollout .{0,20}pods)", ["iac-platform-engineering"],
     "infrastructure as code"),
    (r"\b(android|aosp|lineageos|custom rom|selinux (?:denial|policy)|device tree|"
     r"hal interface)", ["android-platform-engineering"], "Android platform"),
    (r"\b(powershell 5\.1|windows service|win32|com object|msi installer|"
     r"authenticode|etw)", ["windows-platform-engineering"], "Windows platform"),
    (r"\b(vulkan|d3d|webgpu|metal api|shader|compute pipeline|device[- ]lost|"
     r"frame pacing)", ["graphics-gpu-engineering"], "graphics / GPU"),
    (r"\b(embedded|firmware|rtos|cortex-m|microcontroller|watchdog reset|bare[- ]metal)",
     ["embedded-engineering"], "embedded / firmware"),
    (r"\b(game engine|render thread|frame-time spike|emulator|recompiler|"
     r"deterministic tick)", ["game-engineering"], "game / real-time engine"),

    # Data, API, backend, distributed.
    (r"\b(postgres|mysql|sqlite|migration|schema change|query plan|index .{0,15}scan|"
     r"zero-downtime schema)", ["database-engineering"], "database/schema"),
    (r"\b(grpc|rest api|openapi|graphql|wire format|protobuf|api contract|"
     r"deadlineexceeded|idempotency key)", ["api-protocol-engineering"], "API/wire protocol"),
    (r"\b(serialization|persistence contract|backward-compatible .{0,20}(?:payload|format)|"
     r"refresh[- ]token rotation|cache invalidation)", ["data-api"], "data/API contract"),
    (r"\b(microservice|service boundary|sharded|distributed consensus|partition|"
     r"replication lag|cap theorem)", ["distributed-systems-engineering"], "distributed systems"),
    (r"\b(endpoint implementation|service layer|controller|middleware|"
     r"request handler|backend service)", ["backend-api-engineering"], "backend/service"),

    # Frontend / mobile / UX.
    (r"\b(ssr|hydration mismatch|service worker|browser storage|"
     r"next\.js|edge runtime|web vitals)", ["web-platform-engineering"], "web platform/runtime"),
    (r"\b(react|vue|svelte|css|responsive layout|component state|"
     r"settings screen|frontend build)", ["frontend-engineering"], "frontend/browser"),
    (r"\b(accessibility|wcag|keyboard navigation|screen reader|aria|"
     r"focus (?:trap|order)|contrast ratio)", ["ui-ux-accessibility"],
     "UI/UX accessibility"),
    (r"\b(android app|ios app|react native|flutter|dart|mobile screen|"
     r"lifecycle .{0,15}mobile)", ["mobile-engineering"], "mobile"),
    (r"\b(swift|kotlin|scala|elixir|haskell|php|ruby|rails|rails app)",
     ["polyglot-ecosystems"], "specialized language ecosystem"),

    # ML / performance / architecture / docs / refactor.
    (r"\b(machine learning|ml pipeline|training pipeline|data leakage|"
     r"model (?:drift|metric)|inference (?:latency|server)|embedding)", ["ml-ai-engineering"],
     "ML/AI system"),
    (r"\b(latency|throughput|cold[- ]start|frame time|hot loop|profiling|"
     r"memory (?:leak|pressure)|cpu profile|benchmark)", ["performance"], "performance"),
    (r"\b(architecture|system design|adr|tradeoff|module boundary|"
     r"compare .{0,20}architectures)", ["architecture"], "architecture/design"),
    (r"\b(readme|api docs|adr|runbook|changelog|documentation|docstring)",
     ["documentation"], "documentation"),
    (r"\b(refactor|without changing .{0,25}behavior|behavior-preserving|"
     r"clean up .{0,20}module|extract (?:a )?(?:module|function|class))", ["review-refactor"],
     "review/refactor"),
    (r"\b(token usage|context (?:cost|window|budget)|agent context|"
     r"prune .{0,15}output|context compaction)", ["token-efficiency"], "token/context efficiency"),
    (r"\b(verify .{0,25}against|independent (?:check|verification)|"
     r"reference implementation|claim .{0,20}evidence)", ["verification"],
     "verification/evidence"),

    # Build / CI / DevOps (product router: devops-ci-cd default, toolchain when internals).
    (r"\b(github actions|gitlab ci|ci workflow|ci pipeline|build (?:and )?test (?:and|&) release|"
     r"release workflow|semantic-release|changelog (?:automation|generation))\b",
     ["devops-ci-cd"], "CI/CD workflow"),
    (r"\b(cmake|makefile|meson|ninja|linker|compiler (?:flag|error|internals)|"
     r"toolchain|build system|bazel|package build)\b", ["build-toolchain-engineering"],
     "build/toolchain"),

    # Debugging (broad) and tests (broad) last: they are frequently supporting.
    (r"\b(data race|deadlock|intermittent|flaky|non-?deterministic|"
     r"race condition|heisenbug|watchdog reset|restart in a loop|bootloop)",
     ["debugging-advanced"], "advanced debugging"),
    (r"\b(regression|root cause|reproduce .{0,20}(?:bug|failure)|"
     r"failing test|debug|wrong output|traceback|hydration mismatch)",
     ["debugging"], "debugging"),
    # Harness mechanics -> test-engineering; strategy/acceptance -> testing-qa.
    (r"\b(fuzz|property[- ]based|contract test|test harness|mock|fixture|"
     r"deterministic .{0,15}tests|foundry|regression tests for)\b",
     ["test-engineering"], "test harness engineering"),
    (r"\b(integration test|unit test|test plan|test suite|coverage|"
     r"acceptance criteria|regression test)\b", ["testing-qa"], "testing/QA"),
    (r"\b(service|endpoint|request handler|checkout api|backend|"
     r"on-call team|pages the on-call)\b", ["backend-api-engineering"], "backend service/API"),
]

# Language/runtime detection -> the language specialist (product router table).
LANGUAGE_SIGNALS: list[tuple[str, list[str], str]] = [
    (r"\brust\b|\bcargo\b", ["systems-programming"], "language: Rust"),
    (r"\bc\+\+|\bcpp\b|\bcmake\b|\bc\+\+20\b", ["systems-programming"], "language: C/C++"),
    (r"\bgo\b(?!\s*(?:to|al))|\bgolang\b|\bgoroutine", ["go-engineering"], "language: Go"),
    (r"\bjava\b|\bspring\b|\bjvm\b|\bkotlin\b(?!.{0,10}android)", ["dotnet-java-engineering"],
     "language: Java/JVM"),
    (r"\.net\b|\bc#\b|\basp\.net\b|\bentity framework\b", ["dotnet-java-engineering"],
     "language: .NET/C#"),
    (r"\bpython\b|\bfastapi\b|\bdjango\b|\bflask\b|\bpandas\b", ["python-engineering"],
     "language: Python"),
    (r"\btypescript\b|\bjavascript\b|\bnode\.?js\b|\bnpm\b|\bpnpm\b",
     ["javascript-typescript"], "language: JS/TS/Node"),
]

# Composition rules from specialist-routing.md: a narrow module implies a base.
COMPOSITION: list[tuple[str, set[str], str]] = [
    ("security base", SECURITY_FAMILY, "security"),
    ("systems base", SYSTEMS_LANGS, "systems-programming"),
]

MAX_PROPOSED = 4


def reference_names() -> list[str]:
    return sorted(path.stem for path in REFERENCES.glob("*.md"))


def known(name: str, valid: set[str]) -> bool:
    return name in valid


def match_signals(text: str, signals) -> list[tuple[str, str]]:
    """Return (module, evidence) pairs for every signal that fires, in order."""
    fired: list[tuple[str, str]] = []
    for pattern, modules, label in signals:
        if re.search(pattern, text, re.IGNORECASE):
            for module in modules:
                fired.append((module, label))
    return fired


def propose(text: str, valid: set[str]) -> dict:
    out_of_scope = False
    scope_evidence: list[str] = []
    hits = match_signals(text, SIGNALS)
    kept: list[tuple[str, str]] = []
    for module, label in hits:
        if not module:
            out_of_scope = True
            scope_evidence.append(label)
            continue
        if known(module, valid):
            kept.append((module, label))
    lang_hits = match_signals(text, LANGUAGE_SIGNALS)
    kept.extend((m, l) for m, l in lang_hits if known(m, valid))

    # a11y and polyglot as platform-composition add-ons.
    if re.search(r"\b(keyboard|screen reader|wcag|accessibility|aria|"
                 r"focus (?:trap|order)|contrast ratio)\b", text, re.I) \
            and re.search(r"\b(react|android|ios|flutter|screen|app|browser|ui)\b", text, re.I):
        if known("ui-ux-accessibility", valid):
            kept.append(("ui-ux-accessibility", "composition: UI has accessibility requirement"))
    if re.search(r"\b(flutter|swift|kotlin|dart|react native)\b", text, re.I):
        if known("polyglot-ecosystems", valid):
            kept.append(("polyglot-ecosystems", "composition: specialized runtime ecosystem"))
    # Reverse engineering: evidence-led architecture module rides with the core.
    if re.search(r"\b(ghidra|disassembl|decompil|reverse[- ]engineer|"
                 r"undocumented (?:file|binary|save-file) format|reconstruct the .{0,20}format)\b",
                 text, re.I):
        if known("reverse-engineering-architecture", valid):
            kept.append(("reverse-engineering-architecture",
                         "composition: evidence-led RE reconstruction"))

    # Deduplicate, keeping first (most specific) evidence.
    seen: dict[str, str] = {}
    for module, label in kept:
        seen.setdefault(module, label)

    # Composition rules: narrow security/system modules imply their framing base.
    comp_notes: list[str] = []
    selected = set(seen)
    for label, family, base in COMPOSITION:
        if selected & family and base not in seen and known(base, valid):
            seen[base] = f"composition: {label} implied by {sorted(selected & family)[0]}"
            comp_notes.append(base)

    # Order: domain modules first, helpers last; primary is the first non-helper.
    ordered = [m for m in seen if m not in HELPERS]
    helpers = [m for m in seen if m in HELPERS]
    proposed = (ordered + helpers)[:MAX_PROPOSED]
    primary = ordered[0] if ordered else (proposed[0] if proposed else None)

    # Confidence: ordinal, tied to evidence count, not to probabilities.
    n = len(proposed)
    if out_of_scope and not proposed:
        confidence = "n/a (out of scope)"
    elif n == 0:
        confidence = "insufficient signal"
    elif n == 1:
        confidence = "medium"
    else:
        confidence = "low" if n > 3 else "medium"

    notes = [
        "Proposal only. A model may override with a stated reason.",
        "Confidence is ordinal and evidence-count based, not a calibrated probability.",
    ]
    if out_of_scope:
        notes.append("Out-of-scope signals present: " + "; ".join(sorted(set(scope_evidence))))
    if comp_notes:
        notes.append("Composition bases added: " + ", ".join(comp_notes))
    result = {
        "proposed": proposed,
        "primary": primary,
        "in_scope": not (out_of_scope and not proposed) and n > 0,
        "confidence": confidence,
        "evidence": {m: seen[m] for m in proposed},
        "notes": notes,
    }
    if n == 0 and not out_of_scope:
        result["next"] = ("No documented signal fired. Confirm the request is software "
                          "engineering, or select a specialist manually from the router table.")
    return result


def read_request(args) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8", errors="replace")
    raise SystemExit("provide --text or --file")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic specialist-routing assistant")
    parser.add_argument("--text", help="request text")
    parser.add_argument("--file", help="file containing the request text")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--root", default=".", help="project root for project-local overrides")
    args = parser.parse_args()

    valid = set(reference_names())
    local = Path(args.root).resolve() / ".rcoder" / "references"
    if local.is_dir():
        valid |= {path.stem for path in local.glob("*.md")}
    result = propose(read_request(args), valid)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print("Proposed specialists:", ", ".join(result["proposed"]) or "(none)")
    print("Primary:", result["primary"] or "(none)")
    print("In scope:", result["in_scope"], "| Confidence:", result["confidence"])
    for module, label in result["evidence"].items():
        print(f"  - {module}: {label}")
    for note in result["notes"]:
        print("Note:", note)
    if "next" in result:
        print("Next:", result["next"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
