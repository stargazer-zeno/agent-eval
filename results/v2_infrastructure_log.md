# GameVisualFix v2 infrastructure log

## Qwen3.8-Max / Task 001 — stopped before canonical score

Two fresh Qwen Task 001 sessions were retained as `invalid_infrastructure`; neither is a model result and neither contributes to a score.

1. `qwen38_20260821_run1`: the Codex CLI exposed `multi_agent`. The model invoked it, after which the thread did not return a final Controller action. The Harness was corrected to explicitly disable multi-agent, browser, computer, shell, skills, hooks, plugins, and apps.
2. `qwen38_20260821_run2`: the corrected CLI received a valid structured `read_file` action, but its external Qwen event stream omitted `thread.started` / a thread ID. Since the protocol requires explicit `exec resume <thread-id>` and prohibits `--last` / ephemeral replacement, the Controller could not safely continue.

Both failures are separately reproducible Controller/CLI/provider transport failures rather than wrong patches, task failures, evaluator failures, or model-scored outcomes. The pre-task Qwen canary still passed image input, strict schema, and resume; the issue manifests with the full task prompt/event stream.

Per the frozen v2 protocol, a second infrastructure invalidation stops the automatic matrix. The old Qwen3-VL-Plus result remains in the current branch because no valid Qwen3.8-Max Task 001 canonical attempt exists. The remaining eight planned canonical runs were not started.
