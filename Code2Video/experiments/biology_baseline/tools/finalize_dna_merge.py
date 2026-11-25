import contextlib,json,shutil,time
from pathlib import Path
import run_deepseek_experiment as drv
label='B2_dna_deepseek_nonthinking'
folder=drv.EXP/'logs'/label;p=folder/'metrics.json'
old=json.loads(p.read_text());shutil.copy2(p,folder/'metrics_before_merge_wrapper_fix.json')
start=time.monotonic()
with (folder/'merge_recovery.log').open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
 cfg=drv.upstream.RunConfig(api=drv.api,use_feedback=False,use_assets=False)
 a=drv.upstream.TeachingVideoAgent(0,old['topic'],folder=drv.REPO/'src/CASES'/label,cfg=cfg)
 a.section_videos=old['section_videos']
 old['video']=a.merge_videos()
 old['status']='success' if old['video'] and old['successful_sections']==old['sections'] else 'partial_or_failed'
 old['merge_recovery_seconds']=round(time.monotonic()-start,3)
 old['elapsed_seconds']+=old['merge_recovery_seconds']
 p.write_text(json.dumps(old,ensure_ascii=False,indent=2))
print(old['status'],old.get('video'))
