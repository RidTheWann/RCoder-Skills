#!/usr/bin/env python3
"""Conformance tests for the shared RCoder contract and MCP adapters."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "rcoder" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import rcoder_contract as contract  # noqa: E402
import rcoder_mcp as core  # noqa: E402
import rcoder_mcp_modern as modern  # noqa: E402


def main() -> int:
    raw = json.loads(contract.CONTRACT_PATH.read_text(encoding="utf-8"))
    assert raw["contract_id"] == "rcoder.v2"
    assert raw["product"]["version"] == core.product_version()
    assert modern.MODERN_PROTOCOL == contract.MODERN_PROTOCOL
    assert tuple(core.PROTOCOLS) == contract.LEGACY_PROTOCOLS
    assert raw["mcp"]["transports"]["stdio"]["enabled"] is True
    assert raw["mcp"]["transports"]["streamable_http"]["bind_host"] == "127.0.0.1"
    assert raw["mcp"]["transports"]["streamable_http"]["authentication"] == "Bearer token"
    assert raw["mcp"]["structured_output"]["enabled"] is True
    assert raw["mcp"]["skills_manifest"]["inline"] is True

    names = [entry[0] for entry in core.TOOLS]
    assert len(names) == len(set(names))
    assert "rcoder_doctor" in names and "rsaver_redact" in names and "rsaver_ledger" in names
    assert {"rcoder_skill_lint", "rcoder_hooks_config", "rcoder_contract"} <= set(names)
    assert all(entry[3].get("additionalProperties") is False for entry in core.TOOLS)

    # D-022: the legacy stdio core must paginate exactly the collections the contract declares.
    for method, collection in contract.PAGINATED_METHODS.items():
        if method == "skills/list":
            continue  # no skills extension in this core; modern owns it
        page = core.handle(method, {})
        assert len(page[collection]) <= contract.PAGE_SIZE, (method, len(page[collection]))
        collected, cursor = list(page[collection]), page.get("nextCursor")
        while cursor:
            page = core.handle(method, {"cursor": cursor})
            collected += page[collection]
            cursor = page.get("nextCursor")
        assert collected, f"{method} returned an empty collection"
        assert len(collected) == len({repr(item) for item in collected}), \
            f"{method} repeated an item across pages"
    try:
        core.handle("tools/list", {"cursor": "!"})
    except ValueError as error:
        assert "cursor" in str(error).lower()
    else:
        raise AssertionError("an invalid cursor must be rejected as Invalid params input")

    sample = {"tools": list(range(23)), "marker": "preserved"}
    first = contract.paginate_result("tools/list", sample, {})
    assert first["tools"] == list(range(10)) and first["marker"] == "preserved"
    assert first["nextCursor"] == contract.encode_cursor(10)
    second = contract.paginate_result("tools/list", sample, {"cursor": first["nextCursor"]})
    third = contract.paginate_result("tools/list", sample,
                                     {"cursor": contract.encode_cursor(20)})
    assert second["tools"] == list(range(10, 20)) and second["nextCursor"] == contract.encode_cursor(20)
    assert third["tools"] == [20, 21, 22] and "nextCursor" not in third
    for invalid in ("", "!", "Zm9v", contract.encode_cursor(999)):
        try:
            contract.paginate_result("tools/list", {"tools": [1]}, {"cursor": invalid})
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid cursor accepted: {invalid!r}")

    # The Skills extension already carries the complete digest/size manifest inline.
    skill = modern.skill_entry()
    resources = skill["resources"]
    assert resources and resources[0]["uri"].endswith("/SKILL.md")
    assert all(item["digest"].startswith("sha256:") and item["size"] >= 0 for item in resources)
    assert len(resources) <= raw["mcp"]["skills_manifest"]["max_files"]
    print(f"PASS shared contract: version={contract.PRODUCT_VERSION}, tools={len(names)}, page_size={contract.PAGE_SIZE}, manifest_files={len(resources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
