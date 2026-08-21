# Signal Courier

This is a small Godot 4.7.1 top-down scene with two HUD trackers. The public project includes a smoke check and an instrumented runtime capture command; correctness is assessed separately.

Run the game:

```powershell
godot --path . --rendering-method gl_compatibility
```

Run the non-visual smoke check:

```powershell
godot --headless --path . --script res://tests/smoke.gd
```

Capture a fresh runtime image after a patch:

```powershell
godot --path . --rendering-method gl_compatibility --resolution 960x540 `
  --script res://tools/capture.gd -- --scenario BASELINE --width 960 --height 540 `
  --output captures/current.png
```

The capture command uses a real Windows rendering window. It exits automatically after saving the PNG.
