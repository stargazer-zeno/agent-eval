#!/usr/bin/env python3
"""Canonical task-manifest Codex CLI controller evaluation for GameVisualFix."""
from __future__ import annotations

import argparse, hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

try:
    import seed_responses_proxy
    import stateful_controller
except ImportError:  # Importing as harness.run_codex_eval from repository root.
    from harness import seed_responses_proxy
    from harness import stateful_controller

ROOT = Path(__file__).resolve().parents[1]
READABLE = {".gd", ".tscn", ".tres", ".godot", ".md", ".json", ".cfg", ".txt"}
WRITABLE = {".gd", ".tscn", ".tres", ".cfg", ".txt"}
PROTECTED = {"TASK.md", "project.godot"}
PROTECTED_PREFIXES = ("evidence/", "tests/", "tools/")

PROTOCOL = """Return exactly one JSON controller action as your final answer. Required keys: action, path, content, scenario, summary. Actions are list_files, read_file, write_file, run_smoke, observe, submit. Never call shell, web, plugins, tools, or direct file-writing APIs. Read relevant public files before editing. Do not modify TASK.md, project.godot, evidence, tests, tools, or binary assets. Request a fresh post-patch observation before submit.\n"""

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest().upper()

def dotenv(path: Path) -> dict[str, str]:
    values = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1); values[key.strip()] = value.strip().strip('"').strip("'")
    return values

def safe_env() -> dict[str, str]:
    blocked = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.I)
    return {k: v for k, v in os.environ.items() if not blocked.search(k)}

def native_codex(explicit: Path | None) -> Path:
    if explicit: return explicit.resolve()
    if os.name == "nt":
        path = Path(os.environ.get("APPDATA", "")) / "npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
        if path.is_file(): return path.resolve()
    found = shutil.which("codex")
    if not found: raise SystemExit("Codex executable unavailable")
    return Path(found).resolve()

def files(workspace: Path) -> list[str]:
    return sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob("*") if p.is_file() and ".godot" not in p.parts and not p.name.endswith((".uid", ".import")))

def safe_path(workspace: Path, name: str) -> tuple[Path, str]:
    candidate = (workspace / name.replace("\\", "/").lstrip("/")).resolve()
    if workspace.resolve() not in candidate.parents and candidate != workspace.resolve(): raise ValueError("path escapes workspace")
    return candidate, candidate.relative_to(workspace.resolve()).as_posix()

def command(command: list[str], timeout: int, cwd: Path | None = None, env: dict | None = None, stdin: str | None = None, max_output: int | None = 12000) -> tuple[int, str, bool]:
    startup = subprocess.STARTUPINFO() if os.name == "nt" else None
    if startup: startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
    try:
        run = subprocess.run(command, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, startupinfo=startup)
        output = run.stdout + run.stderr
        return run.returncode, output if max_output is None else output[-max_output:], False
    except subprocess.TimeoutExpired as exc:
        output = str(exc.stdout or "")
        return 124, output if max_output is None else output[-max_output:], True

def extract(raw: str) -> tuple[str | None, str | None, dict]:
    thread = message = None; usage = {}
    for line in raw.splitlines():
        try: event = json.loads(line)
        except json.JSONDecodeError: continue
        if event.get("type") == "thread.started": thread = event.get("thread_id")
        item = event.get("item") if isinstance(event.get("item"), dict) else {}
        if event.get("type") == "item.completed" and item.get("type") == "agent_message": message = item.get("text")
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict): usage = event["usage"]
    return thread, message, usage

def json_action(text: str) -> dict:
    match = re.search(r"\{.*\}", text.strip(), re.S)
    if not match: raise ValueError("no JSON action")
    action = json.loads(match.group(0))
    required = {"action", "path", "content", "scenario", "summary"}
    if not isinstance(action, dict) or set(action) != required: raise ValueError("invalid action schema")
    return action

