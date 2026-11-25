"""Strict translation of explicit contract predicates; no inferred biological synonyms."""
from .contracts import digest

PREDICATES={'relation_holds_during','event_precedes','connection_holds_until','state_transition_allowed'}

class ExpectedIntervalResolver:
 def resolve(self,rule,scene,trace,bindings):
  interval=rule.get('interval',{});events={e['event_id']:e for e in scene.get('events',[])}
  role=interval.get('event_role');binding=next((b for b in bindings['bindings'] if b['role']==role and b['status']=='BOUND' and b['kind']=='process'),None)
  eid=interval.get('event_id') or (binding['event_ids'][0] if binding and len(binding['event_ids'])==1 else None)
  result={'source':'event_graph_and_runtime_event_markers','event_role':role,'event_id':eid,'start':None,'end':None,'status':'EXPECTED_INTERVAL_UNRESOLVED','relation_observations_used':False}
  if eid not in events:return result
  markers=trace.get('events',[]);found=[(i,m) for i,m in enumerate(markers) if m.get('id')==eid]
  if len(found)!=1:return result
  i,m=found[0];start=m['time'];event=events[eid]
  explicit_end=[x for x in trace.get('typed_event_markers',[]) if x.get('id')==eid and x.get('phase')=='ended']
  if len(explicit_end)==1:
   return {**result,'start':start,'end':explicit_end[0]['time'],'status':'RESOLVED','source':'independent_typed_start_end_markers','evidence':{'start':m,'end':explicit_end[0]}}
  end=markers[i+1]['time'] if i+1<len(markers) else event.get('end_time')
  # Final event duration is independently declared by the planned event graph, not by
  # relation presence, visibility, or last available sample.
  if end is None and isinstance(event.get('duration'),(int,float)):end=start+event['duration']
  if end is None or end<=start:return result
  return {**result,'start':start,'end':end,'status':'RESOLVED','evidence':{'start_marker':m,'end_marker':markers[i+1] if i+1<len(markers) else None,'declared_duration':event.get('duration')},'boundary_convention':'start inclusive, end exclusive; release event allowed at end'}

class ScientificContractCompiler:
 def compile(self,contract,review,scene,bindings,trace=None):
  if bindings['contract_hash']!=digest(contract) or bindings['scene_sha256']!=digest(scene):raise ValueError('VERSION_CONFLICT')
  rows={x['role']:x for x in bindings['bindings']};rules=[]
  for c in contract['constraints']:
   row={'constraint_id':c['constraint_id'],'contract_hash':digest(contract),'predicate':None,'participants':{},'expected_interval':None,'compile_status':'UNSUPPORTED','evidence_ids':c['evidence_ids'],'full_semantics':False,'reason':None,'contract_review':review.get('decision','NOT_PROVIDED')}
   spec=c.get('executable_predicate')
   if not spec:
    # Native DSL primitive is acceptable only if contract explicitly declares the same
    # semantic operation. Descriptive relation sentences are not renamed to graph edges.
    primitive=c.get('verification',{}).get('primitive');hold=c.get('must_hold',{})
    if primitive in PREDICATES:spec={'predicate':primitive,**hold}
   if c.get('exceptions'):row['reason']='Declared exceptions require explicit executable applicability; not ignored'
   elif c.get('verification',{}).get('capability') not in ['DETERMINISTIC','PARTIAL']:row.update(compile_status='AMBIGUOUS_SEMANTICS',reason='Contract requires semantic/visual judgment; no authorized deterministic equivalence')
   elif not spec:row.update(compile_status='AMBIGUOUS_SEMANTICS',reason='Existing primitive arguments do not express a complete typed temporal predicate; missing explicit relation/event/state semantics')
   elif spec.get('predicate') not in PREDICATES:row['reason']='Unsupported predicate'
   else:
    required=spec.get('participant_roles',c['participant_roles']);missing=[role for role in required if role not in rows or rows[role]['status']!='BOUND']
    row.update(predicate=spec['predicate'],spec=spec)
    if missing:row.update(compile_status='UNRESOLVED_BINDING',reason='Unresolved participants: '+','.join(missing))
    else:
     row['participants']={role:rows[role]['object_ids'] or rows[role]['event_ids'] for role in required}
     row['full_semantics']=c['verification']['capability']=='DETERMINISTIC' and c.get('verification_status')=='INDEPENDENTLY_VERIFIED'
     row['compile_status']='COMPILED' if row['full_semantics'] else 'PARTIALLY_COMPILED'
     if spec['predicate'] in ['relation_holds_during','connection_holds_until']:
      row['expected_interval']=ExpectedIntervalResolver().resolve(spec,scene,trace or {},bindings)
      if row['expected_interval']['status']!='RESOLVED':row.update(compile_status='PARTIALLY_COMPILED',reason='EXPECTED_INTERVAL_UNRESOLVED')
   rules.append(row)
  return {'contract_hash':digest(contract),'scene_sha256':digest(scene),'contract_review':review.get('decision'),'diagnostic_only':review.get('decision')!='PASS','compiled_constraints':rules,'capabilities':sorted(PREDICATES)}
