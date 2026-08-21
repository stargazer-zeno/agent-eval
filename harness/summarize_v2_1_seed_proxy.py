#!/usr/bin/env python3
"""Validate and summarize the GameVisualFix v2.1 Seed/Local canonical suite."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = "gamevisualfix_v2_1_seed_proxy_3x2"
RUNS = ROOT / "experiments" / "v2_1_seed_proxy"
SCORES = ROOT / "results" / "v2_1_seed_proxy_scores.json"
COMPARISON = ROOT / "results" / "v2_1_seed_proxy_comparison.md"
CASE_STUDY = ROOT / "results" / "v2_1_seed_proxy_case_study.md"
REPORT = ROOT / "report" / "v2_1_seed_proxy_report.md"
TRAJECTORIES = ROOT / "trajectories" / "v2_1_seed_proxy"
TASK_ORDER = ("task_001", "task_002", "task_003")
PROVIDER_ORDER = ("seed_evolving", "local_codex")

TASKS = {
    "gamevisualfix_task_001": {
        "label": "T001", "difficulty": "Easy", "name": "Signal Courier",
        "goal": "Calibrate two HUD trackers so each points at its own moving world target.",
        "oracle": "5 directions x 2 viewports, pixel direction/geometry checks, live updates, layout and asset integrity.",
        "hidden_cases": 10,
    },
    "gamevisualfix_task_002": {
        "label": "T002", "difficulty": "Medium", "name": "Orbit Relay",
        "goal": "Correct a camera-space edge indicator while preserving the other tracker and camera behavior.",
        "oracle": "3 camera rotations x 2 zoom levels x 3 viewports; objective direction, threat visibility and clean captures.",
        "hidden_cases": 18,
    },
    "gamevisualfix_task_003": {
        "label": "T003", "difficulty": "Hard", "name": "Echo Dash",
        "goal": "Keep a temporal trail on the correct side through direction changes and interruptions.",
        "oracle": "6 fixed-tick replays x 2 physics rates, each with an 8-frame visual contact sheet.",
        "hidden_cases": 12,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_fingerprint(value: str) -> dict:
    data = value.encode("utf-8")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def safe_action(action: object) -> dict | None:
    if not isinstance(action, dict):
        return None
    output = {key: action.get(key) for key in ("action", "path", "scenario")}
    if isinstance(action.get("content"), str):
        output["content"] = text_fingerprint(action["content"])
    if isinstance(action.get("summary"), str):
        output["summary"] = text_fingerprint(action["summary"])
    return output


def safe_tool_result(result: object) -> dict | None:
    if not isinstance(result, dict):
        return None
    output = {}
    for key, value in result.items():
        if key in {"content", "output"} and isinstance(value, str):
            output[key] = text_fingerprint(value)
        elif key == "files" and isinstance(value, list):
            output[key] = value
        elif key in {"path", "written", "sha256", "error", "accepted", "phase", "exit_code", "timed_out", "image_exists", "image_sha256", "scenario"}:
            output[key] = value
    return output


def normalized_trajectory(source: Path, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    output_lines = []
    events = 0
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        raw = json.loads(raw_line)
        event = {
            "step": raw.get("step"),
            "exit_code": raw.get("exit_code"),
            "timed_out": raw.get("timed_out"),
            "usage": raw.get("usage") if isinstance(raw.get("usage"), dict) else {},
            "action": safe_action(raw.get("action")),
            "tool_result": safe_tool_result(raw.get("tool_result")),
            "failure_class": raw.get("failure_class"),
        }
        canonical = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
        chained = {**event, "previous_hash": previous, "event_hash": event_hash}
        output_lines.append(json.dumps(chained, ensure_ascii=False, separators=(",", ":")))
        previous = event_hash
        events += 1
    destination.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    receipt = {
        "source_path": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(source),
        "normalized_path": destination.relative_to(ROOT).as_posix(),
        "normalized_sha256": sha256(destination),
        "events": events,
        "final_chain_hash": previous,
        "excludes": ["provider_stream", "reasoning", "model_text", "file_content", "submit_summary_text"],
    }
    destination.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def last_usage(events: list[dict]) -> dict:
    for event in reversed(events):
        if isinstance(event.get("usage"), dict) and event["usage"]:
            return event["usage"]
    return {}


def score_record(manifest_path: Path) -> dict:
    run = json.loads(manifest_path.read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (manifest_path.parent / "trajectory.jsonl").read_text(encoding="utf-8").splitlines()]
    evaluation = run.get("evaluation") or {}
    task = TASKS[run["task_id"]]
    destination = TRAJECTORIES / task["label"].lower() / run["provider"] / "trajectory.jsonl"
    receipt = normalized_trajectory(manifest_path.parent / "trajectory.jsonl", destination)
    adapter_path = manifest_path.parent / "adapter_receipt.json"
    adapter_diagnostics = None
    if adapter_path.is_file():
        adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        adapter_diagnostics = {
            "path": adapter_path.relative_to(ROOT).as_posix(),
            "sha256": sha256(adapter_path),
            "streams": adapter.get("streams"),
            "fail_closed_streams": adapter.get("errors"),
            "completed_events": (adapter.get("upstream_event_counts") or {}).get("response.completed", 0),
            "done_markers": (adapter.get("upstream_event_counts") or {}).get("[DONE]", 0),
        }
    return {
        "task": task["label"],
        "task_id": run["task_id"],
        "difficulty": task["difficulty"],
        "provider": run["provider"],
        "model": run["model"],
        "result_status": run["result_status"],
        "invalid_reason": run.get("invalid_reason"),
        "terminal_status": run.get("terminal_status"),
        "submitted": run.get("submitted"),
        "actions": run.get("actions"),
        "action_sequence": [event["action"]["action"] for event in events if isinstance(event.get("action"), dict)],
        "observations_requested": run.get("observations"),
        "successful_fresh_observations": run.get("successful_fresh_observations"),
        "elapsed_seconds": run.get("elapsed_seconds"),
        "token_usage": last_usage(events),
        "scores": {
            "functional": (evaluation.get("functional") or {}).get("score"),
            "visual": (evaluation.get("visual") or {}).get("score"),
            "regression": (evaluation.get("regression") or {}).get("score"),
            "total": evaluation.get("total"),
            "task_success": evaluation.get("task_success"),
        },
        "normalization_counts": run.get("normalization_counts", {}),
        "run_path": manifest_path.relative_to(ROOT).as_posix(),
        "run_sha256": sha256(manifest_path),
        "trajectory_receipt": receipt,
        "canary_receipt": run.get("canary_receipt"),
        "input_hashes": run.get("input_hashes"),
        "codex_cli_version": run.get("codex_cli_version"),
        "codex_executable_sha256": run.get("codex_executable_sha256"),
        "godot_version": run.get("godot_version"),
        "godot_executable_sha256": run.get("godot_executable_sha256"),
        "transport_adapter": run.get("transport_adapter"),
        "adapter_sha256": run.get("adapter_sha256"),
        "adapter_diagnostics": adapter_diagnostics,
    }


def validate(records: list[dict]) -> None:
    expected = {(task, provider) for task in ("T001", "T002", "T003") for provider in PROVIDER_ORDER}
    actual = {(record["task"], record["provider"]) for record in records}
    if len(records) != 6 or actual != expected:
        raise SystemExit(f"canonical matrix mismatch: expected {sorted(expected)}, got {sorted(actual)}")
    for record in records:
        if record["result_status"] != "valid_canonical":
            raise SystemExit(f"non-canonical run entered metrics: {record['run_path']}")
        if not record["canary_receipt"] or not record["canary_receipt"].get("valid"):
            raise SystemExit(f"missing valid canary: {record['run_path']}")
    for task in ("T001", "T002", "T003"):
        pair = [record for record in records if record["task"] == task]
        for key in ("task_manifest_sha256", "task_prompt_sha256", "controller_schema_sha256"):
            if len({record["input_hashes"][key] for record in pair}) != 1:
                raise SystemExit(f"input hash mismatch for {task}: {key}")
    if len({record["codex_executable_sha256"] for record in records}) != 1:
        raise SystemExit("Codex executable drift detected")
    if len({record["godot_executable_sha256"] for record in records}) != 1:
        raise SystemExit("Godot executable drift detected")


def aggregate(records: list[dict], provider: str) -> dict:
    selected = [record for record in records if record["provider"] == provider]
    token_keys = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")
    return {
        "valid_runs": len(selected),
        "task_successes": sum(bool(record["scores"]["task_success"]) for record in selected),
        "task_success_rate": sum(bool(record["scores"]["task_success"]) for record in selected) / len(selected),
        "mean_scores": {key: round(sum(record["scores"][key] for record in selected) / len(selected), 3) for key in ("functional", "visual", "regression", "total")},
        "elapsed_seconds": {"total": round(sum(record["elapsed_seconds"] for record in selected), 3), "mean": round(sum(record["elapsed_seconds"] for record in selected) / len(selected), 3)},
        "actions": {"total": sum(record["actions"] for record in selected), "mean": round(sum(record["actions"] for record in selected) / len(selected), 3)},
        "successful_fresh_observations": sum(record["successful_fresh_observations"] for record in selected),
        "token_usage": {key: sum((record["token_usage"].get(key) or 0) for record in selected) for key in token_keys},
        "adapter_fail_closed_streams": sum((record.get("adapter_diagnostics") or {}).get("fail_closed_streams", 0) for record in selected),
    }


def historical_lineage() -> list[dict]:
    score_path = ROOT / "results" / "v2_seed_local_scores.json"
    lineage = []
    if score_path.is_file():
        old = json.loads(score_path.read_text(encoding="utf-8"))
        lineage.extend({
            "suite_id": old.get("suite_id"),
            "path": item.get("run_path"),
            "status": item.get("status"),
            "reason": item.get("invalid_reason"),
        } for item in old.get("runs", []) if item.get("status") == "invalid_infrastructure")
    for path in sorted((ROOT / "experiments" / "v2_1_canary").glob("seed_evolving_20260821*/canary.json")):
        canary = json.loads(path.read_text(encoding="utf-8"))
        if not canary.get("valid"):
            lineage.append({
                "suite_id": "v2.1_adapter_development_canary",
                "path": path.relative_to(ROOT).as_posix(),
                "status": "diagnostic_canary_failed",
                "reason": f"active_item_errors={canary.get('active_item_errors')}",
            })
    return lineage


def markdown_table(records: list[dict]) -> str:
    rows = ["| Task | Provider | F | V | R | Total | Success | Actions | Fresh obs | Seconds |", "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |"]
    for task in ("T001", "T002", "T003"):
        for provider in PROVIDER_ORDER:
            record = next(item for item in records if item["task"] == task and item["provider"] == provider)
            score = record["scores"]
            rows.append(f"| {task} | {provider} | {score['functional']:.0f} | {score['visual']:.0f} | {score['regression']:.0f} | {score['total']:.0f} | {'yes' if score['task_success'] else 'no'} | {record['actions']} | {record['successful_fresh_observations']} | {record['elapsed_seconds']:.3f} |")
    return "\n".join(rows)


def write_reports(records: list[dict], aggregates: dict, lineage: list[dict]) -> None:
    table = markdown_table(records)
    seed = aggregates["seed_evolving"]
    local = aggregates["local_codex"]
    comparison = f"""# GameVisualFix v2.1 Seed vs Local Codex

