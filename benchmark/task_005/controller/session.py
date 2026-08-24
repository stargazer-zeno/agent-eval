#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
ORACLE = json.loads((TASK / "private/oracle.json").read_text(encoding="utf-8"))

def numbers(path: Path, pattern: str) -> list[int]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    match = re.search(pattern, text)
    return [int(value) for value in match.group(1).split(",")] if match else []

def candidate_values(workspace: Path) -> dict[str, list[int]]:
    return {
        "LOBBY": numbers(workspace / "resources/route_bindings.cfg", r"door_order\s*=\s*\"?([0-3, ]+)"),
        "RESTORED_MIDPOINT": numbers(workspace / "scripts/save/slot_migrator.gd", r"V1_TO_V2[^=]*=\s*\[([^\]]+)\]"),
        "POST_ELEVATOR": numbers(workspace / "scripts/hud/restore_hints.gd", r"RESTORED_HINT_ORDER[^=]*=\s*\[([^\]]+)\]"),
    }

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--workspace",type=Path,required=True); p.add_argument("--godot",type=Path,required=True); p.add_argument("--state",type=Path,required=True); p.add_argument("--scenario",required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--result",type=Path,required=True); a=p.parse_args()
    state=json.loads(a.state.read_text(encoding="utf-8-sig")); before=state["phase"]; phases=ORACLE["phases"]; values=candidate_values(a.workspace)
    expected_by_phase={"LOBBY":ORACLE["route_order"],"RESTORED_MIDPOINT":ORACLE["migration_order"],"POST_ELEVATOR":ORACLE["hint_order"],"FINAL_RESTORE":ORACLE["hint_order"]}
    actual=values.get(before, ORACLE["hint_order"]); expected=expected_by_phase[before]
    advanced=False; after=before
    if a.scenario == "ADVANCE" and before != "FINAL_RESTORE" and actual == expected:
        after=phases[phases.index(before)+1]; advanced=True
    render_actual=values.get(after, ORACLE["hint_order"]); render_expected=expected_by_phase[after]
    command=[str(a.godot.resolve()),"--headless","--path",str(a.workspace.resolve()),"--script","res://tools/capture.gd","--","--output",str(a.output.resolve()),"--phase",after,"--expected",",".join(map(str,render_expected)),"--actual",",".join(map(str,render_actual))]
    completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False)
    if completed.returncode or not a.output.is_file(): print(completed.stdout); return 2
    next_state={"phase":after,"step":int(state.get("step",0))+1,"data":{"last_scenario":a.scenario}}
    result={"phase_before":before,"phase_after":after,"advanced":advanced,"next_state":next_state}
    a.result.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(f"checkpoint replay: {before} -> {after}; advanced={advanced}"); return 0
if __name__=="__main__": raise SystemExit(main())
