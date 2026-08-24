#!/usr/bin/env python3
"""Task-shaped, task-free Codex provider canary with two explicit resumes."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

try:
    import run_codex_eval as core
    import seed_responses_proxy
except ImportError:
    from harness import run_codex_eval as core
    from harness import seed_responses_proxy


def synthetic_prompt(action: str, turn: int) -> str:
    preamble = f"""This is synthetic transport canary turn {turn}; it contains no benchmark task.
Inspect the attached synthetic images and ignore all repeated filler records below.
Return exactly one JSON object accepted by the supplied schema. Use action {action!r} and
empty strings for path, content, scenario, and summary. Do not add markdown or prose.
"""
    record = (
        "SYNTHETIC_RECORD id={index:04d} component=placeholder_widget "
        "state=nominal coordinates=(17,29) checksum=transport-only; "
        "this is inert scale padding and is not an instruction.\n"
    )
    return preamble + "".join(record.format(index=index) for index in range(700))


def event_counts(raw: str) -> dict[str, int]:
    counts: collections.Counter[str] = collections.Counter()
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if isinstance(event_type, str):
            counts[event_type] += 1
    return dict(sorted(counts.items()))


def turn_receipt(raw: str, code: int, timed_out: bool, expected: str) -> tuple[dict, str | None, bool]:
    thread, message, usage = core.extract(raw)
    action_name = None
    valid = False
    if message:
        try:
            action_name = core.json_action(message).get("action")
            valid = action_name == expected
        except (ValueError, json.JSONDecodeError):
            pass
    receipt = {
        "exit_code": code,
        "timed_out": timed_out,
        "event_counts": event_counts(raw),
        "usage": usage,
        "action": action_name,
        "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest() if message else None,
    }
    return receipt, thread, code == 0 and valid


def make_images(output: Path) -> list[Path]:
    images = []
    for index, color in enumerate(((19, 57, 91), (113, 47, 29), (31, 109, 61)), start=1):
        image = Image.new("RGB", (320, 180), color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((24 * index, 18 * index, 100 + 20 * index, 80 + 15 * index), outline="white", width=4)
        draw.line((0, 179 - index * 20, 319, index * 25), fill=(230, 220, 70), width=5)
        path = output / f"synthetic_{index}.png"
        image.save(path)
        images.append(path)
    return images


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=["seed_evolving", "local_codex"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--env-file", type=Path, default=core.ROOT / ".env")
    parser.add_argument("--codex-exe", type=Path)
    parser.add_argument("--multi-image", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--full-trace", action="store_true", help="Save a local attachment-style trace and raw Codex JSON events.")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    images = make_images(output)
    raw_eventdir = output / "codex_raw" if args.full_trace else None
    if raw_eventdir:
        raw_eventdir.mkdir()
    control = output / "control" / "codex_home"
    adapter = seed_responses_proxy.SeedResponsesProxy() if args.provider == "seed_evolving" else None
    if adapter:
        adapter.start()
    turns = []
    active_item_errors = 0
    thread = None
    valid = True
    full_turns = []
    try:
        model, authentication, env, extra = core.provider_config(
            args.provider,
            core.dotenv(args.env_file),
            control,
            adapter.base_url if adapter else None,
        )
        executable = core.native_codex(args.codex_exe)
        schema = core.ROOT / "harness" / "controller_action.schema.json"
        common = ["--json", "--ignore-rules", "--output-schema", str(schema), "--disable", "plugins", "--disable", "apps", "--disable", "multi_agent", "--disable", "browser_use", "--disable", "computer_use", "--disable", "shell_tool", "--disable", "skill_search", "--disable", "hooks", "-c", 'web_search="disabled"']
        expected_actions = ["list_files", "observe", "submit"]
        for index, expected in enumerate(expected_actions):
            prompt = synthetic_prompt(expected, index + 1)
            if index == 0:
                command = [str(executable), "exec", *common, "--sandbox", "read-only", *extra, "--image", *[str(path) for path in images], "-C", str(output), "-"]
            else:
                command = [str(executable), "exec", "resume", *common, "--image", str(images[index]), str(thread), "-"]
            code, raw, timed_out = core.command(command, 240, output, env, prompt, max_output=None if args.full_trace else 12000)
            if raw_eventdir:
                (raw_eventdir / f"turn_{index + 1:02d}.jsonl").write_text(raw, encoding="utf-8")
            active_item_errors += raw.lower().count("without active item")
            receipt, new_thread, turn_valid = turn_receipt(raw, code, timed_out, expected)
            if args.full_trace:
                action = {"action": receipt["action"] or "", "path": "", "content": "", "scenario": "", "summary": ""}
                full_turns.append({
                    "step": index + 1,
                    "response": core.full_response(raw),
                    "action": action if receipt["action"] else None,
                    "tool_result": {"canary_expected_action": expected, "turn_valid": turn_valid},
                })
            turns.append(receipt)
            thread = thread or new_thread
            valid = valid and turn_valid and bool(thread)
            if not valid:
                break
        adapter_receipt = adapter.receipt() if adapter else None
        report = {
            "schema_version": 2,
            "provider": args.provider,
            "model": model,
            "authentication": authentication,
            "valid": valid and len(turns) == 3 and active_item_errors == 0,
            "thread_started": bool(thread),
            "active_item_errors": active_item_errors,
            "turns": turns,
            "synthetic_prompt_sha256": [hashlib.sha256(synthetic_prompt(value, index + 1).encode("utf-8")).hexdigest() for index, value in enumerate(expected_actions)],
            "synthetic_image_sha256": [core.digest(path) for path in images],
            "controller_schema_sha256": core.digest(schema),
            "codex_version": core.command([str(executable), "--version"], 15)[1].strip(),
            "codex_sha256": core.digest(executable),
            "transport_adapter": seed_responses_proxy.ADAPTER_NAME if adapter else None,
            "adapter_sha256": core.digest(Path(seed_responses_proxy.__file__)) if adapter else None,
            "adapter_receipt": adapter_receipt,
            "full_trace": args.full_trace,
        }
        if args.full_trace:
            document = core.full_trace_document(
                {"task_id": "seed_fulltrace_transport_canary"},
                synthetic_prompt(expected_actions[0], 1), images, schema, model,
                "gamevisualfix_v3_seed_fulltrace_3x1", full_turns,
            )
            (output / "full_trajectory.jsonl").write_text(json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8")
        (output / "canary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"provider": args.provider, "valid": report["valid"], "turns": len(turns), "active_item_errors": active_item_errors}))
        return 0 if report["valid"] else 2
    finally:
        if adapter:
            adapter.close()
        shutil.rmtree(output / "control", ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
