#!/usr/bin/env python3
"""Deterministic tests for RSaver's reduction, evidence preservation, and recovery."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RSAVER = ROOT / "scripts" / "rsaver.py"


def run(*arguments, stdin_text=None):
    return subprocess.run(
        [sys.executable, str(RSAVER), *[str(arg) for arg in arguments]],
        text=True, encoding="utf-8", errors="replace", capture_output=True,
        check=False, timeout=20, input=stdin_text,
    )


def run_json(*arguments, stdin_text=None):
    result = run(*arguments, stdin_text=stdin_text)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def build_fixture(path: Path) -> dict:
    lines = ["# Tool output fixture"]
    lines.extend(f"INFO noise iteration {index} with repeated filler tokens" for index in range(80))
    critical = {
        82: "ERROR: parser failed at offset 42",
        83: "sha256=abcdef0123456789abcdef0123456789abcdef01",
        84: "See https://example.com/docs for reference",
        85: "Status: NOT VERIFIED",
    }
    lines.extend(critical[index] for index in sorted(critical))
    lines.append("done")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return critical


def main():
    with tempfile.TemporaryDirectory(prefix="rcoder-rsaver-test-") as temporary:
        root = Path(temporary)
        fixture = root / "log.txt"
        critical = build_fixture(fixture)
        manifest_path = root / "manifest.json"

        canonical = ROOT / "skills" / "rcoder" / "scripts" / "rsaver.py"
        assert canonical.is_file()
        direct = subprocess.run([sys.executable, str(canonical), "--version"],
                                text=True, capture_output=True, check=True, timeout=20)
        assert "RSaver 1.11.0" in direct.stdout
        version = run("--version")
        assert version.returncode == 0 and "RSaver 1.11.0" in version.stdout

        calibration = {
            "prose": "The quick brown fox jumps over the lazy dog. This sentence uses common words.",
            "cjk": "\u8fd9\u662f\u4e00\u4e2a\u7528\u4e8e\u6d4b\u8bd5\u6807\u8bb0\u5316\u6548\u7387\u7684\u4e2d\u6587\u53e5\u5b50\u3002\u4e2d\u6587\u5b57\u7b26\u901a\u5e38\u9700\u8981\u66f4\u591a\u6807\u8bb0\u3002",
            "numbers": "1234567890 9876543210 42 3.141592653589793 2026-11-19",
        }
        for text in calibration.values():
            assert run_json("measure", "-", "--json", stdin_text=text)["total_estimate"] > 0
        cjk_v2 = run_json("measure", "-", "--json", stdin_text=calibration["cjk"])["files"][0]["estimate"]
        cjk_v1 = run_json("measure", "-", "--json", stdin_text=calibration["cjk"])["files"][0]["v1_legacy"]
        assert cjk_v2 > cjk_v1, "CJK scripts must not be undercounted by v2"
        o200k = run_json("measure", "-", "--profile", "openai-o200k", "--json", stdin_text=calibration["cjk"])
        assert o200k["files"][0]["estimate"] < cjk_v2, "profile must change CJK density"
        counter_command = f'"{sys.executable}" -c "import sys; print(len(sys.stdin.read().split()))"'
        hooked = run_json("compare", "-", "--tokenizer-command", counter_command,
                          "--json", stdin_text=calibration["prose"])
        assert hooked["rows"][0]["exact"] is not None
        assert hooked["rows"][0]["exact_source"] == "external-tokenizer-command"
        assert hooked["rows"][0]["v2_error_percent"] is not None

        budget = run_json("budget", "--window", "100000", "--output-reserve", "4000",
                          "--reasoning-reserve", "8000", "--tool-schema", "1000", "--json")
        assert budget["available_input"] == 88000
        assert budget["item_budget"] == 87000

        envelope = {
            "window_tokens": 10000, "output_reserve": 1000, "reasoning_reserve": 2000,
            "tool_schema_tokens": 500, "cache_min_tokens": 1000,
            "items": [
                {"id": "system", "section": "prefix", "tokens": 700,
                 "stability": "static", "priority": "required"},
                {"id": "tools", "section": "prefix", "tokens": 500,
                 "stability": "static", "priority": "required"},
                {"id": "skill", "section": "working", "tokens": 2000,
                 "stability": "dynamic", "priority": "useful"},
                {"id": "old-log", "section": "history", "tokens": 8000,
                 "stability": "dynamic", "priority": "optional"},
                {"id": "prompt", "section": "tail", "tokens": 100,
                 "stability": "dynamic", "priority": "required"},
            ],
        }
        gate = run_json("gate", "-", "--json", stdin_text=json.dumps(envelope))
        decisions = {item["id"]: item["decision"] for item in gate["decisions"]}
        assert decisions["system"] == "keep" and decisions["tools"] == "keep"
        assert decisions["prompt"] == "keep" and decisions["old-log"] == "defer"
        assert decisions["skill"] == "keep"
        assert gate["budget"]["input_estimate"] == 3800
        assert gate["budget"]["projected_total"] == 6800
        assert gate["budget"]["headroom"] == 3200
        assert gate["cache"]["eligible"] is True
        assert gate["deferred_count"] == 1
        assert gate["warnings"] == []

        fragmented = json.loads(json.dumps(envelope))
        fragmented["items"][4]["stability"] = "static"
        fragmented_plan = run_json("gate", "-", "--json", stdin_text=json.dumps(fragmented))
        assert "cache_prefix_fragmented_by_dynamic_item" in fragmented_plan["warnings"]

        short_prefix = json.loads(json.dumps(envelope))
        short_prefix["cache_min_tokens"] = 99999
        short_plan = run_json("gate", "-", "--json", stdin_text=json.dumps(short_prefix))
        assert short_plan["cache"]["eligible"] is False
        assert "cache_prefix_below_minimum" in short_plan["warnings"]

        inline_envelope = {
            "window_tokens": 10000, "output_reserve": 1000, "reasoning_reserve": 2000,
            "items": [
                {"id": "inline-doc", "section": "working", "text": "This is inline documentation text for test.",
                 "stability": "dynamic", "priority": "required"}
            ]
        }
        inline_gate = run_json("gate", "-", "--json", stdin_text=json.dumps(inline_envelope))
        assert inline_gate["decisions"][0]["tokens"] > 0
        assert inline_gate["decisions"][0]["decision"] == "keep"

        assert run("gate", "-", "--json", stdin_text='{"window_tokens": 0, "items": []}').returncode == 2
        assert run("gate", "-", "--json", stdin_text='{"window_tokens": 10, "items": [{"id": 1}]}').returncode == 2
        assert run("budget", "--window", "10", "--output-reserve", "20").returncode == 2

        transcript = root / "transcript.txt"
        transcript.write_text("\n".join(
            ["# session"] + [f"noise {index}" for index in range(60)]
            + ["$ run tests", "$ run tests", "$ run tests",
               "Unverified hypothesis about cache", "The task is complete and all tests pass"]
        ) + "\n", encoding="utf-8")
        drift = run_json("drift", str(transcript), "--json")
        signals = {item["signal"] for item in drift["signals"]}
        assert "objective_absent_from_recent_window" in signals
        assert "constraint_absent_from_recent_window" in signals
        assert "repeated_command" in signals
        assert "completion_claim_with_open_unknowns" in signals
        assert drift["diagnosis"].startswith("NOT VERIFIED")

        tool_loop = root / "tool-loop.txt"
        tool_loop.write_text("\n".join(
            ["# session"] + [f"noise {index}" for index in range(20)]
            + ["TOOL view src/parser.py"] * 4
        ) + "\n", encoding="utf-8")
        tool_drift = run_json("drift", str(tool_loop), "--json")
        assert any(item["signal"] == "repeated_command" for item in tool_drift["signals"])

        state = root / "state.json"
        state.write_text(json.dumps({
            "objective": "Fix the failing parser test and add a regression case",
            "constraints": ["No changes outside src/parser", "Keep public API stable"],
            "verified_facts": ["baseline failure recorded"],
            "decisions": ["Fix root cause not symptom"],
            "unresolved": ["Cache invalidation hypothesis"],
            "security_boundary": "No production access",
            "next_action": "Reproduce timeout with bounded fixture",
        }), encoding="utf-8")
        anchor = run_json("anchor", str(state), "--json")
        assert anchor["block"].count("RSAVER ANCHOR START") == 1
        assert anchor["block"].count("RSAVER ANCHOR END") == 1
        assert "[OBJECTIVE-1]" in anchor["opening"] and "[OBJECTIVE-1]" in anchor["closing"]
        assert "[CONSTRAINT-1]" in anchor["opening"] and "[CONSTRAINT-1]" in anchor["closing"]
        assert "[NEXT-ACTION]" in anchor["closing"]
        assert "[FACT-1]" in anchor["opening"]
        assert anchor["estimate"] <= anchor["max_tokens"]
        assert anchor["warnings"] == []
        bounded = run_json("anchor", str(state), "--max-tokens", "10", "--json")
        assert "anchor_exceeds_budget" in bounded["warnings"]

        envelope_path = root / "gate-envelope.json"
        envelope_path.write_text(json.dumps(envelope), encoding="utf-8")
        reanchored = run_json("reanchor", "--envelope", str(envelope_path), "--state", str(state), "--json")
        ids = {item["id"] for item in reanchored["gate"]["decisions"]}
        assert "rsaver-anchor-start" in ids and "rsaver-anchor-end" in ids
        assert reanchored["gate"]["deferred_count"] >= 1
        assert reanchored["anchor"]["estimate"] > 0
        assert run("anchor", "-", "--json", stdin_text='{"constraints": []}').returncode == 2
        assert run("drift", str(transcript), "--recent-window", "0", "--json").returncode == 2

        pack_source = root / "pack-source.txt"
        pack_source.write_text("\n".join(["INFO repeated heartbeat line with several words here"] * 40) + "\n",
                               encoding="utf-8")
        packed = run_json("pack", str(pack_source), "--json")
        assert packed["worthwhile"] is True
        assert packed["saved_percent"] > 50.0
        pack_manifest = root / "pack.json"
        pack_manifest.write_text(json.dumps(packed), encoding="utf-8")
        restored = root / "restored.txt"
        unpacked = run("unpack", "--manifest", str(pack_manifest), "--out", str(restored))
        assert unpacked.returncode == 0, unpacked.stderr
        assert restored.read_text(encoding="utf-8") == pack_source.read_text(encoding="utf-8")
        assert run("unpack", "--manifest", str(pack_manifest), "--json").returncode == 0

        expectation = root / "expect.json"
        expectation.write_text(json.dumps({
            "objective": "Fix the parser", "required_files": ["src/parser.py"],
            "forbidden_paths": ["/etc"],
        }), encoding="utf-8")
        diff_file = root / "diff.txt"
        diff_file.write_text("--- a/src/parser.py\n+++ b/src/parser.py\n+return fixed\n", encoding="utf-8")
        test_log = root / "test.txt"
        test_log.write_text("ERROR: still failing\n", encoding="utf-8")
        claim_file = root / "claim.txt"
        claim_file.write_text("Task done\n", encoding="utf-8")
        usage_file = root / "usage.json"
        usage_file.write_text(json.dumps({
            "input_tokens": 1000, "output_tokens": 200,
            "input_tokens_details": {"cached_tokens": 300},
            "output_tokens_details": {"reasoning_tokens": 150},
        }), encoding="utf-8")
        cross = run_json("crosscheck", "--expect", str(expectation), "--diff", str(diff_file),
                         "--test-log", str(test_log), "--claim", str(claim_file),
                         "--usage", str(usage_file), "--json")
        assert cross["verdict"] == "FAIL"
        statuses = {item["id"]: item["status"] for item in cross["checks"]}
        assert statuses["required_edits"] == "pass"
        assert statuses["test_result"] == "fail"
        assert statuses["claim_consistency"] == "fail"
        assert cross["usage"]["input_tokens"] == 1000
        assert "cannot zero" in cross["billing_note"].lower()
        passing_log = root / "pass.txt"
        passing_log.write_text("PASS all tests\n", encoding="utf-8")
        passed = run_json("crosscheck", "--expect", str(expectation), "--diff", str(diff_file),
                          "--test-log", str(passing_log), "--claim", str(claim_file), "--json")
        assert passed["verdict"] == "PASS"

        measured = run_json("measure", str(fixture), "--json")
        assert measured["total_estimate"] > 0
        assert measured["files"][0]["lines"] == 86
        assert measured["files"][0]["estimate"] == measured["total_estimate"]

        compacted = run_json("compact", str(fixture), "--max-lines", "20", "--json")
        reduced = compacted["compacted"]
        original_lines = fixture.read_text(encoding="utf-8").splitlines()
        assert compacted["estimate"]["saved_percent"] >= 40.0
        assert compacted["estimate"]["compact_estimate"] < compacted["estimate"]["original_estimate"]
        assert sorted(compacted["critical_lines"]) == sorted(critical)
        assert compacted["omitted_ranges"]
        assert not compacted["budget_exceeded_by_critical"]
        for text in critical.values():
            assert text in reduced, text
        assert all(line in original_lines for line in reduced.splitlines())

        compact_80 = run_json("compact", str(fixture), "--target-savings", "80", "--json")
        assert compact_80["estimate"]["saved_percent"] >= 80.0, f"Expected >= 80% savings, got {compact_80['estimate']['saved_percent']}%"
        for text in critical.values():
            assert text in compact_80["compacted"]

        written = run("compact", str(fixture), "--max-lines", "20", "--manifest", str(manifest_path), "--verify")
        assert written.returncode == 0, written.stderr
        verified = run("verify", "--manifest", str(manifest_path))
        assert verified.returncode == 0 and "RSAVER VERIFY PASS" in verified.stdout

        range_start, range_end = compacted["omitted_ranges"][0]
        recovered = run_json("recover", "--file", str(fixture), "--range", f"{range_start}:{range_end}", "--json")
        assert recovered["text"].splitlines() == original_lines[range_start - 1:range_end]

        selected = run_json("select", str(fixture), "--match", "ERROR|sha256", "--context", "1",
                            "--max-lines", "10", "--json")
        assert selected["critical_lines"] == [82, 83]
        assert len(selected["selected_text"].splitlines()) <= 10
        assert critical[84] in selected["selected_text"]

        small = run_json("dedupe", "-", "--json", stdin_text="A\nA\nERROR: boom\nA\n")
        assert small["stats"]["saved_estimate"] >= 0
        assert "ERROR: boom" in small["deduped_text"]

        repeated = root / "repeated.txt"
        repeated.write_text("\n".join(["INFO worker heartbeat ok"] * 40 + ["ERROR: boom"]) + "\n", encoding="utf-8")
        deduped = run_json("dedupe", str(repeated), "--json")
        assert deduped["stats"]["saved_estimate"] > 0
        assert "original lines 1-40" in deduped["deduped_text"]
        assert "ERROR: boom" in deduped["deduped_text"]

        timestamped = root / "timestamped.txt"
        timestamped.write_text("\n".join(
            [f"2026-11-22T19:0{i:02d}:00.123 [worker-{i}] processed batch {1000+i} ok" for i in range(50)]
            + ["ERROR: worker crashed"]
        ) + "\n", encoding="utf-8")
        norm_deduped = run_json("dedupe", str(timestamped), "--normalize", "--json")
        assert norm_deduped["stats"]["saved_percent"] >= 80.0, f"Expected >= 80% savings, got {norm_deduped['stats']['saved_percent']}%"
        assert "ERROR: worker crashed" in norm_deduped["deduped_text"]
        assert "similar non-critical line(s) collapsed" in norm_deduped["deduped_text"]

        # Test command block deduplication (90%+ savings)
        ps_block = (
            'PS D:\\RCoder-Skills> powershell -Command "python scripts/validate-all"\n'
            'RCoder validation: 3139 checks\n'
            'PASS: skill structure, specialist routing, evaluation data\n'
            '<shellId: 1 completed with exit code 0>\n'
        )
        cmd_file = root / "commands.log"
        cmd_file.write_text(ps_block * 25, encoding="utf-8")
        block_deduped = run_json("dedupe", str(cmd_file), "--blocks", "--json")
        assert block_deduped["stats"]["saved_percent"] >= 90.0, f"Expected >= 90%, got {block_deduped['stats']['saved_percent']}%"
        assert "block 4 lines repeated x24" in block_deduped["deduped_text"]
        assert "RSaver#" in block_deduped["deduped_text"]

        # Test zero-token duplicate word/phrase frequency deduplication (90%+ savings)
        phrase_sample = "powershell -ExecutionPolicy Bypass -Command Get-ChildItem -Recurse. " * 30
        phrase_file = root / "phrases.txt"
        phrase_file.write_text(phrase_sample, encoding="utf-8")
        word_deduped = run_json("dedupe", str(phrase_file), "--words", "--json")
        assert word_deduped["stats"]["saved_percent"] >= 90.0, f"Expected >= 90%, got {word_deduped['stats']['saved_percent']}%"

        # Test pack --method dict and unpack roundtrip
        dict_packed = run_json("pack", str(phrase_file), "--method", "dict", "--json")
        assert dict_packed["saved_percent"] >= 90.0
        dict_manifest = root / "dict_manifest.json"
        dict_manifest.write_text(json.dumps(dict_packed), encoding="utf-8")
        dict_restored = root / "dict_restored.txt"
        unpacked_dict = run("unpack", "--manifest", str(dict_manifest), "--out", str(dict_restored))
        assert unpacked_dict.returncode == 0
        assert dict_restored.read_text(encoding="utf-8") == phrase_sample

        # Adversarial: literal reference/marker text in source must not corrupt restore
        hostile_file = root / "hostile.txt"
        hostile_text = ("deploy failed at stage @0 and marker [RSaver#0: repeat x5] appears literally\n"
                        + "the deploy pipeline checks the token. " * 12)
        hostile_file.write_text(hostile_text, encoding="utf-8")
        hostile_packed = run_json("pack", str(hostile_file), "--method", "dict", "--json")
        hostile_manifest = root / "hostile_manifest.json"
        hostile_manifest.write_text(json.dumps(hostile_packed), encoding="utf-8")
        hostile_restored = root / "hostile_restored.txt"
        hostile_run = run("unpack", "--manifest", str(hostile_manifest), "--out", str(hostile_restored))
        assert hostile_run.returncode == 0, hostile_run.stderr
        assert hostile_restored.read_text(encoding="utf-8") == hostile_text

        tampered = root / "tampered.txt"
        tampered.write_text(fixture.read_text(encoding="utf-8") + "ERROR: new evidence\n", encoding="utf-8")
        failed = run("verify", "--manifest", str(manifest_path), "--file", str(tampered))
        assert failed.returncode == 1 and "RSAVER VERIFY FAIL" in failed.stderr

        assert run("compact", str(fixture), "--critical", "[", "--json").returncode == 2
        assert run("recover", "--file", str(fixture), "--range", "999:1000").returncode == 2
        assert run("measure", str(root / "missing.txt")).returncode == 2

    print("PASS rsaver: bounded reduction, verbatim evidence, recoverability, verification, and dedupe economics")


if __name__ == "__main__":
    main()
