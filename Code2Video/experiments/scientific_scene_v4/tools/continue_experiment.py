from pathlib import Path
import sys,json,copy,shutil,os
sys.path.insert(0,'/autodl-tmp/code2biovideo/Code2Video/experiments/scientific_scene_v4/tools')
import run_experiment as d
E=d.E
g,p=d.compile_topic('dna');ir=d.review_ir(g,p,'dna')
for label,mode in [('A1_stateful_assembly','assembly'),('A2_scene_graph_fsm','full')]:
 f=E/'groups'/label
 archive=f/'initial_before_adapter_fix';archive.mkdir(exist_ok=True)
 for name in ['status.json','source_manifest.json','video.mp4','geometry_trace.json','validation_report.json','rendered_code.py','scientific_video_review.json']:
  if (f/name).exists() and not (archive/name).exists():shutil.copy2(f/name,archive/name)
 d.render(label,g,(f/'generated_code.py').read_text(),mode,ir,tag='engineering_adapter_replay')
f=E/'groups/A3_expert_repair'
tasks=d.load(E/'repairs/repair_tasks.json')
prompt='''Second and FINAL scientific repair attempt. Prior code returned label/caption patches but did NOT implement its claimed center or tracking fixes; runtime rejected it. Generic engine has since been corrected separately by Codex (bounding-box center semantics, live binding update order); do not claim those changes as yours. Need fix primase/Pol-alpha conflation found in IR: use RNA primase-only label and explicitly note short Pol-alpha DNA handoff omitted in this local schematic. The existing lagging fragments start on the right (5prime) and end on the left (3prime), and gapfill end at x=-1.2 meets fragment1 START (5prime), joining 3prime to5prime; do not follow reviewer claims blindly to connect the wrong ends. Return JSON {"visual_patches":{"primase":{"label":"Primase"}},"simplifications":["..."],"code":"complete module defining Section4Scene(ScientificScene), importing ScientificScene from biology_runtime, construct calls self.render_scene(validation_mode='full')","repair_explanation":["..."]}. Only label patch allowed; no coordinate, identity, process, event or constraint changes. No misleading new polarity labels. No helper overrides or filesystem/process/network calls. Retain existing A2 successful code if possible.'''
resp=d.parse_json(d.gateway.request('deepseek','V4_A3_final_repair',prompt+json.dumps({'tasks':tasks,'graph':g,'a2_code':(E/'groups/A2_scene_graph_fsm/rendered_code.py').read_text()},ensure_ascii=False)))
d.write(f/'second_model_repair_response.json',resp)
new=copy.deepcopy(g)
for oid,patch in resp.get('visual_patches',{}).items():
 if oid!='primase' or set(patch)!={'label'}:raise ValueError('Repair outside scope')
 for obj in new['objects']:
  if obj['object_id']==oid:obj['visual_representation'].update(patch)
new['scientific_simplifications']+=resp.get('simplifications',[])
d.schema_validate('scene_graph',new)
review=d.review_ir(new,p,'dna_repaired')
st=d.render(f.name,new,d.clean(resp['code']),'full',review,science_required=True,tag='repair_2')
st['repair_attempts']=2
if st['render_success']:
 # First rejected candidate had no full-video review. This is the first actual new video review.
 final=d.video_review(f.name,new,p)
 approved=review['decision']=='PASS' and final['decision']=='PASS'
 st.update(science_gate=final['decision'],status='APPROVED' if approved else 'ROLLED_BACK',scientifically_committed=approved)
else:st.update(status='ROLLED_BACK',scientifically_committed=False)
if not st['scientifically_committed']:
 pointer=f/'render/.rollback2';pointer.symlink_to('versions/A2_frozen_source',target_is_directory=True);os.replace(pointer,f/'render/current')
st['published_video_path']=st.get('video_path') if st['scientifically_committed'] else str(E/'groups/A2_scene_graph_fsm/video.mp4')
st['candidate_video_path']=st.get('video_path');d.write(f/'status.json',st)
history=d.load(E/'repairs/repair_history.json');history.append({'attempt':2,'result':st,'ir_review':review,'engineering_changes_separate':True,'baseline_preserved':True});d.write(E/'repairs/repair_history.json',history)
for t in tasks:t['status']='APPROVED' if st['scientifically_committed'] else 'NEEDS_HUMAN_REVIEW'
d.write(E/'repairs/repair_tasks.json',tasks);d.archive_calls()
d.mitosis()
