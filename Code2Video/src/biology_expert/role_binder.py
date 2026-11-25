"""Offline, topic-independent role binding. Candidate text alone never proves a role."""
import re,json,hashlib
from .contracts import digest

def tokens(value):
 text=re.sub(r'([a-z])([A-Z])',r'\1 \2',str(value)).lower()
 return set(re.findall(r'[a-z0-9]+',text))
def normalized(value):return '_'.join(sorted(tokens(value)))

class ScientificRoleBinder:
 def bind(self,contract,scene,trace=None):
  trace=trace or {};objects=scene.get('objects',[]);metadata=trace.get('object_metadata',{})
  events=scene.get('events',[]);transitions={t['transition_id']:t for t in scene.get('state_transitions',[])}
  rows=[]
  for entity in contract['scientific_entities']:
   role=entity['role'];rt=tokens(role);candidates=[]
   for obj in objects:
    oid=obj['object_id'];identity=obj.get('scientific_identity',{});props=obj.get('scientific_properties',{})
    names=[oid,identity.get('name',''),identity.get('origin_id','').removeprefix('entity_'),props.get('current_role',''),props.get('role','')]
    exact=[name for name in names if normalized(name)==normalized(role)]
    # Cross-topic abbreviation: only accepts terminal class abbreviation when matching
    # modifiers uniquely identify the object (e.g. "catalyst alpha" vs "cat alpha").
    name_tokens=[tokens(n) for n in names];rt_core=rt-{'enzyme','entity','object'}
    overlap=max((len(rt_core&t)/max(1,len(rt_core)) for t in name_tokens),default=0)
    letter_match=all(x in set().union(*name_tokens) for x in rt if len(x)==1)
    if exact:score=1.0;method='explicit_identity_or_origin'
    elif rt_core and rt_core<=set().union(*name_tokens):score=.95;method='combined_identity_and_property_fields'
    elif overlap>=.5 and letter_match:score=overlap*.8;method='lexical_candidate_only'
    else:continue
    observed=any(oid in f.get('objects',{}) for f in trace.get('scientific_observations',[]))
    relations=[r for r in scene.get('relations',[])+[x for a in scene.get('assemblies',[]) for x in a.get('relations',[])] if oid in [r.get('source'),r.get('target')]]
    declared_type=entity.get('object_type',entity.get('kind'))
    type_valid=declared_type is None or declared_type in [identity.get('kind'),obj.get('object_type')]
    candidates.append({'type_valid':type_valid,'rejection_reason':None if type_valid else 'Declared object type mismatch','object_id':oid,'score':score,'method':method,'evidence':{'matched_fields':exact,'identity':identity,'properties':props,'metadata_registered':oid in metadata,'observed_in_trace':observed,'relations':relations[:5]},'anchors':list(obj.get('anchors',{}))})
   confident=[x for x in candidates if x['score']>=.95 and x.get('type_valid',True)]
   # A category role may bind a set only when every member independently matches.
   if confident:
    distinct=any(len(t)==1 for t in rt)
    if len(confident)>1 and distinct:status='AMBIGUOUS';selected=[]
    else:status='BOUND';selected=confident
   else:status='TYPE_MISMATCH' if candidates and all(not x.get('type_valid',True) for x in candidates) else ('AMBIGUOUS' if candidates else 'UNRESOLVED');selected=[]
   rows.append({'role':role,'kind':'entity','object_ids':[x['object_id'] for x in selected],'event_ids':[],'status':status,'method':selected[0]['method'] if selected else 'insufficient_metadata','evidence':[x['evidence'] for x in selected],'anchors':{x['object_id']:x['anchors'] for x in selected},'candidates':candidates})
  # Process binding uses event role, transition process IDs, caption and target object roles.
  for process in contract['required_processes']:
   role=process['role'];pt=tokens(role);candidates=[]
   for event in events:
    eid=event['event_id'];steps=[transitions[x] for x in event.get('transition_ids',[]) if x in transitions]
    fields=[eid,event.get('role','')]+[t.get('process_id','') for t in steps]
    exact=any(normalized(role)==normalized(x) for x in fields)
    shared=max((len(pt&tokens(x))/max(1,len(pt)) for x in fields),default=0)
    if exact:score=1.0
    elif shared>=.5:score=shared
    else:continue
    candidates.append({'event_id':eid,'score':score,'process_ids':sorted({t.get('process_id','') for t in steps}),'exact':exact})
   strong=[x for x in candidates if x['exact']]
   # Lexical overlap proposes candidates only; never establishes a process identity.
   for candidate in candidates:
    candidate['accepted_semantic_identity']=candidate['exact']
    candidate['rejection_reason']=None if candidate['exact'] else 'Lexical overlap without stable process role or compatible action/state/input-output declaration'
   if len(strong)==1:status='BOUND';selected=strong
   else:status='AMBIGUOUS' if strong else ('REJECTED' if candidates else 'UNRESOLVED');selected=[]
   rows.append({'role':role,'kind':'process','object_ids':[],'event_ids':[x['event_id'] for x in selected],'status':status,'method':'explicit_event_or_process_role' if selected else 'insufficient_event_semantics','evidence':selected,'candidates':candidates})
  # Unlisted constraint participants are not silently bound to scene IDs.
  known={r['role'] for r in rows}
  for c in contract['constraints']:
   for role in c['participant_roles']:
    if role not in known:rows.append({'role':role,'kind':'entity','object_ids':[],'event_ids':[],'status':'UNRESOLVED','method':'missing_contract_entity','evidence':[],'candidates':[]});known.add(role)
  entity_rows={r['role']:r for r in rows if r['kind']=='entity'}
  for constraint in contract['constraints']:
   hold=constraint.get('must_hold',{});relation=hold.get('relation')
   if isinstance(relation,str):
    candidates=[r for r in scene.get('relations',[]) if r.get('type')==relation]
    rows.append({'role':constraint['constraint_id']+'::relation','kind':'relation','object_ids':[],'event_ids':[],'status':'BOUND' if len(candidates)==1 else 'AMBIGUOUS' if candidates else 'UNRESOLVED','method':'exact_relation_type','evidence':candidates,'candidates':[]})
   for key in ['source_anchor','target_anchor']:
    value=hold.get(key)
    if not isinstance(value,str):continue
    matches=[{'object_id':oid,'anchor':value} for row in entity_rows.values() if row['status']=='BOUND' for oid in row['object_ids'] for obj in objects if obj['object_id']==oid and value in obj.get('anchors',{})]
    rows.append({'role':constraint['constraint_id']+'::'+key,'kind':'anchor','object_ids':[m['object_id'] for m in matches] if len(matches)==1 else [],'event_ids':[],'status':'BOUND' if len(matches)==1 else 'AMBIGUOUS' if matches else 'UNRESOLVED','method':'exact_declared_anchor','evidence':matches,'candidates':[]})
  for row in rows:
   row['binding_type']=row['kind'].upper()
   row['candidate_ids']=[c.get('event_id',c.get('object_id')) for c in row.get('candidates',[])]
   row['selected_ids']=row['object_ids']+row['event_ids']
   row['rejected_candidates']=[c for c in row.get('candidates',[]) if c.get('rejection_reason')]
  return {'contract_hash':digest(contract),'scene_sha256':digest(scene),'trace_sha256':digest(trace) if trace else None,'bindings':rows,'unresolved_roles':[r['role'] for r in rows if r['status']=='UNRESOLVED'],'ambiguous_roles':[r['role'] for r in rows if r['status']=='AMBIGUOUS']}
