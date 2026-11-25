"""Serial experiment driver using upstream Planner, Coder and render/repair methods."""
import ast, contextlib, json, os, shutil, subprocess, sys, time, traceback
from pathlib import Path
ROOT=Path('/autodl-tmp/code2biovideo').resolve()
REPO=ROOT/'Code2Video'
EXP=REPO/'experiments/biology_baseline'
ENV=ROOT/'env'
sys.path.insert(0,str(REPO/'src'))
for line in (ROOT/'.env').read_text().splitlines():
    if line.strip() and not line.startswith('#'):
        key,value=line.split('=',1);os.environ[key]=value
os.environ['PATH']=str(ENV/'bin')+':'+os.environ['PATH']
import agent as upstream
from gpt_request import request_deepseek_token

original_run=subprocess.run
render_events=[]
call_count=0

def safe_run(cmd,*args,**kwargs):
    if isinstance(cmd,list) and cmd and Path(str(cmd[0])).name in ('manim','python'):
        cwd=Path(kwargs['cwd']).resolve()
        n=max([int(p.stem) for p in (cwd/"render_logs").glob("*.json") if p.stem.isdigit()]+[0])+1
        for p in cwd.glob('*.py'):
            dest=cwd/'history'/f'{n:03d}'/p.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
        start=time.monotonic()
        actual=[str(ENV/'bin/python'),str(ROOT/'sandbox_exec.py'),str(cwd),*cmd]
        event={'cmd':cmd,'cwd':str(cwd),'stage':os.environ.get('CODE2VIDEO_STAGE')}
        try:
            result=original_run(actual,*args,**kwargs)
            event.update(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
            return result
        except subprocess.TimeoutExpired as exc:
            event.update(returncode=None,error='timeout',stderr=str(exc));raise
        finally:
            event['elapsed_seconds']=round(time.monotonic()-start,3)
            render_events.append(event)
            logdir=cwd/'render_logs';logdir.mkdir(exist_ok=True)
            (logdir/f'{n:03d}.json').write_text(json.dumps(event,indent=2),encoding='utf-8')

    return original_run(cmd,*args,**kwargs)

subprocess.run=safe_run

def api(prompt,**kwargs):
    global call_count
    call_count+=1
    used=sum(len(p.read_text().splitlines()) for p in (EXP/'logs').glob('*/api/requests.jsonl'))
    if used>=45: raise SystemExit('API safety limit exceeded (45 total attempts)')
    kwargs['max_retries']=min(2,45-used)
    try:
        return request_deepseek_token(prompt,**kwargs)
    except Exception as exc:
        if getattr(exc,'status_code',None) in (400,401,402,403,404,422,429):
            raise SystemExit('API stopped: '+type(exc).__name__+' status '+str(exc.status_code))
        raise

def smoke():
    d=EXP/'tests/environment';d.mkdir(parents=True,exist_ok=True)
    # This handwritten fixture tests only the environment; never an Agent output.
    (d/'smoke.py').write_text('from manim import *\nclass Smoke(Scene):\n def construct(self):\n  self.play(Create(Circle()))\n  self.wait(0.2)\n')
    r=safe_run(['manim','-ql','smoke.py','Smoke'],cwd=d,capture_output=True,text=True,timeout=180)
    print('ENVIRONMENT_SMOKE',r.returncode,flush=True)
    if r.returncode: print(r.stderr[-6000:]);raise RuntimeError('Environment smoke failed')
    test="""import os,socket
assert os.getuid()==62001
assert 'DEEPSEEK_API_KEY' not in os.environ
for path in ['/root/.ssh/id_ed25519','/root/autodl-tmp/code2biovideo/.env','/etc/shadow']:
 try: open(path).read(); raise AssertionError('secret readable: '+path)
 except PermissionError: pass
try: socket.socket(); raise AssertionError('network allowed')
except PermissionError: pass
try: open('/usr/sandbox-write-test','w'); raise AssertionError('runtime writable')
except PermissionError: pass
print('ISOLATION_OK')
"""
    r=safe_run(['python','-c',test],cwd=d,capture_output=True,text=True,timeout=30)
    print(r.stdout,r.stderr,flush=True)
    assert r.returncode==0,'Isolation test failed'

def run_topic(label,topic):
    start=time.monotonic(); before=len(render_events)
    audit=EXP/'logs'/label/'api';audit.mkdir(parents=True,exist_ok=True)
    os.environ['CODE2VIDEO_AUDIT_DIR']=str(audit)
    cfg=upstream.RunConfig(api=api,use_feedback=False,use_assets=False,feedback_rounds=1,
        max_fix_bug_tries=2,max_regenerate_tries=2,max_feedback_gen_code_tries=1,
        max_mllm_fix_bugs_tries=1,max_code_token_length=10000)
    agent=upstream.TeachingVideoAgent(0,topic,folder=REPO/'src/CASES'/label,cfg=cfg)
    result={'label':label,'topic':topic,'output_dir':str(agent.output_dir),
            'requested_model':os.environ['DEEPSEEK_MODEL'],'critic':False,'assets':False,
            'start_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'status':'started'}
    try:
        os.environ['CODE2VIDEO_STAGE']=label+':planner_outline'
        agent.generate_outline()
        os.environ['CODE2VIDEO_STAGE']=label+':planner_storyboard'
        agent.generate_storyboard()
        result['sections']=len(agent.sections)
        print('PLANNER_VALID',label,len(agent.sections),flush=True)
        for section in agent.sections:
            os.environ['CODE2VIDEO_STAGE']=label+':coder:'+section.id
            code=agent.generate_section_code(section)
            try: ast.parse(code); valid=True
            except SyntaxError: valid=False
            print('CODER_SYNTAX',section.id,valid,flush=True)
            os.environ['CODE2VIDEO_STAGE']=label+':render_repair:'+section.id
            ok=agent.render_section(section)
            print('SECTION_RESULT',section.id,ok,flush=True)
        result['successful_sections']=len(agent.section_videos)
        result['section_videos']=agent.section_videos
        if agent.section_videos:
            result['video']=agent.merge_videos()
        result['status']='success' if result.get('video') and len(agent.section_videos)==len(agent.sections) else 'partial_or_failed'
    except BaseException as exc:
        result.update(status='failed',error_type=type(exc).__name__,error=str(exc))
        traceback.print_exc()
        if isinstance(exc,SystemExit): raise
    finally:
        result['elapsed_seconds']=round(time.monotonic()-start,3)
        records=[json.loads(l) for l in (audit/'requests.jsonl').read_text().splitlines()] if (audit/'requests.jsonl').exists() else []
        result['api_attempts']=len(records)
        result['api_retries']=sum(r['attempt']>1 for r in records)
        result['usage']={k:sum(r.get('usage',{}).get(k,0) or 0 for r in records) for k in ['prompt_tokens','completion_tokens','total_tokens']}
        result['models']=sorted(set(r['model'] for r in records if 'model' in r))
        events=render_events[before:]
        renders=[r for r in events if r['cmd'][0]=='manim']
        result['render_attempts']=len(renders)
        result['render_attempt_successes']=sum(r.get('returncode')==0 for r in renders)
        result['render_retries']=len(renders)-len(set(tuple(r['cmd']) for r in renders))
        (EXP/'logs'/label/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print('TOPIC_RESULT',json.dumps(result,ensure_ascii=False),flush=True)
    return result

if __name__=='__main__':
    suffix=os.environ.get('CODE2VIDEO_RUN_SUFFIX','')
    topics=[('A2_math_deepseek_nonthinking'+suffix,'Linear transformations and matrices'),('B2_dna_deepseek_nonthinking'+suffix,'DNA replication in eukaryotic cells')]
    if any((EXP/'logs'/label/'metrics.json').exists() for label,_ in topics):
        raise SystemExit('Existing experiment frozen; set a unique CODE2VIDEO_RUN_SUFFIX and review the API attempt cap before rerunning.')
    smoke()
    for label,topic in topics:
        log=EXP/'logs'/label/'run.log';log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w',encoding='utf-8',buffering=1) as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
            run_topic(label,topic)
