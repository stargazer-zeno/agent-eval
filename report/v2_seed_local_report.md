# GameVisualFix v2 Restricted Evaluation Report (Historical)

> This report predates the Responses transport fix. Its Seed runs are infrastructure-invalid and do not enter current metrics. See [v2_1_seed_proxy_report.md](v2_1_seed_proxy_report.md) for the formal v2.1 results.

## Status

**Restricted result, not HR formal multi-model completion.**

- Suite: `gamevisualfix_v2_seed_local_3x2`
- Valid scored provider count: 1 (`gpt-5.6-sol` via Local Codex)
- Seed Evolving: unavailable for full controller task flow after two preserved infrastructure invalidations
- Qwen3.8-Max: skipped under user instruction

## Benchmark

GameVisualFix evaluates repair in three independent Godot 4.7.1 projects. Each task exports a public seed, prompt and visual evidence to a fresh Git workspace. The agent returns schema-checked Controller actions; only the Controller reads/writes public text, runs public smoke or captures a new image. The hidden evaluator runs only after submit.

| ID | Difficulty | Visual repair target | Hidden evaluation |
| --- | --- | --- | --- |
| T001 Twin Tracker Calibration | Easy | Two opposite-native arrow PNGs; Objective profile has an incorrect art-forward offset | 5 positions × 2 viewports; direction dot product plus threat/WASD/layout/asset regression |
| T002 Orbit Relay | Medium | Objective mixes world and camera coordinate spaces under rotated/zoomed camera | 3 rotations × 2 zooms × 3 viewports; direction, clamp and regression checks |
| T003 Echo Dash | Hard | Trail sample phase mixes tick position/facing around a reversal | 6 fixed replay paths × 30/60 physics ticks; temporal contact-sheet, lifecycle and regression checks |

Scoring is Functional 45 + Visual 35 + Regression 20. A total of 100 cannot compensate for a failed mandatory category; `task_success=true` requires all three.

## Harness and validity

The runner uses Codex non-interactive `exec` plus explicit-thread `resume`, read-only sandboxing, schema-bound Controller actions, run-local provider configuration and public-only workspaces. Codex documents `exec` as its scripting/non-interactive interface and `--image` as a variadic initial-image option; the runner groups all initial public images under that option. [OpenAI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

Valid canonical result means a new workspace/session completes without an infrastructure fault. A provider/CLI transport failure or bad Controller manifest is archived as `invalid_infrastructure`; a model's wrong patch, timeout or failed hidden test would instead be a valid model result and would not be rerun.

## Results

| Model | T001 | T002 | T003 | Success rate | Mean F/V/R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Local Codex `gpt-5.6-sol` | 100 ✓ | 100 ✓ | 100 ✓ | 3/3 | 45 / 35 / 20 |
| Seed `doubao-seed-evolving` | N/A | N/A | N/A | N/A | N/A |

Local elapsed times were 106.032 s (7 actions, 1 fresh observation), 120.547 s (6 actions, 1 observation), and 80.813 s (4 actions, 1 observation), respectively. Exact run hashes and all retained invalid lineage are in [`results/v2_seed_local_scores.json`](../results/v2_seed_local_scores.json).

## What the experiment shows

- The public workspace → controlled action → fresh visual evidence → hidden Oracle pipeline runs through all three task types.
- Local Codex achieved behaviorally correct repairs across static directional, camera-space, and fixed-tick temporal visual tasks in one valid attempt each.
- The task suite has a ceiling effect for this model in this one-run setting. It does not differentiate the model at the top end.

## What it does not show

- It is not a Seed-vs-Local or Qwen-vs-Local comparison: Seed's two full-task calls did not yield a Codex-resumable event stream, and Qwen was intentionally skipped.
- It provides no statistical significance, no best-of-N estimate, no recovery comparison, and no claim about production game repositories.
- T002's first Local Codex run had a Controller adapter path bug. Its 100/100 hidden score is deliberately excluded because the requested smoke/fresh observations were not executable; only the corrected rerun is scored.

## Continuation recommendation

To regain multi-model comparability, use a provider adapter that emits the Responses stream lifecycle required by the pinned Codex CLI (or explicitly freeze a separately validated compatible CLI/adapter suite), then rerun all providers from new workspaces under a new suite ID. To reduce ceiling effects, retain the existing deterministic Oracles but add branch-dependent, multi-file temporal repairs and report a pilot calibration set before changing thresholds after seeing outcomes.
