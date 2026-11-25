from pathlib import Path
import sys,os,json,copy,shutil,time
sys.path.insert(0,str(Path(__file__).parent))
import run as d
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.agent import BiologyExpertAgent
from scientific_scene.adapters.biology_expert_adapter import BiologyExpertSceneAdapter
from scientific_scene.scientific_review import RepairRouter,graph_polarity,ScientificConflictAdjudicator
from scientific_scene.models import digest,write
for line in (d.R.parent/'.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
gateway=ModelGateway(d.E/'logs',{'deepseek':6,'qwen':2},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096})
agent=BiologyExpertAgent(d.E/'agent',gateway);expert=BiologyExpertSceneAdapter(agent,d.E/'reviewer_fix/reviews')
def archive():
 (d.E/'logs/api_calls.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in gateway.rows))
 src=d.E/'agent/state/events.jsonl'
 if src.exists():shutil.copy2(src,d.E/'logs/tool_events.jsonl')

def main():
 assert d.load(d.E/'tests/test_results.json')['all_passed'],'Key offline tests not green'
 folder=d.E/'groups/B4_expert_repair';folder.mkdir(exist_ok=True)
 graph=d.load(d.E/'groups/B3_mechanism_fix/scene_graph.json');pack=d.load(d.E/'knowledge/dna_replication/knowledge_pack.json')
 checks=graph_polarity(graph,pack);write(folder/'polarity_before.json',checks)
 assert checks and all(c['status']=='PASS' for c in checks),'Polarity gate prevents paid generation'
 ir=expert.review_ir(graph,pack);write(folder/'ir_before.json',ir)
 calibration=d.load(d.E/'tests/test_results.json')
 conflicts=ScientificConflictAdjudicator().adjudicate(graph,pack,checks,ir,calibration);write(folder/'conflicts_before.json',conflicts)
 router=RepairRouter();issue={'issue_id':'primase_identity_mismatch','root_cause_stage':'SCENE_IR','target_artifact':'scene_ir/dna_section4.json','target_objects':['primase'],'target_fields':['scientific_identity.name','scientific_properties.role','visual_representation.label'],'acceptance_criteria':['Identity, role and display explicitly describe RNA primase only','Pol alpha short DNA handoff stays a declared omission, not assigned to RNA primase','No unrelated scientific field changes']}
 task=router.task(issue);write(d.E/'repair_routing/repair_tasks.json',[task]);write(d.E/'scene_ir/dna_section4.json',graph)
 prompt='''You are the existing DeepSeek Coder performing a REAL layered scientific repair, not rewriting thin animation code. Return JSON only {"patches":[{"object_id":"primase","field":"scientific_identity.name|scientific_properties.role|visual_representation.label","value":"appropriate string"}],"explanation":"brief"}. Must modify all inconsistent fields of primase to represent RNA primase only, without assigning Pol-alpha DNA polymerase activity. The omitted short Pol-alpha handoff remains declared in scientific_simplifications. Only the three exact fields listed in repair task may change. Do not modify polarity, coordinates, events, sources or other objects. This is a schematic local Section4; licensing and origins already covered Section2. The tool will check actual field changes before rendering; prose claims alone are REPAIR_NOT_APPLIED.'''
 response=parse_json(gateway.request('deepseek','V41_layered_IR_repair',prompt+json.dumps({'task':task,'current_object':next(o for o in graph['objects'] if o['object_id']=='primase'),'simplifications':graph.get('scientific_simplifications',[])},ensure_ascii=False)))
 write(folder/'model_patch_response.json',response)
 result=agent._call_registered_repair(router,task,response) if hasattr(agent,'_call_registered_repair') else None
 # Use real agent registry for execution, with explicit bounded callback.
 agent.registry.register('layered_artifact_repair',lambda task,patches:router.apply(d.E,task,patches))
 result=agent._call('layered_artifact_repair',{'task':task,'patches':response['patches']},'Repair the actual IR identity fields','Display-only prior repair did not change scientific identity; enforce target artifact/fields and reject no-op patches.')
 write(d.E/'repair_routing/repair_acceptance.json',result);write(d.E/'repair_routing/patch_diffs/primase_fields.json',result)
 if result['status']=='REPAIR_NOT_APPLIED':
  write(folder/'status.json',{'group':folder.name,'render_success':False,'science_gate':'REVISE','repair_status':'REPAIR_NOT_APPLIED','video_path':None});return
 repaired=d.load(d.E/'scene_ir/dna_section4.json');checks=graph_polarity(repaired,pack)
 assert all(c['status']=='PASS' for c in checks)
 ir2=expert.review_ir(repaired,pack);write(folder/'ir_after.json',ir2)
 conflicts2=ScientificConflictAdjudicator().adjudicate(repaired,pack,checks,ir2,calibration);write(folder/'conflicts_after.json',conflicts2)
 st=d.render(folder.name,repaired)
 if st['render_success']:
  rev=expert.review_video(repaired,pack,st['video_path'],(folder/'rendered_code.py').read_text(),d.load(folder/'geometry_trace.json'));write(folder/'video_review.json',rev)
  runtime=d.load(folder/'validation_report.json')
  resolved={c['original_issue']['issue_id'] for c in conflicts2 if c['status']=='REVIEWER_FALSE_POSITIVE'}
  remaining=[i for i in ir2.get('issues',[]) if i['issue_id'] not in resolved and i.get('severity') in ['blocker','major','uncertain']]
  ir_ok=ir2['decision']=='PASS' or (not remaining and ir2['decision']=='REVISE' and bool(resolved))
  approve=ir_ok and rev['decision']=='PASS' and all(c['status']=='PASS' for c in runtime) and all(c['status']=='PASS' for c in checks)
  st.update(ir_review_decision=ir2['decision'],video_review_decision=rev['decision'],science_gate='SCIENCE_APPROVED' if approve else 'REVISE',repair_attempts=1,repair_approved=approve,render_commit='RENDER_COMMITTED',conflicts=conflicts2,publish_pointer='candidate' if approve else 'B3_mechanism_fix',decision_basis={'ir_critical_remaining':remaining,'deterministic_all_pass':all(c['status']=='PASS' for c in runtime),'polarity_all_pass':True,'full_video':rev['decision']})
  # Separate scientific publication pointer. Engineering candidate stays inspectable.
  publish=d.E/'science_current';tmp=d.E/'.science_next'
  if tmp.exists() or tmp.is_symlink():tmp.unlink()
  target='groups/B4_expert_repair' if approve else 'groups/B3_mechanism_fix';tmp.symlink_to(target,target_is_directory=True);os.replace(tmp,publish)
  write(folder/'status.json',st)
 write(d.E/'repair_routing/repair_history.json',[{'task':task,'field_acceptance':result,'result':st,'model_patch_response':str(folder/'model_patch_response.json'),'published_candidate':st.get('repair_approved',False),'original_preserved':True}])
 task['status']='SCIENCE_APPROVED' if st.get('repair_approved') else 'ROLLED_BACK';write(d.E/'repair_routing/repair_tasks.json',[task])

if __name__=='__main__':
 try:main()
 finally:archive()
