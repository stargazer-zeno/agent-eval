# Task 005 validation

Gate status: **PASS**. The task and state graph were frozen before any v3 model run.

## Reproducibility and state gate

- Godot 4.7.1 clean-copy import, public smoke, and hidden-window Compatibility captures passed.
- In the unmodified workspace, `ADVANCE` at `LOBBY` returned `advanced=false` and remained at `LOBBY`.
- In the Reference workspace, the trusted external Controller produced the audited sequence `LOBBY -> RESTORED_MIDPOINT -> POST_ELEVATOR -> FINAL_RESTORE`; `REPLAY_CURRENT` did not advance state.
- The state file and hash-chain ledger stayed outside the Agent workspace. The private evaluator always started from its own clean replay cases.
- Bug State scored `20/100` (`F=0, V=0, R=20`) and failed in three independent runs.
- Reference State scored `100/100` and passed in three independent runs.
- Representative Lobby hashes were stable across the three runs:
  - Bug: `dd121cacaa62203400af1d37aaf962648dde315744374be15b0c232ca6ce29b6`
  - Reference: `fb5897cdfe6b5b9b9fc5b9fb1aa172c4d597a24b75b4c1326eca77716ca6b752`

## Shortcut and equivalence checks

| Candidate | F | V | R | Total | Success |
| --- | ---: | ---: | ---: | ---: | --- |
| Lobby route only | 15 | 0 | 20 | 35 | false |
| Lobby route plus migration only | 30 | 0 | 20 | 50 | false |
| Non-byte-identical equivalent repair | 45 | 35 | 20 | 100 | true |

Deleting old progress or bypassing stage transitions cannot satisfy the three independent checkpoint gates. Showing all hints or forging the renderer cannot compensate for failed Functional gates. Seal replacement, missing required nodes, non-permutation tables, and altered assets fail Regression. Evaluation is behavioral and does not compare a fixed diff.

## Visual necessity and leak audit

- The Lobby PNG is the only public source of the four seal bit patterns and their recorded-to-door correspondence. The public code uses anonymous indices and unrelated filenames.
- Later stages expose different persisted/current rows. The final HUD order deliberately depends on the Lobby ordering rather than repeating it in text.
- Replacing the image with a caption such as "four different seals" leaves at least 24 plausible permutations, so it cannot determine the route patch.
- A public-tree scan found no Oracle arrays, private stage answers, reference patch, or Controller implementation. The Controller receives private expected rows only outside the workspace and returns a PNG plus non-answer-bearing transition receipt.

## Scope and limitations

The prototype models migration through deterministic tables rather than a production serialization backend. This makes the Ground Truth and partial credit reproducible while retaining the delayed visual dependency. A successful or failed single Seed run remains a case study, not a population estimate.
