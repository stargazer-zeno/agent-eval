#!/usr/bin/env python3
"""OpenAI-compatible, controller-mediated GameVisualFix evaluation runner."""

from __future__ import annotations

import argparse
import base64
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "benchmark" / "task_001" / "public"
PRIVATE = ROOT / "benchmark" / "task_001" / "private"
TASK = PUBLIC / "TASK.md"
INITIAL_IMAGE = PUBLIC / "evidence" / "initial_bug.png"
DERIVED_NAMES = {".godot", "captures", "__pycache__"}
READABLE_SUFFIXES = {".gd", ".tscn", ".tres", ".godot", ".md", ".json", ".cfg", ".txt"}
WRITABLE_SUFFIXES = {".gd", ".tscn", ".tres", ".cfg", ".txt"}
PROTECTED_PREFIXES = ("evidence/", "tests/", "tools/")
PROTECTED_FILES = {"TASK.md", "project.godot"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def copy_public(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in DERIVED_NAMES or name.endswith((".uid", ".import", ".log"))}

    shutil.copytree(PUBLIC, destination, ignore=ignore)


def safe_path(workspace: Path, relative: str) -> tuple[Path, str]:
    normalized = relative.replace("\\", "/").lstrip("/")
    candidate = (workspace / normalized).resolve()
    workspace_resolved = workspace.resolve()
    if candidate != workspace_resolved and workspace_resolved not in candidate.parents:
        raise ValueError("path escapes workspace")
    return candidate, candidate.relative_to(workspace_resolved).as_posix()


def list_files(workspace: Path) -> list[str]:
    files = []
    for path in workspace.rglob("*"):
        if path.is_file() and not any(part in DERIVED_NAMES for part in path.relative_to(workspace).parts):
            if not path.name.endswith((".uid", ".import", ".log")):
                files.append(path.relative_to(workspace).as_posix())
    return sorted(files)


def run_command(command: list[str], timeout: int) -> dict[str, object]:
    startup = subprocess.STARTUPINFO() if os.name == "nt" else None
    if startup is not None:
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            startupinfo=startup,
            check=False,
        )
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output": completed.stdout[-6000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "timed_out": True,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output": ((exc.stdout or "") if isinstance(exc.stdout, str) else "")[-6000:],
        }


def smoke(workspace: Path, godot: Path) -> dict[str, object]:
    imported = run_command([str(godot), "--headless", "--path", str(workspace), "--import"], 90)
    if imported["exit_code"] != 0:
        return {"phase": "import", **imported}
    checked = run_command(
        [str(godot), "--headless", "--path", str(workspace), "--script", "res://tests/smoke.gd"], 90
    )
    return {"phase": "smoke", **checked}


