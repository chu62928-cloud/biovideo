"""Evidence-backed scientific contracts, generic execution and measured coverage.

No topic names, molecular object IDs or biological rules are built into this engine.
"""
from pathlib import Path
import copy,json,hashlib,math,uuid
from jsonschema import Draft202012Validator

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def write(path,x):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def schema_validate(contract):
 schema=json.loads((Path(__file__).parent/'schemas/scientific_contract.schema.json').read_text());Draft202012Validator(schema).validate(contract)

class ContractStore:
 def __init__(self,root):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
 def freeze(self,contract,review):
  schema_validate(contract)
  if review.get('decision')!='PASS':raise ValueError('Independent contract review required before freeze')
  h=digest(contract);path=self.root/(h+'.json')
  if not path.exists():write(path,{'contract':contract,'hash':h,'review':review})
  return {'contract_hash':h,'immutable_path':str(path),'approval_invalidated_on_change':True}
 def verify(self,contract,expected):
  if digest(contract)!=expected:raise ValueError('Frozen contract changed: prior approvals invalid')

def generic_mechanism_validator(artifacts,context):
 contract=context.get('scientific_contract')
 if contract is None:return {'decision':'REVIEW_INCOMPLETE','checks':[],'reason':'Contract absent; topic-specific legacy rules not loaded'}
 return ConstraintExecutor().execute(contract,artifacts.get('scene_graph',{}),artifacts.get('trace',{}),context.get('bindings',{}))

