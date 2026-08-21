# Task 002 Renderer Incident — Resolved 2026-08-21

## Status

**Resolved before model exposure.** This record is retained for reproducibility; Task 002 passed its complete Gate after the configuration repair described below.

## Evidence

The clean public project imports and its headless smoke test exits successfully. However, the required Windows hidden-window OpenGL Compatibility capture process exits with `3221225477` (`CrashHandlerException: signal 11`) on this host's AMD Radeon driver before `tools/capture.gd` can write an image. The private suite uses the same renderer path and fails identically.

## Root cause and repair

The initial drawing implementation used a CanvasItem triangle. Replacing it with lines and circles did not resolve the crash. The actual cause was that Task 002 lacked the already-validated Godot project settings used by Task 001: disabled window stretch, disabled VSync, texture defaults, and fixed physics tick configuration. Adding these renderer-stability settings restored capture without changing task semantics, scoring threshold, prompt, Oracle condition, or engine.

## Resolution evidence

- The public Seed now has a fresh initial runtime PNG and remains in the bug state (`OBJECTIVE_SPACE_MODE = "mixed"`).
- Bug state: three independent 18-case runs each produced `0/100`, `task_success=false`.
- Oracle state: the documented one-line behavioral patch produced three independent `100/100`, `task_success=true` runs.
- No model had access to Task 002 before validation; Task 003 and the v2 matrix are still pending.

## Safe continuation

Future hosts must rerun the Gate because this recovery is specific to the Windows/OpenGL configuration. The benchmark must still reject any task whose renderer differs materially from this validated path.
