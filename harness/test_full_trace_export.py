#!/usr/bin/env python3
"""Unit tests for local attachment-style full trace export."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    import run_codex_eval as core
except ImportError:
    from harness import run_codex_eval as core


class FullTraceExportTests(unittest.TestCase):
    def test_full_response_keeps_emitted_text_and_reasoning_summary(self) -> None:
        raw = "\n".join([
            json.dumps({"type": "item.completed", "item": {"type": "reasoning", "summary": [{"type": "summary_text", "text": "visible summary"}]}}),
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "{\"action\":\"submit\"}"}}),
        ])
        self.assertEqual(core.full_response(raw), {
            "assistant_text": "{\"action\":\"submit\"}",
            "reasoning_content": "visible summary",
            "reasoning_available": True,
        })

    def test_document_uses_attachment_style_prompt_and_tool_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "initial_bug.png"
            image.write_bytes(b"png-fixture")
            schema = root / "schema.json"
            schema.write_text(json.dumps({"type": "object", "properties": {}}), encoding="utf-8")
            action = {"action": "observe", "path": "", "content": "", "scenario": "BASELINE", "summary": ""}
            document = core.full_trace_document(
                {"task_id": "fixture_task"}, "Repair the project.", [image], schema,
                "doubao-seed-evolving", "fixture_suite", [{
                    "step": 1,
                    "response": {"assistant_text": json.dumps(action), "reasoning_content": "", "reasoning_available": False},
                    "action": action,
                    "tool_result": {"image_exists": True},
                }],
            )
            self.assertEqual(document["task_id"], "fixture_task")
            self.assertEqual(document["prompt"][2]["role"], "assistant")
            self.assertEqual(document["prompt"][3]["role"], "tool")
            self.assertEqual(document["prompt"][2]["reasoning_content"], "")
            self.assertEqual(document["prompt"][2]["tool_calls"][0]["function"]["name"], "controller_action")
            self.assertEqual(document["meta"]["initial_images"][0]["sha256"], hashlib.sha256(b"png-fixture").hexdigest().upper())
            self.assertEqual(document["candidates"][0][0]["role"], "assistant")


if __name__ == "__main__":
    unittest.main(verbosity=2)
