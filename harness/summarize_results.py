#!/usr/bin/env python3
"""Create sanitized aggregate results and hash-chained trajectories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "experiments" / "task_001"
TRAJECTORY_ROOT = ROOT / "trajectories" / "task_001"
RESULTS = ROOT / "results"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def evaluation_for(run_dir: Path, manifest: dict) -> dict | None:
    path = run_dir / "evaluation" / "evaluation.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    value = manifest.get("evaluation")
    return value if isinstance(value, dict) else None


def failure_class(manifest: dict) -> str | None:
    if manifest.get("valid_api"):
        return None
    if manifest.get("failure_class"):
        return str(manifest["failure_class"])
    summary = str(manifest.get("summary", "")).lower()
    if "403" in summary:
        return "invalid_auth"
    if "timeout" in summary:
        return "invalid_provider_timeout"
    return "invalid_api"


def normalize_trajectory(run_dir: Path, provider: str) -> tuple[str | None, int, int, int]:
    source = run_dir / "trajectory.jsonl"
    destination = TRAJECTORY_ROOT / provider / run_dir.name
    destination.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        (destination / "raw.jsonl").write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
        )
    previous = "0" * 64
    count = 0
    tokens = 0
    actions = 0
    normalized_lines = []
    if source.is_file():
        for raw in source.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            action = event.get("action") if isinstance(event.get("action"), dict) else None
            usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
            normalized = {
                "step": event.get("step"),
                "action": action.get("action") if action else None,
                "path": action.get("path") if action else None,
                "tool_result": event.get("tool_result"),
                "api_error": event.get("api_error"),
                "usage": usage,
                "model_text_sha256": digest_bytes(str(event.get("model_text", "")).encode("utf-8")),
                "previous_hash": previous,
            }
            canonical = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            previous = digest_bytes(canonical)
            normalized["event_hash"] = previous
            normalized_lines.append(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")))
            count += 1
            actions += 1 if action else 0
            reported = usage.get("total_tokens")
            if reported is None:
                reported = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
            tokens += int(reported or 0)
    normalized_path = destination / "normalized.jsonl"
    normalized_path.write_text(
        "\n".join(normalized_lines) + ("\n" if normalized_lines else ""),
        encoding="utf-8", newline="\n",
    )
    artifacts = run_dir / "artifacts"
    screenshots = 0
    if artifacts.is_dir():
        image_dest = destination / "screenshots"
        image_dest.mkdir(exist_ok=True)
        for image in sorted(artifacts.glob("*.png")):
            shutil.copy2(image, image_dest / image.name)
            screenshots += 1
    receipt = {
        "schema_version": 1, "event_count": count, "action_count": actions,
        "total_reported_tokens": tokens, "successful_screenshot_files": screenshots,
        "chain_head": previous if count else None,
        "raw_sha256": digest_file(destination / "raw.jsonl") if source.is_file() else None,
        "normalized_sha256": digest_file(normalized_path),
    }
    (destination / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return receipt["chain_head"], actions, tokens, screenshots


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    runs = []
    for run_dir in sorted(path for path in RUNS_ROOT.iterdir() if path.is_dir()):
        manifest_path = run_dir / "run.json"
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        provider = str(manifest.get("provider"))
        evaluation = evaluation_for(run_dir, manifest)
        chain, action_count, tokens, screenshots = normalize_trajectory(run_dir, provider)
        valid = bool(manifest.get("valid_api")) and bool(manifest.get("submitted"))
        runs.append({
            "run_id": run_dir.name,
            "provider": provider,
            "model": manifest.get("model"),
            "valid_model_result": valid,
            "comparison_eligible": bool(manifest.get("comparison_eligible", True)) if valid else False,
            "attempt_role": manifest.get("attempt_role"),
            "failure_class": failure_class(manifest),
            "submitted": bool(manifest.get("submitted")),
            "action_count": action_count,
            "fresh_screenshot_files": screenshots,
            "reported_total_tokens_sum": tokens,
            "elapsed_seconds": manifest.get("elapsed_seconds"),
            "functional": evaluation.get("functional", {}).get("score") if valid and evaluation else None,
            "visual": evaluation.get("visual", {}).get("score") if valid and evaluation else None,
            "regression": evaluation.get("regression", {}).get("score") if valid and evaluation else None,
            "total": evaluation.get("total") if valid and evaluation else None,
            "task_success": evaluation.get("task_success") if valid and evaluation else None,
            "diagnostic_baseline_total": evaluation.get("total") if not valid and evaluation else None,
            "trajectory_chain_head": chain,
            "run_manifest_sha256": digest_file(manifest_path),
            "patch_sha256": digest_file(run_dir / "final.patch") if (run_dir / "final.patch").is_file() else None,
        })
    aggregate = {
        "schema_version": 1,
        "mode": "multi_provider_pilot",
        "generated_at": "2026-08-21",
        "dataset": {"task_count": 1, "hidden_primary_cases": 10, "task_id": "gamevisualfix_task_001"},
        "metrics": {
            "functional_max": 45, "visual_max": 35, "regression_max": 20, "total_max": 100,
            "task_success_rule": "build_integrity_gate AND functional=45 AND visual=35 AND regression=20",
            "invalid_runs_excluded_from_model_score_comparison": True,
        },
        "runs": runs,
        "summary": {
            "configured_providers": len({r["provider"] for r in runs}),
            "valid_model_results": sum(1 for r in runs if r["valid_model_result"]),
            "comparison_eligible_valid_results": sum(1 for r in runs if r["valid_model_result"] and r["comparison_eligible"]),
            "successful_tasks": sum(1 for r in runs if r["task_success"] is True),
        },
    }
    (RESULTS / "scores.json").write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
