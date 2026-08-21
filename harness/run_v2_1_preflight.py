#!/usr/bin/env python3
"""Run model-free public and private preflight checks for all v2.1 tasks."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

try:
    import run_codex_eval as core
except ImportError:
    from harness import run_codex_eval as core


def task_config(task_dir: Path) -> dict:
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    if "harness" not in task:
        task["harness"] = {
            "public_root": "public",
            "prompt": "public/TASK.md",
            "smoke_adapter": "tests/smoke.gd",
            "observation_adapter": "tools/capture.gd",
            "default_scenario": "BASELINE",
            "allowed_scenarios": ["BASELINE", "E", "N", "W", "S", "NE"],
            "private_evaluator": "private/evaluate.py",
        }
    return task


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    godot = args.godot.resolve()
    records = []
    all_valid = True
    for task_id in ("task_001", "task_002", "task_003"):
        task_dir = core.ROOT / "benchmark" / task_id
        task = task_config(task_dir)
        task_output = output / task_id
        workspace = task_output / "workspace"
        evaluation_dir = task_output / "evaluation"
        task_output.mkdir()
        shutil.copytree(task_dir / task["harness"]["public_root"], workspace, ignore=lambda _, names: {name for name in names if name in {".godot", ".git"} or name.endswith((".uid", ".import"))})
        import_code, _, import_timed = core.command([str(godot), "--headless", "--path", str(workspace), "--import"], 90)
        smoke_code, _, smoke_timed = core.command([str(godot), "--headless", "--path", str(workspace), "--script", "res://" + task["harness"]["smoke_adapter"]], 90)
        capture_path = task_output / "capture.png"
        capture = core.capture(workspace, task, godot, capture_path, task["harness"]["default_scenario"])
        evaluation_dir.mkdir()
        evaluator = task_dir / task["harness"]["private_evaluator"]
        eval_code, _, eval_timed = core.command([sys.executable, str(evaluator), "--candidate", str(workspace), "--godot", str(godot), "--output", str(evaluation_dir)], 300)
        evaluation_path = evaluation_dir / "evaluation.json"
        valid = import_code == 0 and smoke_code == 0 and capture.get("exit_code") == 0 and capture.get("image_exists") and eval_code == 0 and evaluation_path.is_file()
        all_valid = all_valid and bool(valid)
        records.append({
            "task_id": task["task_id"],
            "valid": bool(valid),
            "input_hashes": {
                "task_manifest_sha256": core.digest(task_dir / "task.json"),
                "task_prompt_sha256": core.digest(task_dir / task["harness"]["prompt"]),
                "smoke_adapter_sha256": core.digest(task_dir / task["harness"]["public_root"] / task["harness"]["smoke_adapter"]),
                "capture_adapter_sha256": core.digest(task_dir / task["harness"]["public_root"] / task["harness"]["observation_adapter"]),
                "private_evaluator_sha256": core.digest(evaluator),
            },
            "import": {"exit_code": import_code, "timed_out": import_timed},
            "smoke": {"exit_code": smoke_code, "timed_out": smoke_timed},
            "capture": {key: value for key, value in capture.items() if key != "output"},
            "evaluator": {"exit_code": eval_code, "timed_out": eval_timed, "result_exists": evaluation_path.is_file(), "result_sha256": core.digest(evaluation_path) if evaluation_path.is_file() else None},
        })
    report = {
        "schema_version": 1,
        "valid": all_valid,
        "godot_version": core.command([str(godot), "--version"], 30)[1].strip(),
        "godot_sha256": core.digest(godot),
        "tasks": records,
    }
    (output / "preflight.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": all_valid, "tasks": [{"task_id": item["task_id"], "valid": item["valid"]} for item in records]}))
    return 0 if all_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