class ConstraintExecutor:
 METHODS={'identity','exists','relation','connected','endpoint_distance','distance','direction','event_order','state','count','visibility','persistent_relation','lifecycle','relative_position','spacing'}
 def execute(self,contract,scene,trace,bindings=None):
  bindings=bindings or {};objects={o['object_id']:o for o in scene.get('objects',[])}
  frames=trace.get('scientific_observations',[]);events=trace.get('events',[]);checks=[]
  for c in contract['constraints']:
   primitive=c['verification'].get('primitive');args=copy.deepcopy(c.get('must_hold',{}));roles=c.get('participant_roles',[])
   ids=[bindings.get(role,role) for role in roles];ids=[x for item in ids for x in (item if isinstance(item,list) else [item])]
   result={'check_id':c['constraint_id'],'type':c['type'],'constraint_hash':digest(c),'contract_hash':digest(contract),'status':'NOT_MEASURED','object_ids':ids,'evidence_ids':c['evidence_ids'],'capability':c['verification']['capability'],'observation_refs':[],'reason':None}
   if primitive not in self.METHODS:
    result.update(status='UNSUPPORTED_CONSTRAINT',reason='No generic primitive '+str(primitive));checks.append(result);continue
   if c['verification']['capability'] not in ['DETERMINISTIC','PARTIAL']:
    result['reason']='Semantic/visual claim needs independent observation review';checks.append(result);continue
   if c.get('exceptions'):
    result.update(status='UNSUPPORTED_CONSTRAINT',reason='Exception semantics are not yet executable; refusing to ignore declared exceptions');checks.append(result);continue
   when=c.get('when',{})
   allowed_when={'event_state','state_key','state_value'}
   if set(when)-allowed_when:
    result.update(status='UNSUPPORTED_CONSTRAINT',reason='Unsupported applicability condition');checks.append(result);continue
   relevant=frames
   if when.get('state_key'):relevant=[f for f in relevant if f.get('state_variables',{}).get(when['state_key'])==when.get('state_value')]
   interval=c.get('applies_to',{}).get('event_role')
   if interval:
    eid=bindings.get(interval,interval);relevant=[f for f in frames if f.get('current_event')==eid]
   try:
    passed=None;observed={}
    if primitive=='exists':passed=bool(ids) and all(i in objects for i in ids);observed={'registered':sorted(objects)}
    elif primitive=='identity':
     if relevant and ids:
      fingerprints={};changes=[]
      for f in relevant:
       for i in ids:
        obj=f.get('objects',{}).get(i)
        if obj is None:changes.append({'time':f['time'],'object':i,'reason':'missing'});continue
        value=(obj.get('instance_id'),obj.get('origin_id'))
        if i in fingerprints and fingerprints[i]!=value:changes.append({'time':f['time'],'object':i})
        fingerprints[i]=value
      passed=not changes;observed={'changes':changes,'frames':len(relevant)}
    elif primitive in ['relation','persistent_relation','connected']:
     rel=args.get('relation');samples=relevant if primitive=='persistent_relation' else (relevant[-1:] if relevant else [])
     if samples and len(ids)>=2:
      missing=[]
      for f in samples:
       rels=f.get('relations',[])
       if primitive=='connected':
        edges={}
        for r in rels:edges.setdefault(r['source'],set()).add(r['target']);edges.setdefault(r['target'],set()).add(r['source'])
        todo=[ids[0]];seen=set()
        while todo:
         x=todo.pop()
         if x in seen:continue
         seen.add(x);todo+=list(edges.get(x,set())-seen)
        ok=ids[1] in seen
       else:ok=any(r['source']==ids[0] and r['target']==ids[1] and (rel is None or r['type']==rel) for r in rels)
       if not ok:missing.append(f['time'])
      passed=not missing;observed={'missing_times':missing,'frames':len(samples)}
    elif primitive in ['endpoint_distance','distance','relative_position','direction','spacing']:
     if relevant and len(ids)>=2:
      values=[]
      for f in relevant:
       a=f.get('objects',{}).get(ids[0]);b=f.get('objects',{}).get(ids[1])
       if a is None or b is None:continue
       pa=a.get('anchors',{}).get(args.get('source_anchor','center'),a.get('center'));pb=b.get('anchors',{}).get(args.get('target_anchor','center'),b.get('center'))
       if pa is None or pb is None:continue
       if primitive in ['distance','endpoint_distance','spacing']:values.append((f['time'],math.dist(pa,pb)))
       elif primitive=='relative_position':values.append((f['time'],sum((y-x)*v for x,y,v in zip(pa,pb,args['axis']))))
       else:
        # Compare local directed vectors specified by contract; not global screen coordinates.
        va=[y-x for x,y in zip(a['anchors'][args['a_start']],a['anchors'][args['a_end']])];vb=[y-x for x,y in zip(b['anchors'][args['b_start']],b['anchors'][args['b_end']])]
        denominator=math.sqrt(sum(x*x for x in va)*sum(x*x for x in vb));values.append((f['time'],sum(x*y for x,y in zip(va,vb))/denominator if denominator else None))
      valid=[v for _,v in values if v is not None]
      if valid:
       lo=args.get('min',-float('inf'));hi=args.get('max',args.get('tolerance',float('inf')));passed=all(lo<=v<=hi for v in valid);observed={'values':values,'frames':len(valid)}
    elif primitive=='event_order':
     names=[bindings.get(role,role) for role in args.get('ordered_roles',roles)];actual=[e.get('id',e.get('event_id')) for e in events]
     if actual:passed=all(n in actual for n in names) and all(actual.index(a)<actual.index(b) for a,b in zip(names,names[1:]));observed={'expected':names,'actual':actual}
    elif primitive=='state':
     if relevant:
      vals=[f.get('state_variables',{}).get(args['key']) for f in relevant];passed=all(v==args['value'] for v in vals);observed={'values':vals}
    elif primitive=='count':
     if relevant:
      counts=[sum((o.get('kind')==args['kind']) and (not args.get('visible_only') or o.get('visible')) for o in f.get('objects',{}).values()) for f in relevant];passed=all(v==args['value'] for v in counts);observed={'counts':counts}
    elif primitive in ['visibility','lifecycle']:
     if relevant and ids:
      vals=[all(f.get('objects',{}).get(i,{}).get('visible',False) for i in ids) for f in relevant];passed=all(v==args.get('visible',True) for v in vals);observed={'visible_samples':sum(vals),'frames':len(vals)}
    result['observed']=observed
    if passed is not None:
     result['status']='PASS' if passed else 'FAIL';result['observation_refs']=['runtime_trace'] if relevant else ['scene_graph']
     if c['verification']['capability']=='PARTIAL' and passed:result['status']='PARTIALLY_VERIFIED'
   except (KeyError,TypeError,ValueError,IndexError) as ex:result.update(status='NOT_MEASURED',reason='Required fields absent: '+str(ex))
   checks.append(result)
  return {'checks':checks,'contract_hash':digest(contract),'decision':'REVISE' if any(c['status']=='FAIL' for c in checks) else ('PASS' if checks and all(c['status']=='PASS' for c in checks) else 'REVIEW_INCOMPLETE')}

