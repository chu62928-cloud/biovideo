"""Evidence-first typed scientific models; no biological topic blueprints."""
from pathlib import Path
import copy,json,uuid
from jsonschema import Draft202012Validator
from .contracts import digest,write
from .providers import parse_json

def validate_typed_model(model,evidence=None):
 schema=json.loads((Path(__file__).parent/'schemas/typed_science_model.schema.json').read_text());Draft202012Validator(schema).validate(model)
 ids=[e['semantic_id'] for e in model['entities']];relations={r['semantic_id']:r for r in model['relations']};processes={p['process_semantic_id']:p for p in model['processes']}
 if len(ids)!=len(set(ids)) or len(relations)!=len(model['relations']) or len(processes)!=len(model['processes']):raise ValueError('Duplicate semantic ID')
 for r in relations.values():
  if r['source_entity'] not in ids or r['target_entity'] not in ids:raise ValueError('Undefined relation entity reference')
 for p in processes.values():
  roles={x['role'] for x in p['participants']}
  if len(roles)!=len(p['participants']):raise ValueError('Duplicate participant role')
  if any(x['entity_ref'] not in ids for x in p['participants']):raise ValueError('Undefined process entity reference')
  if not set(p['input_roles']+p['output_roles'])<=roles:raise ValueError('Undefined input/output role')
  if not set(p['temporal_scope'].get('after',[])+p['temporal_scope'].get('concurrent_with',[]))<=set(processes):raise ValueError('Unknown temporal process reference')
  for o in p['observables']:
   if o.get('relation_ref') is not None and o['relation_ref'] not in relations:raise ValueError('Unknown observable relation')
   if not set(o.get('ordered_process_ids',[]))<=set(processes):raise ValueError('Unknown observable process')
   if o['predicate'] in ['relation_holds_during','connection_holds_until']:
    if o.get('source_role') not in roles or o.get('target_role') not in roles:raise ValueError('Undefined observable role')
    r=relations.get(o.get('relation_ref'));mapping={x['role']:x['entity_ref'] for x in p['participants']}
    if not r or mapping[o['source_role']]!=r['source_entity'] or mapping[o['target_role']]!=r['target_entity']:raise ValueError('Observable participant type/reference mismatch')
 if evidence is not None:
  by={e['evidence_id']:e for e in evidence};errors=[]
  for item in model['entities']+model['relations']+model['processes']+[o for p in model['processes'] for o in p['observables']]:
   for eid in item['evidence_ids']:
    if eid not in by:errors.append('Unknown evidence '+eid)
   for support in item['support']:
    ev=by.get(support['evidence_id']);passages=ev.get('passages',[]) if ev else []
    if not any(support['quote'] in q['text'] and support['location']==q['location'] for q in passages):errors.append('Quote or location absent for '+support['evidence_id'])
  if errors:raise ValueError('UNRESOLVED_EVIDENCE: '+str(errors[:8]))
 return True

class TypedScienceModelBuilder:
 def __init__(self,gateway):self.gateway=gateway
 def build(self,task,retrieval):
  if not retrieval.get('evidence'):raise ValueError('UNRESOLVED_EVIDENCE: no retrieved content')
  schema=json.loads((Path(__file__).parent/'schemas/typed_science_model.schema.json').read_text())
  prompt='''Construct a small TYPED scientific process model for this actual user task using ONLY the supplied retrieved passages. Return one JSON matching schema. No historical model, scene or topic blueprint is supplied. Choose a narrow, accurately supported process with 2-5 entities and 1-3 processes that can be represented as an editable schematic. Use stable project semantic IDs. Each entity/relation/process/observable must have exact contiguous support quotes and actual paragraph location from source. Types, participant roles, input/output roles, start/end conditions, preconditions/effects and allowed exceptions must be explicit. Separate scientific content from geometry/time coordinates. Observables use only listed generic predicates; DETERMINISTIC means the full narrowly stated property can actually be observed in trace, not that a relation label proves all chemistry. A continuous interaction observable may explicitly require an interaction to remain during the active process, supported by source; do not invent persistence/strict event order absent support. For state_transition_allowed use explicit precondition and to_value. For event_precedes identify actual processes, not entities. Mark uncertain content unresolved rather than fill from memory. Organism scope must be consistent. Do not give scientific PASS or validated=true. No topic-specific Python/code or coordinates. This is a proposal that undergoes independent review.'''
  sources=[]
  for e in retrieval['evidence']:
   sources.append({k:e[k] for k in ['evidence_id','url','title']}|{'passages':e['passages'][:28]})
  model=parse_json(self.gateway.request('deepseek','typed_scientific_model_build',prompt+json.dumps({'task':task,'schema':schema,'sources':sources},ensure_ascii=False)))
  validate_typed_model(model,retrieval['evidence']);return model

