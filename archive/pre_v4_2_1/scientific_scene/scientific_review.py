"""Evidence-bound polarity, conflict adjudication and actual artifact repair."""
import copy, json, math, hashlib
from pathlib import Path
from .models import anchor,digest,schema_validate,Assembly
from .state_machine import TransitionEngine

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def polarity_check(template,nascent,before,after,evidence_ids,verified_ids):
 out={'check_id':'polarity_'+nascent['object_id'],'stage':'SCENE_IR','status':'UNCERTAIN','object_ids':[template['object_id'],nascent['object_id']],'rule_ids':['DNA_STRAND_POLARITY'],'evidence_ids':evidence_ids,'expected':{'nascent_addition_port':"3'",'template_reading':"3' to 5'",'antiparallel':True},'observed':{},'validator':'deterministic_local_path','artifact_sha256':digest([template,nascent,before,after])}
 labels=template['scientific_properties'].get('endpoint_labels',{});ends=nascent['scientific_properties'].get('endpoint_labels',{})
 growth=nascent['scientific_properties'].get('growth_port')
 if set(labels)!={'start','end'} or set(labels.values())!={"3'","5'"} or growth not in ends or not evidence_ids or not set(evidence_ids)<=set(verified_ids):return out
 tpoints=template['visual_representation'].get('points',[])
 if len(tpoints)<2 or len(before)<2 or len(after)<2:return out
 # Local template segment nearest the actual growing tip, invariant to rotation/mirroring.
 tip=after[-1] if growth=='end' else after[0]
 nearest=min(zip(tpoints,tpoints[1:]),key=lambda ab:math.dist(tip,[(x+y)/2 for x,y in zip(*ab)]))
 tangent=sub(nearest[1],nearest[0]);read=tangent if labels['start']=="3'" else [-x for x in tangent]
 delta=sub(after[-1],before[-1]) if growth=='end' else sub(after[0],before[0])
 other_delta=math.dist(after[0],before[0]) if growth=='end' else math.dist(after[-1],before[-1])
 direction=sub(after[-1],after[0]);synthesis=direction if ends.get('start')=="5'" and ends.get('end')=="3'" else ([-x for x in direction] if ends.get('start')=="3'" and ends.get('end')=="5'" else None)
 if ends[growth]!="3'":
  out['status']='FAIL';out['observed']={'wrong_growth_port_label':ends[growth]};return out
 if synthesis is None or math.sqrt(dot(delta,delta))<1e-8:return out
 cos=dot(delta,read)/(math.sqrt(dot(delta,delta)*dot(read,read)) or 1)
 out['observed']={'local_template_reading_vector':read,'growth_vector':delta,'reading_alignment_cosine':cos,'growth_port':growth,'growth_port_label':ends[growth],'opposite_end_motion':other_delta,'synthesis_alignment':dot(synthesis,read)}
 out['status']='PASS' if ends[growth]=="3'" and cos>.5 and dot(synthesis,read)>0 and other_delta<1e-6 else 'FAIL'
 return out

def graph_polarity(graph,pack):
 verified={f['fact_id'] for f in pack['facts'] if f.get('verification')=='VERIFIED'}
 objects={o['object_id']:copy.deepcopy(o) for o in graph['objects']};results=[]
 for action in graph['state_transitions']:
  if action['operation']=='extend':
   oid=action['targets'][0];obj=objects[oid];template_id=obj['scientific_properties'].get('template_id')
   if template_id in objects:
    results.append(polarity_check(objects[template_id],obj,obj['visual_representation']['points'],action['params']['points'],obj['scientific_properties'].get('polarity_evidence_ids',[]),verified))
   elif obj['scientific_properties'].get('material')=='DNA':
    results.append({'check_id':'polarity_'+oid,'stage':'SCENE_IR','status':'UNCERTAIN','object_ids':[oid],'rule_ids':['DNA_STRAND_POLARITY'],'evidence_ids':[],'expected':{},'observed':{'reason':'No template mapping or growth-port contract'},'validator':'deterministic_local_path','artifact_sha256':digest(obj)})
  for oid,changes in action.get('params',{}).get('visual_updates',{}).items():objects[oid]['visual_representation'].update(copy.deepcopy(changes))
  if action['operation']=='extend':objects[action['targets'][0]]['visual_representation']['points']=copy.deepcopy(action['params']['points'])
 return results

