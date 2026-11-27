#!/usr/bin/env python3
"""Regression tests for RFC Context Fabric's persistence and delivery invariants."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "rcoder" / "scripts"))

from context_fabric import (  # noqa: E402
    CanaryMismatch,
    ContextFabric,
    DeliveryNotFound,
    PromptAlreadyPrepared,
)


class ContextFabricTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rfc-context-fabric-")
        self.root = Path(self.temp.name)
        self.fabric = ContextFabric(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def put_basics(self):
        self.fabric.store_context(
            "session-01", "objective", "Current objective",
            "Implement the durable context handoff.", source_ref="issue: RFC-1", now=100,
        )
        self.fabric.store_context(
            "session-01", "constraint", "Hard constraint",
            "Never claim unverified checks passed.", now=101,
        )
        self.fabric.store_context(
            "session-01", "evidence", "Old note",
            "This note expires at timestamp 120.", ttl_seconds=20, now=100,
        )

    def test_explicit_hydration_and_per_prompt_identity(self):
        self.put_basics()
        first = self.fabric.build_context("session-01", "prompt-001", now=110)
        second = self.fabric.build_context("session-01", "prompt-002", now=111)
        self.assertIn("Current objective", first["text"])
        self.assertIn("Hard constraint", first["text"])
        self.assertIn("Current objective", second["text"])
        self.assertNotEqual(first["payload_sha256"], "")
        self.assertEqual(first["session_id"], "session-01")
        with self.assertRaises(PromptAlreadyPrepared):
            self.fabric.build_context("session-01", "prompt-001", now=112)

    def test_canary_acceptance_is_scoped_to_session_and_prompt(self):
        self.put_basics()
        token = "RFC-ACK-5f1c9a2b"
        built = self.fabric.build_context(
            "session-01", "prompt-001", ack_token=token, now=110
        )
        self.assertIn(token, built["text"])
        response = f"{token}\nThe context was received. Echo again: {token}"
        # B-5(a): the raw model response contains the exact acknowledgement token.
        self.assertIn(token, response)
        result = self.fabric.record_response(
            "session-01", "prompt-001", response, token, now=111
        )
        self.assertTrue(result["acknowledged"])
        self.assertTrue(result["transcript_token_free"])
        exported = self.fabric.export_transcript("session-01", "prompt-001")
        serialized = json.dumps(exported, ensure_ascii=False)
        self.assertTrue(exported["acknowledged"])
        # B-7(b) and A36: the exported transcript contains zero token occurrences.
        self.assertNotIn(token, serialized)
        self.assertIn("The context was received", serialized)
        self.assertNotIn("ack_token_sha256", serialized)

    def test_canary_cannot_be_replayed_across_session_or_prompt(self):
        self.put_basics()
        token = "RFC-ACK-4e8b2d77"
        self.fabric.build_context("session-01", "prompt-001", ack_token=token, now=110)
        with self.assertRaises(DeliveryNotFound):
            self.fabric.record_response("session-01", "prompt-002", token, token, now=111)
        with self.assertRaises(DeliveryNotFound):
            self.fabric.record_response("session-02", "prompt-001", token, token, now=111)
        with self.assertRaises(CanaryMismatch):
            self.fabric.record_response("session-01", "prompt-001", token, "RFC-ACK-wrong", now=111)
        with self.assertRaises(CanaryMismatch):
            self.fabric.build_context("session-01", "prompt-003", ack_token=token, now=112)

    def test_missing_echo_does_not_mark_delivery_acknowledged(self):
        self.put_basics()
        token = "RFC-ACK-713e5d9a"
        self.fabric.build_context("session-01", "prompt-001", ack_token=token, now=110)
        result = self.fabric.record_response(
            "session-01", "prompt-001", "Response without delivery marker.", token, now=111
        )
        self.assertFalse(result["acknowledged"])
        exported = self.fabric.export_transcript("session-01", "prompt-001")
        self.assertFalse(exported["acknowledged"])
        self.assertIn("Response without delivery marker", json.dumps(exported))

    def test_gc_uses_explicit_time_and_deterministic_inclusive_boundary(self):
        self.fabric.store_context(
            "session-01", "fact", "Expires at 110", "boundary fixture", ttl_seconds=10, now=100
        )
        self.fabric.store_context(
            "session-01", "fact", "Expires at 111", "later fixture", ttl_seconds=11, now=100
        )
        self.fabric.store_context(
            "session-01", "constraint", "Pinned past expiry", "pinned fixture",
            ttl_seconds=10, pinned=True, now=100,
        )
        at_boundary = self.fabric.gc(now=110)
        self.assertEqual(at_boundary["expired_items_deleted"], 1)
        stats = self.fabric.stats()
        self.assertEqual(stats["context_items"], 2)
        after_boundary = self.fabric.gc(now=111)
        self.assertEqual(after_boundary["expired_items_deleted"], 1)
        self.assertEqual(self.fabric.stats()["context_items"], 1)
        self.assertEqual(self.fabric.gc(now=111)["expired_items_deleted"], 0)

    def test_gc_requires_explicit_clock(self):
        with self.assertRaises(TypeError):
            self.fabric.gc()

    def test_content_addressed_artifact_deduplication_and_secret_redaction(self):
        first = self.fabric.store_context(
            "session-01", "fact", "Credential sample", 'api_key="test-secret-value"', now=100
        )
        second = self.fabric.store_context(
            "session-02", "fact", "Different title", 'api_key="test-secret-value"', now=101
        )
        self.assertEqual(first["content_sha256"], second["content_sha256"])
        self.assertTrue(first["redacted"])
        self.assertEqual(self.fabric.stats()["artifacts"], 1)
        built = self.fabric.build_context("session-01", "prompt-001", now=102)
        self.assertNotIn("test-secret-value", built["text"])
        self.assertIn("[REDACTED_SECRET]", built["text"])

    def test_budget_never_silently_truncates_a_context_item(self):
        self.fabric.store_context(
            "session-01", "objective", "Large objective", "A" * 4000, now=100
        )
        built = self.fabric.build_context("session-01", "prompt-001", budget_bytes=512, now=101)
        self.assertEqual(built["selected_item_ids"], [])
        self.assertEqual(len(built["excluded_item_ids"]), 1)
        self.assertNotIn("AAAA", built["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
