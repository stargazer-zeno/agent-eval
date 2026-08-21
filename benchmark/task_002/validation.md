# Task 002 validation

Validated on 2026-08-21 using Godot 4.7.1, Windows hidden-window OpenGL Compatibility rendering, and the task-local capture Oracle (`task002_capture_oracle_v2`).

| State | Repetitions | Hidden cases / run | Result |
| --- | ---: | ---: | --- |
| Public Bug Seed (`mixed`) | 3 | 18 | 0/100; `task_success=false` |
| Reference Patch (`camera`) | 3 | 18 | 100/100; `task_success=true` |

Each hidden matrix combines three camera rotations (`0°, 30°, -55°`), two zoom values (`0.72, 1.25`), and three viewports (`960×540, 1280×720, 1024×600`). Functional scoring uses the yellow Objective indicator's image-derived direction against the camera-space objective vector (`dot >= 0.98`). Visual scoring additionally requires the red Threat indicator to remain visible; Regression requires all captures to succeed.

The public initial image was captured from the Bug Seed at `BASELINE`. The reference patch changes only the Objective coordinate-space mode and is evaluated by behavior, not by diff identity.
