# GameVisualFix v2.1 Seed vs Local Codex

Suite: `gamevisualfix_v2_1_seed_proxy_3x2`. Only the six `valid_canonical` runs below enter metrics.

| Task | Provider | F | V | R | Total | Success | Actions | Fresh obs | Seconds |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| T001 | seed_evolving | 45 | 35 | 20 | 100 | yes | 5 | 1 | 105.969 |
| T001 | local_codex | 45 | 35 | 20 | 100 | yes | 8 | 1 | 76.016 |
| T002 | seed_evolving | 45 | 35 | 20 | 100 | yes | 4 | 1 | 89.188 |
| T002 | local_codex | 0 | 0 | 0 | 0 | no | 4 | 2 | 107.485 |
| T003 | seed_evolving | 45 | 35 | 20 | 100 | yes | 3 | 1 | 111.875 |
| T003 | local_codex | 45 | 35 | 20 | 100 | yes | 6 | 1 | 80.172 |

Seed completed 3/3 tasks (100% success, mean 100.0); Local completed 2/3 (66.7%, mean 66.667). Seed used 12 actions and 307.032s; Local used 18 actions and 263.673s. These descriptive results come from one attempt per pair and do not establish statistical superiority.

The sole failure is T002 Local: it read the source, requested two fresh baseline observations, made no write, and submitted. The hidden 18-case matrix therefore remained in the injected bug state and scored 0/45 Functional, 0/35 Visual, 0/20 Regression. It is a valid model failure, not an infrastructure invalidation.

Seed's previous v2 stream failures remain historical lineage. The v2.1 adapter restored protocol compatibility without changing model output, task prompts, Controller schema, budgets, or evaluators.
