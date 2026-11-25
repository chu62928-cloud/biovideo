"""Re-test existing Agent code after TeX environment repair; preserve prior metrics."""
import contextlib,json,time,shutil,os
from pathlib import Path
import run_deepseek_experiment as drv

label='A2_math_deepseek_nonthinking'
folder=drv.EXP/'logs'/label
p=folder/'metrics.json'
assert p.exists(),'Wait for the main run to finish first'
old=json.loads(p.read_text());shutil.copy2(p,folder/'metrics_before_environment_recovery.json')
start=time.monotonic()
os.environ['CODE2VIDEO_AUDIT_DIR']=str(folder/'api')
cfg=drv.upstream.RunConfig(api=drv.api,use_feedback=False,use_assets=False,
    max_fix_bug_tries=2,max_regenerate_tries=1,max_code_token_length=10000)
with (folder/'environment_recovery.log').open('w',buffering=1) as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
 agent=drv.upstream.TeachingVideoAgent(0,old['topic'],folder=drv.REPO/'src/CASES'/label,cfg=cfg)
 agent.generate_outline();agent.generate_storyboard()
 for section in agent.sections:
  os.environ['CODE2VIDEO_STAGE']=label+':environment_recovery:'+section.id
  agent.generate_section_code(section)
  scene=section.id.title().replace('_','')+'Scene'
  video=agent.output_dir/'media/videos'/section.id/'480p15'/(scene+'.mp4')
  if video.exists():agent.section_videos[section.id]=str(video)
  else: print('RECOVERY_RESULT',section.id,agent.render_section(section),flush=True)
 if old.get('video') and Path(old['video']).exists():
  shutil.copy2(old['video'],Path(old['video']).with_suffix('.before_environment_recovery.mp4'))
 old['video']=agent.merge_videos() if agent.section_videos else None
 old['successful_sections']=len(agent.section_videos);old['section_videos']=agent.section_videos
 old['status']='success' if len(agent.section_videos)==len(agent.sections) else 'partial_or_failed'
 old['environment_recovery_seconds']=round(time.monotonic()-start,3)
 old['elapsed_seconds']+=old['environment_recovery_seconds']
 old['render_attempts']+=sum(e['cmd'][0]=='manim' for e in drv.render_events)
 old['render_attempt_successes']+=sum(e['cmd'][0]=='manim' and e.get('returncode')==0 for e in drv.render_events)
 records=[json.loads(l) for l in (folder/'api/requests.jsonl').read_text().splitlines()]
 old['api_attempts']=len(records);old['api_retries']=sum(r['attempt']>1 for r in records)
 old['usage']={k:sum(r.get('usage',{}).get(k,0) or 0 for r in records) for k in ['prompt_tokens','completion_tokens','total_tokens']}
 old['note']='Contains environment failures, long installation pause and recovery; not clean model latency.'
 p.write_text(json.dumps(old,ensure_ascii=False,indent=2))
 print(json.dumps(old,ensure_ascii=False),flush=True)
print('Recovery complete',old['status'],old['successful_sections'])
