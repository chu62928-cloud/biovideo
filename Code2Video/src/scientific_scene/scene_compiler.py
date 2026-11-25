"""Data-driven storyboard compiler. Only the model produces the experimental teaching plan."""
import copy,json
from .models import schema_validate,write,digest
from .validation import graph_checks
def compile_storyboard(storyboard,knowledge_pack,asset_registry,gateway=None,plan=None):
 blueprint=asset_registry
 process_ids=list(blueprint['processes'])
 if plan is None:
  prompt='''Compile the given fixed educational storyboard into a compact scientific scene PLAN. The verified editable assembly and process recipes below are engineering-prepared references, not model discoveries. Choose the supplied processes in scientific order. Return JSON only {"events":[{"event_id":"exact requested ID","caption":"short English caption","process_ids":["known process"],"duration":6.0}],"scientific_simplifications":["..."]}. Each process must be used exactly once, no invention. Use every requested event ID once. Total duration must match target, with clear introductions, visible change, and final hold. Preserve facts, molecular identity and mechanism causal order. Do not output coordinates/code/validated flags.'''
  request={'storyboard':storyboard,'knowledge_facts':[f for f in knowledge_pack['facts'] if f['verification']=='VERIFIED'],'available_processes':{k:{'required_states':p['required_states'],'purpose':p.get('purpose'),'preconditions':p['preconditions'],'postconditions':p['postconditions']} for k,p in blueprint['processes'].items()},'required_event_ids':storyboard['required_event_ids'],'target_seconds':storyboard['duration_target'],'scientific_simplifications':blueprint['assumptions']}
  from biology_expert.providers import parse_json
  plan=parse_json(gateway.request('deepseek','scene_compiler_'+blueprint['topic_id'],prompt+json.dumps(request,ensure_ascii=False)))
 if [e['event_id'] for e in plan['events']]!=storyboard['required_event_ids']:raise ValueError('Model omitted/changed event IDs')
 chosen=[p for e in plan['events'] for p in e['process_ids']]
 if sorted(chosen)!=sorted(process_ids):raise ValueError('Model must use each known process exactly once')
 duration=sum(e['duration'] for e in plan['events'])
 if abs(duration-storyboard['duration_target'])>2:raise ValueError('Compiled duration outside target tolerance')
 graph={'scene_id':blueprint['scene_id'],'topic_id':blueprint['topic_id'],'audience':'grades_10_12','objects':copy.deepcopy(blueprint['objects']),'assemblies':[copy.deepcopy(blueprint['assembly'])],'relations':copy.deepcopy(blueprint['assembly']['relations']),'events':[],'state_transitions':[],'constraints':copy.deepcopy(blueprint['constraints']),'assets':copy.deepcopy(blueprint['assets']),'evidence_refs':blueprint['assembly']['evidence_ids'],'event_order':list(zip(storyboard['required_event_ids'],storyboard['required_event_ids'][1:])),'scientific_simplifications':plan.get('scientific_simplifications',[])+blueprint['assumptions'],'provenance':{'plan_origin':'REAL_LLM' if gateway else 'EXPLICIT_OFFLINE_FIXTURE','blueprint_hash':digest(blueprint),'knowledge_hash':digest(knowledge_pack),'prompt_storyboard_hash':digest(storyboard)}}
 for ev in plan['events']:
  actions=[]
  for pid in ev['process_ids']:
   process=blueprint['processes'][pid]
   for i,a in enumerate(process['actions']):
    t=copy.deepcopy(a);t.update(transition_id=ev['event_id']+'_'+pid+'_'+str(i),process_id=pid,assembly_id=blueprint['assembly']['assembly_id'])
    t.setdefault('preconditions',[]);t.setdefault('postconditions',[]);t.setdefault('invariants',[]);t.setdefault('targets',[])
    if i==0:t['preconditions']=process['preconditions']+t['preconditions']
    if i==len(process['actions'])-1:t['postconditions']+=process['postconditions']
    t['duration']=ev['duration']/sum(len(blueprint['processes'][p]['actions']) for p in ev['process_ids'])
    t['evidence_ids']=process['evidence_ids'];actions.append(t)
  graph['state_transitions']+=actions
  graph['events'].append({'event_id':ev['event_id'],'caption':ev['caption'],'transition_ids':[t['transition_id'] for t in actions],'duration':ev['duration']})
 schema_validate('scene_graph',graph)
 evidence={f['fact_id'] for f in knowledge_pack['facts'] if f['verification']=='VERIFIED'}
 errors=graph_checks(graph,evidence)
 if errors:raise ValueError(str(errors))
 return {'scene_graph':graph,'assembly_instances':graph['assemblies'],'state_transitions':graph['state_transitions'],'validation_plan':graph['constraints'],'compile_report':{'schema_pass':True,'references_pass':True,'scientific_gate':'PENDING_EXPERT_REVIEW','plan':plan}}

# Reviewed typed models are the new semantic planning path; legacy blueprint compiler remains for history.
from .typed_planner import plan_typed_scene,bind_typed_plan
