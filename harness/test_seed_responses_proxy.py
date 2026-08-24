#!/usr/bin/env python3
from __future__ import annotations

import http.server
import io
import json
import threading
import unittest
import urllib.error
import urllib.request

try:
    from harness import seed_responses_proxy as proxy
except ImportError:  # Direct execution from the harness directory.
    import seed_responses_proxy as proxy


def normalized(events: list[dict]) -> tuple[list[dict], dict]:
    diagnostics = proxy.Diagnostics()
    result = list(proxy.StreamNormalizer(diagnostics).normalize(events))
    return result, diagnostics.receipt()


def created() -> dict:
    return {"type": "response.created", "sequence_number": 99, "response": {"id": "resp_test", "status": "in_progress", "output": []}}


def completed() -> dict:
    return {"type": "response.completed", "sequence_number": 1, "response": {"id": "resp_test", "status": "completed", "usage": {"input_tokens": 3, "output_tokens": 2}}}


class RequestBodyTests(unittest.TestCase):
    def test_missing_partial_is_forwarded_as_false(self) -> None:
        body = proxy.agent_plan_request_body(b'{"model":"doubao-seed-evolving","stream":true}')
        self.assertEqual(json.loads(body), {"model": "doubao-seed-evolving", "stream": True, "partial": False})

    def test_explicit_partial_and_non_json_are_unchanged(self) -> None:
        explicit = b'{"partial":true}'
        self.assertEqual(proxy.agent_plan_request_body(explicit), explicit)
        self.assertEqual(proxy.agent_plan_request_body(b"not-json"), b"not-json")