Suite: `{SUITE}`. Only the six `valid_canonical` runs below enter metrics.

{table}

Seed completed 3/3 tasks (100% success, mean 100.0); Local completed 2/3 (66.7%, mean 66.667). Seed used {seed['actions']['total']} actions and {seed['elapsed_seconds']['total']:.3f}s; Local used {local['actions']['total']} actions and {local['elapsed_seconds']['total']:.3f}s. These descriptive results come from one attempt per pair and do not establish statistical superiority.

The sole failure is T002 Local: it read the source, requested two fresh baseline observations, made no write, and submitted. The hidden 18-case matrix therefore remained in the injected bug state and scored 0/45 Functional, 0/35 Visual, 0/20 Regression. It is a valid model failure, not an infrastructure invalidation.

Seed's previous v2 stream failures remain historical lineage. The v2.1 adapter restored protocol compatibility without changing model output, task prompts, Controller schema, budgets, or evaluators.
"""
    COMPARISON.write_text(comparison, encoding="utf-8")
    case_study = f"""# GameVisualFix v2.1 Case Study

## Successful Seed trajectories

- T001: `read_file -> write_file -> observe -> run_smoke -> submit` (5 actions, 100/100).
- T002: `write_file -> observe -> run_smoke -> submit` (4 actions, 100/100).
- T003: `write_file -> observe -> submit` (3 actions, 100/100).

