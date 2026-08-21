from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image


DOT_THRESHOLD = 0.98
SCENARIOS = {
    "E": (1.0, 0.0),
    "N": (0.0, -1.0),
    "W": (-1.0, 0.0),
    "S": (0.0, 1.0),
    "NE": (math.sqrt(0.5), -math.sqrt(0.5)),
}
RESOLUTIONS = ((960, 540), (1280, 720))
OBJECTIVE_BODY = (76, 230, 161)
OBJECTIVE_TIP = (176, 255, 210)
THREAT_BODY = (236, 78, 92)
THREAT_TIP = (255, 190, 197)
TIP_PIXEL_RANGE = (38, 45)
BODY_PIXEL_RANGE = (790, 830)
SCALE_TOLERANCE = 0.001
MIN_ALPHA = 0.99


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task 001 independent evaluator")
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("manifest.json"),
    )
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def vector_dot(left: list[float] | tuple[float, float], right: tuple[float, float]) -> float:
    return float(left[0]) * right[0] + float(left[1]) * right[1]


def distance(left: list[float], right: tuple[float, float]) -> float:
    return math.hypot(float(left[0]) - right[0], float(left[1]) - right[1])


def rotated(vector: list[float], radians: float) -> tuple[float, float]:
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        float(vector[0]) * cosine - float(vector[1]) * sine,
        float(vector[0]) * sine + float(vector[1]) * cosine,
    )


def angle(vector: list[float]) -> float:
    return math.atan2(float(vector[1]), float(vector[0]))


def expected_geometry(width: int, height: int, scenario: str) -> dict[str, tuple[float, float]]:
    direction = SCENARIOS[scenario]
    threat_direction = (-direction[1], direction[0])
    player = (width * 0.5, (height - 145.0) * 0.52)
    play_height = max(220.0, height - 150.0)
    radius = min(width * 0.22, play_height * 0.34)
    return {
        "objective_direction": direction,
        "threat_direction": threat_direction,
        "player": player,
        "objective": (player[0] + direction[0] * radius, player[1] + direction[1] * radius),
        "threat": (
            player[0] + threat_direction[0] * radius,
            player[1] + threat_direction[1] * radius,
        ),
        "objective_center": (160.0, height - 68.0),
        "threat_center": (width - 160.0, height - 68.0),
    }