def capture(workspace: Path, task: dict, godot: Path, output: Path, scenario: str) -> dict:
    allowed = task["harness"]["allowed_scenarios"]
    if scenario and scenario not in allowed: raise ValueError("scenario is not public")
    output.parent.mkdir(parents=True, exist_ok=True)
    script = workspace / task["harness"]["observation_adapter"]
    code, log, timed = command([str(godot), "--headless", "--path", str(workspace), "--import"], 90)
    if code: return {"phase":"import","exit_code":code,"output":log,"timed_out":timed}
    selected = scenario or task["harness"]["default_scenario"]
    code, log, timed = command([str(godot), "--path", str(workspace), "--display-driver", "windows", "--rendering-driver", "opengl3", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy", "--position", "12000,12000", "--script", "res://" + str(script.relative_to(workspace)).replace("\\", "/"), "--", "--output", str(output.resolve()), "--scenario", selected], 120)
    return {"phase":"capture","exit_code":code,"output":log,"timed_out":timed,"image_exists":output.is_file(),"image_sha256":digest(output) if output.is_file() else None,"scenario":selected}

def provider_config(provider: str, secrets: dict[str, str], home: Path, base_override: str | None = None) -> tuple[str, str, dict[str, str], list[str]]:
    env = safe_env(); args: list[str] = []
    if provider == "local_codex": return "gpt-5.6-sol", "chatgpt_login", env, ["--model", "gpt-5.6-sol", "-c", "model_reasoning_effort=ultra"]
    if provider == "seed_evolving": key, model, name, base = "Seed_Agent_Plan_key", "doubao-seed-evolving", "volcengine-agent-plan", base_override or seed_responses_proxy.DEFAULT_UPSTREAM
    elif provider == "qwen38": key, model, name, base = "QWEN_API_KEY", "qwen3.8-max", "qwen38", secrets.get("QWEN_BASE_URL", "")
    else: raise SystemExit("provider must be local_codex, seed_evolving, or qwen38")
    if not secrets.get(key) or not base: raise SystemExit(f"{key} or provider base URL is unavailable")
    home.mkdir(parents=True); env[key] = secrets[key]; env["CODEX_HOME"] = str(home)
    summaries = "model_supports_reasoning_summaries = true\n" if provider == "seed_evolving" else ""
    # Seed can emit very large reasoning items.  Without an explicit custom-
    # provider context limit, a long controller thread can cross the upstream
    # window before Codex compacts it.  Keep reasoning policy unchanged, but
    # compact early enough to preserve the declared 30-action task budget.
    context = (
        "model_context_window = 256000\n"
        "model_auto_compact_token_limit = 180000\n"
        if provider == "seed_evolving" else ""
    )
    config = f'''model = "{model}"\nmodel_provider = "{name}"\n{summaries}{context}approval_policy = "never"\nsandbox_mode = "read-only"\n[model_providers.{name}]\nname = "{name}"\nbase_url = "{base}"\nenv_key = "{key}"\nwire_api = "responses"\nrequest_max_retries = 2\nstream_max_retries = 2\nstream_idle_timeout_ms = 180000\n'''
    (home / "config.toml").write_text(config, encoding="utf-8", newline="\n")
    extra = ["--model", model] + (["-c", "model_reasoning_effort=high"] if provider == "qwen38" else [])
    return model, provider, env, extra


def sanitized_codex_events(raw: str) -> str:
    """Retain lifecycle telemetry without archiving model or reasoning text."""
    output = []
    for line in raw.splitlines():
        try:
            source = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = {"type": source.get("type")}
        if source.get("type") == "thread.started":
            event["thread_id"] = source.get("thread_id")
        if source.get("type") == "turn.completed" and isinstance(source.get("usage"), dict):
            event["usage"] = source["usage"]
        item = source.get("item") if isinstance(source.get("item"), dict) else None
        if item:
            event["item_type"] = item.get("type")
            text = item.get("text")
            if isinstance(text, str):
                event["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        output.append(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(output) + ("\n" if output else "")


def _event_item_text(item: dict) -> str:
    """Return only text explicitly exposed by a Codex JSON item."""
    direct = item.get("text")
    if isinstance(direct, str):
        return direct
    parts = item.get("content")
    if not isinstance(parts, list):
        parts = item.get("summary")
    if not isinstance(parts, list):
        return ""
    return "\n".join(
        value["text"] for value in parts
        if isinstance(value, dict) and isinstance(value.get("text"), str)
    )


def full_response(raw: str) -> dict:
    """Extract model-visible text and reasoning summaries from Codex --json.

    This deliberately records only fields emitted by Codex.  It never invents
    a chain-of-thought when a provider supplies no reasoning summary.
    """
    messages: list[str] = []
    reasoning: list[str] = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event.get("item"), dict) else None
        if event.get("type") != "item.completed" or item is None:
            continue
        text = _event_item_text(item)
        if not text:
            continue
        if item.get("type") == "agent_message":
            messages.append(text)
        elif item.get("type") in {"reasoning", "reasoning_summary"}:
            reasoning.append(text)
    return {
        "assistant_text": messages[-1] if messages else "",
        "reasoning_content": "\n\n".join(reasoning),
        "reasoning_available": bool(reasoning),
    }


def controller_tool_schema(schema_path: Path) -> dict:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return {
        "type": "function",
        "function": {
            "name": "controller_action",
            "description": "Submit exactly one GameVisualFix Controller Action.",
            "parameters": schema,
        },
    }


def full_trace_document(task: dict, task_prompt: str, initial_images: list[Path], schema_path: Path, model: str, suite_id: str, turns: list[dict]) -> dict:
    """Create one attachment-style complete Agent episode for local inspection."""
    image_receipts = [{"path": path.name if path.parent.name == "evidence" else path.as_posix(), "sha256": digest(path)} for path in initial_images if path.is_file()]
    prompt: list[dict] = [
        {"role": "system", "content": [{"type": "text", "text": PROTOCOL}]},
        {"role": "user", "content": [{"type": "text", "text": task_prompt}]},
    ]
    last_assistant: dict | None = None
    for turn in turns:
        response = turn["response"]
        assistant = {
            "role": "assistant",
            "content": [{"type": "text", "text": response["assistant_text"]}],
            "reasoning_content": response["reasoning_content"],
            "reasoning_available": response["reasoning_available"],
            "signature": None,
            "tool_calls": [],
        }
        action = turn.get("action")
        if isinstance(action, dict):
            tool_call_id = f"controller-step-{turn['step']:02d}"
            assistant["tool_calls"] = [{
                "id": tool_call_id,
                "type": "function",
                "function": {"name": "controller_action", "arguments": json.dumps(action, ensure_ascii=False, separators=(",", ":"))},
            }]
            prompt.append(assistant)
            prompt.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": [{"type": "text", "text": json.dumps(turn.get("tool_result", {}), ensure_ascii=False, sort_keys=True)}],
            })
        else:
            prompt.append(assistant)
        last_assistant = assistant
    return {
        "task_id": task["task_id"],
        "prompt": prompt,
        "tools": [controller_tool_schema(schema_path)],
        "candidates": [[last_assistant]] if last_assistant else [],
        "meta": {
            "format": "gamevisualfix_full_agent_trajectory_v1",
            "experiment_suite_id": suite_id,
            "model": model,
            "initial_images": image_receipts,
            "candidate_semantics": "final actual assistant response; not a reference answer",
            "reasoning_semantics": "only provider/Codex-emitted reasoning summaries; unavailable summaries are empty",
            "raw_events": "stored only in the run-local ignored codex_raw directory",
        },
    }


