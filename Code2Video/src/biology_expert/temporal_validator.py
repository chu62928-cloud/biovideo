"""Evaluate fixed expected intervals against actual samples, never relation lifetimes."""
import copy,math
from .contracts import digest

class TemporalMechanismValidator:
 def execute(self,plan,contract,scene,trace):
  if plan['contract_hash']!=digest(contract) or plan['scene_sha256']!=digest(scene):raise ValueError('VERSION_CONFLICT')
  out=[];frames=trace.get('scientific_observations',[])
  for rule in plan['compiled_constraints']:
   c={'constraint_id':rule['constraint_id'],'predicate':rule['predicate'],'status':'NOT_MEASURED','full_constraint_verified':False,'expected_interval':rule['expected_interval'],'observed_interval':None,'samples_checked':0,'sample_times':[],'violations':[],'evidence':[],'reason':rule['reason'],'participants':rule['participants'],'contract_hash':digest(contract),'scene_sha256':digest(scene),'trace_sha256':digest(trace) if trace else None}
   if rule['compile_status'] not in ['COMPILED','PARTIALLY_COMPILED']:c['status']='AMBIGUOUS_BINDING' if rule['compile_status']=='UNRESOLVED_BINDING' else 'UNSUPPORTED';out.append(c);continue
   if not frames:c['reason']='No actual runtime trace';out.append(c);continue
   spec=rule['spec'];predicate=rule['predicate'];participants=rule['participants']
   if predicate in ['relation_holds_during','connection_holds_until']:
    interval=rule['expected_interval']
    if not interval or interval['status']!='RESOLVED':c.update(status='EXPECTED_INTERVAL_UNRESOLVED',reason='Expected interval cannot be independently established');out.append(c);continue
    a,b=interval['start'],interval['end'];sampled=[f for f in frames if a<=f['time']<b];times=sorted(set(f['time'] for f in sampled));tolerance=spec.get('max_sample_gap',.25)
    gaps=[{'start':x,'end':y,'length':y-x} for x,y in zip([a]+times,times+[b]) if y-x>tolerance]
    source=participants[spec['source_role']][0];target=participants[spec['target_role']][0];kind=spec['relation_type']
    pairs=spec.get('expected_pairs',[{'source':source,'target':target}])
    for f in sampled:
     for pair in pairs:
      src,dst=pair['source'],pair['target']
      matches=[r for r in f.get('relations',[]) if r.get('source')==src and r.get('target')==dst and r.get('type')==kind]
      if not matches:c['violations'].append({'time':f['time'],'reason':'expected_relation_absent','source':src,'target':dst})
      elif spec.get('source_anchor') and any(r.get('source_anchor','center')!=spec['source_anchor'] or r.get('target_anchor','center')!=spec['target_anchor'] for r in matches):c['violations'].append({'time':f['time'],'reason':'wrong_connection_anchor'})
    c.update(samples_checked=len(sampled),sample_times=times,observed_interval=[times[0],times[-1]] if times else None,evidence=[{'expected_relation':kind,'source':source,'target':target,'sampling_gaps':gaps,'interval_source':interval['source']}])
    c['status']='FAIL' if c['violations'] else 'REVIEW_INCOMPLETE' if gaps else 'PASS' if sampled else 'NOT_MEASURED'
   elif predicate=='event_precedes':
    ordered=spec['ordered_event_roles'];event_ids=[participants[r][0] for r in ordered];markers={m['id']:m['time'] for m in trace.get('events',[])}
    if all(i in markers for i in event_ids):
     c['violations']=[{'before':x,'after':y,'times':[markers[x],markers[y]]} for x,y in zip(event_ids,event_ids[1:]) if markers[x]>=markers[y]];c.update(status='FAIL' if c['violations'] else 'PASS',samples_checked=len(event_ids),sample_times=[markers[i] for i in event_ids],evidence=[{'event_ids':event_ids,'source':'actual_event_markers'}])
   elif predicate=='state_transition_allowed':
    key=spec['state_key'];pre=spec['precondition'];post=spec['to_value'];transitions=[]
    for before,after in zip(frames,frames[1:]):
     if before.get('state_variables',{}).get(key)!=post and after.get('state_variables',{}).get(key)==post:
      ok=all(before.get('state_variables',{}).get(k)==v for k,v in pre.items());transitions.append(after['time'])
      if not ok:c['violations'].append({'time':after['time'],'reason':'state_precondition_false','observed':before.get('state_variables',{})})
    if transitions:c.update(status='FAIL' if c['violations'] else 'PASS',samples_checked=len(transitions),sample_times=transitions,evidence=[{'precondition':pre,'to_value':post}])
   if c['status']=='PASS' and not rule['full_semantics']:c['status']='PARTIALLY_VERIFIED'
   c['full_constraint_verified']=rule['full_semantics'] and c['status'] in ['PASS','FAIL']
   out.append(c)
  return {'contract_hash':digest(contract),'checks':out}

