# v3 Seed long-session transport diagnosis

The first Task 004 attempt is retained as `invalid_infrastructure`. It completed 12 Controller actions and four fresh observations, then the thirteenth `exec resume` failed at the provider/Codex transport boundary.

The decisive receipt is quantitative: turn 12 reported 208,023 input tokens and 31,688 output tokens. Replaying that output plus the next Controller result would cross the 256k custom-provider context window before another useful action. The task evaluator itself completed normally (`exit_code=0`) and returned 45/100, so capture and evaluation were not the cause.

The corrective change declares the Seed context window to Codex and sets `model_auto_compact_token_limit=180000`. It does not change the model, reasoning policy, task Prompt, action/observation/time budgets, task semantics, or evaluator. A unit fixture verifies the run-local config and confirms that the credential value is not written to it. The failed attempt remains preserved, and only one fresh Task 004 rerun is permitted.