All three Seed runs produced a successful fresh observation and a complete hidden evaluation. No Controller action failed. During T002, two upstream streams introduced a standard `function_call` item outside the adapter's message/reasoning normalization scope; the proxy failed them closed and Codex's configured in-attempt stream retry recovered. This is transport recovery inside one canonical attempt, not an additional attempt.

## Valid Local failure on T002

The Local trajectory was `read_file -> observe -> observe -> submit`. It never issued `write_file`; both observations therefore showed the original state. All 18 hidden combinations of rotation, zoom and viewport rendered successfully, but objective direction dots remained below the 0.98 threshold in at least part of the matrix, so the gated score was 0/100. The repeated observation did not become recovery because it was not followed by a revised diagnosis or patch.

## Interpretation

The five 100/100 results create a strong ceiling effect. T002 Local demonstrates that the evaluator can still separate a plausible-looking, fully renderable but unfixed submission. With n=3 tasks and one attempt per pair, action count, time and token differences are descriptive only.
"""
    CASE_STUDY.write_text(case_study, encoding="utf-8")
    dataset_rows = "\n".join(
        f"| {value['label']} | {value['difficulty']} | {value['goal']} | {value['oracle']} | {value['hidden_cases']} |"
        for value in TASKS.values()
    )
    report = f"""# GameVisualFix v2.1 数据集设计与模型测试报告

