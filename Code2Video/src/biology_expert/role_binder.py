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
    candidates.append({'object_id':oid,'score':score,'method':method,'evidence':{'matched_fields':exact,'identity':identity,'properties':props,'metadata_registered':oid in metadata,'observed_in_trace':observed,'relations':relations[:5]},'anchors':list(obj.get('anchors',{}))})
   confident=[x for x in candidates if x['score']>=.95]
   # A category role may bind a set only when every member independently matches.
   if confident:
    distinct=any(len(t)==1 for t in rt)
    if len(confident)>1 and distinct:status='AMBIGUOUS';selected=[]
    else:status='BOUND';selected=confident
   else:status='AMBIGUOUS' if candidates else 'UNRESOLVED';selected=[]
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
   if not strong:
    unambiguous=[x for x in candidates if x['score']>=.5]
    if len(unambiguous)==1:strong=unambiguous
   if len(strong)==1:status='BOUND';selected=strong
   else:status='AMBIGUOUS' if candidates else 'UNRESOLVED';selected=[]
   rows.append({'role':role,'kind':'process','object_ids':[],'event_ids':[x['event_id'] for x in selected],'status':status,'method':'explicit_event_or_process_role' if selected else 'insufficient_event_semantics','evidence':selected,'candidates':candidates})
  # Unlisted constraint participants are not silently bound to scene IDs.
  known={r['role'] for r in rows}
  for c in contract['constraints']:
   for role in c['participant_roles']:
    if role not in known:rows.append({'role':role,'kind':'entity','object_ids':[],'event_ids':[],'status':'UNRESOLVED','method':'missing_contract_entity','evidence':[],'candidates':[]});known.add(role)
  return {'contract_hash':digest(contract),'scene_sha256':digest(scene),'trace_sha256':digest(trace) if trace else None,'bindings':rows,'unresolved_roles':[r['role'] for r in rows if r['status']=='UNRESOLVED'],'ambiguous_roles':[r['role'] for r in rows if r['status']=='AMBIGUOUS']}
