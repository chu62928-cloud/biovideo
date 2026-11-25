"""V4 plugin for the existing single BiologyExpertAgent; generation and review remain separate."""
import json,uuid,copy
from ..models import Assembly,write,digest,schema_validate
from ..state_machine import TransitionEngine
from ..validation import validate_graph,validate_runtime,item
from biology_expert.providers import parse_json
class BiologyExpertSceneAdapter:
 def __init__(self,agent,root):
  self.agent=agent;self.root=root
  agent.registry.register('scene_graph_validator',self.inspect)
 def inspect(self,graph,pack):
  checks=validate_graph(graph,pack)
  a=Assembly(graph['assemblies'][0],graph['objects']);engine=TransitionEngine()
  for step in graph['state_transitions']:
   result=engine.apply(a,step)
   checks.append(item(step['transition_id'],'state_transition','PASS' if result['committed'] else 'FAIL',step['targets'],evidence=step['evidence_ids'],observed=result,expected='Pre/post/invariants satisfied; failed action retains previous state'))
   if not result['committed']:break
  return checks
 def review_ir(self,graph,pack):
  checks=self.agent._call('scene_graph_validator',{'graph':graph,'pack':pack},'Review compiled Scene IR','Verify real schemas, references and executable transitions before asking for semantic judgment.')
  failed=any(c['status'] in ['FAIL','ERROR'] for c in checks)
  prompt="""You are the BiologyExpertAgent's scientific Scene IR review tool. Review objects, continuous identity/topology, biological roles, event ordering, transition pre/postconditions and stated simplifications. The graph and reusable recipes were generated/prepared independently of this review. Use verified knowledge facts and actual source excerpts. Return JSON {"decision":"PASS|REVISE|NEEDS_HUMAN_REVIEW|ERROR","issues":[{"issue_id":"...","severity":"blocker|major|minor|uncertain","description":"...","root_cause_stage":"SCENE_IR|ASSEMBLY|PROCESS_TEMPLATE|ANIMATION_IMPLEMENTATION|KNOWLEDGE","target_objects":[],"target_events":[],"repair_scope":"...","acceptance_criteria":["..."]}],"notes":["..."]}. At most3 important issues, concise. Do not demand processes outside the declared teaching scope. A cartoon is not a real molecule; distinguish schematic geometry from science. Look at connection continuity and genuine adjacent endpoints, not 'validated=true'. An uncertainty important to the teaching mechanism cannot be passed automatically. Check that role labels match the common teaching model, and identify the earliest artifact where a concrete bad label appears. No scientific PASS if deterministic checks fail."""
  payload={'facts':[f for f in pack['facts'] if f['verification']=='VERIFIED'],'graph':graph,'measured_static_checks':checks}
  semantic=parse_json(self.agent.gateway.request('deepseek','V4_IR_science_review',prompt+json.dumps(payload,ensure_ascii=False)))
  decision='REVISE' if failed else semantic['decision']
  if any(i['severity']=='blocker' for i in semantic.get('issues',[])) and decision=='PASS':decision='REVISE'
  out={'review_id':'V4-IR-'+uuid.uuid4().hex[:10],'stage':'SCENE_IR','decision':decision,'issues':semantic.get('issues',[]),'notes':semantic.get('notes',[]),'checks':checks,'scene_hash':digest(graph)}
  write(self.root/(out['review_id']+'.json'),out)
  return out
 def review_video(self,graph,pack,video,code,trace):
  checks=validate_runtime(graph,trace)
  prompt="""Scientifically review the COMPLETE MP4 with the supplied stateful Scene IR, actual measured anchors/paths and transition observations. This is scientific meaning, not a layout-only review. Check topology/identity/primer-before-extension, extension at a consistent growing end, genuine adjacent nick endpoints, or sister-chromatid attachment then separation as appropriate to the actual topic. No need to review unrelated processes. A layout change alone cannot fix mechanism.
Return JSON {"science":{"decision":"PASS|REVISE|NEEDS_HUMAN_REVIEW|ERROR","issues":[{"issue_id":"...","severity":"blocker|major|minor|uncertain","description":"...","root_cause_stage":"SCENE_IR|ASSEMBLY|PROCESS_TEMPLATE|ANIMATION_IMPLEMENTATION","target_objects":["EXACT declared ID"],"target_events":["EXACT event ID"],"repair_scope":"affected_event|assembly_geometry|process_rule","acceptance_criteria":["measurable correction"]}],"notes":["..."]}}. At most3 issues, each under80words. Use only actual IDs. The grid is a spatial reference, not a layout requirement. If unreadable/ambiguous, report uncertainty. Distinguish an observed scientific error from an optional extra teaching detail. Schematic polarity/copy count cannot be proven by a label alone. Keep response concise complete JSON; do not reproduce all source/code.
"""
  payload={'facts':[f for f in pack['facts'] if f['verification']=='VERIFIED'],'graph':graph,'actual_checks':checks,'actual_code':code,'runtime_events':trace.get('events',[]),'actual_observations_sample':trace.get('scientific_observations',[])[::max(1,len(trace.get('scientific_observations',[]))//10)]}
  try:
   data=parse_json(self.agent.gateway.request('qwen','V4_complete_video_science',prompt+json.dumps(payload,ensure_ascii=False),video=video))['science']
   unknown=set(x for i in data.get('issues',[]) for x in i.get('target_objects',[]))-{o['object_id'] for o in graph['objects']}
   if unknown:raise ValueError('Reviewer cited unknown objects: '+str(unknown))
   decision=data['decision']
   if any(c['status']=='FAIL' for c in checks):decision='REVISE'
   if decision=='PASS' and any(i['severity']=='blocker' for i in data.get('issues',[])):decision='REVISE'
   if decision=='PASS' and any(c['status'] in ['UNCERTAIN','NOT_MEASURED','ERROR'] for c in checks):decision='NEEDS_HUMAN_REVIEW'
   out={'review_id':'V4-VIDEO-'+uuid.uuid4().hex[:10],'stage':'RENDERED_VIDEO','decision':decision,'issues':data.get('issues',[]),'notes':data.get('notes',[]),'checks':checks,'scene_hash':digest(graph),'video_sha256':__import__('hashlib').sha256(__import__('pathlib').Path(video).read_bytes()).hexdigest(),'code_sha256':__import__('hashlib').sha256(code.encode()).hexdigest(),'full_video':True}
  except Exception as e:out={'review_id':'V4-VIDEO-'+uuid.uuid4().hex[:10],'stage':'RENDERED_VIDEO','decision':'ERROR','issues':[],'error_type':type(e).__name__,'error':str(e),'checks':checks,'full_video':True}
  write(self.root/(out['review_id']+'.json'),out);return out


def repair_tasks(review):
 return [{'repair_id':'REP-'+i['issue_id'],'issue_id':i['issue_id'],'root_cause_stage':i['root_cause_stage'],'target_objects':i.get('target_objects',[]),'target_events':i.get('target_events',[]),'repair_scope':i.get('repair_scope','affected_event'),'preserve_constraints':['persistent identity','unaffected events'],'acceptance_criteria':i.get('acceptance_criteria',[]),'required_validators':['schema','runtime','full_decode','video_science'],'status':'PENDING'} for i in review.get('issues',[])]
