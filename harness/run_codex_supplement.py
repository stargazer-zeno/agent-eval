#!/usr/bin/env python3
"""Run a two-turn Codex CLI supplement in a sanitized public workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import run_api_eval as core


def run(command: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    completed = subprocess.run(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
    )
    return completed.returncode, completed.stdout


def thread_id(jsonl: str) -> str | None:
    for line in jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        value = event.get("thread_id")
        if isinstance(value, str):
            return value
        value = event.get("thread", {}).get("id") if isinstance(event.get("thread"), dict) else None
        if isinstance(value, str):
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--godot", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("output already exists")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    artifacts.mkdir()
    core.copy_public(workspace)
    run(["git", "init", "-b", "main"], workspace, 30)
    run(["git", "config", "user.name", "GameVisualFix Harness"], workspace, 30)
    run(["git", "config", "user.email", "harness@invalid.local"], workspace, 30)
    files = core.list_files(workspace)
    run(["git", "add", "--", *files], workspace, 30)
    run(["git", "commit", "-m", "seed workspace"], workspace, 30)

    prompt = core.TASK.read_text(encoding="utf-8") + f"""

You are in a sanitized public-only workspace. Do not inspect parent directories or any path outside it.
You may edit the workspace and run the public smoke test with this executable:
{args.godot.resolve()}
Do not create a fresh screenshot yourself. Finish this turn with the required JSON action; use observe after a candidate patch.
"""
    command = [
        "codex", "exec", "--json", "--image", str(core.INITIAL_IMAGE),
        "--model", "gpt-5.6-sol", "--sandbox", "workspace-write",
        "--ignore-user-config", "--ignore-rules", "--output-schema", str(core.ROOT / "harness" / "action.schema.json"),
        "-c", 'model_reasoning_effort="ultra"', "-c", 'approval_policy="never"',
        "-C", str(workspace), prompt,
    ]
    started = time.monotonic()
    try:
        code1, raw1 = run(command, workspace, 900)
    except subprocess.TimeoutExpired:
        code1, raw1 = 124, ""
    tid = thread_id(raw1)
    fresh = artifacts / "observation_1.png"
    capture_result = core.capture(workspace, args.godot.resolve(), fresh)
    raw2 = ""
    code2 = None
    if tid and fresh.is_file():
        resume_prompt = "Inspect this controller-generated fresh post-patch runtime screenshot. If the fix is incomplete, revise the workspace and run public checks. Finish with submit JSON and a concise summary."
        resume = [
            "codex", "exec", "resume", "--json", "--image", str(fresh),
            "--model", "gpt-5.6-sol", "--ignore-user-config", "--ignore-rules",
            "--output-schema", str(core.ROOT / "harness" / "action.schema.json"),
            "-c", 'model_reasoning_effort="ultra"', "-c", 'approval_policy="never"',
            tid, resume_prompt,
        ]
        try:
            code2, raw2 = run(resume, workspace, 600)
        except subprocess.TimeoutExpired:
            code2, raw2 = 124, ""
    (output / "trajectory.jsonl").write_text(raw1 + raw2, encoding="utf-8")
    patch = core.create_patch(core.PUBLIC, workspace)
    (output / "final.patch").write_text(patch, encoding="utf-8", newline="\n")
    evaluation_dir = output / "evaluation"
    evaluator = core.run_command([
        sys.executable, str(core.PRIVATE / "evaluate.py"), "--candidate", str(workspace),
        "--godot", str(args.godot.resolve()), "--output", str(evaluation_dir),
        "--manifest", str(core.PRIVATE / "manifest.json"),
    ], 240)
    evaluation_path = evaluation_dir / "evaluation.json"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8")) if evaluation_path.is_file() else None
    manifest = {
        "schema_version": 1, "provider": "codex_login", "model": "gpt-5.6-sol",
        "task_id": "gamevisualfix_task_001", "mode": "supplement_relaxed_host_isolation",
        "valid_api": bool(tid) and code1 == 0 and code2 == 0, "submitted": code2 == 0,
        "observations": 1 if fresh.is_file() else 0,
        "elapsed_seconds": round(time.monotonic() - started, 3), "thread_id": tid,
        "initial_exit_code": code1, "resume_exit_code": code2, "capture": capture_result,
        "summary": "Codex CLI two-turn supplement; not equivalent to strict OS/VM isolation.",
        "evaluator_process": evaluator, "evaluation": evaluation,
    }
    (output / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"thread": bool(tid), "codes": [code1, code2], "evaluation_total": evaluation.get("total") if evaluation else None, "task_success": evaluation.get("task_success") if evaluation else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
