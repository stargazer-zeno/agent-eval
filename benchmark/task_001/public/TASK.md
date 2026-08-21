Players report a visual inconsistency in the two HUD trackers. Use the attached runtime screenshot as the primary bug evidence.

Diagnose the root cause in this existing Godot project and implement the smallest robust fix. Both tracker types must continue to point toward their own tracked world object as targets move, at different directions and window sizes. Preserve existing game behavior and committed image assets.

After a candidate patch, request a fresh runtime observation from the harness and inspect it. If the fix is incomplete, use that new evidence to revise your diagnosis and patch. You may run the provided public checks.

Do not modify the task evidence or tests. Keep the patch focused. When you need a new screenshot, return action "observe". When the task is complete, return action "submit" with a brief summary of checks performed.
