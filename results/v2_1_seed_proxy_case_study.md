# GameVisualFix v2.1 Case Study

## Successful Seed trajectories

- T001: `read_file -> write_file -> observe -> run_smoke -> submit` (5 actions, 100/100).
- T002: `write_file -> observe -> run_smoke -> submit` (4 actions, 100/100).
- T003: `write_file -> observe -> submit` (3 actions, 100/100).

All three Seed runs produced a successful fresh observation and a complete hidden evaluation. No Controller action failed. During T002, two upstream streams introduced a standard `function_call` item outside the adapter's message/reasoning normalization scope; the proxy failed them closed and Codex's configured in-attempt stream retry recovered. This is transport recovery inside one canonical attempt, not an additional attempt.

## Valid Local failure on T002

The Local trajectory was `read_file -> observe -> observe -> submit`. It never issued `write_file`; both observations therefore showed the original state. All 18 hidden combinations of rotation, zoom and viewport rendered successfully, but objective direction dots remained below the 0.98 threshold in at least part of the matrix, so the gated score was 0/100. The repeated observation did not become recovery because it was not followed by a revised diagnosis or patch.

## Interpretation

The five 100/100 results create a strong ceiling effect. T002 Local demonstrates that the evaluator can still separate a plausible-looking, fully renderable but unfixed submission. With n=3 tasks and one attempt per pair, action count, time and token differences are descriptive only.