class ScientificConflictAdjudicator:
 def adjudicate(self,graph,pack,checks,review,calibration):
  facts={f['fact_id'] for f in pack['facts'] if f.get('verification')=='VERIFIED'};out=[]
  for issue in review.get('issues',[]):
   # Structured rule IDs are required for new reviews. Historical issues are explicitly
   # mapped in a separate provenance file, never classified by arbitrary wording alone.
   if issue.get('rule_id')!='DNA_STRAND_POLARITY':continue
   ids=set(issue.get('target_objects',[]));relevant=[c for c in checks if ids.intersection(c['object_ids'])]
   status='NEEDS_HUMAN_REVIEW';resolution=None
   evidence=set(x for c in relevant for x in c['evidence_ids'])
   if relevant and all(c['status']=='PASS' for c in relevant) and evidence and evidence<=facts and calibration.get('all_passed') and calibration.get('includes_negative_controls'):
    status='REVIEWER_FALSE_POSITIVE';resolution='Scoped polarity claim contradicted by source-bound local-path evidence and positive/negative/rotation tests. Other issues retained.'
   out.append({'conflict_id':'CONFLICT_'+issue['issue_id'],'rule_id':'DNA_STRAND_POLARITY','deterministic_result':'PASS' if relevant and all(c['status']=='PASS' for c in relevant) else 'UNCERTAIN','llm_result':'FAIL','status':status,'reason':issue.get('description'),'repair_allowed':False,'resolution':resolution,'evidence_ids':sorted(evidence),'scene_sha256':digest(graph),'original_issue':copy.deepcopy(issue),'calibration_sha256':digest(calibration)})
  return out

class RepairRouter:
 ARTIFACTS={'KNOWLEDGE':'knowledge/knowledge_pack.json','SCRIPT':'script/section4.json','ASSET':'assets/asset_registry.json','ASSEMBLY':'assemblies/assembly.json','SCENE_IR':'scene_ir/dna_section4.json','PROCESS_TEMPLATE':'processes/process.json','ANIMATION_IMPLEMENTATION':'src/manim_adapter.py','LAYOUT':'scene_ir/dna_section4.json'}
 def task(self,issue):
  stage=issue['root_cause_stage']
  if stage not in self.ARTIFACTS:raise ValueError('Unknown repair root')
  return {'repair_id':'REP_'+issue['issue_id'],'issue_id':issue['issue_id'],'root_cause_stage':stage,'target_artifact':issue.get('target_artifact',self.ARTIFACTS[stage]),'target_object_ids':issue.get('target_objects',[]),'target_fields':issue.get('target_fields',[]),'acceptance_criteria':issue.get('acceptance_criteria',[]),'status':'PENDING'}
 def apply(self,root,task,patches):
  root=Path(root).resolve();path=(root/task['target_artifact']).resolve()
  if not path.is_relative_to(root):raise ValueError('Artifact path escapes experiment')
  before=json.loads(path.read_text());candidate=copy.deepcopy(before);changed=[]
  objects={o['object_id']:o for o in candidate.get('objects',[])}
  for patch in patches:
   oid=patch['object_id'];field=patch['field']
   if oid not in objects or oid not in task['target_object_ids'] or field not in task['target_fields']:raise ValueError('Patch outside task boundary')
   node=objects[oid];parts=field.split('.')
   for key in parts[:-1]:node=node[key]
   old=node.get(parts[-1]);value=patch['value']
   if old!=value:changed.append({'object_id':oid,'field':field,'before':old,'after':value});node[parts[-1]]=value
  if not changed:return {'status':'REPAIR_NOT_APPLIED','changed':[],'before_sha256':digest(before),'after_sha256':digest(before)}
  schema_validate('scene_graph',candidate)
  tmp=path.with_suffix('.candidate.json');tmp.write_text(json.dumps(candidate,ensure_ascii=False,indent=2));tmp.replace(path)
  return {'status':'CANDIDATE_CREATED','changed':changed,'before_sha256':digest(before),'after_sha256':digest(candidate),'target_artifact':task['target_artifact'],'requires_downstream_regeneration':True}
