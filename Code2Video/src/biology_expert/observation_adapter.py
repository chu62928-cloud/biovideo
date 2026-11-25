"""Measured subchecks and strict semantic evidence replay; no biological constants."""
import copy,re,math,json
from .contracts import digest,ScientificCoverageAuditor

class RuntimeObservationAdapter:
 def execute(self,contract,scene,trace,bindings):
  if bindings['contract_hash']!=digest(contract) or bindings['scene_sha256']!=digest(scene):raise ValueError('VERSION_CONFLICT: bindings do not match inputs')
  rows={r['role']:r for r in bindings['bindings']};frames=trace.get('scientific_observations',[]);checks=[]
  for c in contract['constraints']:
   bound=[rows[r] for r in c['participant_roles'] if r in rows and rows[r]['status']=='BOUND'];ids=list(dict.fromkeys(i for r in bound for i in r['object_ids']))
   base={'constraint_id':c['constraint_id'],'contract_hash':digest(contract),'scene_sha256':digest(scene),'trace_sha256':digest(trace) if trace else None,'verification_method':'runtime_trace','object_ids':ids,'event_ids':[],'observed_interval':None,'observations_checked':0,'evidence_ids':c['evidence_ids'],'subchecks':[],'status':'NOT_MEASURED','full_constraint_verified':False}
   if not frames:
    # Planned structure can be checked without claiming animation observation.
    if ids:base['static_evidence']={'check':'role_registration','status':'PASS','object_ids':ids,'source':'scene_graph_only','constraint_semantics_verified':False}
    static_relations=[r for r in scene.get('relations',[]) if r.get('source') in ids and r.get('target') in ids]
    if static_relations:base.setdefault('static_subchecks',[]).append({'primitive':'structural_relation_registration','status':'PASS','relations':static_relations,'scope':'Actual planned graph edges among bound contract participants; semantic relation correctness not established'})
    base['reason']='No actual runtime observations';checks.append(base);continue
   if not ids:
    base.update(status='AMBIGUOUS_BINDING' if any(rows.get(r,{}).get('status')=='AMBIGUOUS' for r in c['participant_roles']) else 'NOT_MEASURED',reason='No reliably bound participants');checks.append(base);continue
   process=c.get('applies_to',{}).get('process',c.get('applies_to',{}).get('event_role'))
   evs=rows.get(process,{}).get('event_ids',[])
   # If process unresolved, object lifecycle checks cover observed visible interval only,
   # never assert the requested process occurred.
   relevant=[f for f in frames if not evs or f.get('current_event') in evs]
   base['event_ids']=evs
   lifecycle=[]
   for oid in ids:
    samples=[f for f in relevant if oid in f.get('objects',{}) and f['objects'][oid].get('visible')]
    if not samples:continue
    # Scientific identity continuity is an observable prerequisite, not complete semantics.
    first=samples[0]['objects'][oid]
    if first.get('origin_id') is None or first.get('instance_id') is None:continue
    bad=[{'time':f['time'],'observed_origin':f['objects'][oid].get('origin_id')} for f in samples if (f['objects'][oid].get('origin_id'),f['objects'][oid].get('instance_id'))!=(first.get('origin_id'),first.get('instance_id'))]
    lifecycle.append({'subcheck_id':c['constraint_id']+'::identity::'+oid,'primitive':'identity','status':'FAIL' if bad else 'PASS','object_ids':[oid],'observed_interval':[samples[0]['time'],samples[-1]['time']],'observations_checked':len(samples),'evidence':{'violations':bad,'expected_origin':first.get('origin_id'),'source':'actual_runtime_instance_and_origin'},'scope':'Identity continuity only; does not prove biochemical role'})
   # Persistent interaction can be measured when exact participants are bound and runtime
   # explicitly registers an active relation. Never infer a relation synonym from topic.
   # Persistent mechanism checks use independently resolved intervals in temporal_validator.
   base['subchecks']=lifecycle
   if lifecycle:
    base['status']='FAIL' if any(x['status']=='FAIL' for x in lifecycle) else 'PARTIALLY_VERIFIED'
    base['observations_checked']=sum(x['observations_checked'] for x in lifecycle);base['observed_interval']=[min(x['observed_interval'][0] for x in lifecycle),max(x['observed_interval'][1] for x in lifecycle)]
   else:base['reason']='Bound objects not visibly observed in applicable interval'
   checks.append(base)
  return {'contract_hash':digest(contract),'scene_sha256':digest(scene),'trace_sha256':digest(trace) if trace else None,'checks':checks,'measured_observations':[dict(s,parent_constraint_id=c['constraint_id'],contract_hash=digest(contract),scene_sha256=digest(scene),trace_sha256=digest(trace),verification_method='runtime_trace',evidence_ids=c['evidence_ids'],full_constraint_verified=False) for c in checks for s in c['subchecks']]}

