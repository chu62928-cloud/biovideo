"""V4 experiment runner. Real model outputs, immutable historical inputs, diagnostic gates."""
from pathlib import Path
import os, sys, json, time, copy, shutil, traceback, subprocess, hashlib, re
R=Path('/autodl-tmp/code2biovideo/Code2Video').resolve()
E=R/'experiments/scientific_scene_v4'
sys.path.insert(0,str(R/'src'))
from scientific_scene.models import write,digest,schema_validate
from scientific_scene.scene_compiler import compile_storyboard
from scientific_scene.validation import validate_runtime
from scientific_scene.adapters.biology_expert_adapter import BiologyExpertSceneAdapter
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway,parse_json
from biology_v2_pipeline import TransactionRenderer,sha,trace_metrics

def load(p):return json.loads(Path(p).read_text())
def clean(s):
 m=re.search(r'```(?:python)?\s*([\s\S]*?)```',s)
 return (m.group(1) if m else s).strip()+'\n'
for line in (R.parent/'.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
gateway=ModelGateway(E/'logs',{'deepseek':10,'qwen':3},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096})
agent=BiologyExpertAgent(E/'agent',gateway)
expert=BiologyExpertSceneAdapter(agent,E/'validation/reviews')

def archive_calls():
 (E/'logs/api_calls.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in gateway.rows))
 source=E/'agent/state/events.jsonl'
 if source.exists():shutil.copy2(source,E/'logs/tool_events.jsonl')

def compile_topic(topic):
 b=load(E/'scene_ir'/f'{topic}_blueprint.json');p=load(E/'knowledge'/b['topic_id']/'knowledge_pack.json');s=load(E/'scene_ir'/f'{topic}_storyboard_input.json')
 dest=E/'scene_ir'/topic;dest.mkdir(exist_ok=True)
 if (dest/'scene_graph.json').exists():return load(dest/'scene_graph.json'),p
 out=compile_storyboard(s,p,b,gateway=gateway)
 for key,val in out.items():write(dest/(key+'.json'),val)
 g=out['scene_graph'];g['title']=s['title'];write(dest/'scene_graph.json',g)
 write(E/'scene_ir'/('dna_section4.json' if topic=='dna' else 'mitosis_short.json'),g)
 return g,p

def review_ir(g,p,label):
 dest=E/'validation'/(label+'_ir_review.json')
 if dest.exists():return load(dest)
 out=expert.review_ir(g,p);write(dest,out);return out

def payload(g,folder):
 dest=folder/'payload'
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(E/'assets',dest)
 shutil.copytree(R/'src/scientific_scene',dest/'scientific_scene',ignore=shutil.ignore_patterns('__pycache__'))
 (dest/'__init__.py').write_text('')
 write(dest/'scene_graph.json',g)
 runtime=folder/'biology_runtime_v4.py'
 runtime.write_text((R/'src/biology_runtime.py').read_text()+'\nfrom assets.scientific_scene.adapters.manim_adapter import ScientificScene\n')
 return dest,runtime

def coder(g,mode,label,previous=None,repair=None):
 prompt='''You are the existing Code2Video DeepSeek Coder. Generate a COMPLETE Python module, ONLY one python fenced block. Define Section4Scene(ScientificScene), import ScientificScene from biology_runtime. The supplied graph is a complete editable scientific assembly and model-planned teaching events. The trusted general adapter creates all components and binds real anchors; call self.render_scene(validation_mode=MODE) inside construct. MODE is exactly the supplied mode. Do not rebuild the prepared components or duplicate the lesson manually. Do not override setup/tear_down/capture_geometry/apply_transition. No filesystem, process, network, eval, exec, getattr, setattr. Do not introduce new molecular objects or alter the science merely to improve layout. You may set self.camera.background_color and introduce a short final hold via self.wait if appropriate; do not exceed duration bounds. This thin experimental module is genuinely model-generated; engineering component/recipe contribution is tracked separately. Use only biology_runtime, manim, numpy, math imports. Return executable code, no explanations.'''
 data={'mode':mode,'scene_graph':g,'previous_successful_code':previous,'repair_task':repair}
 return clean(gateway.request('deepseek',label,prompt+json.dumps(data,ensure_ascii=False)))

def render(label,g,code,mode,ir,science_required=False,tag='initial'):
 folder=E/'groups'/label;folder.mkdir(parents=True,exist_ok=True)
 write(folder/'scene_graph.json',g);write(folder/'assembly_states.json',[x['state_variables'] for x in g['assemblies']]);write(folder/'state_transitions.json',g['state_transitions'])
 write(folder/'config.json',{'group':label,'mode':mode,'model':os.environ['DEEPSEEK_MODEL'],'shared_blueprint':g['provenance'],'sampling':'Existing provider defaults, unchanged','ir_review_decision':ir['decision'],'diagnostic_if_not_pass':True})
 (folder/('generated_code.py' if tag=='initial' else tag+'_generated_code.py')).write_text(code)
 assets,runtime=payload(g,folder)
 tx=TransactionRenderer(folder/'render',runtime,assets,duration_range=(25,36) if g['topic_id']=='dna_replication' else (8,16))
 def check(stage,trace,layout):
  checks=validate_runtime(g,trace);write(stage/'validation_report.json',checks)
  if science_required and any(c['status']!='PASS' for c in checks):raise ValueError('Scientific runtime gate requires all necessary checks PASS')
 result=tx.attempt(code,tag,extra_validator=check)
 write(folder/(tag+'_transaction.json'),result)
 log=E/'logs/render_events.jsonl'
 with log.open('a') as f:f.write(json.dumps({'group':label,**result})+'\n')
 state={'group':label,'status':'COMPLETED' if result['committed'] else 'RENDER_FAILED','generation_attempted':True,'render_success':result['committed'],'science_gate':'PENDING' if result['committed'] else 'ERROR','ir_science_gate':ir['decision'],'video_path':None,'unresolved_blockers':[],'code_sha256':None,'video_sha256':None,'repair_attempts':0}
 if result['committed']:
  version=Path(result['after']['version'])
  for name in ['rendered_code.py','video.mp4','geometry_trace.json','validation_report.json','layout_metrics.json']:shutil.copy2(version/name,folder/name)
  trace=load(folder/'geometry_trace.json');checks=load(folder/'validation_report.json')
  state.update(video_path=str(folder/'video.mp4'),code_sha256=sha(folder/'rendered_code.py'),video_sha256=sha(folder/'video.mp4'),duration_seconds=result['after']['duration_seconds'],science_gate='REVISE' if any(c['status']=='FAIL' for c in checks) else 'NEEDS_HUMAN_REVIEW')
  write(folder/'assembly_states.json',trace.get('expected_snapshots',[]))
  subprocess.run([str(R.parent/'env/bin/ffmpeg'),'-y','-v','error','-ss','2','-i',str(folder/'video.mp4'),'-frames:v','1',str(folder/'preview.jpg')],check=True)
  write(folder/'source_manifest.json',{'code_sha256':state['code_sha256'],'video_sha256':state['video_sha256'],'trace_sha256':sha(folder/'geometry_trace.json'),'scene_hash':digest(g),'ir_review_id':ir.get('review_id'),'component_library_hashes':{str(p.relative_to(R)):sha(p) for p in (R/'src/scientific_scene').rglob('*.py')},'code_origin':'REAL_DEEPSEEK_CODER','plan_origin':g['provenance']['plan_origin'],'component_recipes_origin':'CODEX_ENGINEERING_PREPARATION','review_is_not_student_evaluation':True})
 else:
  state.update(error=result.get('error'),failed_stage='FULL_RENDER_OR_RUNTIME_GATE')
 write(folder/'status.json',state);return state

def baseline():
 f=E/'groups/A0_v3_baseline';f.mkdir(exist_ok=True)
 if (f/'status.json').exists():return
 v=R/'experiments/biology_expert_v3/outputs/REP-dd947104c24f/render/attempts/scientific_attempt_2_format_replay'
 code=v/'rendered_code.py';video=v/'media/videos/rendered_code/480p15/Section4Scene.mp4'
 write(f/'source_manifest.json',{'code_path':str(code),'video_path':str(video),'code_sha256':sha(code),'video_sha256':sha(video),'reference_only':True,'rerendered':False})
 write(f/'config.json',{'baseline':'Frozen actual V3 repair candidate, NOT APPROVED'})
 write(f/'status.json',{'group':'A0_v3_baseline','status':'FROZEN_REFERENCE','generation_attempted':False,'render_success':True,'science_gate':'REVISE','video_path':str(video),'code_path':str(code),'code_sha256':sha(code),'video_sha256':sha(video),'known_issues':['fork topology ambiguity','ligase nick adjacency','leading polymerase label origin CODE'],'scene_graph':None,'reason_missing_scene_ir':'V3 baseline predates V4 IR; no reconstructed graph passed off as original'})

def initial_dna():
 baseline();g,p=compile_topic('dna');ir=review_ir(g,p,'dna')
 previous=None
 for label,mode in [('A1_stateful_assembly','assembly'),('A2_scene_graph_fsm','full')]:
  f=E/'groups'/label
  if (f/'status.json').exists():
   st=load(f/'status.json')
   if st.get('render_success'):previous=(f/'rendered_code.py').read_text()
   continue
  f.mkdir(exist_ok=True)
  code=coder(g,mode,'V4_'+label,previous)
  st=render(label,g,code,mode,ir)
  if st['render_success']:previous=code
 archive_calls()

def video_review(label,g,p):
 f=E/'groups'/label;dest=f/'scientific_video_review.json'
 if dest.exists():return load(dest)
 out=expert.review_video(g,p,str(f/'video.mp4'),(f/'rendered_code.py').read_text(),load(f/'geometry_trace.json'))
 write(dest,out);st=load(f/'status.json');st['science_gate']=out['decision'];st['unresolved_blockers']=[x['issue_id'] for x in out.get('issues',[])];write(f/'status.json',st)
 return out

def repair():
 g,p=compile_topic('dna');ir=review_ir(g,p,'dna');src=E/'groups/A2_scene_graph_fsm';dest=E/'groups/A3_expert_repair';dest.mkdir(exist_ok=True)
 if not load(src/'status.json').get('render_success'):
  write(dest/'status.json',{'group':dest.name,'status':'NOT_ATTEMPTED','render_success':False,'science_gate':'ERROR','video_path':None,'reason':'A2 has no actual successful render'});return
 review=video_review(src.name,g,p)
 issues=review.get('issues',[])
 if not issues:
  # Deterministic uncertainty/failure is also a legitimate located repair source.
  issues=[{'issue_id':c['check_id'],'root_cause_stage':c['suggested_repair_stage'],'target_objects':c['object_ids'],'target_events':c['event_ids'],'repair_scope':'affected_event','description':c['description'] or c['expected_condition'],'acceptance_criteria':[c['expected_condition']]} for c in review['checks'] if c['status']!='PASS']
 if not issues:
  write(dest/'status.json',{'group':dest.name,'status':'NOT_ATTEMPTED','render_success':False,'science_gate':'NEEDS_HUMAN_REVIEW','video_path':None,'reason':'No evidence-backed repair target; no gratuitous change','a2_review':review['review_id']});return
 tasks=[dict(repair_id='REP-V4-'+str(i+1),issue_id=x['issue_id'],root_cause_stage=x['root_cause_stage'],target_objects=x.get('target_objects',[]),target_events=x.get('target_events',[]),repair_scope=x.get('repair_scope','affected_event'),preserve_constraints=['same persistent identities','same events','unaffected assembly components'],acceptance_criteria=x.get('acceptance_criteria',[]),required_validators=['schema','runtime','full_decode','full_video_science'],status='PENDING',description=x.get('description','')) for i,x in enumerate(issues)]
 write(E/'repairs/repair_tasks.json',tasks)
 prompt='''You are the existing DeepSeek Coder working on scientific repair. Return JSON only {"visual_patches": {"EXACT object ID": {"label": "...", "label_side":"up|down", "label_size":16}}, "caption_patches":{"EXACT event ID":"..."},"code":"COMPLETE Python module","repair_explanation":["..."]}. Change only affected representations/captions; preserve scientific coordinates, identities, processes, all constraints and unrelated components. This bounded patch surface cannot change assembly topology or process chemistry. If a repair needs topology/chemical changes, return empty patches and explanation stating NEEDS_HUMAN_REVIEW at its true root layer; do not claim layout fixes the science. Code imports ScientificScene from biology_runtime; Section4Scene.construct calls self.render_scene(validation_mode='full'). No filesystem/process/network operations, no helper overrides. Ensure visually legible, honest scientific simplifications. Preserve the supplied successful A2 code where possible.'''
 response=parse_json(gateway.request('deepseek','V4_A3_scientific_repair',prompt+json.dumps({'repair_tasks':tasks,'scene_graph':g,'successful_code':(src/'rendered_code.py').read_text()},ensure_ascii=False)))
 write(dest/'model_repair_response.json',response)
 repaired=copy.deepcopy(g);objs={o['object_id']:o for o in repaired['objects']};events={e['event_id']:e for e in repaired['events']}
 for oid,patch in response.get('visual_patches',{}).items():
  if oid not in objs or not set(patch)<={'label','label_side','label_size','label_color'}:raise ValueError('Repair exceeds allowed representation boundary')
  objs[oid]['visual_representation'].update(patch)
 for eid,caption in response.get('caption_patches',{}).items():events[eid]['caption']=caption
 schema_validate('scene_graph',repaired)
 # Reuse exact A2 baseline in the transaction; candidate publication requires scientific checks.
 assets,runtime=payload(g,dest);tx=TransactionRenderer(dest/'render',runtime,assets,duration_range=(25,36))
 seed=dest/'render/versions/A2_frozen_source';seed.mkdir(parents=True,exist_ok=True)
 for name in ['rendered_code.py','video.mp4','geometry_trace.json']:shutil.copy2(src/name,seed/name)
 write(seed/'status.json',{'success':True,'tag':'A2_frozen_source','code_sha256':sha(seed/'rendered_code.py'),'video_sha256':sha(seed/'video.mp4'),'duration_seconds':load(src/'status.json')['duration_seconds']})
 pointer=dest/'render/current'
 if not pointer.exists():pointer.symlink_to('versions/A2_frozen_source',target_is_directory=True)
 code=clean(response['code']);st=render(dest.name,repaired,code,'full',ir,science_required=True,tag='repair_1')
 st['repair_attempts']=1
 if st['render_success']:
  final=video_review(dest.name,repaired,p)
  approved=final['decision']=='PASS' and ir['decision']=='PASS'
  if not approved:
   tx=TransactionRenderer(dest/'render',runtime,assets)
   temp=dest/'render/.rollback';temp.symlink_to('versions/A2_frozen_source',target_is_directory=True);os.replace(temp,dest/'render/current')
   st.update(science_gate=final['decision'],status='ROLLED_BACK',scientifically_committed=False)
  else:st.update(science_gate='PASS',status='APPROVED',scientifically_committed=True)
 else:st.update(status='ROLLED_BACK',scientifically_committed=False)
 st['candidate_video_path']=st.get('video_path');st['published_video_path']=str(src/'video.mp4')
 write(dest/'status.json',st)
 for task in tasks:task['status']='APPROVED' if st['status']=='APPROVED' else ('NEEDS_HUMAN_REVIEW' if task['root_cause_stage'] in ['ASSEMBLY','PROCESS_TEMPLATE','SCENE_IR'] else 'ROLLED_BACK')
 write(E/'repairs/repair_tasks.json',tasks);write(E/'repairs/repair_history.json',[{'attempt':1,'tasks':tasks,'result':st,'model_response':str(dest/'model_repair_response.json'),'baseline_preserved':sha(src/'video.mp4')==sha(seed/'video.mp4')}]);archive_calls()

def mitosis():
 g,p=compile_topic('mitosis');ir=review_ir(g,p,'mitosis');label='B1_mitosis';f=E/'groups'/label
 if not (f/'status.json').exists():
  code=coder(g,'full','V4_B1_mitosis');render(label,g,code,'full',ir)
 if load(f/'status.json').get('render_success'):video_review(label,g,p)
 archive_calls()

if __name__=='__main__':
 try:
  {'dna':initial_dna,'repair':repair,'mitosis':mitosis}[sys.argv[1]]()
 except Exception:
  traceback.print_exc();raise
 finally:archive_calls()
