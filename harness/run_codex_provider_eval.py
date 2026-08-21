#!/usr/bin/env python3
"""Run a Codex-login or external Responses model through controller actions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import run_api_eval as core


SEED_MODEL = "doubao-seed-evolving"
LOCAL_MODEL = "gpt-5.6-sol"
PROVIDER = "volcengine-agent-plan"
PROTOCOL = """Operate through the controller protocol. Return exactly one JSON action as your final answer per turn.
Actions: list_files, read_file(path), write_file(path,content), run_smoke, observe, submit(summary).
Always include action, path, content, and summary. Use an empty string for fields unused by the selected action.
Do not use Codex shell/apply_patch/web tools directly; ask the controller to read or write files. Read relevant files before editing.
Do not modify TASK.md, project.godot, evidence, tests, tools, or binary assets. You must inspect a successful fresh post-patch observation before submit. Keep the patch minimal.
"""


def codex_config() -> str:
    return f'''model = "{SEED_MODEL}"
model_provider = "{PROVIDER}"
model_supports_reasoning_summaries = true
approval_policy = "never"
sandbox_mode = "read-only"

[shell_environment_policy]
inherit = "none"
ignore_default_excludes = false

[model_providers.{PROVIDER}]
name = "Volcengine Agent Plan"
base_url = "https://ark.cn-beijing.volces.com/api/plan/v3"
env_key = "Seed_Agent_Plan_key"
wire_api = "responses"
request_max_retries = 2
stream_max_retries = 2
stream_idle_timeout_ms = 180000
'''


def sanitized_environment() -> dict[str, str]:
    blocked = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.IGNORECASE)
    return {name: value for name, value in os.environ.items() if not blocked.search(name)}


def provider_environment(key: str, codex_home: Path) -> dict[str, str]:
    environment = sanitized_environment()
    environment["Seed_Agent_Plan_key"] = key
    environment["CODEX_HOME"] = str(codex_home)
    return environment


def codex_version() -> str:
    completed = subprocess.run(
        ["codex", "--version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=15, check=False,
    )
    return completed.stdout.strip() or "unknown"


def run_codex(command: list[str], prompt: str, cwd: Path, environment: dict[str, str], timeout: int) -> tuple[int, str, bool]:
    try:
        completed = subprocess.run(
            command, cwd=cwd, env=environment, input=prompt,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
        return completed.returncode, completed.stdout, False
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return 124, output, True


def parse_codex_output(raw: str) -> tuple[str | None, str | None, dict[str, int]]:
    thread = None
    message = None
    usage: dict[str, int] = {}
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            thread = event["thread_id"]
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            message = item.get("text")
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
    return thread, message, usage


def controller_action(action: dict[str, object], workspace: Path, godot: Path, artifacts: Path, observations: int) -> tuple[object, Path | None, int, bool, str]:
    name = str(action.get("action", ""))
    if name == "list_files":
        return {"files": core.list_files(workspace)}, None, observations, False, ""
    if name == "read_file":
        path, relative = core.safe_path(workspace, str(action.get("path", "")))
        if not path.is_file() or path.suffix.lower() not in core.READABLE_SUFFIXES:
            raise ValueError("file is missing or not readable text")
        return {"path": relative, "content": path.read_text(encoding="utf-8", errors="replace")[:50000]}, None, observations, False, ""
    if name == "write_file":
        path, relative = core.safe_path(workspace, str(action.get("path", "")))
        if relative in core.PROTECTED_FILES or relative.startswith(core.PROTECTED_PREFIXES):
            raise ValueError("protected path")
        if path.suffix.lower() not in core.WRITABLE_SUFFIXES:
            raise ValueError("file type is not writable")
        content = action.get("content")
        if not isinstance(content, str) or len(content) > 100000:
            raise ValueError("content must be a bounded string")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        return {"written": relative, "sha256": core.sha256(path)}, None, observations, False, ""
    if name == "run_smoke":
        return core.smoke(workspace, godot), None, observations, False, ""
    if name == "observe":
        if observations >= 3:
            raise ValueError("observation budget exhausted")
        observations += 1
        image = artifacts / f"observation_{observations}.png"
        result = core.capture(workspace, godot, image)
        return result, image if image.is_file() and result.get("exit_code") == 0 else None, observations, False, ""
    if name == "submit":
        return {"accepted": True}, None, observations, True, str(action.get("summary", ""))[:2000]
    raise ValueError("unknown action")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--env-file", default=core.ROOT / ".env", type=Path)
    parser.add_argument("--preload-public", action="store_true")
    parser.add_argument(
        "--local-login", action="store_true",
        help="Use the current Codex ChatGPT login with gpt-5.6-sol instead of Seed Agent Plan.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("output directory already exists")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    raw_root = output / "codex_raw"
    codex_home = output / "control" / "codex_home" if not args.local_login else None
    artifacts.mkdir()
    raw_root.mkdir()
    core.copy_public(workspace)
    if args.local_login:
        environment = sanitized_environment()
        model = LOCAL_MODEL
        provider_name = "codex_login_controller"
    else:
        assert codex_home is not None
        codex_home.mkdir(parents=True)
        (codex_home / "config.toml").write_text(codex_config(), encoding="utf-8", newline="\n")
        secrets = core.load_dotenv(args.env_file)
        key = secrets.get("Seed_Agent_Plan_key", "")
        if not key:
            raise SystemExit("Seed_Agent_Plan_key is not configured")
        environment = provider_environment(key, codex_home)
        model = SEED_MODEL
        provider_name = "seed_evolving_codex"
    schema = core.ROOT / "harness" / "controller_action.schema.json"
    common = [
        "--json", "--ignore-rules", "--output-schema", str(schema),
        "-c", 'web_search="disabled"',
        "--disable", "plugins", "--disable", "apps",
    ]
    if args.local_login:
        common.extend([
            "--ignore-user-config", "--model", model,
            "-c", 'model_reasoning_effort="ultra"',
            "-c", 'approval_policy="never"',
            "-c", 'shell_environment_policy.inherit="none"',
        ])
    started = time.monotonic()
    thread = None
    observations = 0
    submitted = False
    valid_provider = True
    summary = ""
    trajectory = output / "trajectory.jsonl"
    trajectory.touch()

    for step in range(1, 19):
        if time.monotonic() - started > 1500:
            valid_provider = False
            summary = "run timeout"
            break
        if step == 1:
            prompt = PROTOCOL + "\nTASK:\n" + core.TASK.read_text(encoding="utf-8")
            images = [core.INITIAL_IMAGE]
            if args.preload_public:
                snapshots = []
                for relative in core.list_files(workspace):
                    path = workspace / relative
                    if path.suffix.lower() in core.READABLE_SUFFIXES and relative != "TASK.md":
                        snapshots.append(f"\n--- {relative} ---\n" + path.read_text(encoding="utf-8", errors="replace"))
                prompt += "\nPUBLIC WORKSPACE TEXT SNAPSHOT (already read; do not reread unless necessary):\n" + "".join(snapshots)
                prompt += "\nThe attached images are, in order: initial runtime evidence, objective_arrow.png, threat_arrow.png. Diagnose now and prefer a focused write_file action."
                images.extend([workspace / "assets" / "objective_arrow.png", workspace / "assets" / "threat_arrow.png"])
            command = ["codex", "exec", *common]
            if args.local_login:
                command.extend(["--sandbox", "read-only"])
            command.extend(["--image", *[str(path) for path in images], "-C", str(workspace), "-"])
        else:
            prompt = pending_prompt
            command = ["codex", "exec", "resume", *common]
            if pending_image is not None:
                command.extend(["--image", str(pending_image)])
            command.extend([str(thread), "-"])
        exit_code, raw, timed_out = run_codex(command, prompt, workspace, environment, 240)
        (raw_root / f"turn_{step:02d}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        new_thread, model_text, usage = parse_codex_output(raw)
        if step == 1:
            thread = new_thread
        event: dict[str, object] = {
            "step": step, "exit_code": exit_code, "timed_out": timed_out,
            "usage": usage, "model_text": model_text,
        }
        if exit_code != 0 or not thread or not model_text:
            valid_provider = False
            summary = "Codex/provider turn failed or returned no agent message"
            event["failure_class"] = "provider_or_codex_transport"
            with trajectory.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            break
        try:
            action = core.extract_json(model_text)
            event["action"] = action
            result, image, observations, submitted, submit_summary = controller_action(
                action, workspace, args.godot.resolve(), artifacts, observations
            )
            if submit_summary:
                summary = submit_summary
        except Exception as exc:
            result, image = {"error": str(exc)[:500]}, None
        event["tool_result"] = result
        with trajectory.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        if submitted:
            break
        pending_image = image
        prefix = "Fresh post-patch runtime observation. Inspect the attached image. " if image else "Controller result. "
        pending_prompt = PROTOCOL + "\n" + prefix + core.text_result(result)

    patch_path = output / "final.patch"
    patch_path.write_text(core.create_patch(core.PUBLIC, workspace), encoding="utf-8", newline="\n")
    evaluation_dir = output / "evaluation"
    evaluator = core.run_command([
        sys.executable, str(core.PRIVATE / "evaluate.py"), "--candidate", str(workspace),
        "--godot", str(args.godot.resolve()), "--output", str(evaluation_dir),
        "--manifest", str(core.PRIVATE / "manifest.json"),
    ], 240)
    evaluation_file = evaluation_dir / "evaluation.json"
    evaluation = json.loads(evaluation_file.read_text(encoding="utf-8")) if evaluation_file.is_file() else None
    manifest = {
        "schema_version": 1, "provider": provider_name, "model": model,
        "task_id": "gamevisualfix_task_001", "mode": "codex_cli_controller_actions",
        "codex_cli_version": codex_version(),
        "model_metadata": "official_codex_catalog" if args.local_login else "fallback_unknown_model",
        "authentication": "chatgpt_login" if args.local_login else "seed_agent_plan_key",
        "reasoning_effort": "ultra" if args.local_login else None,
        "public_text_preloaded": args.preload_public,
        "comparison_eligible": not args.preload_public,
        "comparison_group": "codex_public_preload_v1" if args.preload_public else "codex_incremental_v1",
        "attempt_role": (
            "canonical_local_controller" if args.local_login
            else ("compatibility_rerun_public_preload" if args.preload_public else "canonical")
        ),
        "valid_api": valid_provider, "submitted": submitted, "observations": observations,
        "elapsed_seconds": round(time.monotonic() - started, 3), "thread_id": thread,
        "summary": summary, "patch_sha256": core.sha256(patch_path),
        "prompt_sha256": core.sha256(core.TASK), "initial_image_sha256": core.sha256(core.INITIAL_IMAGE),
        "evaluator_process": evaluator, "evaluation": evaluation,
    }
    (output / "run.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    # Credentials and run-local session state are never archived.
    if codex_home is not None:
        for path in codex_home.rglob("*"):
            if path.is_file():
                path.unlink()
    print(json.dumps({
        "valid_api": valid_provider, "submitted": submitted, "observations": observations,
        "score": evaluation.get("total") if evaluation else None,
        "task_success": evaluation.get("task_success") if evaluation else None,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