## 结论

`{SUITE}` 已完整执行。Seed Evolving 三题均形成可 resume、可观察、可提交、可隐藏评分的端到端结果，三题均为 100/100；Local Codex 在 T001/T003 为 100/100，在 T002 为有效 0/100。六个结果均为 `valid_canonical`，本 suite 没有正式 attempt 被标记为 `invalid_infrastructure`。

## 数据集设计

| Task | 难度标签 | 公开目标 | 隐藏 Oracle | 隐藏 case |
| --- | --- | --- | --- | ---: |
{dataset_rows}

公开侧只提供任务描述、初始视觉证据、可读项目和有限场景 observation；参考补丁、case 矩阵与 evaluator 留在 Agent workspace 之外。三题统一以 Functional 45、Visual 35、Regression 20 计分，三项满分才算 task success。任务 prompt、Controller schema、Godot/Codex 二进制和同题输入 hash 在汇总时再次校验。

## Transport 修复

旧 v2 Seed 调用因 Agent Plan 的 Responses added envelope 缺少标准空容器，Codex 0.149 对 delta 报 `without active item`。v2.1 在 `127.0.0.1` 随机端口运行标准库代理，向固定 Seed 上游转发请求，为 message/reasoning item 和 part 补齐 `content`、`summary`、`text`、`annotations`、`logprobs`、`output` 等生命周期容器，统一生成单调 `sequence_number`，并在缺失时补 added/done。代理不改写 delta、reasoning、usage、HTTP 状态或完成状态；未知/畸形流直接失败。实现依据为 [official OpenAI Responses streaming events](https://developers.openai.com/api/reference/resources/responses/streaming-events)。

单元测试覆盖完整流、缺 text item、缺 reasoning item、multi-item、缺 done、HTTP error、畸形 SSE、单调序号、Seed 不完整 envelope 与凭据不落诊断。正式运行前，Harness fixture self-test、三题 import/smoke/capture/evaluator preflight、Seed 与 Local 三图/长 prompt/两次 resume canary 全部通过。成功 Seed canary 的 active-item error 为 0。

## 正式结果

{table}

Seed：成功率 3/3，平均 100.0，{seed['actions']['total']} actions，{seed['successful_fresh_observations']} 次成功 fresh observation，总耗时 {seed['elapsed_seconds']['total']:.3f}s。Local：成功率 2/3，平均 {local['mean_scores']['total']:.3f}，{local['actions']['total']} actions，{local['successful_fresh_observations']} 次成功 fresh observation，总耗时 {local['elapsed_seconds']['total']:.3f}s。

最终 turn 的累计 usage 汇总：Seed input {seed['token_usage']['input_tokens']}、cached input {seed['token_usage']['cached_input_tokens']}、output {seed['token_usage']['output_tokens']}、reasoning output {seed['token_usage']['reasoning_output_tokens']}；Local input {local['token_usage']['input_tokens']}、cached input {local['token_usage']['cached_input_tokens']}、output {local['token_usage']['output_tokens']}、reasoning output {local['token_usage']['reasoning_output_tokens']}。这些是 Provider/Codex 返回的线程累计 telemetry，不代表计费核算。

## 过程与 Case Study

Seed 三题都完成补丁、fresh observation 和 submit，且没有 Controller action error。T002 中有 2 条上游流出现代理不负责猜测的 `function_call` item，代理按协议 fail closed，Codex 在同一 attempt 的既有 stream retry 内恢复并完成 4 个 Controller turn；这属于可观察的 transport recovery，不是额外 attempt。Local T002 的 `read_file -> observe -> observe -> submit` 没有写入补丁；隐藏 18-case 渲染链正常，但 bug 未修复，Functional/Visual/Regression 均为 0。这一结果按预注册规则保留，没有重跑。

## Lineage 与有效性

旧 `gamevisualfix_v2_seed_local_3x2` 的两次 Seed T001 transport invalid 和一次 Local T002 adapter-path invalid 均保留为历史，不进入 v2.1 指标。v2.1 adapter 开发中前两次 synthetic Seed canary 分别记录 active-item error，第三次修复后通过；它们不是正式任务 attempt。历史/诊断 lineage 共 {len(lineage)} 条，详见机器矩阵的 `excluded_lineage`。

## 局限

每个模型只有 3 个合成 Godot 任务、每对只有 1 次有效 attempt，样本量不足以做显著性、稳定性或广泛泛化结论。五个满分产生 ceiling effect，Easy/Medium/Hard 是数据集设计标签，不等于对任一模型校准后的难度。Local T002 的单次失败也不能单独证明稳定的模型差异。运行使用单一机器、账户、Godot 4.7.1 与 Codex 0.149.0；外推到其他引擎、真实大型仓库或 Provider 版本需重新验证。

## 产物与安全

机器矩阵位于 `results/v2_1_seed_proxy_scores.json`；去 reasoning、去正文的 action/observation hash-chain 位于 `trajectories/v2_1_seed_proxy/`；对比与 Case Study 位于 `results/`。run-local Codex home 已回收，代理 receipt 只含事件类型、字段名、计数和结构哈希；`.env`、Authorization、API key、原始 Provider delta/reasoning 均不进入报告或 Git。
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    manifest_paths = sorted(RUNS.glob("task_*/*/run.json"))
    for path in manifest_paths:
        run = json.loads(path.read_text(encoding="utf-8"))
        if run.get("schema_version") != 3 or run.get("experiment_suite_id") != SUITE:
            raise SystemExit(f"unexpected manifest in v2.1 run root: {path}")
    records = [score_record(path) for path in manifest_paths]
    validate(records)
    records.sort(key=lambda item: (("T001", "T002", "T003").index(item["task"]), PROVIDER_ORDER.index(item["provider"])))
    aggregates = {provider: aggregate(records, provider) for provider in PROVIDER_ORDER}
    lineage = historical_lineage()
    normalization = collections.Counter()
    for record in records:
        if record["provider"] == "seed_evolving":
            normalization.update(record["normalization_counts"])
    output = {
        "schema_version": 1,
        "suite_id": SUITE,
        "validity_rule": "metrics include only schema-v3 valid_canonical runs with a valid task-shaped canary",
        "canonical_runs": records,
        "aggregate": aggregates,
        "seed_normalization_counts": dict(sorted(normalization.items())),
        "excluded_lineage": lineage,
        "limitations": [
            "one valid attempt per Task/Provider pair",
            "three synthetic Godot tasks per model",
            "five of six runs at the 100-point ceiling",
            "single machine/account/version configuration",
            "descriptive comparison only; no statistical inference",
        ],
    }
    SCORES.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_reports(records, aggregates, lineage)
    print(json.dumps({"suite_id": SUITE, "canonical_runs": len(records), "aggregate": aggregates}, ensure_ascii=False))


if __name__ == "__main__":
    main()
