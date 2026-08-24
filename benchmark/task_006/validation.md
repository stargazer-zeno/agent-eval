# Task 006 validation

Gate status: **PASS**. The phase graph and evaluator were frozen before any v3 model run.

## Reproducibility and phase gate

- Godot 4.7.1 clean-copy import, public smoke, and hidden-window Compatibility contact-sheet generation passed.
- `REPLAY_CURRENT` kept `CALM` unchanged. Two `STEP_FIGHT` actions advanced the unmodified Bug workspace through `CALM -> MIRRORED_ENRAGED -> INTERRUPTED_RESUME`; progression does not conceal later failures.
- Each successful observation produced phase-before/after, advance flag, workspace/state/image hashes, timestamp, and a hash-chain receipt outside the Agent workspace.
- Bug State scored `20/100` (`F=0, V=0, R=20`) and failed in three runs; Reference State scored `100/100` and passed in three runs.
- The representative 30-tick CALM hashes were stable across all repeats:
  - Bug: `7a7d0592ef8c255460d5880ae59120c582a031176023dc92ef11abc1fc6a35a5`
  - Reference: `8afe80fa1dc50991975fe8127e51314b27231b234b0c9f9c55d74f9a48c7a2f5`
- The hidden cross-product covers three phases, two tick rates, and two directions (12 deterministic contact sheets).

## Shortcut and equivalence checks

| Candidate | F | V | R | Total | Success |
| --- | ---: | ---: | ---: | ---: | --- |
| Initial ordering/position/facing only | 25 | 0 | 20 | 45 | false |
| Parity-only change | 0 | 0 | 20 | 20 | false |
| Hidden telegraph | 0 | 0 | 0 | 0 | false |
| Non-byte-identical equivalent repair | 45 | 35 | 20 | 100 | true |

Freezing a phase cannot affect the evaluator's independent phase replays. Disabling mirror, clearing the pool, extending lifetime, hard-coding a phase, or forging the public capture cannot compensate for the immutable-payload and lifecycle Functional gates. Visibility, damage timing, duration, capacity, lifetime, and required nodes are Regression invariants.

## Visual necessity and leak audit

- The trace exposes tick and signal ordering only. The initial contact sheet uniquely provides the trail's signed side of motion, tip direction, reversal boundary, and frame-local relationship to the boss.
- A caption such as "the purple trail is briefly on the wrong side" cannot preserve the per-frame handedness and timing needed to distinguish pre-commit sampling, stale facing, or live-state rendering.
- Later mirrored and interrupted sheets contain phase-specific evidence that is not present in the initial Prompt or trace.
- A public-tree scan found no source-field-to-mask mapping, required Boolean values, private Oracle, reference patch, or Controller implementation. The generic capture tool receives a non-explanatory diagnostic mask from the trusted external Controller.

## Scope and limitations

The contact sheets are deterministic synthetic renderings of a lifecycle contract rather than captures from a full boss implementation. This preserves exact diagnostics and replay stability, but conclusions from one run must remain a case study. Recovery is credited only if a fresh later-phase receipt is followed by a materially changed edit; a complete first repair yields `Recovery=N/A`.
