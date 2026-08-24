# Task 004 validation

Gate status: **PASS**. The task was frozen and validated before any v3 model run.

## Reproducibility gate

- Godot 4.7.1 clean-copy import, public smoke, and all four declared observation scenarios passed with the Windows hidden-window Compatibility renderer.
- The unmodified Bug State scored `25/100` (`F=5, V=0, R=20`) and `task_success=false` in three independent evaluator runs.
- The Reference State scored `100/100` (`F=45, V=35, R=20`) and `task_success=true` in three independent evaluator runs.
- The representative hidden render hash was stable across all three runs in each state:
  - Bug: `c4e507d75dfb381166a22b28d9ae3a45aaf7a39a15ef764a86ed2ef1264afebe`
  - Reference: `e9fc5d02ef82b4191368df9e07c58c045dd3c70cd932a9ec67850e6549396247`
- All 36 hidden combinations (six rotations, two parity states, and three viewports) completed deterministically.

## Shortcut and equivalence checks

| Candidate | F | V | R | Total | Success |
| --- | ---: | ---: | ---: | ---: | --- |
| Mapping-only repair | 25 | 0 | 20 | 45 | false |
| Transform-only repair | 25 | 0 | 20 | 45 | false |
| World glyph asset replacement | 5 | 0 | 0 | 5 | false |
| Non-byte-identical equivalent repair | 45 | 35 | 20 | 100 | true |

Fixed rotations, fixed viewports, mirror disabling, hidden markers, moved landmarks, and glyph replacement are additionally rejected by the cross-product cases, required-node checks, or frozen asset hashes. The evaluator compares behavior rather than a reference diff.

## Visual necessity and leak audit

- Without the two raster inputs, the public binding contains eight behaviorally plausible glyph assignments and the transform code has two plausible composition orders. Text identifiers deliberately do not encode visual identity.
- A normal caption such as "eight different cyan and yellow symbols" omits the 5x5 bit patterns, reflected handedness, and cross-image identity correspondences required to choose a unique patch.
- A public-package scan found no Oracle order, reference patch, private evaluator data, or answer-bearing filename. Generated capture sidecars were removed from the public evidence package.
- Both initial PNGs remain task-essential inputs; model-produced captions are not treated as ground truth.

## Scope and limitations

This is a deterministic synthetic prototype, not evidence of population-level model performance. Semantic telemetry is emitted by the same rendering path and is used for exact identity/geometry checks; the PNG is independently required to be nontrivial and stable. The Gate establishes benchmark validity, not model difficulty.