class ScientificCoverageAuditor:
 def audit(self,contract,execution,goal_review=None):
  results={c['check_id']:c for c in execution['checks']};requirements=contract['coverage_requirements'];covered=set();gaps=[]
  for req in requirements:
   associated=[results.get(i) for i in req['constraint_ids']]
   # A rule being declared or returning a model claim is not measured coverage.
   ok=associated and all(c and c['status'] in ['PASS','FAIL'] and c.get('observation_refs') for c in associated)
   if ok:covered.add(req['item_id'])
   else:gaps.append({'item_id':req['item_id'],'kind':req['kind'],'critical':req['critical'],'reason':'No rule' if not req['constraint_ids'] else 'Rule absent/unsupported/unmeasured'})
  out={'topic_id':contract['topic_id'],'contract_hash':digest(contract),'uncovered_items':gaps,'unsupported_checks':[c['check_id'] for c in execution['checks'] if c['status']=='UNSUPPORTED_CONSTRAINT'],'critical_gaps':[g for g in gaps if g['critical']],'contract_goal_coverage':goal_review or {'decision':'NOT_MEASURED','reason':'No independent user-goal/contract completeness review'},'actual_observation_coverage':sum(c['status'] in ['PASS','FAIL'] and bool(c.get('observation_refs')) for c in execution['checks']),'checks_total':len(execution['checks'])}
  for kind,label in [('entity','entities'),('relation','relations'),('process','processes'),('temporal','temporal_constraints'),('persistent','persistent_relations')]:
   items=[x for x in requirements if x['kind']==kind];out[label+'_total']=len(items);out[label+'_covered']=sum(x['item_id'] in covered for x in items)
  out['decision']='PASS' if not out['critical_gaps'] and goal_review and goal_review.get('decision')=='PASS' else 'REVIEW_INCOMPLETE'
  return out

