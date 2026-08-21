#!/usr/bin/env python3
"""Build a credential-free, restricted-suite summary from preserved run manifests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = "gamevisualfix_v2_seed_local_3x2"
RUNS = ROOT / "experiments" / "v2_seed_local"
OUT = ROOT / "results" / "v2_seed_local_scores.json"
TRAJECTORIES = ROOT / "trajectories" / "v2_seed_local"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def scores(run: dict) -> dict:
    evaluation = run.get("evaluation") or {}
    return {
        "functional": (evaluation.get("functional") or {}).get("score"),
        "visual": (evaluation.get("visual") or {}).get("score"),
        "regression": (evaluation.get("regression") or {}).get("score"),
        "total": evaluation.get("total"),
        "task_success": evaluation.get("task_success"),
    }


def main() -> None:
    records = []
    for manifest_path in sorted(RUNS.glob("task_*/*/run.json")):
        run = json.loads(manifest_path.read_text(encoding="utf-8"))
        relative = manifest_path.relative_to(ROOT).as_posix()
        invalid_reason = None
        if run["provider"] == "seed_evolving":
            invalid_reason = "provider_stream_missing_thread_and_controller_action"
        elif manifest_path.parent.name == "local_codex_20260821_run1" and run["task_id"] == "gamevisualfix_task_002":
            invalid_reason = "controller_manifest_adapter_path"
        records.append({
            "run_path": relative,
            "run_sha256": sha256(manifest_path),
            "task_id": run["task_id"],
            "provider": run["provider"],
            "model": run["model"],
            "status": "invalid_infrastructure" if invalid_reason else "valid_canonical",
            "invalid_reason": invalid_reason,
            "valid_api": run.get("valid_api"),
            "submitted": run.get("submitted"),
            "actions": sum(1 for _ in (manifest_path.parent / "trajectory.jsonl").open(encoding="utf-8")),
            "fresh_observations": run.get("observations"),
            "elapsed_seconds": run.get("elapsed_seconds"),
            "scores": scores(run),
        })
        normalized_dir = TRAJECTORIES / manifest_path.parent.parent.name / run["provider"] / manifest_path.parent.name
        normalized_dir.mkdir(parents=True, exist_ok=True)
        previous = "0" * 64
        output_lines = []
        trajectory_path = manifest_path.parent / "trajectory.jsonl"
        for raw_line in trajectory_path.read_text(encoding="utf-8").splitlines():
            source = json.loads(raw_line)
            # Keep only Controller-observable data; discard model text and any
            # raw provider stream. This is sufficient for stage analysis while
            # avoiding an archive of hidden reasoning.
            event = {key: source.get(key) for key in ("step", "exit_code", "timed_out", "usage", "action", "tool_result", "failure_class") if key in source}
            canonical = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            event["previous_sha256"] = previous
            event["event_sha256"] = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
            previous = event["event_sha256"]
            output_lines.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
        (normalized_dir / "controller_actions.hashchain.jsonl").write_text("\n".join(output_lines) + "\n", encoding="utf-8")
        (normalized_dir / "receipt.json").write_text(json.dumps({"source": relative.replace("run.json", "trajectory.jsonl"), "source_sha256": sha256(trajectory_path), "terminal_hash": previous}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    valid = [item for item in records if item["status"] == "valid_canonical"]
    local = [item for item in valid if item["provider"] == "local_codex"]
    summary = {
        "suite_id": SUITE,
        "mode": "restricted_provider_matrix",
        "intended_providers": ["seed_evolving", "local_codex"],
        "scored_providers": ["local_codex"],
        "task_count": 3,
        "scoring": {"functional": 45, "visual": 35, "regression": 20, "task_success": "all mandatory categories pass"},
        "validity_rule": "Only status=valid_canonical contributes to metrics. Invalid infrastructure runs are retained below.",
        "provider_availability": {
            "seed_evolving": "blocked_after_two_task_001_transport_invalidations",
            "local_codex": "available",
        },
        "runs": records,
        "aggregate": {
            "local_codex": {
                "valid_runs": len(local),
                "task_success_rate": f"{sum(bool(x['scores']['task_success']) for x in local)}/{len(local)}" if local else "0/0",
                "mean_total": sum(x["scores"]["total"] for x in local) / len(local) if local else None,
                "mean_functional": sum(x["scores"]["functional"] for x in local) / len(local) if local else None,
                "mean_visual": sum(x["scores"]["visual"] for x in local) / len(local) if local else None,
                "mean_regression": sum(x["scores"]["regression"] for x in local) / len(local) if local else None,
            },
            "seed_evolving": {"valid_runs": 0, "task_success_rate": "N/A", "reason": "provider availability blocker; not a model score"},
        },
        "interpretation_boundary": "This artifact reports one available provider across three tasks; it is not a Seed-vs-Local comparison or a three-model matrix.",
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "valid_runs": len(valid), "all_runs": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
