#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, shutil, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
PUBLIC = TASK / "public"
ORACLE = json.loads((Path(__file__).with_name("oracle.json")).read_text(encoding="utf-8"))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_capture(candidate: Path, godot: Path, out: Path, angle: int, mirror: bool, viewport: list[int]) -> tuple[dict|None,int]:
    command=[str(godot),"--headless","--path",str(candidate),"--script","res://tools/capture.gd","--","--output",str(out),"--scenario","HIDDEN","--angle",str(angle),"--mirror",str(mirror).lower(),"--width",str(viewport[0]),"--height",str(viewport[1])]
    completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False)
    meta=out.with_suffix(".json")
    return (json.loads(meta.read_text(encoding="utf-8")) if meta.is_file() else None,completed.returncode)

def expected_position(offset: list[float], angle: int, mirror: bool, viewport: list[int]) -> tuple[float,float]:
    radians=math.radians(-angle); x,y=offset
    rx=x*math.cos(radians)-y*math.sin(radians); ry=x*math.sin(radians)+y*math.cos(radians)
    if mirror: rx=-rx
    return viewport[0]*0.825+rx*0.28, 42+viewport[1]*0.23+ry*0.28

def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--candidate",type=Path,required=True);p.add_argument("--godot",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();a.candidate=a.candidate.resolve();a.godot=a.godot.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
    import_run=subprocess.run([str(a.godot),"--headless","--path",str(a.candidate),"--import"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",timeout=90,check=False)
    cases=[]; build=import_run.returncode==0; mapping_ok=True; transform_ok=True; visual_ok=True
    for angle in ORACLE["hidden_angles"]:
        for mirror in (False,True):
            for viewport in ORACLE["viewports"]:
                name=f"{viewport[0]}x{viewport[1]}_{angle}_{int(mirror)}.png"; meta,code=run_capture(a.candidate,a.godot,a.output/name,angle,mirror,viewport)
                ok=code==0 and meta is not None; build=build and ok
                case_map=ok and meta["order"]==ORACLE["correct_order"]
                case_transform=ok
                if ok:
                    for offset,actual in zip(meta["landmark_offsets"],meta["projected"]):
                        expected=expected_position(offset,angle,mirror,viewport)
                        if math.dist(expected,actual)>1.25: case_transform=False
                mapping_ok=mapping_ok and case_map;transform_ok=transform_ok and case_transform
                # A nontrivial colored render is the visual hard gate; identity and geometry are checked above from the same render path.
                image=a.output/name; case_visual=ok and image.is_file() and image.stat().st_size>1500
                visual_ok=visual_ok and case_visual
                cases.append({"angle":angle,"mirror":mirror,"viewport":viewport,"mapping":case_map,"transform":case_transform,"visual":case_visual})
    assets=list((PUBLIC/"assets").rglob("*.png")); regression=all((a.candidate/path.relative_to(PUBLIC)).is_file() and sha(path)==sha(a.candidate/path.relative_to(PUBLIC)) for path in assets)
    nodes=(a.candidate/"scenes/main.tscn").read_text(encoding="utf-8",errors="replace") if (a.candidate/"scenes/main.tscn").is_file() else ""
    regression=regression and all(name in nodes for name in ("Player","WorldLandmarks","Minimap"))
    functional=(20 if mapping_ok else 0)+(20 if transform_ok else 0)+(5 if build else 0)
    visual=35 if visual_ok and mapping_ok and transform_ok else 0
    regression_score=20 if regression else 0
    success=build and functional==45 and visual==35 and regression_score==20
    result={"schema_version":1,"task_id":"gamevisualfix_task_004","build_gate":build,"functional":{"score":functional,"max":45,"mapping":mapping_ok,"transform":transform_ok},"visual":{"score":visual,"max":35,"passed":visual_ok},"regression":{"score":regression_score,"max":20,"passed":regression},"total":functional+visual+regression_score if build else 0,"task_success":success,"cases":cases}
    (a.output/"evaluation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(json.dumps({"total":result["total"],"task_success":success}));return 0
if __name__=="__main__": raise SystemExit(main())