class ScientificMutationTester:
 def generate(self,contract,scene,trace,bindings=None):
  cases=[];bindings=bindings or {}
  for c in contract['constraints']:
   roles=c.get('participant_roles',[]);ids=[bindings.get(r,r) for r in roles];ids=[i for x in ids for i in (x if isinstance(x,list) else [x])]
   primitive=c['verification'].get('primitive');s=copy.deepcopy(scene);t=copy.deepcopy(trace);valid=False;kind=None
   frames=t.get('scientific_observations',[])
   if primitive=='exists' and ids:
    before=len(s.get('objects',[]));s['objects']=[o for o in s.get('objects',[]) if o['object_id']!=ids[0]];valid=before!=len(s['objects']);kind='delete_required_object'
   elif primitive=='identity' and ids and len(frames)>1:
    for f in frames[len(frames)//2:]:
     if ids[0] in f['objects']:f['objects'][ids[0]]['origin_id']='MUTATED_ID';valid=True
    kind='change_identity'
   elif primitive in ['relation','persistent_relation','connected'] and len(ids)>=2 and frames:
    for f in frames[len(frames)//2:]:
     before=len(f.get('relations',[]));f['relations']=[r for r in f.get('relations',[]) if not(r['source']==ids[0] and r['target']==ids[1])];valid|=len(f['relations'])!=before
    kind='early_terminate_relation' if primitive=='persistent_relation' else 'disconnect_required_relation'
   elif primitive=='event_order' and len(t.get('events',[]))>=2:t['events'][0],t['events'][-1]=t['events'][-1],t['events'][0];valid=True;kind='reverse_event_order'
   elif primitive=='state' and frames:
    for f in frames:f.setdefault('state_variables',{})[c['must_hold']['key']]='MUTATED_STATE'
    valid=True;kind='wrong_event_state'
   elif primitive=='count' and frames:
    for f in frames:f.setdefault('objects',{})['MUTATED_EXTRA']={'kind':c['must_hold']['kind'],'origin_id':'MUTATED_EXTRA','instance_id':-1,'visible':True}
    valid=True;kind='change_discrete_count'
   elif primitive in ['endpoint_distance','distance','spacing','relative_position','direction'] and ids and frames:
    for f in frames:
     if ids[0] in f.get('objects',{}):
      o=f['objects'][ids[0]];o['center']=[100,100,0]
      for key in o.get('anchors',{}):o['anchors'][key]=[100,100,0]
      valid=True
    kind='displace_endpoint_or_relation'
   cases.append({'case_id':'MUT_'+c['constraint_id'],'constraint_id':c['constraint_id'],'contract_hash':digest(contract),'mutation_type':kind,'expected':'FAIL','valid_sample':valid,'scene':s if valid else None,'trace':t if valid else None,'not_tested_reason':None if valid else 'No executable mutation for this constraint/observation'})
  # Independent irrelevant appearance change must not be treated as science error.
  s=copy.deepcopy(scene)
  for o in s.get('objects',[]):
   if not isinstance(o.get('visual_representation'),dict):o['visual_representation']={}
   o['visual_representation']['color']='#123456'
  cases.append({'case_id':'CONTROL_VISUAL_COLOR','constraint_id':None,'contract_hash':digest(contract),'mutation_type':'irrelevant_color','expected':'UNCHANGED','valid_sample':True,'scene':s,'trace':copy.deepcopy(trace)})
  return cases
 def run(self,contract,scene,trace,bindings=None):
  executor=ConstraintExecutor();baseline=executor.execute(contract,scene,trace,bindings);results=[]
  for case in self.generate(contract,scene,trace,bindings):
   result={k:v for k,v in case.items() if k not in ['scene','trace']}
   if not case['valid_sample']:result.update(actual='NOT_TESTED',detected=None,false_positive=None)
   else:
    observed=executor.execute(contract,case['scene'],case['trace'],bindings)
    if case['expected']=='UNCHANGED':detected=observed==baseline;result.update(actual='UNCHANGED' if detected else 'CHANGED',detected=detected,false_positive=not detected)
    else:
     target=next(c for c in observed['checks'] if c['check_id']==case['constraint_id']);base=next(c for c in baseline['checks'] if c['check_id']==case['constraint_id'])
     # If baseline not measurable/passing, cannot claim a successful mutation detector.
     valid=base['status']=='PASS';result.update(valid_sample=valid,actual=target['status'],detected=target['status']=='FAIL' if valid else None,false_positive=False,not_tested_reason=None if valid else 'Baseline constraint did not PASS; mutation efficacy unproven')
   results.append(result)
  return {'contract_hash':digest(contract),'baseline':baseline,'cases':results,'valid_cases':sum(r['valid_sample'] for r in results),'detected':sum(r.get('detected') is True and r['expected']=='FAIL' for r in results),'missed':sum(r['valid_sample'] and r['expected']=='FAIL' and r.get('detected') is False for r in results),'false_positives':sum(r.get('false_positive') is True for r in results)}

class ScientificConflictAdjudicator:
 def adjudicate(self,contract,deterministic,semantic):
  # No special rule IDs or automatic dismissal of a model issue. Independent evidence review
  # is required for substantive scientific resolution.
  by={c['check_id']:c for c in deterministic['checks']};conflicts=[]
  for issue in semantic.get('issues',[]):
   if not isinstance(issue,dict):
    conflicts.append({'status':'NEEDS_HUMAN_REVIEW','repair_allowed':False,'reason':'Unstructured semantic issue','original_issue':issue});continue
   cid=issue.get('constraint_id');measured=by.get(cid)
   if measured and measured['status']=='PASS':conflicts.append({'conflict_id':str(uuid.uuid4()),'constraint_id':cid,'contract_hash':digest(contract),'status':'NEEDS_HUMAN_REVIEW','repair_allowed':False,'deterministic':measured,'semantic_issue':issue,'reason':'Measured subset may not establish full scientific meaning; independent evidence adjudication required'})
  return conflicts

class ReferenceAwareVideoReviewer:
 def __init__(self,gateway):self.gateway=gateway
 def review(self,artifacts,contract,evidence,visual_references=None):
  from .providers import parse_json
  prompt='''Compare the COMPLETE generated video against the frozen scientific contract and actual retrieved source/reference event-state representations. Compare scientific entities, events, causal ordering, persistent relations and visible mechanism, NOT pixel resemblance. References may simplify or be wrong; use source scope. Never assume intention or metadata proves a visible event. For each critical constraint state observed evidence and timestamp if actually readable, else NOT_MEASURED. Return JSON {"science":{"decision":"PASS|REVISE|REVIEW_INCOMPLETE|NEEDS_HUMAN_REVIEW|ERROR","issues":[{"constraint_id":"actual ID or null","description":"...","evidence_ids":[]}],"checks":[{"constraint_id":"...","status":"PASS|FAIL|NOT_MEASURED|UNCERTAIN","observation":"..."}],"reference_comparison":{"new_evidence":[],"missing_video_reference":true,"limitations":[]}}}. Do not turn unavailable reference video into fabricated visual evidence. At most6 issues, concise.'''
  payload={'contract':contract,'retrieved_evidence':evidence,'visual_references':visual_references or [],'reference_events':artifacts.get('reference_events',[]),'actual_events':artifacts.get('trace',{}).get('events',[]),'actual_inventory':artifacts.get('scene_graph',{}).get('objects',[]),'deterministic':artifacts.get('execution')}
  result=parse_json(self.gateway.request('qwen','contract_reference_video_review',prompt+json.dumps(payload,ensure_ascii=False),video=artifacts['video']))['science']
  result.update(contract_hash=digest(contract),video_sha256=hashlib.sha256(Path(artifacts['video']).read_bytes()).hexdigest(),mode='FULL_VIDEO_WITH_RETRIEVED_REFERENCE_CONTEXT')
  return result
