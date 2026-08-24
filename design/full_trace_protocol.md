# GameVisualFix Full-Trace Replay Protocol

## Purpose and scope

`gamevisualfix_v3_seed_fulltrace_3x1` is a separate replay suite. It reruns the frozen v3 Tasks 004–006 with `doubao-seed-evolving` through the same Codex Controller Harness, but records local complete dialogue-style episodes for inspection. It does not replace the public, de-identified v3 canonical matrix.

## Record format

Each `full_trajectory.jsonl` has one JSON object and follows the structural convention of the supplied training-style example:

```text
task_id + prompt[] + tools[] + candidates[] + meta
```

`prompt[]` contains the controller system protocol, task text, each actual assistant response, and the matching Controller tool receipt. Assistant messages include `content`, `tool_calls`, `reasoning_content`, `reasoning_available`, and `signature`. `signature` is `null` because Codex CLI does not emit a reusable signature. `candidates` contains the final actual assistant response only as a convenience snapshot; it is explicitly not a reference answer or training label.

## Reasoning boundary

The exporter records only a reasoning summary if the Seed/Codex Responses stream explicitly emits one. It writes an empty `reasoning_content` and `reasoning_available=false` otherwise. It never synthesizes hidden chain-of-thought, reconstructs omitted reasoning, or converts token telemetry into text.

## Storage and safety

The full trace and raw Codex JSON events stay under the ignored local path `experiments/v3_seed_fulltrace/`. They are not committed or pushed automatically. Before any manual sharing, scan the exact credential values from the local env file and review task text, tool receipts, and model output. The tracked v3 archive remains the source for reproducible public claims because it excludes model text, provider streams, reasoning, and run-local sessions.

## Evaluation policy

Tasks, prompts, images, Oracle, thresholds, action budget (30), observation budget (8), and time budget (40 minutes) remain frozen. Each replay is a new full-trace attempt under a distinct suite ID, not a replacement for its original canonical attempt. A full trace may support qualitative analysis, but the previously reported v3 scores remain the only original v3 matrix.
