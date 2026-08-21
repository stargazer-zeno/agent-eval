from __future__ import annotations

import argparse, json, math, subprocess, sys
from pathlib import Path
from PIL import Image

ROTATIONS = (0.0, 30.0, -55.0)
ZOOMS = (0.72, 1.25)
SIZES = ((960, 540), (1280, 720), (1024, 600))
YELLOW, RED = (245, 196, 81), (238, 100, 116)

def parse() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True, type=Path); p.add_argument("--godot", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path); p.add_argument("--manifest", type=Path)
    return p.parse_args()

def expected(rotation: float) -> tuple[float, float]:
    radians = math.radians(-rotation); x, y = 520.0, -170.0
    x, y = x * math.cos(radians) - y * math.sin(radians), x * math.sin(radians) + y * math.cos(radians)
    length = math.hypot(x, y); return x / length, y / length

def direction(image_path: Path, color: tuple[int, int, int]) -> tuple[float, float] | None:
    image = Image.open(image_path).convert("RGB"); center = (image.width / 2.0, image.height / 2.0)
    best, best_distance = None, 0.0
    # The arrows are 4–5 pixels wide; 2px sampling preserves their direction
    # while keeping the fixed 18-case evaluator comfortably bounded on CPU.
    for y in range(0, image.height, 2):
        for x in range(0, image.width, 2):
            pixel = image.getpixel((x, y))
            if all(abs(pixel[i] - color[i]) <= 3 for i in range(3)):
                dx, dy = x - center[0], y - center[1]; distance = math.hypot(dx, dy)
                if distance > best_distance: best, best_distance = (dx, dy), distance
    return (best[0] / best_distance, best[1] / best_distance) if best is not None and best_distance > 50 else None

def capture(a: argparse.Namespace, rotation: float, zoom: float, size: tuple[int, int], image: Path) -> tuple[int, str]:
    si = subprocess.STARTUPINFO() if sys.platform == "win32" else None
    if si: si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 0
    command = [str(a.godot.resolve()), "--path", str(a.candidate.resolve()), "--display-driver", "windows", "--rendering-driver", "opengl3", "--rendering-method", "gl_compatibility", "--audio-driver", "Dummy", "--position", "12000,12000", "--script", "res://tools/capture.gd", "--", "--output", str(image.resolve()), "--scenario", "BASELINE", "--rotation", str(rotation), "--zoom", str(zoom), "--width", str(size[0]), "--height", str(size[1])]
    run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, startupinfo=si)
    return run.returncode, (run.stdout + run.stderr)[-1000:]

def main() -> int:
    a = parse(); a.output.mkdir(parents=True, exist_ok=True); cases = []
    for size in SIZES:
        for rotation in ROTATIONS:
            for zoom in ZOOMS:
                image = a.output / f"{size[0]}x{size[1]}_{rotation}_{zoom}.png"; code, log = capture(a, rotation, zoom, size, image)
                objective = direction(image, YELLOW) if code == 0 and image.exists() else None
                threat = direction(image, RED) if code == 0 and image.exists() else None
                target = expected(rotation); dot = objective[0] * target[0] + objective[1] * target[1] if objective else -1.0
                cases.append({"size": list(size), "rotation": rotation, "zoom": zoom, "capture_exit": code, "objective_dot": dot, "threat_visible": threat is not None, "log": log})
    functional = 45.0 if len(cases) == 18 and all(x["objective_dot"] >= .98 for x in cases) else 0.0
    visual = 35.0 if functional and all(x["threat_visible"] for x in cases) else 0.0
    regression = 20.0 if functional and all(x["capture_exit"] == 0 for x in cases) else 0.0
    report = {"task_id":"gamevisualfix_task_002", "functional":{"score":functional,"max":45}, "visual":{"score":visual,"max":35}, "regression":{"score":regression,"max":20}, "total":functional+visual+regression, "task_success":functional == 45 and visual == 35 and regression == 20, "case_count":len(cases), "cases":cases, "evaluator_version":"task002_capture_oracle_v2"}
    (a.output / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"total":report["total"], "task_success":report["task_success"], "case_count":len(cases)})); return 0

if __name__ == "__main__": raise SystemExit(main())