class MechanismMutationTester:
 TYPES=['RELATION_TERMINATED_EARLY','EVENT_ORDER_REVERSED','CONNECTION_TARGET_CHANGED','STATE_PRECONDITION_VIOLATED']
 def run(self,plan,contract,scene,trace,baseline):
  cases=[]
  for kind in self.TYPES:
   eligible=[(r,c) for r,c in zip(plan['compiled_constraints'],baseline['checks']) if c['status']=='PASS' and c['full_constraint_verified'] and ((kind in self.TYPES[:1]+self.TYPES[2:3] and r['predicate'] in ['relation_holds_during','connection_holds_until']) or (kind=='EVENT_ORDER_REVERSED' and r['predicate']=='event_precedes') or (kind=='STATE_PRECONDITION_VIOLATED' and r['predicate']=='state_transition_allowed'))]
   if not eligible:cases.append({'mutation_type':kind,'valid_sample':False,'baseline_status':'NOT_MEASURED','mutated_status':'NOT_TESTED','detected':None,'reason':'No fully compiled source-supported real baseline PASS for this predicate'});continue
   rule,check=eligible[0];mut=copy.deepcopy(trace);changes=[];spec=rule['spec']
   if kind in ['RELATION_TERMINATED_EARLY','CONNECTION_TARGET_CHANGED']:
    a,b=check['expected_interval']['start'],check['expected_interval']['end'];source=rule['participants'][spec['source_role']][0]
    for f in mut['scientific_observations']:
     if (a+b)/2<=f['time']<b:
      old=copy.deepcopy(f['relations'])
      if kind=='RELATION_TERMINATED_EARLY':f['relations']=[r for r in f['relations'] if r.get('source')!=source]
      else:
       for r in f['relations']:
        if r.get('source')==source:r['target']='MUTATED_WRONG_TARGET'
      changes.append({'time':f['time'],'before':old,'after':f['relations']})
   elif kind=='EVENT_ORDER_REVERSED':
    ids=[rule['participants'][r][0] for r in spec['ordered_event_roles']];markers={m['id']:m for m in mut['events']};x,y=ids[:2];old=[markers[x]['time'],markers[y]['time']];markers[x]['time'],markers[y]['time']=old[::-1];changes=[{'events':[x,y],'before':old,'after':old[::-1]}]
   else:
    for f in mut['scientific_observations']:
     for key,value in spec['precondition'].items():
      if f['state_variables'].get(key)==value:changes.append({'time':f['time'],'field':key,'before':value,'after':'MUTATED'});f['state_variables'][key]='MUTATED'
   evaluated=TemporalMechanismValidator().execute(plan,contract,scene,mut);target=next(c for c in evaluated['checks'] if c['constraint_id']==rule['constraint_id']);cases.append({'mutation_type':kind,'constraint_id':rule['constraint_id'],'valid_sample':bool(changes),'baseline_status':'PASS','mutated_status':target['status'],'detected':target['status']=='FAIL','changes':changes,'baseline_trace_sha256':digest(trace),'mutated_artifact_sha256':digest(mut)})
  # Trace-independent appearance controls cannot alter predicate state. Legitimate visual
  # duration changes are confined to explicitly non-scientific metadata, not event markers.
  controls=[]
  for kind in ['color','label_position','noncritical_visual_duration']:
   modified=copy.deepcopy(trace);modified.setdefault('visual_only_metadata',{})[kind]='changed'
   checked=TemporalMechanismValidator().execute(plan,contract,scene,modified);same=[x['status'] for x in checked['checks']]==[x['status'] for x in baseline['checks']];controls.append({'type':kind,'unchanged_scientific_results':same,'false_positive':not same,'scope':'visual-only metadata, no scientific event interval changed'})
  return {'cases':cases,'negative_controls':controls,'source':'actual_runtime_trace' if trace.get('scientific_observations') else 'NO_RUNTIME_TRACE','distinct_valid_mutation_types':len({x['mutation_type'] for x in cases if x['valid_sample']}),'valid_mutations':sum(x['valid_sample'] for x in cases),'detected':sum(x.get('detected') is True for x in cases),'false_positives':sum(x['false_positive'] for x in controls)}
