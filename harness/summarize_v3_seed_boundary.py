#!/usr/bin/env python3
"""Archive and summarize the frozen GameVisualFix v3 Seed boundary suite."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = "gamevisualfix_v3_seed_boundary_3x1"
SOURCE = ROOT / "experiments" / "v3_seed_boundary"
ARCHIVE = SOURCE / "archive"
TRAJECTORIES = ROOT / "trajectories" / "v3_seed_boundary"
SCORES = ROOT / "results" / "v3_seed_boundary_scores.json"

ATTEMPTS = [
    ("task_004_invalid_infrastructure", SOURCE / "task_004/seed_evolving_20260824", False),
    ("task_004_canonical", SOURCE / "task_004/seed_evolving_20260824_rerun1", True),
    ("task_005_invalid_infrastructure", SOURCE / "task_005/seed_evolving_20260824", False),
    ("task_005_canonical", SOURCE / "task_005/seed_evolving_20260824_rerun1", True),
    ("task_006_canonical", SOURCE / "task_006/seed_evolving_20260824", True),
]

STAGES = {
    "gamevisualfix_task_004": {
        "perception": "observed",
        "localization": "observed",
        "editing": "not_observed",
        "verification": "pre_patch_only",
        "state_tracking": "not_applicable",
        "recovery": "not_applicable",
        "failure_stage": "editing",
    },
    "gamevisualfix_task_005": {
        "perception": "observed",
        "localization": "observed",
        "editing": "observed",
        "verification": "observed_partial",
        "state_tracking": "partial_midpoint_only",
        "recovery": "observed",
        "failure_stage": "state_tracking_delayed_dependency",
    },
    "gamevisualfix_task_006": {
        "perception": "observed_initial_and_mirrored",
        "localization": "observed",
        "editing": "observed",
        "verification": "observed_hidden_complete",
        "state_tracking": "partial_no_interrupted_public_observation",
        "recovery": "not_applicable_first_patch_success",
        "failure_stage": None,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fingerprint(value: str) -> dict:
    data = value.encode("utf-8")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def safe_action(action: object) -> dict | None:
    if not isinstance(action, dict):
        return None
    output = {key: action.get(key) for key in ("action", "path", "scenario")}
    output["content"] = fingerprint(action.get("content", ""))
    output["summary"] = fingerprint(action.get("summary", ""))
    return output


def safe_result(result: object) -> dict | None:
    if not isinstance(result, dict):
        return None
    output = {}
    for key, value in result.items():
        if key in {"content", "output"} and isinstance(value, str):
            output[key] = fingerprint(value)
        elif key == "files" and isinstance(value, list):
            canonical = json.dumps(value, separators=(",", ":"))
            output["files"] = {"count": len(value), **fingerprint(canonical)}
        elif key in {
            "path", "written", "sha256", "error", "accepted", "phase", "exit_code",
            "timed_out", "image_exists", "image_sha256", "scenario", "phase_before",
            "phase_after", "advanced", "workspace_sha256", "state_sha256", "receipt_sha256",
        }:
            output[key] = value
    return output


def normalize(source: Path, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    lines = []
    events = []
    for line in source.read_text(encoding="utf-8").splitlines():
        raw = json.loads(line)
        event = {
            "step": raw.get("step"),
            "exit_code": raw.get("exit_code"),
            "timed_out": raw.get("timed_out"),
            "failure_class": raw.get("failure_class"),
            "usage": raw.get("usage") if isinstance(raw.get("usage"), dict) else {},
            "action": safe_action(raw.get("action")),
            "tool_result": safe_result(raw.get("tool_result")),
        }
        canonical = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        current = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
        chained = {**event, "previous_hash": previous, "event_hash": current}
        lines.append(json.dumps(chained, ensure_ascii=False, separators=(",", ":")))
        events.append(event)
        previous = current
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    receipt = {
        "source_sha256": sha256(source),
        "normalized_sha256": sha256(destination),
        "events": len(events),
        "final_chain_hash": previous,
        "excludes": ["provider_stream", "reasoning", "model_text", "file_content", "submit_summary_text"],
    }
    destination.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return {"receipt": receipt, "events": events}


def token_totals(events: list[dict]) -> dict:
    keys = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    return {key: sum(int((event.get("usage") or {}).get(key) or 0) for event in events) for key in keys}


def copy_if_present(source: Path, destination: Path) -> None:
    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def copy_lifecycle(source: Path, destination: Path) -> None:
    """Copy controller lifecycle telemetry without a reusable thread id."""
    lines = []
    for line in source.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        event.pop("thread_id", None)
        lines.append(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def archive_attempt(name: str, source: Path, canonical: bool) -> dict:
    run_path = source / "run.json"
    trajectory_path = source / "trajectory.jsonl"
    if not run_path.is_file() or not trajectory_path.is_file():
        raise SystemExit(f"missing attempt artifact: {source}")
    run = json.loads(run_path.read_text(encoding="utf-8"))
    if run.get("experiment_suite_id") != SUITE:
        raise SystemExit(f"suite mismatch: {run_path}")
    if canonical and run.get("result_status") != "valid_canonical":
        raise SystemExit(f"non-valid attempt selected as canonical: {run_path}")
    if not canonical and run.get("result_status") != "invalid_infrastructure":
        raise SystemExit(f"lineage attempt was not infrastructure-invalid: {run_path}")

    destination = ARCHIVE / name
    destination.mkdir(parents=True, exist_ok=True)
    trajectory_destination = TRAJECTORIES / name / "trajectory.jsonl"
    normalized = normalize(trajectory_path, trajectory_destination)
    for artifact in sorted((source / "artifacts").glob("*")):
        if artifact.is_file() and artifact.suffix.lower() in {".png", ".json"}:
            copy_if_present(artifact, TRAJECTORIES / name / "artifacts" / artifact.name)
    copy_if_present(source / "state_ledger.jsonl", TRAJECTORIES / name / "state_ledger.jsonl")
    patch_source = source / "final.patch"
    if patch_source.is_file():
        # `git diff` can append Windows line-ending warnings on stderr because
        # the runner captures both streams.  Preserve the diff, not diagnostics.
        patch_lines = [line for line in patch_source.read_text(encoding="utf-8", errors="replace").splitlines() if not line.startswith("warning:")]
        (destination / "final.patch").write_text("\n".join(patch_lines) + ("\n" if patch_lines else ""), encoding="utf-8")
    copy_if_present(source / "evaluation/evaluation.json", destination / "evaluation.json")
    copy_if_present(source / "adapter_receipt.json", destination / "adapter_receipt.json")
    for event in sorted((source / "codex_events").glob("*.jsonl")):
        copy_lifecycle(event, destination / "lifecycle_events" / event.name)

    evaluation = run.get("evaluation") or {}
    receipt = {
        "schema_version": 1,
        "experiment_suite_id": SUITE,
        "attempt_name": name,
        "canonical": canonical,
        "task_id": run.get("task_id"),
        "provider": run.get("provider"),
        "model": run.get("model"),
        "result_status": run.get("result_status"),
        "invalid_reason": run.get("invalid_reason"),
        "terminal_status": run.get("terminal_status"),
        "submitted": run.get("submitted"),
        "actions": run.get("actions"),
        "observations": run.get("observations"),
        "successful_fresh_observations": run.get("successful_fresh_observations"),
        "elapsed_seconds": run.get("elapsed_seconds"),
        "token_telemetry": token_totals(normalized["events"]),
        "token_telemetry_semantics": "sum of provider-reported per-turn usage; descriptive, not a cross-provider budget",
        "scores": {
            "functional": (evaluation.get("functional") or {}).get("score"),
            "visual": (evaluation.get("visual") or {}).get("score"),
            "regression": (evaluation.get("regression") or {}).get("score"),
            "total": evaluation.get("total"),
            "task_success": evaluation.get("task_success"),
        },
        "input_hashes": run.get("input_hashes"),
        "canary_receipt": run.get("canary_receipt"),
        "codex_cli_version": run.get("codex_cli_version"),
        "codex_executable_sha256": run.get("codex_executable_sha256"),
        "godot_version": run.get("godot_version"),
        "godot_executable_sha256": run.get("godot_executable_sha256"),
        "transport_adapter": run.get("transport_adapter"),
        "adapter_sha256": run.get("adapter_sha256"),
        "normalized_trajectory": normalized["receipt"],
        "stage_labels": STAGES.get(run.get("task_id")) if canonical else None,
        "source_run_sha256": sha256(run_path),
    }
    (destination / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    TRAJECTORIES.mkdir(parents=True, exist_ok=True)
    attempts = [archive_attempt(*specification) for specification in ATTEMPTS]
    canonical = [attempt for attempt in attempts if attempt["canonical"]]
    task_ids = {attempt["task_id"] for attempt in canonical}
    expected = {"gamevisualfix_task_004", "gamevisualfix_task_005", "gamevisualfix_task_006"}
    if task_ids != expected or len(canonical) != 3:
        raise SystemExit(f"canonical matrix mismatch: {sorted(task_ids)}")
    scores = {
        "schema_version": 1,
        "mode": "canonical_single_model",
        "experiment_suite_id": SUITE,
        "dataset_task_count": 3,
        "model_count": 1,
        "attempt_policy": "one valid canonical attempt per task; one fresh rerun only after infrastructure invalid",
        "primary_metric": "task_success_rate",
        "runs": canonical,
        "invalid_infrastructure_lineage": [attempt for attempt in attempts if not attempt["canonical"]],
        "aggregate": {
            "provider": "seed_evolving",
            "model": "doubao-seed-evolving",
            "task_successes": sum(bool(attempt["scores"]["task_success"]) for attempt in canonical),
            "task_success_rate": round(sum(bool(attempt["scores"]["task_success"]) for attempt in canonical) / 3, 6),
            "mean_scores": {
                key: round(sum(attempt["scores"][key] for attempt in canonical) / 3, 3)
                for key in ("functional", "visual", "regression", "total")
            },
            "actions_total": sum(attempt["actions"] for attempt in canonical),
            "fresh_observations_total": sum(attempt["successful_fresh_observations"] for attempt in canonical),
            "wall_time_seconds_total": round(sum(attempt["elapsed_seconds"] for attempt in canonical), 3),
            "token_telemetry": {
                key: sum(attempt["token_telemetry"][key] for attempt in canonical)
                for key in canonical[0]["token_telemetry"]
            },
            "token_telemetry_semantics": "sum of provider-reported per-turn usage; descriptive, not a cross-provider budget",
        },
        "interpretation_limits": [
            "three synthetic tasks",
            "one model and one valid attempt per task",
            "no statistical significance or general model ranking",
            "task_006 success indicates remaining ceiling in the public architecture contract",
        ],
    }
    SCORES.write_text(json.dumps(scores, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    canaries = []
    for path in (
        SOURCE / "canary_seed_20260824_run2/canary.json",
        SOURCE / "canary_seed_20260824_run3/canary.json",
        SOURCE / "canary_seed_20260824_run4/canary.json",
    ):
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            canaries.append({"source": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "valid": value.get("valid"), "turns": len(value.get("turns") or []), "active_item_errors": value.get("active_item_errors"), "codex_version": value.get("codex_version"), "codex_sha256": value.get("codex_sha256")})
    (SOURCE / "canary_receipts.json").write_text(json.dumps({"schema_version": 1, "receipts": canaries}, indent=2) + "\n", encoding="utf-8")
    (SOURCE / "manifest.json").write_text(json.dumps({"schema_version": 1, "experiment_suite_id": SUITE, "dataset_index": "benchmark/dataset_v3.json", "scores": "results/v3_seed_boundary_scores.json", "attempts": [{key: value for key, value in attempt.items() if key in {"attempt_name", "canonical", "task_id", "result_status", "invalid_reason", "terminal_status", "scores", "source_run_sha256"}} for attempt in attempts]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"suite": SUITE, "canonical_runs": len(canonical), "task_successes": scores["aggregate"]["task_successes"], "mean_total": scores["aggregate"]["mean_scores"]["total"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
