# GameVisualFix v3 Seed Full-Trace Replay

Suite: `gamevisualfix_v3_seed_fulltrace_partialfix_3x1`
Model: `doubao-seed-evolving` through Codex CLI Controller
Purpose: locally retain attachment-style complete Agent trajectories without changing the public v3 evaluation matrix.

## Result

| Task | Terminal | Actions | Fresh observations | F | V | R | Total | Success |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| T004 Glyph Atlas | submitted | 15 | 4 | 25 | 0 | 20 | 45 | false |
| T005 Checkpoint Mosaic | model turn timeout | 27 | 8 | 30 | 0 | 20 | 50 | false |
| T006 Mirrorstorm | submitted | 17 | 2 | 45 | 35 | 20 | 100 | true |

Task Success Rate is `1/3`; mean total score is `65.000`. These are new replay outcomes and must not be substituted for the original de-identified v3 results.

## Full trajectory location

Each local run directory contains:

- `full_trajectory.jsonl`: one attachment-style episode with `task_id`, `prompt`, `tools`, `candidates`, and `meta`;
- `codex_raw/turn_*.jsonl`: raw Codex JSON events for every turn;
- `trajectory.jsonl`, screenshots, state ledger, final patch, and evaluator output.

The exact directories are named in [the machine-readable replay scores](../results/v3_seed_fulltrace_replay_scores.json). They are intentionally ignored by Git. The exporter preserves only Seed/Codex-emitted reasoning summaries; it does not reconstruct hidden chain-of-thought.

## Transport lineage

Three early T004 local attempts are preserved as `invalid_infrastructure`. Seed emitted a completed assistant item without `response.completed`; Codex retried and the upstream then rejected the retry for a missing `partial` field. The proxy now explicitly forwards an absent `partial=false` and, only after an upstream-completed assistant item, synthesizes the missing terminal event. Unit tests cover both the successful compatibility path and the fail-closed incomplete-stream path. The repair did not change tasks, prompts, images, budgets, Oracle, evaluator, thresholds, or model configuration.

## Data handling

The full traces are local-only because they include model text and provider-returned reasoning summaries. Before reporting these results, all full-trace directories were scanned against exact locally configured credential values; no match was found. Public Git artifacts contain only this score summary and protocol, not the full text trajectory.