def color_points(
    image: Image.Image,
    center: tuple[float, float],
    color: tuple[int, int, int],
    radius: int = 32,
    tolerance: int = 2,
) -> list[tuple[int, int]]:
    rgb = image.convert("RGB")
    cx, cy = int(round(center[0])), int(round(center[1]))
    points: list[tuple[int, int]] = []
    for y in range(max(0, cy - radius), min(rgb.height, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(rgb.width, cx + radius + 1)):
            pixel = rgb.getpixel((x, y))
            if all(abs(pixel[index] - color[index]) <= tolerance for index in range(3)):
                points.append((x, y))
    return points


def visual_forward(
    image: Image.Image,
    center: tuple[float, float],
    tip_color: tuple[int, int, int],
    body_color: tuple[int, int, int],
) -> dict[str, Any]:
    tips = color_points(image, center, tip_color)
    body = color_points(image, center, body_color)
    pixel_counts_valid = (
        TIP_PIXEL_RANGE[0] <= len(tips) <= TIP_PIXEL_RANGE[1]
        and BODY_PIXEL_RANGE[0] <= len(body) <= BODY_PIXEL_RANGE[1]
    )
    if not pixel_counts_valid:
        return {"valid": False, "tip_pixels": len(tips), "body_pixels": len(body), "vector": [0.0, 0.0]}
    tip_center = (
        sum(point[0] for point in tips) / len(tips),
        sum(point[1] for point in tips) / len(tips),
    )
    delta = (tip_center[0] - center[0], tip_center[1] - center[1])
    length = math.hypot(*delta)
    if length < 5.0:
        return {"valid": False, "tip_pixels": len(tips), "body_pixels": len(body), "vector": [0.0, 0.0]}
    return {
        "valid": True,
        "tip_pixels": len(tips),
        "body_pixels": len(body),
        "tip_center": list(tip_center),
        "vector": [delta[0] / length, delta[1] / length],
    }


def run_private_suite(args: argparse.Namespace) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    args.output.mkdir(parents=True, exist_ok=True)
    suite = Path(__file__).with_name("suite.gd").resolve()
    run_options: dict[str, Any] = {}
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        run_options["startupinfo"] = startupinfo
        run_options["creationflags"] = subprocess.CREATE_NO_WINDOW

    import_command = [
        str(args.godot.resolve()),
        "--headless",
        "--path",
        str(args.candidate.resolve()),
        "--import",
    ]
    imported = subprocess.run(
        import_command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
        **run_options,
    )
    if imported.returncode != 0 or "SCRIPT ERROR" in imported.stdout or "SCRIPT ERROR" in imported.stderr:
        return imported, None

    command = [
        str(args.godot.resolve()),
        "--path",
        str(args.candidate.resolve()),
        "--display-driver",
        "windows",
        "--rendering-driver",
        "opengl3",
        "--rendering-method",
        "gl_compatibility",
        "--audio-driver",
        "Dummy",
        "--fixed-fps",
        "60",
        "--resolution",
        "960x540",
        "--position",
        "-10000,-10000",
        "--script",
        str(suite),
        "--",
        "--output-dir",
        str(args.output.resolve()),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
        **run_options,
    )
    completed.stdout = imported.stdout + completed.stdout
    completed.stderr = imported.stderr + completed.stderr
    result_path = args.output / "suite_result.json"
    suite_result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    return completed, suite_result


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    completed, suite = run_private_suite(args)
    report: dict[str, Any] = {
        "task_id": manifest["task_id"],
        "candidate": str(args.candidate.resolve()),
        "godot": str(args.godot.resolve()),
        "process_exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "runner": {
            "display_driver": "windows",
            "rendering_driver": "opengl3",
            "rendering_method": "gl_compatibility",
            "audio_driver": "Dummy",
            "offscreen_position": [-10000, -10000],
            "windows_sw_hide": sys.platform == "win32",
            "windows_create_no_window": sys.platform == "win32",
        },
        "functional": {"score": 0.0, "max": 45.0, "cases": []},
        "visual": {"score": 0.0, "max": 35.0, "cases": []},
        "regression": {"score": 0.0, "max": 20.0, "checks": []},
        "integrity": {"passed": True, "checks": []},
        "shortcut_guards": {},
        "resolved": False,
    }

    process_clean = (
        completed.returncode == 0
        and suite is not None
        and len(suite.get("cases", [])) == 10
        and not suite.get("suite_errors")
        and "SCRIPT ERROR" not in completed.stdout
        and "SCRIPT ERROR" not in completed.stderr
    )

    for relative_path, expected_hash in manifest["protected_files"].items():
        actual_path = args.candidate / relative_path
        actual_hash = sha256(actual_path) if actual_path.is_file() else None
        passed = actual_hash == expected_hash
        report["integrity"]["checks"].append(
            {"path": relative_path, "expected": expected_hash, "actual": actual_hash, "passed": passed}
        )
        report["integrity"]["passed"] &= passed

    case_lookup: dict[tuple[int, int, str], dict[str, Any]] = {}
    if suite is not None:
        for case in suite.get("cases", []):
            case_lookup[(int(case["width"]), int(case["height"]), case["scenario"])] = case

    all_threat_state = True
    all_target_geometry = True
    all_visual_visibility = True
    resolution_layout: dict[tuple[int, int], bool] = {resolution: True for resolution in RESOLUTIONS}

    for width, height in RESOLUTIONS:
        for scenario in SCENARIOS:
            geometry = expected_geometry(width, height, scenario)
            case = case_lookup.get((width, height, scenario))
            functional_entry: dict[str, Any] = {"width": width, "height": height, "scenario": scenario, "passed": False}
            visual_entry: dict[str, Any] = {"width": width, "height": height, "scenario": scenario, "passed": False}
            if case is None or case.get("missing_required_node", True):
                report["functional"]["cases"].append(functional_entry)
                report["visual"]["cases"].append(visual_entry)
                all_threat_state = False
                all_target_geometry = False
                all_visual_visibility = False
                resolution_layout[(width, height)] = False
                continue

            objective_geometry_ok = (
                distance(case["player_position"], geometry["player"]) <= 0.5
                and distance(case["objective_position"], geometry["objective"]) <= 0.5
                and case["objective_bound_target"] == "ObjectiveBeacon"
            )
            threat_geometry_ok = (
                distance(case["threat_position"], geometry["threat"]) <= 0.5
                and case["threat_bound_target"] == "ThreatDrone"
            )
            objective_state_dot = float(case["objective_dot"])
            threat_state_dot = float(case["threat_dot"])
            functional_pass = objective_geometry_ok and objective_state_dot >= DOT_THRESHOLD
            if functional_pass:
                report["functional"]["score"] += 4.5
            functional_entry.update(
                {
                    "objective_dot": objective_state_dot,
                    "geometry_ok": objective_geometry_ok,
                    "passed": functional_pass,
                }
            )
            report["functional"]["cases"].append(functional_entry)

            threat_state_pass = threat_geometry_ok and threat_state_dot >= DOT_THRESHOLD
            all_threat_state &= threat_state_pass
            all_target_geometry &= objective_geometry_ok and threat_geometry_ok

            centers_ok = (
                distance(case["objective_center"], geometry["objective_center"]) <= 0.5
                and distance(case["threat_center"], geometry["threat_center"]) <= 0.5
                and bool(case["objective_visible"])
                and bool(case["threat_visible"])
            )
            transform_ok = (
                distance(case["objective_global_scale"], (1.0, 1.0)) <= SCALE_TOLERANCE
                and distance(case["threat_global_scale"], (1.0, 1.0)) <= SCALE_TOLERANCE
                and float(case["objective_effective_alpha"]) >= MIN_ALPHA
                and float(case["threat_effective_alpha"]) >= MIN_ALPHA
            )
            resolution_layout[(width, height)] &= centers_ok

            capture_path = Path(case.get("capture_path", ""))
            image_valid = (
                int(case.get("capture_error", -1)) == 0
                and capture_path.is_file()
                and int(case.get("image_width", 0)) == width
                and int(case.get("image_height", 0)) == height
            )
            if image_valid:
                image = Image.open(capture_path)
                objective_visual = visual_forward(image, geometry["objective_center"], OBJECTIVE_TIP, OBJECTIVE_BODY)
                threat_visual = visual_forward(image, geometry["threat_center"], THREAT_TIP, THREAT_BODY)
                objective_visual_dot = vector_dot(objective_visual["vector"], geometry["objective_direction"])
                threat_visual_dot = vector_dot(threat_visual["vector"], geometry["threat_direction"])
                visual_pass = (
                    centers_ok
                    and transform_ok
                    and objective_visual["valid"]
                    and threat_visual["valid"]
                    and objective_visual_dot >= DOT_THRESHOLD
                    and threat_visual_dot >= DOT_THRESHOLD
                )
                visual_entry.update(
                    {
                        "objective": objective_visual,
                        "threat": threat_visual,
                        "objective_dot": objective_visual_dot,
                        "threat_dot": threat_visual_dot,
                        "transform_ok": transform_ok,
                        "passed": visual_pass,
                    }
                )
            else:
                visual_pass = False
                visual_entry["capture_valid"] = False
            if visual_pass:
                report["visual"]["score"] += 3.5
            all_visual_visibility &= (
                centers_ok
                and image_valid
                and objective_visual.get("valid", False)
                and threat_visual.get("valid", False)
            )
            report["visual"]["cases"].append(visual_entry)

            report["regression"]["score"] += 1.0 if threat_state_pass else 0.0

    dynamic = suite.get("dynamic", {}) if suite is not None else {}
    dynamic_before = dynamic.get("before", {})
    dynamic_after = dynamic.get("after", {})
    objective_delta = angle(dynamic_after.get("objective_target_direction", [0.0, 0.0])) - angle(
        dynamic_before.get("objective_target_direction", [0.0, 0.0])
    )
    threat_delta = angle(dynamic_after.get("threat_target_direction", [0.0, 0.0])) - angle(
        dynamic_before.get("threat_target_direction", [0.0, 0.0])
    )
    objective_predicted_forward = rotated(
        dynamic_before.get("objective_visible_forward", [0.0, 0.0]), objective_delta
    )
    threat_predicted_forward = rotated(
        dynamic_before.get("threat_visible_forward", [0.0, 0.0]), threat_delta
    )
    objective_dynamic_pass = (
        dynamic_after.get("objective_bound_target") == "ObjectiveBeacon"
        and vector_dot(dynamic_after.get("objective_target_direction", [0.0, 0.0]), (0.6, 0.8)) >= 0.999
        and vector_dot(dynamic_after.get("objective_visible_forward", [0.0, 0.0]), objective_predicted_forward) >= 0.999
    )
    threat_dynamic_pass = (
        dynamic_after.get("threat_bound_target") == "ThreatDrone"
        and vector_dot(dynamic_after.get("threat_target_direction", [0.0, 0.0]), (-0.8, 0.6)) >= 0.999
        and vector_dot(dynamic_after.get("threat_visible_forward", [0.0, 0.0]), threat_predicted_forward) >= 0.999
    )
    report["regression"]["checks"].append({"name": "objective_live_update", "passed": objective_dynamic_pass, "points": 2.0 if objective_dynamic_pass else 0.0})
    report["regression"]["checks"].append({"name": "threat_live_update", "passed": threat_dynamic_pass, "points": 2.0 if threat_dynamic_pass else 0.0})
    report["regression"]["score"] += 2.0 if objective_dynamic_pass else 0.0
    report["regression"]["score"] += 2.0 if threat_dynamic_pass else 0.0

    for resolution, passed in resolution_layout.items():
        report["regression"]["checks"].append({"name": f"layout_{resolution[0]}x{resolution[1]}", "passed": passed, "points": 1.0 if passed else 0.0})
        report["regression"]["score"] += 1.0 if passed else 0.0

    asset_paths = ("assets/objective_arrow.png", "assets/threat_arrow.png")
    for asset_path in asset_paths:
        integrity_check = next(check for check in report["integrity"]["checks"] if check["path"] == asset_path)
        passed = bool(integrity_check["passed"])
        report["regression"]["checks"].append({"name": f"asset_hash:{asset_path}", "passed": passed, "points": 1.0 if passed else 0.0})
        report["regression"]["score"] += 1.0 if passed else 0.0

    behavior = suite.get("behavior", {}) if suite is not None else {}
    expected_keys = {
        "move_up": ((0.0, -1.0), 87),
        "move_left": ((-1.0, 0.0), 65),
        "move_down": ((0.0, 1.0), 83),
        "move_right": ((1.0, 0.0), 68),
    }
    movement_checks: dict[str, bool] = {}
    for action, (expected_direction, expected_key) in expected_keys.items():
        movement = behavior.get("movement", {}).get(action, {})
        delta = movement.get("delta", [0.0, 0.0])
        delta_length = math.hypot(float(delta[0]), float(delta[1]))
        movement_checks[action] = (
            delta_length >= 1.0
            and vector_dot([float(delta[0]) / delta_length, float(delta[1]) / delta_length], expected_direction) >= 0.999
            and expected_key in movement.get("event_codes", [])
        )
    wasd_pass = len(movement_checks) == 4 and all(movement_checks.values())
    completion_pass = (
        behavior.get("required_nodes_present", False)
        and behavior.get("completion_before", True) is False
        and behavior.get("completion_after", False) is True
        and behavior.get("marker_completed", False) is True
    )
    required_nodes_pass = suite is not None and all(
        not case.get("missing_required_node", True) for case in suite.get("cases", [])
    )
    behavior_gate_pass = process_clean and required_nodes_pass and wasd_pass and completion_pass
    report["regression"]["checks"].append(
        {
            "name": "startup_required_nodes_wasd_completion",
            "passed": behavior_gate_pass,
            "points": 2.0 if behavior_gate_pass else 0.0,
            "process_clean": process_clean,
            "required_nodes": required_nodes_pass,
            "wasd": movement_checks,
            "completion": completion_pass,
        }
    )
    report["regression"]["score"] += 2.0 if behavior_gate_pass else 0.0

    report["shortcut_guards"] = {
        "global_algorithm_flip_or_threat_edit_rejected": all_threat_state,
        "target_swap_or_move_rejected": all_target_geometry,
        "hidden_tracker_rejected": all_visual_visibility,
        "single_direction_hardcode_rejected": len(report["functional"]["cases"]) == 10 and objective_dynamic_pass,
        "asset_rewrite_rejected": all(
            next(check for check in report["integrity"]["checks"] if check["path"] == path)["passed"]
            for path in asset_paths
        ),
    }

    report["functional"]["score"] = round(report["functional"]["score"], 1)
    report["visual"]["score"] = round(report["visual"]["score"], 1)
    report["regression"]["score"] = round(report["regression"]["score"], 1)
    report["diagnostic_total"] = round(
        report["functional"]["score"] + report["visual"]["score"] + report["regression"]["score"], 1
    )
    report["build_integrity_gate"] = report["integrity"]["passed"] and behavior_gate_pass
    report["total"] = report["diagnostic_total"] if report["build_integrity_gate"] else 0.0
    report["resolved"] = (
        report["build_integrity_gate"]
        and report["functional"]["score"] == 45.0
        and report["visual"]["score"] == 35.0
        and report["regression"]["score"] == 20.0
        and all(report["shortcut_guards"].values())
    )
    report["task_success"] = report["resolved"]
    return report


def main() -> int:
    args = parse_args()
    report = evaluate(args)
    result_path = args.output / "evaluation.json"
    result_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "EVALUATION functional={functional}/45 visual={visual}/35 regression={regression}/20 "
        "total={total}/100 resolved={resolved}".format(
            functional=report["functional"]["score"],
            visual=report["visual"]["score"],
            regression=report["regression"]["score"],
            total=report["total"],
            resolved=report["resolved"],
        )
    )
    return 0 if report["process_exit_code"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
