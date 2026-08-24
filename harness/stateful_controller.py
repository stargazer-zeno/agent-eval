#!/usr/bin/env python3
"""Trusted task-local observation state for GameVisualFix v3.

The state file lives outside the Agent workspace.  A task controller receives
only the current public state and returns a rendered PNG plus its next state.
Every successful observation is chained so the transition history can be
audited without exposing hidden evaluator data.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if any(part in {".git", ".godot", "__pycache__"} for part in path.parts):
            continue
        if path.name.endswith((".uid", ".import")):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


class StatefulObservation:
    def __init__(self, task_dir: Path, task: dict, workspace: Path, control_dir: Path) -> None:
        self.task_dir = task_dir.resolve()
        self.task = task
        self.workspace = workspace.resolve()
        self.control_dir = control_dir.resolve()
        self.control_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.control_dir / "session_state.json"
        self.ledger_path = self.control_dir / "state_ledger.jsonl"
        initial = task["harness"].get("initial_state", "STATELESS")
        self.state_path.write_text(
            json.dumps({"phase": initial, "step": 0, "data": {}}, indent=2) + "\n",
            encoding="utf-8",
        )
        self.previous_hash = "0" * 64

    def observe(self, scenario: str, output: Path, godot: Path, timeout: int = 180) -> dict:
        allowed = self.task["harness"]["allowed_scenarios"]
        selected = scenario or self.task["harness"]["default_scenario"]
        if selected not in allowed:
            raise ValueError("scenario is not public")
        adapter = self.task_dir / self.task["harness"]["controller_adapter"]
        if not adapter.is_file():
            raise FileNotFoundError(f"controller adapter is missing: {adapter}")
        result_path = self.control_dir / "adapter_result.json"
        if result_path.exists():
            result_path.unlink()
        command = [
            sys.executable,
            str(adapter),
            "--workspace", str(self.workspace),
            "--godot", str(godot.resolve()),
            "--state", str(self.state_path),
            "--scenario", selected,
            "--output", str(output.resolve()),
            "--result", str(result_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=self.task_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
            timed_out = False
            log = completed.stdout[-12000:]
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as error:
            timed_out = True
            log = str(error.stdout or "")[-12000:]
            exit_code = 124
        if exit_code or not result_path.is_file():
            return {
                "phase": "controller_adapter",
                "exit_code": exit_code,
                "timed_out": timed_out,
                "output": log,
                "image_exists": output.is_file(),
                "scenario": selected,
            }
        result = json.loads(result_path.read_text(encoding="utf-8"))
        required = {"phase_before", "phase_after", "advanced", "next_state"}
        if not required.issubset(result) or not isinstance(result["next_state"], dict):
            raise ValueError("controller adapter returned an invalid state result")
        state_text = json.dumps(result["next_state"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.state_path.write_text(json.dumps(result["next_state"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt = {
            "scenario": selected,
            "phase_before": result["phase_before"],
            "phase_after": result["phase_after"],
            "advanced": bool(result["advanced"]),
            "workspace_sha256": tree_sha256(self.workspace),
            "state_sha256": hashlib.sha256(state_text.encode("utf-8")).hexdigest(),
            "image_sha256": sha256(output) if output.is_file() else None,
            "image_exists": output.is_file(),
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        canonical = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        receipt["previous_sha256"] = self.previous_hash
        receipt["event_sha256"] = hashlib.sha256((self.previous_hash + canonical).encode("utf-8")).hexdigest()
        self.previous_hash = receipt["event_sha256"]
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
        return {
            "phase": "capture",
            "exit_code": 0,
            "timed_out": False,
            "output": log,
            "image_exists": output.is_file(),
            "image_sha256": receipt["image_sha256"],
            "scenario": selected,
            "phase_before": receipt["phase_before"],
            "phase_after": receipt["phase_after"],
            "advanced": receipt["advanced"],
            "workspace_sha256": receipt["workspace_sha256"],
            "state_sha256": receipt["state_sha256"],
            "receipt_sha256": receipt["event_sha256"],
        }

    def export_ledger(self, destination: Path) -> None:
        destination.write_text(
            self.ledger_path.read_text(encoding="utf-8") if self.ledger_path.is_file() else "",
            encoding="utf-8",
        )