def transport_failure(raw: str, code: int, timed_out: bool, thread: str | None) -> tuple[bool, str]:
    """Separate reproducible transport failures from valid model failures."""
    if timed_out:
        return False, "model_turn_timeout"
    lowered = raw.lower()
    markers = (
        "without active item", "error sending request", "stream disconnected",
        "connection refused", "connection reset", "dns error", "tls error",
        "upstream unavailable", "http status 401", "http status 403",
        "http status 429", "http status 500", "http status 502",
        "http status 503", "http status 504",
    )
    if any(marker in lowered for marker in markers):
        return True, "provider_or_codex_transport"
    if code and not thread:
        return True, "codex_process_failed_before_thread"
    return False, "missing_or_invalid_controller_action"


def public_canary_receipt(path: Path | None) -> dict | None:
    if path is None:
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    return {
        "path": path.resolve().relative_to(ROOT).as_posix() if ROOT in path.resolve().parents else path.name,
        "sha256": digest(path),
        "provider": report.get("provider"),
        "model": report.get("model"),
        "valid": report.get("valid"),
        "turns": report.get("turns"),
        "thread_started": report.get("thread_started"),
        "active_item_errors": report.get("active_item_errors"),
    }

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--task-id", required=True, choices=["task_001","task_002","task_003","task_004","task_005","task_006"]); p.add_argument("--provider", required=True); p.add_argument("--godot", required=True, type=Path); p.add_argument("--output", required=True, type=Path); p.add_argument("--env-file", type=Path, default=ROOT / ".env"); p.add_argument("--codex-exe", type=Path); p.add_argument("--canary-receipt", type=Path); p.add_argument("--suite-id", default="gamevisualfix_v2_1_seed_proxy_3x2"); p.add_argument("--full-trace", action="store_true", help="Save a local attachment-style JSONL trace with actual returned text and reasoning summaries."); args = p.parse_args()
    task_dir = ROOT / "benchmark" / args.task_id; task_json = task_dir / "task.json"; task = json.loads(task_json.read_text(encoding="utf-8"))
    # Task 001 predates v2's nested manifest. Preserve its frozen metadata and
    # supply the v2 dispatch contract here rather than rewriting the pilot spec.
    if "harness" not in task:
        task["harness"] = {"public_root":"public", "prompt":"public/TASK.md", "initial_visual":"public/evidence/initial_bug.png", "preload_images":["public/evidence/initial_bug.png", "public/assets/objective_arrow.png", "public/assets/threat_arrow.png"], "smoke_adapter":"tests/smoke.gd", "observation_adapter":"tools/capture.gd", "default_scenario":"BASELINE", "allowed_scenarios":["BASELINE","E","N","W","S","NE"], "private_evaluator":"private/evaluate.py", "action_budget":18, "observation_budget":3, "time_budget_seconds":1500}
    public = task_dir / task["harness"]["public_root"]
    output = args.output.resolve()
    if output.exists(): raise SystemExit("output must not already exist")
    output.mkdir(parents=True); workspace, artifacts, eventdir = output / "workspace", output / "artifacts", output / "codex_events"; artifacts.mkdir(); eventdir.mkdir()
    raw_eventdir = output / "codex_raw" if args.full_trace else None
    if raw_eventdir:
        raw_eventdir.mkdir()
    shutil.copytree(public, workspace, ignore=lambda _, names: {n for n in names if n in {".godot", ".git"} or n.endswith((".uid", ".import"))})
    code, _, _ = command(["git", "init", "-b", "main"], 30, workspace); command(["git", "add", "-A"], 30, workspace); command(["git", "commit", "-m", "baseline", "--no-gpg-sign"], 30, workspace)
    home = output / "control" / "codex_home"
    proxy = seed_responses_proxy.SeedResponsesProxy() if args.provider == "seed_evolving" else None
    if proxy:
        proxy.start()
    started = time.monotonic()
    thread = None
    observations = successful_observations = action_count = 0
    submitted = False
    result_status = "valid_canonical"
    invalid_reason = None
    terminal_status = "action_budget_exhausted"
    summary = ""
    trajectory = output / "trajectory.jsonl"
    full_turns: list[dict] = []
    pending_image = None
    session = None
    try:
        model, auth, env, extra = provider_config(args.provider, dotenv(args.env_file), home, proxy.base_url if proxy else None)
        # External providers use only this run-local config; ignoring it would
        # silently route the request to the default OpenAI provider.
        executable = native_codex(args.codex_exe)
        schema = ROOT / "harness" / "controller_action.schema.json"
        common = ["--json", "--ignore-rules", "--output-schema", str(schema), "--disable", "plugins", "--disable", "apps", "--disable", "multi_agent", "--disable", "browser_use", "--disable", "computer_use", "--disable", "shell_tool", "--disable", "skill_search", "--disable", "hooks", "-c", 'web_search="disabled"']
        prompt = PROTOCOL + "\nTASK:\n" + (workspace / "TASK.md").read_text(encoding="utf-8")
        input_mode = task["harness"].get("input_mode", "public_text_snapshot")
        if input_mode == "public_text_snapshot":
            for relative in files(workspace):
                path = workspace / relative
                if path.suffix.lower() in READABLE and relative != "TASK.md":
                    prompt += f"\n--- {relative} ---\n" + path.read_text(encoding="utf-8", errors="replace")[:30000]
        elif input_mode != "lazy_workspace":
            raise ValueError(f"unsupported input_mode: {input_mode}")
        if task["harness"].get("state_mode") == "controller_persistent":
            session = stateful_controller.StatefulObservation(task_dir, task, workspace, output / "control" / "state")
        initial = [workspace / value.replace("public/", "") for value in task["harness"].get("preload_images", [])]
        for step in range(1, int(task["harness"]["action_budget"]) + 1):
            if time.monotonic() - started > int(task["harness"]["time_budget_seconds"]):
                terminal_status = "model_run_timeout"
                summary = "run timeout"
                break
            if step == 1:
                initial_images = [str(value) for value in initial if value.is_file()]
                image_args = ["--image", *initial_images] if initial_images else []
                cmd = [str(executable), "exec", *common, "--sandbox", "read-only", *extra, *image_args, "-C", str(workspace), "-"]
            else:
                cmd = [str(executable), "exec", "resume", *common, *(["--image", str(pending_image)] if pending_image else []), str(thread), "-"]
            code, raw, timed = command(cmd, 240, workspace, env, prompt, max_output=None if args.full_trace else 12000)
            if raw_eventdir:
                (raw_eventdir / f"turn_{step:02d}.jsonl").write_text(raw, encoding="utf-8")
            (eventdir / f"turn_{step:02d}.jsonl").write_text(sanitized_codex_events(raw), encoding="utf-8")
            new_thread, message, usage = extract(raw)
            thread = thread or new_thread
            event = {"step": step, "exit_code": code, "timed_out": timed, "usage": usage}
            trace_turn = {"step": step, "response": full_response(raw)} if args.full_trace else None
            if code or not thread or not message:
                infrastructure, reason = transport_failure(raw, code, timed, thread)
                event["failure_class"] = reason
                terminal_status = reason
                summary = reason
                if infrastructure:
                    result_status = "invalid_infrastructure"
                    invalid_reason = reason
                trajectory.open("a", encoding="utf-8").write(json.dumps(event) + "\n")
                if trace_turn is not None:
                    trace_turn["tool_result"] = {"error": reason}
                    full_turns.append(trace_turn)
                break
            pending_image = None
            try:
                action = json_action(message)
                event["action"] = action
                action_count += 1
                name = action["action"]
                if name == "list_files":
                    result = {"files": files(workspace)}
                elif name == "read_file":
                    path, rel = safe_path(workspace, action["path"])
                    result = {"path": rel, "content": path.read_text(encoding="utf-8", errors="replace")[:50000]} if path.is_file() and path.suffix.lower() in READABLE else {"error": "not readable"}
                elif name == "write_file":
                    path, rel = safe_path(workspace, action["path"])
                    if rel in PROTECTED or rel.startswith(PROTECTED_PREFIXES) or path.suffix.lower() not in WRITABLE:
                        raise ValueError("protected/unwritable path")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(action["content"], encoding="utf-8", newline="\n")
                    result = {"written": rel, "sha256": digest(path)}
                elif name == "run_smoke":
                    code, log, timed = command([str(args.godot.resolve()), "--headless", "--path", str(workspace), "--script", "res://" + task["harness"]["smoke_adapter"]], 90)
                    result = {"exit_code": code, "output": log, "timed_out": timed}
                elif name == "observe":
                    if observations >= int(task["harness"]["observation_budget"]):
                        raise ValueError("observation budget exhausted")
                    observations += 1
                    pending_image = artifacts / f"observation_{observations}.png"
                    if session is not None:
                        result = session.observe(action["scenario"], pending_image, args.godot.resolve())
                    else:
                        result = capture(workspace, task, args.godot.resolve(), pending_image, action["scenario"])
                    if result["exit_code"] == 0 and result["image_exists"]:
                        successful_observations += 1
                    else:
                        pending_image = None
                elif name == "submit":
                    submitted = True
                    terminal_status = "submitted"
                    summary = action["summary"][:2000]
                    result = {"accepted": True}
                else:
                    raise ValueError("unknown action")
            except Exception as exc:
                result = {"error": str(exc)[:500]}
            event["tool_result"] = result
            trajectory.open("a", encoding="utf-8").write(json.dumps(event, ensure_ascii=False) + "\n")
            if trace_turn is not None:
                trace_turn["action"] = action if "action" in event else None
                trace_turn["tool_result"] = result
                full_turns.append(trace_turn)
            if submitted:
                break
            prompt = PROTOCOL + "\nController result:\n" + json.dumps(result, ensure_ascii=False)

        _, patch_text, _ = command(["git", "diff", "--no-ext-diff"], 30, workspace)
        (output / "final.patch").write_text(patch_text, encoding="utf-8")
        eval_dir = output / "evaluation"
        eval_dir.mkdir()
        evaluator = task_dir / task["harness"]["private_evaluator"]
        eval_code, _, eval_timed = command([sys.executable, str(evaluator), "--candidate", str(workspace), "--godot", str(args.godot.resolve()), "--output", str(eval_dir)], 300)
        evaluation_path = eval_dir / "evaluation.json"
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8")) if evaluation_path.is_file() else None
        if evaluation is None:
            result_status = "invalid_infrastructure"
            invalid_reason = invalid_reason or "private_evaluator_produced_no_result"
        codex_version = command([str(executable), "--version"], 15)[1].strip()
        godot_version = command([str(args.godot.resolve()), "--version"], 30)[1].strip()
        adapter_receipt = proxy.receipt() if proxy else None
        if adapter_receipt:
            (output / "adapter_receipt.json").write_text(json.dumps(adapter_receipt, indent=2) + "\n", encoding="utf-8")
        if session is not None:
            session.export_ledger(output / "state_ledger.jsonl")
        if args.full_trace:
            initial_paths = [workspace / value.replace("public/", "") for value in task["harness"].get("preload_images", [])]
            full_document = full_trace_document(task, (workspace / "TASK.md").read_text(encoding="utf-8"), initial_paths, schema, model, args.suite_id, full_turns)
            (output / "full_trajectory.jsonl").write_text(json.dumps(full_document, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest = {
            "schema_version": 3,
            "experiment_suite_id": args.suite_id,
            "task_id": task["task_id"],
            "provider": args.provider,
            "model": model,
            "authentication": auth,
            "mode": "codex_cli_controller_actions",
            "full_trace": args.full_trace,
            "input_mode": input_mode,
            "state_mode": task["harness"].get("state_mode", "stateless"),
            "transport_adapter": seed_responses_proxy.ADAPTER_NAME if proxy else None,
            "adapter_sha256": digest(Path(seed_responses_proxy.__file__)) if proxy else None,
            "normalization_counts": adapter_receipt["normalization_counts"] if adapter_receipt else {},
            "canary_receipt": public_canary_receipt(args.canary_receipt),
            "result_status": result_status,
            "invalid_reason": invalid_reason,
            "terminal_status": terminal_status,
            "codex_cli_version": codex_version,
            "codex_executable_sha256": digest(executable),
            "godot_version": godot_version,
            "godot_executable_sha256": digest(args.godot.resolve()),
            "input_hashes": {
                "task_manifest_sha256": digest(task_json),
                "task_prompt_sha256": digest(task_dir / task["harness"]["prompt"]),
                "controller_schema_sha256": digest(schema),
                "runner_sha256": digest(Path(__file__)),
                "public_tree_sha256": stateful_controller.tree_sha256(public),
                "controller_adapter_sha256": digest(task_dir / task["harness"]["controller_adapter"]) if task["harness"].get("controller_adapter") else None,
            },
            "valid_api": result_status == "valid_canonical",
            "submitted": submitted,
            "actions": action_count,
            "observations": observations,
            "successful_fresh_observations": successful_observations,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "thread_id": thread,
            "summary": {
                "bytes": len(summary.encode("utf-8")),
                "sha256": hashlib.sha256(summary.encode("utf-8")).hexdigest(),
            },
            "evaluation": evaluation,
            "evaluator_exit_code": eval_code,
            "evaluator_timed_out": eval_timed,
        }
        (output / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"result_status": result_status, "submitted": submitted, "score": evaluation.get("total") if evaluation else None, "task_success": evaluation.get("task_success") if evaluation else None}))
        return 0 if result_status == "valid_canonical" else 2
    finally:
        if proxy:
            proxy.close()
        if home.exists():
            shutil.rmtree(home, ignore_errors=True)
if __name__=="__main__": raise SystemExit(main())
