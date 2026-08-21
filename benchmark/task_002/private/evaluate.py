from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
def main() -> int:
 p=argparse.ArgumentParser(); p.add_argument('--candidate',type=Path,required=True); p.add_argument('--godot',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--manifest',type=Path); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
 si=subprocess.STARTUPINFO() if sys.platform=='win32' else None
 if si: si.dwFlags|=subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=0
 cmd=[str(a.godot),'--path',str(a.candidate),'--display-driver','windows','--rendering-driver','opengl3','--rendering-method','gl_compatibility','--audio-driver','Dummy','--script',str(Path(__file__).with_name('suite.gd')),'--','--output-dir',str(a.output)]
 run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180,startupinfo=si)
 suite_path=a.output/'suite_result.json'; suite=json.loads(suite_path.read_text()) if suite_path.exists() else {'cases':[]}
 cases=suite.get('cases',[]); functional=45.0 if len(cases)==18 and all(float(x.get('objective_dot',0))>=.98 for x in cases) else 0.0
 visual=35.0 if functional and all(39<=float(x['objective_tip'][0])<=float(x['width'])-39 and 39<=float(x['objective_tip'][1])<=float(x['height'])-39 for x in cases) else 0.0
 regression=20.0 if functional and all(float(x.get('threat_dot',0))>=.98 for x in cases) else 0.0
 report={'task_id':'gamevisualfix_task_002','process_exit_code':run.returncode,'functional':{'score':functional,'max':45},'visual':{'score':visual,'max':35},'regression':{'score':regression,'max':20},'total':functional+visual+regression,'task_success':functional==45 and visual==35 and regression==20,'case_count':len(cases),'stdout':run.stdout[-2000:],'stderr':run.stderr[-2000:]}
 (a.output/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report)); return 0 if run.returncode==0 else 2
if __name__=='__main__': raise SystemExit(main())
