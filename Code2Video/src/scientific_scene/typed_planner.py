"""Scene planning from reviewed semantic IDs, without topic process blueprints."""
from pathlib import Path
import copy,json
from biology_expert.contracts import digest
from biology_expert.typed_science_builder import validate_typed_model

def plan_typed_scene(model,review,duration=7):
 validate_typed_model(model)
 if review.get('decision')!='PASS' or review.get('model_hash')!=digest(model):raise ValueError('Only reviewed immutable typed models may enter scene planning')
 entities=model['entities'];processes=model['processes'];objects=[];mapping={}
 for i,entity in enumerate(entities):
  oid='object_'+str(i+1);mapping[entity['semantic_id']]=oid
  objects.append({'object_id':oid,'entity_semantic_id':entity['semantic_id'],'scientific_identity':{'name':entity['scientific_name'],'kind':entity['entity_type'],'origin_id':entity['semantic_id']},'scientific_properties':{'semantic_id':entity['semantic_id']},'anchors':{'center':{'kind':'center'}},'visual_representation':{'format':'circle','center':[-4+i*8/max(1,len(entities)-1),0,0],'radius':.24,'color':['#66DDAA','#FFBB66','#66BBEE','#DD88CC','#DDDD77'][i%5],'label':entity['scientific_name'],'precision':'generic role schematic, not molecular structure'}})
 pmap={p['process_semantic_id']:'event_'+str(i+1) for i,p in enumerate(processes)};slots={};visiting=set()
 def schedule(pid):
  if pid in slots:return slots[pid]
  if pid in visiting:raise ValueError('Cyclic process dependency')
  visiting.add(pid);p=next(x for x in processes if x['process_semantic_id']==pid);after=p['temporal_scope'].get('after',[]);start=max([schedule(x)[1] for x in after]+[.5]);length=(duration-1)/max(1,len(processes));slots[pid]=(start,start+length);visiting.remove(pid);return slots[pid]
 for p in processes:schedule(p['process_semantic_id'])
 scale=(duration-.5)/max(v[1] for v in slots.values());events=[]
 for p in processes:
  start,end=slots[p['process_semantic_id']];events.append({'event_id':pmap[p['process_semantic_id']],'process_semantic_id':p['process_semantic_id'],'action_category':p['action_category'],'participant_bindings':{x['role']:mapping[x['entity_ref']] for x in p['participants']},'start_trigger':pmap[p['process_semantic_id']]+'_started','end_trigger':pmap[p['process_semantic_id']]+'_ended','start_time':start*scale,'end_time':end*scale,'state_before':copy.deepcopy(p['preconditions']),'state_after':copy.deepcopy(p['effects']),'relation_semantic_ids':[o['relation_ref'] for o in p['observables'] if o.get('relation_ref')],'caption':p['scientific_name']})
 relations=[{'semantic_id':r['semantic_id'],'type':r['semantic_id'],'source':mapping[r['source_entity']],'target':mapping[r['target_entity']],'source_anchor':'center','target_anchor':'center','representation':'schematic association, not anatomical bond'} for r in model['relations']]
 return {'scene_id':'typed_'+model['model_id'],'typed_model_hash':digest(model),'objects':objects,'relations':relations,'events':events,'state_transitions':[{'process_semantic_id':e['process_semantic_id'],'state_before':e['state_before'],'state_after':e['state_after']} for e in events],'duration':duration,'provenance':{'planner':'generic typed deterministic scene compiler','model_origin':'independent evidence-grounded model','no_topic_blueprint':True},'visual_limitations':['Generic components express role association and process state only; full molecular mechanism requires independent video semantic review']}

def bind_typed_plan(model,compiled,scene):
 if scene['typed_model_hash']!=digest(model) or compiled['model_hash']!=digest(model):raise ValueError('VERSION_CONFLICT')
 objects={o['entity_semantic_id']:o['object_id'] for o in scene['objects']};events={e['process_semantic_id']:e for e in scene['events']};rules=[]
 for item in compiled['constraints']:
  p=events[item['process_semantic_id']];spec=copy.deepcopy(item['spec']);participants={role:[objects[entity]] for role,entity in item['participant_entity_refs'].items()}
  if spec['predicate']=='event_precedes':participants={pid:[events[pid]['event_id']] for pid in spec['ordered_event_roles']}
  rules.append({'constraint_id':item['constraint_id'],'predicate':item['predicate'],'spec':spec,'participants':participants,'expected_interval':{'status':'RESOLVED','source':'typed_scene_independent_start_end','event_id':p['event_id'],'start':p['start_time'],'end':p['end_time'],'model_hash':digest(model)},'compile_status':item['compile_status'],'full_semantics':item['full_semantics'],'reason':None,'evidence_ids':item['evidence_ids'],'process_semantic_id':item['process_semantic_id']})
 return {'contract_hash':digest(model),'scene_sha256':digest(scene),'compiled_constraints':rules,'model_hash':digest(model)}