def capture(workspace: Path, godot: Path, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    imported = run_command([str(godot), "--headless", "--path", str(workspace), "--import"], 90)
    if imported["exit_code"] != 0:
        return {"phase": "import", **imported, "image_exists": False, "image_sha256": None}
    command = [
        str(godot), "--path", str(workspace), "--display-driver", "windows",
        "--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
        "--audio-driver", "Dummy", "--position", "12000,12000",
        "--script", "res://tools/capture.gd", "--", "--scenario", "BASELINE",
        "--width", "960", "--height", "540", "--output", str(output.resolve()),
    ]
    result = run_command(command, 90)
    result["phase"] = "capture"
    result["image_exists"] = output.is_file()
    result["image_sha256"] = sha256(output) if output.is_file() else None
    return result


def data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def extract_json(text: str) -> dict[str, object]:
    stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("response contains no JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    return value


def api_request(base_url: str, key: str, payload: dict[str, object], timeout: int) -> dict[str, object]:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


SYSTEM = """You are a coding agent in a controller-mediated Godot workspace. Diagnose and fix the task.
Return exactly one JSON object per step, with no prose outside JSON. Valid actions:
{"action":"list_files"}
{"action":"read_file","path":"relative/path"}
{"action":"write_file","path":"relative/path","content":"complete replacement text"}
{"action":"run_smoke"}
{"action":"observe"}
{"action":"submit","summary":"brief checks and diagnosis"}
You cannot access hidden tests. Read relevant files before editing. Do not modify TASK.md, project.godot, evidence, tests, tools, or binary assets. You must request and inspect a fresh observation after your patch before submit. Keep the patch minimal."""


def text_result(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))[:14000]


def create_patch(original: Path, workspace: Path) -> str:
    chunks: list[str] = []
    original_files = {p.relative_to(original).as_posix(): p for p in original.rglob("*") if p.is_file()}
    workspace_files = {p.relative_to(workspace).as_posix(): p for p in workspace.rglob("*") if p.is_file()}
    for relative in sorted(set(original_files) | set(workspace_files)):
        if any(part in DERIVED_NAMES for part in Path(relative).parts) or relative.endswith((".uid", ".import", ".log")):
            continue
        before = original_files.get(relative)
        after = workspace_files.get(relative)
        if before and after and before.read_bytes() == after.read_bytes():
            continue
        if Path(relative).suffix.lower() not in READABLE_SUFFIXES:
            chunks.append(f"Binary change: {relative}\n")
            continue
        before_text = before.read_text(encoding="utf-8", errors="replace").splitlines(True) if before else []
        after_text = after.read_text(encoding="utf-8", errors="replace").splitlines(True) if after else []
        chunks.extend(difflib.unified_diff(before_text, after_text, f"a/{relative}", f"b/{relative}"))
    return "".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--config", default=ROOT / "harness" / "api_models.json", type=Path)
    parser.add_argument("--env-file", default=ROOT / ".env", type=Path)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    provider = config["providers"][args.provider]
    protocol = config["protocol"]
    secrets = load_dotenv(args.env_file)
    key = secrets.get(provider["api_key_env"], "")
    base_url = secrets.get(provider["base_url_env"], "")
    if not key or not base_url:
        raise SystemExit("provider credentials are not configured")

    output = args.output.resolve()
    if output.exists():
        raise SystemExit("output directory already exists")
    output.mkdir(parents=True)
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    artifacts.mkdir()
    copy_public(workspace)
    (output / "trajectory.jsonl").touch()
    started = time.monotonic()
    manifest: dict[str, object] = {
        "schema_version": 1, "provider": args.provider, "model": provider["model"],
        "task_id": "gamevisualfix_task_001", "started_at_unix": int(time.time()),
        "prompt_sha256": sha256(TASK), "initial_image_sha256": sha256(INITIAL_IMAGE),
        "max_steps": protocol["max_steps"], "max_observations": protocol["max_observations"],
    }
    messages: list[dict[str, object]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": [
            {"type": "text", "text": TASK.read_text(encoding="utf-8")},
            {"type": "image_url", "image_url": {"url": data_url(INITIAL_IMAGE)}},
        ]},
    ]
    observations = 0
    submitted = False
    valid_api = True
    final_summary = ""

    with (output / "trajectory.jsonl").open("a", encoding="utf-8") as log:
        for step in range(1, int(protocol["max_steps"]) + 1):
            if time.monotonic() - started > int(protocol["run_timeout_seconds"]):
                final_summary = "controller run timeout"
                break
            payload = {
                "model": provider["model"], "messages": messages,
                "temperature": 0, "max_tokens": 2500,
            }
            try:
                request_timeout = int(provider.get("request_timeout_seconds", protocol["request_timeout_seconds"]))
                response = api_request(base_url, key, payload, request_timeout)
                choice = response.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content", "")
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)
                usage = response.get("usage", {})
                event: dict[str, object] = {"step": step, "model_text": content, "usage": usage}
            except urllib.error.HTTPError as exc:
                valid_api = False
                final_summary = f"API HTTP {exc.code}"
                event = {"step": step, "api_error": {"type": "HTTPError", "status": exc.code}}
                log.write(json.dumps(event, ensure_ascii=False) + "\n")
                break
            except Exception as exc:
                valid_api = False
                final_summary = f"API error: {type(exc).__name__}"
                event = {"step": step, "api_error": {"type": type(exc).__name__}}
                log.write(json.dumps(event, ensure_ascii=False) + "\n")
                break

            messages.append({"role": "assistant", "content": content})
            try:
                action = extract_json(content)
                name = str(action.get("action", ""))
                event["action"] = action
                if name == "list_files":
                    result: object = {"files": list_files(workspace)}
                elif name == "read_file":
                    path, relative = safe_path(workspace, str(action.get("path", "")))
                    if not path.is_file() or path.suffix.lower() not in READABLE_SUFFIXES:
                        raise ValueError("file is missing or not readable text")
                    result = {"path": relative, "content": path.read_text(encoding="utf-8", errors="replace")[:50000]}
                elif name == "write_file":
                    path, relative = safe_path(workspace, str(action.get("path", "")))
                    if relative in PROTECTED_FILES or relative.startswith(PROTECTED_PREFIXES):
                        raise ValueError("protected path")
                    if path.suffix.lower() not in WRITABLE_SUFFIXES:
                        raise ValueError("file type is not writable")
                    content_value = action.get("content")
                    if not isinstance(content_value, str) or len(content_value) > 100000:
                        raise ValueError("content must be a bounded string")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content_value, encoding="utf-8", newline="\n")
                    result = {"written": relative, "sha256": sha256(path)}
                elif name == "run_smoke":
                    result = smoke(workspace, args.godot.resolve())
                elif name == "observe":
                    if observations >= int(protocol["max_observations"]):
                        raise ValueError("observation budget exhausted")
                    observations += 1
                    image = artifacts / f"observation_{observations}.png"
                    capture_result = capture(workspace, args.godot.resolve(), image)
                    result = capture_result
                    if image.is_file() and capture_result["exit_code"] == 0:
                        messages.append({"role": "user", "content": [
                            {"type": "text", "text": "Fresh post-patch runtime observation receipt: " + text_result(capture_result)},
                            {"type": "image_url", "image_url": {"url": data_url(image)}},
                        ]})
                        event["tool_result"] = result
                        log.write(json.dumps(event, ensure_ascii=False) + "\n")
                        continue
                elif name == "submit":
                    submitted = True
                    final_summary = str(action.get("summary", ""))[:2000]
                    result = {"accepted": True}
                else:
                    raise ValueError("unknown action")
            except Exception as exc:
                result = {"error": str(exc)[:500]}
            event["tool_result"] = result
            log.write(json.dumps(event, ensure_ascii=False) + "\n")
            if submitted:
                break
            messages.append({"role": "user", "content": "Controller result: " + text_result(result)})

    patch_text = create_patch(PUBLIC, workspace)
    (output / "final.patch").write_text(patch_text, encoding="utf-8", newline="\n")
    evaluation_dir = output / "evaluation"
    evaluator = run_command([
        sys.executable, str(PRIVATE / "evaluate.py"), "--candidate", str(workspace),
        "--godot", str(args.godot.resolve()), "--output", str(evaluation_dir),
        "--manifest", str(PRIVATE / "manifest.json"),
    ], 240)
    evaluation_file = evaluation_dir / "evaluation.json"
    evaluation = json.loads(evaluation_file.read_text(encoding="utf-8")) if evaluation_file.is_file() else None
    manifest.update({
        "finished_at_unix": int(time.time()), "elapsed_seconds": round(time.monotonic() - started, 3),
        "valid_api": valid_api, "submitted": submitted, "observations": observations,
        "summary": final_summary, "patch_sha256": sha256(output / "final.patch"),
        "evaluator_process": evaluator, "evaluation": evaluation,
    })
    (output / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "provider": args.provider, "model": provider["model"], "valid_api": valid_api,
        "submitted": submitted, "observations": observations,
        "task_success": evaluation.get("task_success") if evaluation else False,
        "score": evaluation.get("total") if evaluation else None,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
