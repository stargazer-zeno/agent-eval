from __future__ import annotations

import argparse, json, subprocess, sys
from pathlib import Path
from PIL import Image

SCENARIOS = {
    "RIGHT": [1,1,1,1,1,1,1,1], "LEFT": [-1,-1,-1,-1,-1,-1,-1,-1],
    "RIGHT_TO_LEFT": [1,1,1,1,-1,-1,-1,-1], "LEFT_TO_RIGHT": [-1,-1,-1,-1,1,1,1,1],
    "REPEATED": [1,1,0,-1,-1,0,1,1], "INTERRUPTED": [1,1,1,0,0,-1,-1,-1],
}
PURPLE, BLUE = (189,123,255), (119,185,255)

def parse():
    p=argparse.ArgumentParser(); p.add_argument('--candidate',required=True,type=Path); p.add_argument('--godot',required=True,type=Path); p.add_argument('--output',required=True,type=Path); p.add_argument('--manifest',type=Path); return p.parse_args()

def centers(path: Path, index: int):
    image=Image.open(path).convert('RGB'); col=index%4; row=index//4; left, top=42+col*230,88+row*210
    pixels={PURPLE:[],BLUE:[]}
    for y in range(top+35,top+145,2):
        for x in range(left+35,left+175,2):
            value=image.getpixel((x,y))
            for color in pixels:
                if all(abs(value[i]-color[i])<=3 for i in range(3)): pixels[color].append((x,y))
    output=[]
    for color in (PURPLE,BLUE):
        values=pixels[color]
        output.append((sum(v[0] for v in values)/len(values),sum(v[1] for v in values)/len(values)) if values else None)
    return output

def capture(a, scenario, tick, output):
    si=subprocess.STARTUPINFO() if sys.platform=='win32' else None
    if si: si.dwFlags|=subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=0
    command=[str(a.godot.resolve()),'--path',str(a.candidate.resolve()),'--display-driver','windows','--rendering-driver','opengl3','--rendering-method','gl_compatibility','--audio-driver','Dummy','--position','12000,12000','--fixed-fps',str(tick),'--script','res://tools/capture.gd','--','--output',str(output.resolve()),'--scenario',scenario]
    run=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90,startupinfo=si); return run.returncode

def main():
    a=parse(); a.output.mkdir(parents=True,exist_ok=True); cases=[]
    for scenario, faces in SCENARIOS.items():
        for tick in (30,60):
            image=a.output/f'{scenario}_{tick}.png'; code=capture(a,scenario,tick,image); passed=code==0 and image.exists(); frame=[]
            if passed:
                for index,facing in enumerate(faces):
                    trail,player=centers(image,index); delta=(trail[0]-player[0]) if trail and player else None
                    expected=-facing
                    # On an interruption frame the pooled trail is exactly
                    # behind a stationary player and is occluded by the player
                    # sprite; absence of a separable purple centroid is valid.
                    ok = trail is None if expected == 0 else (delta is not None and delta * expected > 20)
                    frame.append({'tick':index,'facing':facing,'trail_delta_x':delta,'passed':ok})
                passed=all(item['passed'] for item in frame)
            cases.append({'scenario':scenario,'physics_tick_rate':tick,'capture_exit':code,'frames':frame,'passed':passed})
    functional=45.0 if len(cases)==12 and all(x['passed'] for x in cases) else 0.0
    visual=35.0 if functional and all(len(x['frames'])==8 for x in cases) else 0.0
    regression=20.0 if functional and all(x['capture_exit']==0 for x in cases) else 0.0
    report={'task_id':'gamevisualfix_task_003','functional':{'score':functional,'max':45},'visual':{'score':visual,'max':35},'regression':{'score':regression,'max':20},'total':functional+visual+regression,'task_success':functional==45 and visual==35 and regression==20,'case_count':len(cases),'cases':cases,'evaluator_version':'task003_contact_sheet_v1'}
    (a.output/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps({'total':report['total'],'task_success':report['task_success'],'case_count':len(cases)})); return 0
if __name__=='__main__': raise SystemExit(main())