class TypedScienceModelReviewer:
 def __init__(self,gateway):self.gateway=gateway
 def review(self,model,evidence,task):
  validate_typed_model(model,evidence)
  prompt='''Independently review the proposed typed scientific model against original source excerpts and original task. Do NOT trust generator assurances. Return JSON {"decision":"PASS|REVISE|NEEDS_HUMAN_REVIEW|INSUFFICIENT_EVIDENCE","issues":[{"target_id":"...","reason":"...","evidence_ids":[]}],"observable_reviews":[{"constraint_id":"...","decision":"PASS|REVISE|INSUFFICIENT_EVIDENCE","reason":"source entails this exact scope/persistence/order and computational observable preserves meaning"}],"scope_review":"..."}. Check every observable, participant identity/types, organism context, input/output, causal state changes, required actors, omissions, exceptions and whether narrow observable semantics are source-supported. A fully formal but biologically false model must fail. A schematic need not simulate molecular chemistry but must honestly delimit what it proves. Require direct source entailment, not merely matching words. No approval from model self-explanation. At most5 main issues, concise.'''
  used={x['evidence_id'] for i in model['entities']+model['relations']+model['processes']+[o for p in model['processes'] for o in p['observables']] for x in i['support']}
  excerpts=[{k:e[k] for k in ['evidence_id','url','title']}|{'passages':[q for q in e['passages'] if any(s['quote'] in q['text'] for i in model['entities']+model['relations']+model['processes']+[o for p in model['processes'] for o in p['observables']] for s in i['support'] if s['evidence_id']==e['evidence_id'])]} for e in evidence if e['evidence_id'] in used]
  out=parse_json(self.gateway.request('deepseek','independent_typed_science_review',prompt+json.dumps({'task':task,'model':model,'actual_evidence':excerpts},ensure_ascii=False)))
  expected={o['constraint_id'] for p in model['processes'] for o in p['observables']};reviewed={x['constraint_id'] for x in out.get('observable_reviews',[]) if x['decision']=='PASS'}
  if out['decision']=='PASS' and expected!=reviewed:out['decision']='INSUFFICIENT_EVIDENCE';out.setdefault('issues',[]).append({'reason':'Missing independent PASS for every proposed observable'})
  out.update(model_hash=digest(model),separate_request=True,independent_provider=False);return out

def freeze_model(model,review,folder):
 if review.get('decision')!='PASS' or review.get('model_hash')!=digest(model):raise ValueError('Scientific model gate not PASS or hash mismatch')
 path=Path(folder)/(digest(model)+'.json');write(path,{'model':model,'review':review,'model_hash':digest(model)});return path

class TypedContractCompiler:
 def compile(self,model,review):
  validate_typed_model(model)
  if review.get('model_hash')!=digest(model):raise ValueError('VERSION_CONFLICT: science review belongs to another model')
  relations={r['semantic_id']:r for r in model['relations']};rules=[]
  for p in model['processes']:
   rolemap={x['role']:x['entity_ref'] for x in p['participants']}
   for observable in p['observables']:
    o=copy.deepcopy(observable);r=relations.get(o.get('relation_ref'));spec={'predicate':o['predicate'],'participant_roles':list(rolemap),'interval':{'event_role':p['process_semantic_id']}}
    if r:spec.update(source_role=o['source_role'],target_role=o['target_role'],relation_type=r['semantic_id'])
    if o['predicate']=='event_precedes':spec.update(ordered_event_roles=o.get('ordered_process_ids',[]),participant_roles=o.get('ordered_process_ids',[]))
    if o['predicate']=='state_transition_allowed':spec.update(state_key=o.get('state_key'),to_value=o.get('to_value'),precondition=o.get('precondition',{}))
    status='COMPILED' if review.get('decision')=='PASS' and o['capability']=='DETERMINISTIC' and not p['exceptions'] else 'PARTIALLY_COMPILED' if o['capability']=='PARTIAL' else 'UNSUPPORTED'
    rules.append({'constraint_id':o['constraint_id'],'process_semantic_id':p['process_semantic_id'],'entity_semantic_ids':list(rolemap.values()),'relation_semantic_id':o.get('relation_ref'),'predicate':o['predicate'],'spec':spec,'participant_entity_refs':rolemap,'evidence_ids':o['evidence_ids'],'source_support':o['support'],'compile_status':status,'full_semantics':status=='COMPILED','exceptions':p['exceptions'],'model_hash':digest(model)})
  return {'model_hash':digest(model),'science_review':review['decision'],'constraints':rules,'frozen_standard':'Typed observable text/roles/relations as independently reviewed; no semantic replacement'}