class SemanticObservationAdapter:
 def adapt(self,contract,review,video_sha256,model=None):
  known={c['constraint_id']:c for c in contract['constraints']};out=[]
  mismatch=review.get('contract_hash')!=digest(contract) or review.get('video_sha256')!=video_sha256
  for cid,c in known.items():
   candidates=[x for x in review.get('checks',[]) if isinstance(x,dict) and x.get('constraint_id')==cid];r=candidates[0] if len(candidates)==1 else {}
   observation=r.get('observation','');numbers=re.findall(r'(\d+(?:\.\d+)?)\s*(?:[-–]\s*(\d+(?:\.\d+)?))?\s*s\b',observation)
   interval=[min(float(n[0]) for n in numbers),max(float(n[1] or n[0]) for n in numbers)] if numbers else None
   valid=not mismatch and bool(observation.strip()) and interval is not None and r.get('status') in ['PASS','FAIL','UNCERTAIN','NOT_MEASURED']
   out.append({'constraint_id':cid,'contract_hash':digest(contract),'video_sha256':video_sha256,'review_model':model,'verification_method':'video_semantic_review','status':r.get('status') if valid else 'NOT_MEASURED','evidence_status':'TIMESTAMP_MATCHED' if valid else 'VERSION_CONFLICT' if mismatch else 'INSUFFICIENT_VIDEO_EVIDENCE','evidence_level':'TIMESTAMP_MATCHED' if valid else 'MODEL_CLAIM_ONLY','independently_frame_verified':False,'observed_interval':interval if valid else None,'observed_objects_or_events':observation if valid else None,'reference_evidence_ids':c['evidence_ids'],'uncertainty':review.get('reference_comparison',{}).get('limitations',[]),'raw_check':r,'limitation':'Model-reported interval, not per-frame deterministic measurement'})
  return out

def merged_coverage(contract,runtime,semantic,goal_review=None):
 sem={x['constraint_id']:x for x in semantic};checks=[]
 for c in runtime['checks']:
  s=sem.get(c['constraint_id']);status=c['status'];refs=[]
  if status=='FAIL':refs=['runtime_trace']
  elif s and s['status']=='FAIL':status='FAIL';refs=['video_semantic_review']
  elif s and s['status']=='PASS' and s.get('evidence_level') in ['FRAME_SEMANTICALLY_REVIEWED','RUNTIME_CORROBORATED']:status='PASS';refs=['video_semantic_review']
  # Partial trace prerequisites are reported separately; do not satisfy full coverage.
  checks.append({'check_id':c['constraint_id'],'status':status,'observation_refs':refs,'partial_observation_refs':['runtime_trace'] if c['subchecks'] else []})
 cov=ScientificCoverageAuditor().audit(contract,{'checks':checks},goal_review)
 cov['partially_observed_constraints']=sum(bool(c['subchecks']) for c in runtime['checks']);cov['semantic_observations_supported']=sum(s['status'] in ['PASS','FAIL'] for s in semantic)
 return cov

class ObservationMutationTester:
 def run(self,contract,scene,trace,bindings,baseline):
  cases=[]
  for parent in baseline['checks']:
   targets=[s for s in parent['subchecks'] if s['status']=='PASS' and s['primitive']=='identity']
   if not targets:continue
   target=targets[0];oid=target['object_ids'][0];mut=copy.deepcopy(trace);samples=[f for f in mut['scientific_observations'] if oid in f['objects'] and f['objects'][oid].get('visible') and target['observed_interval'][0]<=f['time']<=target['observed_interval'][1]]
   changes=[]
   for f in samples[len(samples)//2:]:
    old=f['objects'][oid].get('origin_id');f['objects'][oid]['origin_id']='MUTATION_UNEXPLAINED_IDENTITY';changes.append({'time':f['time'],'object_id':oid,'field':'origin_id','before':old,'after':'MUTATION_UNEXPLAINED_IDENTITY'})
   evaluated=RuntimeObservationAdapter().execute(contract,scene,mut,bindings);p=next(c for c in evaluated['checks'] if c['constraint_id']==parent['constraint_id']);sub=next((s for s in p['subchecks'] if s['subcheck_id']==target['subcheck_id']),{})
   valid=len(samples)>1 and bool(changes)
   cases.append({'mutation_id':'MUT_'+target['subcheck_id'],'constraint_id':parent['constraint_id'],'subcheck_id':target['subcheck_id'],'mutation_type':'required_object_identity_change','valid_sample':valid,'baseline_status':'PASS','mutated_status':sub.get('status','NOT_MEASURED'),'detected':valid and sub.get('status')=='FAIL','scope':'Contract participant identity prerequisite; parent scientific semantics remain partial','changes':changes,'mutated_artifact_sha256':digest(mut),'baseline_trace_sha256':digest(trace)})
  modified=copy.deepcopy(scene)
  for obj in modified.get('objects',[]):
   if isinstance(obj.get('visual_representation'),dict):obj['visual_representation']['color']='#2468AC'
  # Rebind hashes for equivalent appearance input; use binder, never hand edit IDs.
  from .role_binder import ScientificRoleBinder
  b=ScientificRoleBinder().bind(contract,modified,trace);negative=RuntimeObservationAdapter().execute(contract,modified,trace,b)
  signature=lambda x:[(c['constraint_id'],c['status'],[(s['subcheck_id'],s['status']) for s in c['subchecks']]) for c in x['checks']]
  unchanged=signature(negative)==signature(baseline)
  return {'contract_hash':digest(contract),'baseline_trace_sha256':digest(trace) if trace else None,'cases':cases,'valid_scientific_mutations':sum(x['valid_sample'] for x in cases),'detected':sum(x['detected'] for x in cases),'missed':sum(x['valid_sample'] and not x['detected'] for x in cases),'false_positives':int(not unchanged),'negative_control':{'type':'irrelevant_color_change','status':'UNCHANGED' if unchanged else 'CHANGED','false_positive':not unchanged},'not_tested_reason':None if cases else 'No actual PASS prerequisite to mutate; no synthetic runtime generated'}
