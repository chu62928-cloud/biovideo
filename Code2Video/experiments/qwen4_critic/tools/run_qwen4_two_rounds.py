"""Observe two native Critic rounds, preserving baseline inputs and repair methods."""
import os,sys,json,time,shutil,difflib,hashlib
from pathlib import Path
R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video';E=REPO/'experiments/qwen4_critic'
sys.path.insert(0,str(R))
import run_deepseek_experiment as baseline
u=baseline.upstream
from gpt_request import request_deepseek_token
for line in (R/'.env').read_text().splitlines():
 if line and not line.startswith('#'):
  key,value=line.split('=',1);os.environ[key]=value
os.environ['QWEN_CRITIC_AUDIT_DIR']=str(E/'logs/critic')
os.environ['CODE2VIDEO_AUDIT_DIR']=str(E/'logs/coder')
SOURCE=REPO/'src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells'
def coder(prompt,**kwargs):
 base_used=sum(len(p.read_text().splitlines()) for p in (REPO/'experiments/biology_baseline/logs').glob('*/api/requests.jsonl'))
 ledger=E/'logs/coder/requests.jsonl';new_used=len(ledger.read_text().splitlines()) if ledger.exists() else 0
 if base_used+new_used>=45:raise SystemExit('Existing 45-attempt DeepSeek limit reached')
 kwargs['max_retries']=min(2,45-base_used-new_used)
 return request_deepseek_token(prompt,**kwargs)
cfg=u.RunConfig(api=coder,use_feedback=True,use_assets=False,feedback_rounds=2,
 max_fix_bug_tries=2,max_regenerate_tries=2,max_feedback_gen_code_tries=1,
 max_mllm_fix_bugs_tries=1,max_code_token_length=10000)
a=u.TeachingVideoAgent(0,'DNA replication in eukaryotic cells',folder=REPO/'src/CASES/C_qwen4_critic_two_rounds',cfg=cfg)
if (a.output_dir/'experiment_started.json').exists():raise SystemExit('Experiment already exists; refusing overwrite')
(a.output_dir/'experiment_started.json').write_text(json.dumps({'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':str(SOURCE),'topic':a.learning_topic,'critic_model':os.environ['QWEN_MODEL'],'feedback_rounds':2,'prompt_changes':False,'new_input_injections':False},indent=2))
for name in ['outline.json','storyboard.json',*[f'section_{i}.py' for i in range(1,7)]]:shutil.copy2(SOURCE/name,a.output_dir/name)
a.GRID_IMG_PATH=REPO/'src/assets/reference/GRID.png';a.GRID_IMG_PATH.parent.mkdir(exist_ok=True,parents=True)
shutil.copy2(REPO/'experiments/gemini3_critic_probe/GRID_upstream.png',a.GRID_IMG_PATH)
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob('*') if p.is_file() and p.suffix in ['.json','.py','.mp4']}
(E/'input_hashes.json').write_text(json.dumps(hashes,indent=2))
events=[];last_round={}
native_feedback=a.get_mllm_feedback;native_optimize=a.optimize_with_feedback
def observed_feedback(section,video_path,round_number=1):
 os.environ['CODE2VIDEO_STAGE']=f'round_{round_number}:critic:{section.id}';last_round[section.id]=round_number
 feedback=native_feedback(section,video_path,round_number)
 record={'section':section.id,'round':round_number,'input_video':video_path,'has_issues':feedback.has_issues,'suggested_improvements':feedback.suggested_improvements,'raw_response':feedback.raw_response}
 record['status']='critic_failed' if feedback.raw_response and feedback.raw_response.startswith('Error:') else 'critic_returned'
 dest=E/f'round_{round_number}'/'feedback';dest.mkdir(exist_ok=True,parents=True)
 (dest/(section.id+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2))
 if record['status']=='critic_failed':raise SystemExit('Critic failed; stop instead of treating as no issues')
 return feedback
def observed_optimize(section,feedback):
 rn=last_round[section.id];dest=E/f'round_{rn}'
 for name in ['code','scenes','diffs']:(dest/name).mkdir(exist_ok=True,parents=True)
 before=a.section_codes[section.id];os.environ['CODE2VIDEO_STAGE']=f'round_{rn}:native_optimize:{section.id}';t=time.monotonic()
 ok=native_optimize(section,feedback);after=a.section_codes[section.id]
 (dest/'code'/(section.id+'.py')).write_text(after)
 (dest/'diffs'/(section.id+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before',tofile='after')))
 video=a.section_videos.get(section.id)
 if video and Path(video).exists():shutil.copy2(video,dest/'scenes'/(section.id+'.mp4'))
 item={'section':section.id,'round':rn,'has_issues':feedback.has_issues,'improvements':len(feedback.suggested_improvements),'native_optimize_success':ok,'code_changed':before!=after,'elapsed_seconds':round(time.monotonic()-t,3),'video_present':bool(video and Path(video).exists()),'video_is_new_optimized_result':bool(ok and feedback.has_issues and feedback.suggested_improvements)}
 events.append(item);(E/'round_events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
 print('ROUND_RESULT',json.dumps(item),flush=True);return ok
a.get_mllm_feedback=observed_feedback;a.optimize_with_feedback=observed_optimize
started=time.monotonic();status='started'
try:
 a.generate_outline();a.generate_storyboard()
 for section in a.sections:
  os.environ['CODE2VIDEO_STAGE']='native_initial_code:'+section.id;a.generate_section_code(section)
  os.environ['CODE2VIDEO_STAGE']='native_render_section:'+section.id
  print('SECTION_RESULT',section.id,a.render_section(section),flush=True)
 a.merge_videos();status='completed'
except BaseException as exc:
 status='failed';print('EXPERIMENT_ERROR',type(exc).__name__,str(exc),flush=True)
 import traceback;traceback.print_exc()
finally:
 merged={};saved=dict(a.section_videos)
 for rn in [1,2]:
  videos={p.stem:str(p) for p in (E/f'round_{rn}'/'scenes').glob('*.mp4')}
  if videos:
   a.section_videos=videos;mp4=a.merge_videos(output_filename=f'DNA_qwen4_critic_round_{rn}.mp4')
   merged[str(rn)]={'video':mp4,'scenes':len(videos),'all_scenes':len(videos)==len(a.sections),'note':'Failed optimization can retain a previous successful video; consult round_events.json.'}
 a.section_videos=saved
 c=[json.loads(l) for l in (E/'logs/critic/requests.jsonl').read_text().splitlines()] if (E/'logs/critic/requests.jsonl').exists() else []
 d=[json.loads(l) for l in (E/'logs/coder/requests.jsonl').read_text().splitlines()] if (E/'logs/coder/requests.jsonl').exists() else []
 final={'status':status,'elapsed_seconds':round(time.monotonic()-started,3),'output_dir':str(a.output_dir),'rounds':merged,'events':events,'critic_attempts_including_probe':len(c),'coder_attempts':len(d),
  'critic_usage':{k:sum((x.get('usage') or {}).get(k,0) or 0 for x in c) for k in ['prompt_tokens','completion_tokens','total_tokens']},
  'coder_usage':{k:sum((x.get('usage') or {}).get(k,0) or 0 for x in d) for k in ['prompt_tokens','completion_tokens','total_tokens']}}
 (E/'metrics.json').write_text(json.dumps(final,ensure_ascii=False,indent=2));print('FINAL_METRICS',json.dumps(final,ensure_ascii=False),flush=True)
 for name,expected in hashes.items():assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==expected,'Frozen baseline modified'