class NormalizerTests(unittest.TestCase):
    def test_compliant_stream_is_preserved_except_sequence(self) -> None:
        events = [
            created(),
            {"type": "response.output_item.added", "output_index": 0, "item": {"id": "msg_1", "type": "message", "status": "in_progress", "role": "assistant", "content": []}},
            {"type": "response.content_part.added", "item_id": "msg_1", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []}},
            {"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "ok", "logprobs": []},
            {"type": "response.content_part.done", "item_id": "msg_1", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": "ok", "annotations": []}},
            {"type": "response.output_item.done", "output_index": 0, "item": {"id": "msg_1", "type": "message", "status": "completed", "role": "assistant", "content": [{"type": "output_text", "text": "ok", "annotations": []}]}},
            completed(),
        ]
        result, receipt = normalized(events)
        self.assertEqual(len(result), len(events))
        self.assertEqual(receipt["normalization_counts"], {})
        for index, (actual, expected) in enumerate(zip(result, events)):
            self.assertEqual(actual["sequence_number"], index)
            self.assertEqual({k: v for k, v in actual.items() if k != "sequence_number"}, {k: v for k, v in expected.items() if k != "sequence_number"})

    def test_missing_text_item_and_part_are_inserted(self) -> None:
        result, receipt = normalized([
            created(),
            {"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "hello"},
            completed(),
        ])
        types = [event["type"] for event in result]
        self.assertEqual(types, [
            "response.created", "response.output_item.added", "response.content_part.added",
            "response.output_text.delta", "response.content_part.done", "response.output_item.done",
            "response.completed",
        ])
        self.assertEqual(result[4]["part"]["text"], "hello")
        self.assertEqual(receipt["normalization_counts"]["response.output_item.added"], 1)

    def test_incomplete_seed_envelopes_are_enriched(self) -> None:
        result, receipt = normalized([
            created(),
            {"type": "response.output_item.added", "output_index": 0, "item": {"id": "msg_1", "type": "message", "status": "in_progress", "role": "assistant"}},
            {"type": "response.content_part.added", "item_id": "msg_1", "output_index": 0, "content_index": 0, "part": {"type": "output_text"}},
            {"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "ok"},
            completed(),
        ])
        added = next(event for event in result if event["type"] == "response.output_item.added")
        part = next(event for event in result if event["type"] == "response.content_part.added")
        delta = next(event for event in result if event["type"] == "response.output_text.delta")
        self.assertEqual(added["item"]["content"], [])
        self.assertEqual(part["part"], {"type": "output_text", "text": "", "annotations": []})
        self.assertEqual(delta["logprobs"], [])
        self.assertEqual(receipt["normalization_counts"]["response.output_item.added"], 1)

    def test_missing_reasoning_item_and_part_are_inserted(self) -> None:
        result, _ = normalized([
            created(),
            {"type": "response.reasoning_summary_text.delta", "item_id": "rs_1", "output_index": 0, "summary_index": 0, "delta": "thought"},
            completed(),
        ])
        types = [event["type"] for event in result]
        self.assertIn("response.reasoning_summary_part.added", types)
        self.assertIn("response.reasoning_summary_part.done", types)
        done = next(event for event in result if event["type"] == "response.output_item.done")
        self.assertEqual(done["item"]["summary"][0]["text"], "thought")

    def test_multiple_items_are_tracked_independently(self) -> None:
        result, _ = normalized([
            created(),
            {"type": "response.reasoning_summary_text.delta", "item_id": "rs_1", "output_index": 0, "summary_index": 0, "delta": "r"},
            {"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 1, "content_index": 0, "delta": "m"},
            completed(),
        ])
        done = [event for event in result if event["type"] == "response.output_item.done"]
        self.assertEqual([event["output_index"] for event in done], [0, 1])
        self.assertEqual([event["item"]["type"] for event in done], ["reasoning", "message"])

    def test_missing_done_events_are_inserted(self) -> None:
        result, receipt = normalized([
            created(),
            {"type": "response.output_item.added", "output_index": 0, "item": {"id": "msg_1", "type": "message", "status": "in_progress", "role": "assistant", "content": []}},
            {"type": "response.content_part.added", "item_id": "msg_1", "output_index": 0, "content_index": 0, "part": {"type": "output_text", "text": "", "annotations": []}},
            {"type": "response.output_text.delta", "item_id": "msg_1", "output_index": 0, "content_index": 0, "delta": "done"},
            completed(),
        ])
        self.assertEqual(result[-3]["type"], "response.content_part.done")
        self.assertEqual(result[-2]["type"], "response.output_item.done")
        self.assertEqual(receipt["normalization_counts"]["response.output_item.done"], 1)

    def test_sequence_numbers_are_strictly_monotonic(self) -> None:
        result, _ = normalized([created(), completed()])
        self.assertEqual([event["sequence_number"] for event in result], list(range(len(result))))

    def test_malformed_sse_fails(self) -> None:
        with self.assertRaises(proxy.NormalizationError):
            list(proxy.parse_sse(io.BytesIO(b"data: {bad}\n\n")))
        with self.assertRaises(proxy.NormalizationError):
            list(proxy.StreamNormalizer().normalize([created()]))


class _UpstreamHandler(http.server.BaseHTTPRequestHandler):
    status = 429
    body = b'{"error":"rate limited"}'
    authorization = None

    def log_message(self, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        type(self).authorization = self.headers.get("Authorization")
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(type(self).body)))
        self.end_headers()
        self.wfile.write(type(self).body)


class ProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.upstream = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
        self.thread = threading.Thread(target=self.upstream.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.upstream.shutdown()
        self.upstream.server_close()
        self.thread.join(timeout=5)

    def test_http_error_passthrough_and_credentials_not_logged(self) -> None:
        secret = "not-for-logs-123"
        upstream = f"http://127.0.0.1:{self.upstream.server_port}/api/plan/v3"
        with proxy.SeedResponsesProxy(upstream) as server:
            request = urllib.request.Request(server.base_url + "/responses", data=b"{}", headers={"Authorization": secret}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request)
            self.assertEqual(caught.exception.code, 429)
            self.assertEqual(caught.exception.read(), _UpstreamHandler.body)
            receipt = server.receipt()
        self.assertEqual(_UpstreamHandler.authorization, secret)
        self.assertNotIn(secret, json.dumps(receipt))
        self.assertNotIn("rate limited", json.dumps(receipt))


if __name__ == "__main__":
    unittest.main()
