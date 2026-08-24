#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]; ORACLE=json.loads((TASK/"private/oracle.json").read_text(encoding="utf-8"))
FIELDS=[("scripts/combat/attack_controller.gd","SAMPLE_AFTER_MOVEMENT_COMMIT",True),("scripts/combat/telegraph_sample.gd","CAPTURE_POSITION",True),("scripts/combat/telegraph_sample.gd","CAPTURE_FACING",True),("scripts/combat/telegraph_sample.gd","CAPTURE_PARITY",True),("scripts/combat/telegraph_sample.gd","CAPTURE_EPOCH",True),("scripts/render/telegraph_renderer.gd","READ_LIVE_ARENA_STATE",False),("scripts/render/telegraph_pool.gd","REJECT_STALE_EPOCH",True),("scripts/render/telegraph_pool.gd","RESET_ON_REUSE",True)]
def boolean(root:Path,relative:str,name:str)->bool|None:
    path=root/relative; text=path.read_text(encoding="utf-8",errors="replace") if path.is_file() else ""; match=re.search(rf"{name}\s*(?::=|=)\s*(true|false)",text,re.I); return match.group(1).lower()=="true" if match else None
def fault_mask(root:Path)->int:
    values={name:boolean(root,path,name) for path,name,_ in FIELDS}; mask=0
    if values["SAMPLE_AFTER_MOVEMENT_COMMIT"] is not True: mask|=1
    if values["CAPTURE_POSITION"] is not True or values["CAPTURE_FACING"] is not True: mask|=2
    if values["CAPTURE_PARITY"] is not True: mask|=4
    if values["CAPTURE_EPOCH"] is not True or values["REJECT_STALE_EPOCH"] is not True: mask|=8
    if values["READ_LIVE_ARENA_STATE"] is not False or values["RESET_ON_REUSE"] is not True: mask|=16
    return mask
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--workspace",type=Path,required=True);p.add_argument("--godot",type=Path,required=True);p.add_argument("--state",type=Path,required=True);p.add_argument("--scenario",required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--result",type=Path,required=True);a=p.parse_args();state=json.loads(a.state.read_text(encoding="utf-8-sig"));before=state["phase"];phases=ORACLE["phases"];after=before;advanced=False
    if a.scenario=="STEP_FIGHT" and before!=phases[-1]: after=phases[phases.index(before)+1];advanced=True
    mask=fault_mask(a.workspace);cmd=[str(a.godot.resolve()),"--headless","--path",str(a.workspace.resolve()),"--script","res://tools/capture.gd","--","--output",str(a.output.resolve()),"--phase",after,"--fault-mask",str(mask)]
    done=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False)
    if done.returncode or not a.output.is_file():print(done.stdout);return 2
    nxt={"phase":after,"step":int(state.get("step",0))+1,"data":{"last_scenario":a.scenario}};a.result.write_text(json.dumps({"phase_before":before,"phase_after":after,"advanced":advanced,"next_state":nxt},indent=2)+"\n",encoding="utf-8");print(f"fight replay: {before} -> {after}; advanced={advanced}; diagnostic_mask={mask}");return 0
if __name__=="__main__":raise SystemExit(main())
