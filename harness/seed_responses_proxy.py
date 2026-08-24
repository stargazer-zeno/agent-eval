#!/usr/bin/env python3
"""Local fail-closed Responses SSE normalizer for the Seed Agent Plan."""
from __future__ import annotations

import collections
import contextlib
import hashlib
import http.server
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import BinaryIO, Iterable, Iterator

ADAPTER_NAME = "seed_responses_sse_normalizer"
ADAPTER_VERSION = "1.1.0"
DEFAULT_UPSTREAM = "https://ark.cn-beijing.volces.com/api/plan/v3"
TERMINAL_EVENTS = {
    "response.completed",
    "response.failed",
    "response.incomplete",
}
SENSITIVE_FIELDS = {"delta", "text", "reasoning", "content", "output_text"}


class NormalizationError(RuntimeError):
    """Raised when an upstream stream cannot be normalized reliably."""


@dataclass
class PartState:
    index: int
    kind: str
    added: bool = False
    done: bool = False
    fragments: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(self.fragments)


@dataclass
class ItemState:
    output_index: int
    item_id: str
    kind: str
    added: bool = False
    done: bool = False
    parts: dict[int, PartState] = field(default_factory=dict)


class Diagnostics:
    """Thread-safe structural telemetry that cannot retain model text."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.streams = 0
        self.errors = 0
        self.upstream_events: collections.Counter[str] = collections.Counter()
        self.output_events: collections.Counter[str] = collections.Counter()
        self.inserted_events: collections.Counter[str] = collections.Counter()
        self.field_shapes: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
        self._structure_hash = hashlib.sha256()

    def begin_stream(self) -> None:
        with self._lock:
            self.streams += 1

    def error(self) -> None:
        with self._lock:
            self.errors += 1

    def record(self, event: dict, *, upstream: bool, inserted: bool = False) -> None:
        event_type = event.get("type")
        if not isinstance(event_type, str):
            raise NormalizationError("event type is missing")
        fields = sorted(key for key in event if key not in SENSITIVE_FIELDS)
        structural = json.dumps(
            {"type": event_type, "fields": fields},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        with self._lock:
            target = self.upstream_events if upstream else self.output_events
            target[event_type] += 1
            if upstream and event_type != "[DONE]":
                nested = []
                for container_name in ("item", "part", "response"):
                    container = event.get(container_name)
                    if isinstance(container, dict):
                        nested.extend(f"{container_name}.{key}" for key in sorted(container))
                shape = ",".join(fields + nested)
                self.field_shapes[event_type][shape] += 1
            if inserted:
                self.inserted_events[event_type] += 1
            self._structure_hash.update(structural)

    def receipt(self) -> dict:
        with self._lock:
            return {
                "adapter": ADAPTER_NAME,
                "version": ADAPTER_VERSION,
                "streams": self.streams,
                "errors": self.errors,
                "upstream_event_counts": dict(sorted(self.upstream_events.items())),
                "output_event_counts": dict(sorted(self.output_events.items())),
                "normalization_counts": dict(sorted(self.inserted_events.items())),
                "field_shapes": {
                    event_type: dict(sorted(shapes.items()))
                    for event_type, shapes in sorted(self.field_shapes.items())
                },
                "structure_sha256": self._structure_hash.hexdigest(),
            }


def parse_sse(stream: BinaryIO) -> Iterator[dict]:
    """Parse JSON SSE records. Comments are ignored and unknown fields fail closed."""
    data_lines: list[bytes] = []
    for raw in stream:
        line = raw.rstrip(b"\r\n")
        if not line:
            if data_lines:
                yield _decode_sse_data(data_lines)
                data_lines = []
            continue
        if line.startswith(b":"):
            continue
        if line.startswith(b"data:"):
            data_lines.append(line[5:].lstrip(b" "))
            continue
        if line.startswith((b"event:", b"id:", b"retry:")):
            continue
        raise NormalizationError("malformed SSE field")
    if data_lines:
        yield _decode_sse_data(data_lines)


def _decode_sse_data(lines: list[bytes]) -> dict:
    payload = b"\n".join(lines)
    if payload == b"[DONE]":
        return {"type": "[DONE]"}
    try:
        event = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NormalizationError("malformed SSE JSON") from exc
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise NormalizationError("SSE data is not a typed object")
    return event


def encode_sse(event: dict) -> bytes:
    if event.get("type") == "[DONE]":
        return b"data: [DONE]\n\n"
    payload = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return b"event: " + event["type"].encode("ascii") + b"\ndata: " + payload + b"\n\n"


def agent_plan_request_body(body: bytes) -> bytes:
    """Make the Seed Agent Plan streaming contract explicit without logging it.

    The upstream may reject a reconnect request that omits ``partial``.  The
    controller has no use for partial final responses, so an absent value is
    forwarded as JSON ``false``.  Existing explicit values are preserved.
    """
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return body
    if not isinstance(payload, dict) or "partial" in payload:
        return body
    payload["partial"] = False
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class StreamNormalizer:
    def __init__(self, diagnostics: Diagnostics | None = None) -> None:
        self.diagnostics = diagnostics or Diagnostics()
        self.sequence = 0
        self.items: dict[int, ItemState] = {}
        self.seen_terminal = False

    def normalize(self, events: Iterable[dict]) -> Iterator[dict]:
        self.diagnostics.begin_stream()
        for upstream_event in events:
            self.diagnostics.record(upstream_event, upstream=True)
            event = self._canonicalize(upstream_event)
            enriched = event != upstream_event
            event_type = event["type"]
            if event_type == "[DONE]":
                if not self.seen_terminal:
                    raise NormalizationError("DONE received before a terminal response event")
                yield event
                continue
            if self.seen_terminal:
                raise NormalizationError("event received after terminal response event")
            if not event_type.startswith("response."):
                raise NormalizationError("unknown non-Responses event")

            inserted = self._prepare(event)
            for synthetic in inserted:
                yield self._numbered(synthetic, inserted=True)
            if event_type in TERMINAL_EVENTS:
                for synthetic in self._close_all():
                    yield self._numbered(synthetic, inserted=True)
                self.seen_terminal = True
            self._observe(event)
            yield self._numbered(event, inserted=enriched)

        if not self.seen_terminal:
            raise NormalizationError("stream ended without terminal response event")

    @staticmethod
    def _canonicalize(event: dict) -> dict:
        """Fill required empty containers while preserving every upstream value."""
        event_type = event["type"]
        result = dict(event)
        if event_type in {"response.created", "response.in_progress"} and isinstance(event.get("response"), dict):
            response = dict(event["response"])
            response.setdefault("output", [])
            result["response"] = response
        if event_type in {"response.output_item.added", "response.output_item.done"} and isinstance(event.get("item"), dict):
            item = dict(event["item"])
            if item.get("type") == "message":
                item.setdefault("content", [])
                item.setdefault("role", "assistant")
            elif item.get("type") == "reasoning":
                item.setdefault("summary", [])
            result["item"] = item
        if event_type in {"response.content_part.added", "response.content_part.done"} and isinstance(event.get("part"), dict):
            part = dict(event["part"])
            if part.get("type") == "output_text":
                part.setdefault("text", "")
                part.setdefault("annotations", [])
            result["part"] = part
        if event_type in {"response.reasoning_summary_part.added", "response.reasoning_summary_part.done"} and isinstance(event.get("part"), dict):
            part = dict(event["part"])
            if part.get("type") == "summary_text":
                part.setdefault("text", "")
            result["part"] = part
        if event_type == "response.output_text.delta":
            result.setdefault("logprobs", [])
        return result

    def _numbered(self, event: dict, *, inserted: bool = False) -> dict:
        outgoing = dict(event)
        outgoing["sequence_number"] = self.sequence
        self.sequence += 1
        self.diagnostics.record(outgoing, upstream=False, inserted=inserted)
        return outgoing

    def _prepare(self, event: dict) -> list[dict]:
        event_type = event["type"]
        if event_type == "response.output_item.added":
            return []
        if event_type == "response.output_item.done":
            state = self._state_from_item_event(event)
            inserted = self._ensure_item(state)
            self._seed_parts_from_item(state, event.get("item"))
            inserted.extend(self._close_parts(state))
            return inserted
        if event_type.startswith("response.output_text."):
            state = self._state_from_delta(event, "message")
            inserted = self._ensure_item(state)
            part = self._part(state, event, "output_text")
            inserted.extend(self._ensure_part(state, part))
            return inserted
        if event_type.startswith("response.content_part."):
            state = self._state_from_delta(event, "message")
            inserted = self._ensure_item(state)
            part = self._part(state, event, "output_text")
            if event_type == "response.content_part.done" and not part.added:
                inserted.extend(self._ensure_part(state, part))
            return inserted
        if event_type.startswith("response.reasoning_summary_"):
            state = self._state_from_delta(event, "reasoning")
            inserted = self._ensure_item(state)
            part = self._part(state, event, "summary_text")
            if event_type != "response.reasoning_summary_part.added":
                inserted.extend(self._ensure_part(state, part))
            return inserted
        return []

    def _observe(self, event: dict) -> None:
        event_type = event["type"]
        if event_type == "response.output_item.added":
            state = self._state_from_item_event(event)
            state.added = True
            self._seed_parts_from_item(state, event.get("item"))
            return
        if event_type == "response.output_item.done":
            state = self._state_from_item_event(event)
            state.done = True
            self._seed_parts_from_item(state, event.get("item"))
            return
        if event_type.startswith(("response.output_text.", "response.content_part.")):
            state = self._state_from_delta(event, "message")
            part = self._part(state, event, "output_text")
            if event_type == "response.content_part.added":
                part.added = True
            elif event_type == "response.output_text.delta":
                self._append_delta(part, event)
            elif event_type == "response.output_text.done":
                self._set_final_text(part, event)
            elif event_type == "response.content_part.done":
                self._set_part_final(part, event)
                part.done = True
            return
        if event_type.startswith("response.reasoning_summary_"):
            state = self._state_from_delta(event, "reasoning")
            part = self._part(state, event, "summary_text")
            if event_type == "response.reasoning_summary_part.added":
                part.added = True
            elif event_type == "response.reasoning_summary_text.delta":
                self._append_delta(part, event)
            elif event_type == "response.reasoning_summary_text.done":
                self._set_final_text(part, event)
            elif event_type == "response.reasoning_summary_part.done":
                self._set_part_final(part, event)
                part.done = True

    def _state_from_item_event(self, event: dict) -> ItemState:
        item = event.get("item")
        index = event.get("output_index")
        if not isinstance(item, dict) or not isinstance(index, int):
            raise NormalizationError("output item event lacks item/output_index")
        item_id = item.get("id")
        kind = item.get("type")
        if not isinstance(item_id, str) or kind not in {"message", "reasoning"}:
            raise NormalizationError("unsupported output item")
        return self._get_item(index, item_id, kind)

    def _state_from_delta(self, event: dict, kind: str) -> ItemState:
        index = event.get("output_index")
        item_id = event.get("item_id")
        if not isinstance(index, int) or not isinstance(item_id, str):
            raise NormalizationError("item event lacks item_id/output_index")
        return self._get_item(index, item_id, kind)

    def _get_item(self, index: int, item_id: str, kind: str) -> ItemState:
        state = self.items.get(index)
        if state is None:
            state = ItemState(index, item_id, kind)
            self.items[index] = state
        elif state.item_id != item_id or state.kind != kind:
            raise NormalizationError("conflicting output item identity")
        return state

    def _part(self, state: ItemState, event: dict, kind: str) -> PartState:
        key = "summary_index" if state.kind == "reasoning" else "content_index"
        index = event.get(key)
        if not isinstance(index, int):
            raise NormalizationError(f"item event lacks {key}")
        part = state.parts.get(index)
        if part is None:
            part = PartState(index, kind)
            state.parts[index] = part
        elif part.kind != kind:
            raise NormalizationError("conflicting part identity")
        return part

    def _ensure_item(self, state: ItemState) -> list[dict]:
        if state.added:
            return []
        state.added = True
        item = (
            {"id": state.item_id, "type": "message", "status": "in_progress", "role": "assistant", "content": []}
            if state.kind == "message"
            else {"id": state.item_id, "type": "reasoning", "status": "in_progress", "summary": []}
        )
        return [{"type": "response.output_item.added", "output_index": state.output_index, "item": item}]

    def _ensure_part(self, state: ItemState, part: PartState) -> list[dict]:
        if part.added:
            return []
        part.added = True
        if state.kind == "message":
            return [{
                "type": "response.content_part.added",
                "item_id": state.item_id,
                "output_index": state.output_index,
                "content_index": part.index,
                "part": {"type": "output_text", "text": "", "annotations": []},
            }]
        return [{
            "type": "response.reasoning_summary_part.added",
            "item_id": state.item_id,
            "output_index": state.output_index,
            "summary_index": part.index,
            "part": {"type": "summary_text", "text": ""},
        }]

    def _seed_parts_from_item(self, state: ItemState, item: object) -> None:
        if not isinstance(item, dict):
            return
        values = item.get("content" if state.kind == "message" else "summary")
        if not isinstance(values, list):
            return
        for index, value in enumerate(values):
            if not isinstance(value, dict):
                continue
            kind = "output_text" if state.kind == "message" else "summary_text"
            part = state.parts.setdefault(index, PartState(index, kind))
            text = value.get("text")
            if isinstance(text, str) and not part.fragments:
                part.fragments = [text]

    @staticmethod
    def _append_delta(part: PartState, event: dict) -> None:
        delta = event.get("delta")
        if not isinstance(delta, str):
            raise NormalizationError("text delta is not a string")
        part.fragments.append(delta)

    @staticmethod
    def _set_final_text(part: PartState, event: dict) -> None:
        text = event.get("text")
        if isinstance(text, str):
            part.fragments = [text]

    @staticmethod
    def _set_part_final(part: PartState, event: dict) -> None:
        value = event.get("part")
        if isinstance(value, dict) and isinstance(value.get("text"), str):
            part.fragments = [value["text"]]

    def _close_parts(self, state: ItemState) -> list[dict]:
        inserted: list[dict] = []
        for part in sorted(state.parts.values(), key=lambda value: value.index):
            inserted.extend(self._ensure_part(state, part))
            if part.done:
                continue
            part.done = True
            if state.kind == "message":
                inserted.append({
                    "type": "response.content_part.done",
                    "item_id": state.item_id,
                    "output_index": state.output_index,
                    "content_index": part.index,
                    "part": {"type": "output_text", "text": part.text, "annotations": []},
                })
            else:
                inserted.append({
                    "type": "response.reasoning_summary_part.done",
                    "item_id": state.item_id,
                    "output_index": state.output_index,
                    "summary_index": part.index,
                    "part": {"type": "summary_text", "text": part.text},
                })
        return inserted

    def _close_all(self) -> list[dict]:
        inserted: list[dict] = []
        for state in sorted(self.items.values(), key=lambda value: value.output_index):
            inserted.extend(self._ensure_item(state))
            inserted.extend(self._close_parts(state))
            if state.done:
                continue
            state.done = True
            if state.kind == "message":
                content = [
                    {"type": "output_text", "text": part.text, "annotations": []}
                    for part in sorted(state.parts.values(), key=lambda value: value.index)
                ]
                item = {"id": state.item_id, "type": "message", "status": "completed", "role": "assistant", "content": content}
            else:
                summary = [
                    {"type": "summary_text", "text": part.text}
                    for part in sorted(state.parts.values(), key=lambda value: value.index)
                ]
                item = {"id": state.item_id, "type": "reasoning", "status": "completed", "summary": summary}
            inserted.append({"type": "response.output_item.done", "output_index": state.output_index, "item": item})
        return inserted


class _ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "SeedResponsesProxy"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        owner: SeedResponsesProxy = self.server.owner  # type: ignore[attr-defined]
        length = self.headers.get("Content-Length")
        if length is None:
            self.send_error(411)
            return
        try:
            body = self.rfile.read(int(length))
        except (ValueError, OSError):
            self.send_error(400)
            return
        body = agent_plan_request_body(body)
        upstream_url = owner.upstream.rstrip("/") + "/" + self.path.lstrip("/")
        headers = {
            key: value for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "connection", "transfer-encoding", "accept-encoding"}
        }
        request = urllib.request.Request(upstream_url, data=body, headers=headers, method="POST")
        try:
            response = urllib.request.urlopen(request, timeout=owner.upstream_timeout)
        except urllib.error.HTTPError as exc:
            self._send_passthrough(exc.code, exc.headers, exc.read())
            return
        except (urllib.error.URLError, TimeoutError, OSError):
            owner.diagnostics.error()
            self.send_error(502, "upstream unavailable")
            return
        with contextlib.closing(response):
            content_type = response.headers.get("Content-Type", "")
            if response.status != 200 or "text/event-stream" not in content_type.lower():
                self._send_passthrough(response.status, response.headers, response.read())
                return
            self.send_response(response.status)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                normalizer = StreamNormalizer(owner.diagnostics)
                for event in normalizer.normalize(parse_sse(response)):
                    self.wfile.write(encode_sse(event))
                    self.wfile.flush()
            except (NormalizationError, BrokenPipeError, ConnectionResetError):
                owner.diagnostics.error()
            finally:
                self.close_connection = True

    def _send_passthrough(self, status: int, headers: object, body: bytes) -> None:
        self.send_response(status)
        content_type = headers.get("Content-Type") if hasattr(headers, "get") else None
        if content_type:
            self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True


class _ThreadingServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False


class SeedResponsesProxy:
    """Managed loopback-only proxy with an ephemeral port."""

    def __init__(self, upstream: str = DEFAULT_UPSTREAM, upstream_timeout: int = 240) -> None:
        parsed = urllib.parse.urlparse(upstream)
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("non-loopback upstream must use HTTPS")
        self.upstream = upstream
        self.upstream_timeout = upstream_timeout
        self.diagnostics = Diagnostics()
        self._server = _ThreadingServer(("127.0.0.1", 0), _ProxyHandler)
        self._server.owner = self  # type: ignore[attr-defined]
        self._thread = threading.Thread(target=self._server.serve_forever, name="seed-responses-proxy", daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}"

    def start(self) -> "SeedResponsesProxy":
        self._thread.start()
        return self

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)

    def __enter__(self) -> "SeedResponsesProxy":
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def receipt(self) -> dict:
        return self.diagnostics.receipt()
