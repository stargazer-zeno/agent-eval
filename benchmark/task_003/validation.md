# Task 003 validation

Validated on 2026-08-21 using Godot 4.7.1, Windows hidden-window OpenGL Compatibility rendering, and fixed-tick contact-sheet Oracle `task003_contact_sheet_v1`.

| State | Repetitions | Hidden cases / run | Result |
| --- | ---: | ---: | --- |
| Public Bug Seed (`before`) | 3 | 12 | 0/100; `task_success=false` |
| Reference Patch (`after`) | 3 | 12 | 100/100; `task_success=true` |

The hidden evaluator captures six fixed replays (`Right`, `Left`, `Right→Left`, `Left→Right`, `Repeated`, `Interrupted`) at 30 and 60 fixed physics ticks. It derives the purple trail and blue player centers separately in each of eight contact-sheet cells. For moving frames, the trail must be on the signed opposite side of the current facing; a stationary interruption frame is accepted when the trail is naturally occluded by the player sprite.

The public initial image is the `RIGHT_TO_LEFT` Bug Seed replay. The oracle evaluates visible behavior, not reference diff identity.
