#!/usr/bin/env python3
"""Shared RCoder 2.0 contract and transport-neutral MCP list pagination."""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "rcoder-v2.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
PRODUCT_VERSION = CONTRACT["product"]["version"]
MODERN_PROTOCOL = CONTRACT["mcp"]["modern_protocol"]
LEGACY_PROTOCOLS = tuple(CONTRACT["mcp"]["legacy_protocols"])
PAGE_SIZE = int(CONTRACT["mcp"]["pagination"]["page_size"])
CURSOR_PREFIX = "rcoder-v1:"
PAGINATED_METHODS = dict(CONTRACT["mcp"]["pagination"]["collections"])


def encode_cursor(offset: int) -> str:
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("cursor offset must be a non-negative integer")
    raw = f"{CURSOR_PREFIX}{offset}".encode("ascii")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: Any) -> int:
    if not isinstance(cursor, str) or not cursor or len(cursor) > 128:
        raise ValueError("invalid pagination cursor")
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode("ascii")
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError("invalid pagination cursor") from error
    if not raw.startswith(CURSOR_PREFIX):
        raise ValueError("unsupported pagination cursor")
    value = raw[len(CURSOR_PREFIX):]
    if not value.isdecimal():
        raise ValueError("invalid pagination cursor offset")
    offset = int(value)
    if offset < 0 or offset > 100000:
        raise ValueError("pagination cursor offset is out of bounds")
    return offset


def paginate_result(method: str, result: dict, params: dict) -> dict:
    """Return a copied result with a bounded page and opaque nextCursor when needed."""
    collection = PAGINATED_METHODS.get(method)
    if not collection:
        return result
    items = result.get(collection)
    if not isinstance(items, list):
        return result
    cursor = params.get("cursor")
    offset = decode_cursor(cursor) if cursor is not None else 0
    if offset > len(items):
        raise ValueError("pagination cursor is past the end of the collection")
    end = min(offset + PAGE_SIZE, len(items))
    page = dict(result)
    page[collection] = items[offset:end]
    page.pop("nextCursor", None)
    if end < len(items):
        page["nextCursor"] = encode_cursor(end)
    return page
