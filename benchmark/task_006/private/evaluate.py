#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path

TASK=Path(__file__).resolve().parents[1];PUBLIC=TASK/"public";ORACLE=json.loads((TASK/"private/oracle.json").read_text(encoding="utf-8"));FIELDS=[("scripts/combat/attack_controller.gd","SAMPLE_AFTER_MOVEMENT_COMMIT",True),("scripts/combat/telegraph_sample.gd","CAPTURE_POSITION",True),("scripts/combat/telegraph_sample.gd","CAPTURE_FACING",True),("scripts/combat/telegraph_sample.gd","CAPTURE_PARITY",True),("scripts/combat/telegraph_sample.gd","CAPTURE_EPOCH",True),("scripts/render/telegraph_renderer.gd","READ_LIVE_ARENA_STATE",False),("scripts/render/telegraph_pool.gd","REJECT_STALE_EPOCH",True),("scripts/render/telegraph_pool.gd","RESET_ON_REUSE",True)]
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def boolean(root:Path,relative:str,name:str)->bool|None:
    path=root/relative;text=path.read_text(encoding="utf-8",errors="replace") if path.is_file() else "";match=re.search(rf"{name}\s*(?::=|=)\s*(true|false)",text,re.I);return match.group(1).lower()=="true" if match else None
def values(root:Path)->dict:return {name:boolean(root,path,name) for path,name,_ in FIELDS}
def mask(v:dict)->int:
    m=0
    if v["SAMPLE_AFTER_MOVEMENT_COMMIT"] is not True:m|=1
    if v["CAPTURE_POSITION"] is not True or v["CAPTURE_FACING"] is not True:m|=2
    if v["CAPTURE_PARITY"] is not True:m|=4
    if v["CAPTURE_EPOCH"] is not True or v["REJECT_STALE_EPOCH"] is not True:m|=8
    if v["READ_LIVE_ARENA_STATE"] is not False or v["RESET_ON_REUSE"] is not True:m|=16
    return m
def capture(candidate:Path,godot:Path,out:Path,phase:str,tick:int,direction:int,faults:int)->bool:
    cmd=[str(godot),"--headless","--path",str(candidate),"--script","res://tools/capture.gd","--","--output",str(out),"--phase",phase,"--tick-rate",str(tick),"--direction",str(direction),"--fault-mask",str(faults)];done=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False);return done.returncode==0 and out.is_file() and out.stat().st_size>2500
def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--candidate",type=Path,required=True);p.add_argument("--godot",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();a.candidate=a.candidate.resolve();a.godot=a.godot.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True);imp=subprocess.run([str(a.godot),"--headless","--path",str(a.candidate),"--import"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False);build=imp.returncode==0;v=values(a.candidate);faults=mask(v)
    ordering=v["SAMPLE_AFTER_MOVEMENT_COMMIT"] is True;payload=all(v[x] is True for x in ("CAPTURE_POSITION","CAPTURE_FACING","CAPTURE_PARITY","CAPTURE_EPOCH"));renderer=v["READ_LIVE_ARENA_STATE"] is False;pool=v["REJECT_STALE_EPOCH"] is True and v["RESET_ON_REUSE"] is True;functional=(15 if ordering else 0)+(15 if payload else 0)+(10 if renderer else 0)+(5 if pool else 0)
    cases=[];phase_ok={phase:True for phase in ORACLE["phases"]}
    for phase in ORACLE["phases"]:
        for tick in ORACLE["tick_rates"]:
            for direction in ORACLE["directions"]:
                out=a.output/f"{phase.lower()}_{tick}_{direction}.png";rendered=capture(a.candidate,a.godot,out,phase,tick,direction,faults);correct=faults==0;phase_ok[phase]=phase_ok[phase] and rendered and correct;cases.append({"phase":phase,"tick_rate":tick,"direction":direction,"rendered":rendered,"correct":correct})
    visual=(10 if phase_ok["CALM"] else 0)+(15 if phase_ok["MIRRORED_ENRAGED"] else 0)+(10 if phase_ok["INTERRUPTED_RESUME"] else 0)
    texts="\n".join((a.candidate/x).read_text(encoding="utf-8",errors="replace") if (a.candidate/x).is_file() else "" for x,_,_ in FIELDS);scene=(a.candidate/"scenes/main.tscn").read_text(encoding="utf-8",errors="replace") if (a.candidate/"scenes/main.tscn").is_file() else "";regression=all(x in scene for x in ("Boss","AttackController","TelegraphRenderer","TelegraphPool","Arena","Player")) and all(x in texts for x in ("DAMAGE_TICK_OFFSET := 3","ATTACK_DURATION_TICKS := 8","TELEGRAPH_VISIBLE := true","ALPHA := 1.0","MAX_POOL_SIZE := 12","LIFETIME_TICKS := 3"));rscore=20 if regression else 0;success=build and functional==45 and visual==35 and rscore==20;result={"schema_version":1,"task_id":"gamevisualfix_task_006","build_gate":build,"functional":{"score":functional,"max":45,"ordering":ordering,"immutable_payload":payload,"sample_only_renderer":renderer,"pool_epoch":pool},"visual":{"score":visual,"max":35,"phase_pass":phase_ok},"regression":{"score":rscore,"max":20,"passed":regression},"total":functional+visual+rscore if build else 0,"task_success":success,"cases":cases};(a.output/"evaluation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps({"total":result["total"],"task_success":success}));return 0
if __name__=="__main__":raise SystemExit(main())
