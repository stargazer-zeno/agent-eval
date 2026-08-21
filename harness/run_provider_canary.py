#!/usr/bin/env python3
"""No-task Codex provider canary: JSON schema, image input, and resume."""
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
from PIL import Image
import run_codex_eval as core

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument('--provider',required=True); p.add_argument('--output',required=True,type=Path); p.add_argument('--env-file',type=Path,default=core.ROOT/'.env'); p.add_argument('--codex-exe',type=Path); a=p.parse_args()
    out=a.output.resolve(); out.mkdir(parents=True,exist_ok=False); image=out/'canary.png'; Image.new('RGB',(32,32),(17,34,51)).save(image)
    model,auth,env,extra=core.provider_config(a.provider,core.dotenv(a.env_file),out/'control'/'codex_home'); exe=core.native_codex(a.codex_exe); schema=core.ROOT/'harness'/'controller_action.schema.json'; common=['--json','--ignore-rules','--output-schema',str(schema),'--disable','plugins','--disable','apps','-c','web_search="disabled"']
    prompt='This is a no-task transport canary. Inspect the attached image. Return exactly one valid schema object with action list_files and empty path, content, scenario, summary.'
    code,raw,timed=core.command([str(exe),'exec',*common,'--sandbox','read-only',*extra,'--image',str(image),'-C',str(out),'-'],240,out,env,prompt); thread,msg,usage=core.extract(raw); first={'exit_code':code,'timed_out':timed,'thread':thread,'message':msg,'usage':usage,'raw_tail':raw[-2000:]}
    valid=False; second={}
    try:
        valid=code==0 and bool(thread) and core.json_action(msg or {}).get('action')=='list_files'
        if valid:
            code,raw,timed=core.command([str(exe),'exec','resume',*common,'--image',str(image),str(thread),'-'],240,out,env,'Return exactly one valid schema object with action submit and empty path, content, scenario, summary.')
            _,msg,usage=core.extract(raw); second={'exit_code':code,'timed_out':timed,'message':msg,'usage':usage,'raw_tail':raw[-2000:]}; valid=code==0 and core.json_action(msg or '').get('action')=='submit'
    except Exception as exc: second={'error':str(exc)}; valid=False
    report={'provider':a.provider,'model':model,'authentication':auth,'valid':valid,'first':first,'second':second,'codex_sha256':core.digest(exe)}; (out/'canary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); shutil.rmtree(out/'control',ignore_errors=True); print(json.dumps({'provider':a.provider,'valid':valid})); return 0 if valid else 2
if __name__=='__main__': raise SystemExit(main())
