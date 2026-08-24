#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]; PUBLIC=TASK/"public"; ORACLE=json.loads((TASK/"private/oracle.json").read_text(encoding="utf-8"))
def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def numbers(path: Path, pattern: str)->list[int]:
    text=path.read_text(encoding="utf-8",errors="replace") if path.is_file() else ""; match=re.search(pattern,text)
    return [int(value) for value in match.group(1).split(",")] if match else []
def values(candidate: Path)->dict:
    return {"route":numbers(candidate/"resources/route_bindings.cfg",r"door_order\s*=\s*\"?([0-3, ]+)"),"migration":numbers(candidate/"scripts/save/slot_migrator.gd",r"V1_TO_V2[^=]*=\s*\[([^\]]+)\]"),"hint":numbers(candidate/"scripts/hud/restore_hints.gd",r"RESTORED_HINT_ORDER[^=]*=\s*\[([^\]]+)\]")}
def capture(candidate:Path,godot:Path,out:Path,phase:str,expected:list[int],actual:list[int],viewport:list[int])->bool:
    cmd=[str(godot),"--headless","--path",str(candidate),"--script","res://tools/capture.gd","--","--output",str(out),"--phase",phase,"--expected",",".join(map(str,expected)),"--actual",",".join(map(str,actual)),"--width",str(viewport[0]),"--height",str(viewport[1])]
    done=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False); return done.returncode==0 and out.is_file() and out.stat().st_size>1800
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--candidate",type=Path,required=True);p.add_argument("--godot",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();a.candidate=a.candidate.resolve();a.godot=a.godot.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
    imported=subprocess.run([str(a.godot),"--headless","--path",str(a.candidate),"--import"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False); build=imported.returncode==0; got=values(a.candidate)
    gates={"route":got["route"]==ORACLE["route_order"],"migration":got["migration"]==ORACLE["migration_order"],"hint":got["hint"]==ORACLE["hint_order"]}; functional=sum(15 for ok in gates.values() if ok)
    phases=[("LOBBY",ORACLE["route_order"],got["route"]),("RESTORED_MIDPOINT",ORACLE["migration_order"],got["migration"]),("POST_ELEVATOR",ORACLE["hint_order"],got["hint"]),("FINAL_RESTORE",ORACLE["hint_order"],got["hint"])]; visual_cases=[]
    for phase,expected,actual in phases:
        for viewport in ORACLE["viewports"]:
            out=a.output/f"{phase.lower()}_{viewport[0]}x{viewport[1]}.png"; rendered=capture(a.candidate,a.godot,out,phase,expected,actual,viewport); matched=actual==expected; visual_cases.append({"phase":phase,"viewport":viewport,"rendered":rendered,"matched":matched})
    visual_pass=all(case["rendered"] and case["matched"] for case in visual_cases); visual=35 if visual_pass else 0
    assets=list((PUBLIC/"assets").rglob("*.png")); regression=all((a.candidate/x.relative_to(PUBLIC)).is_file() and sha(x)==sha(a.candidate/x.relative_to(PUBLIC)) for x in assets)
    scene=(a.candidate/"scenes/main.tscn").read_text(encoding="utf-8",errors="replace") if (a.candidate/"scenes/main.tscn").is_file() else ""; regression=regression and all(name in scene for name in ("Player","LobbyDoors","CheckpointStore","RestoreHUD","Elevator"))
    regression=regression and sorted(got["route"])==[0,1,2,3] and sorted(got["migration"])==[0,1,2,3] and sorted(got["hint"])==[0,1,2,3]; rscore=20 if regression else 0; success=build and functional==45 and visual==35 and rscore==20
    result={"schema_version":1,"task_id":"gamevisualfix_task_005","build_gate":build,"functional":{"score":functional,"max":45,"checkpoint_gates":gates},"visual":{"score":visual,"max":35,"passed":visual_pass},"regression":{"score":rscore,"max":20,"passed":regression},"total":functional+visual+rscore if build else 0,"task_success":success,"cases":visual_cases};(a.output/"evaluation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps({"total":result["total"],"task_success":success}));return 0
if __name__=="__main__": raise SystemExit(main())
