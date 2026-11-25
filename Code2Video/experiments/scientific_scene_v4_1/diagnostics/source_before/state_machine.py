"""Transactional generic actions. Scientific meaning is injected as conditions."""
import copy,math
from .models import anchor
from .validation import conditions
OPERATIONS={'attach','detach','connect','disconnect','transform_state','move_along_path','extend','split','merge','replace_component'}
class TransitionEngine:
 def __init__(self):self.events=[]
 def apply(self,assembly,action,context=None,validate=True):
  previous=copy.deepcopy(assembly);candidate=copy.deepcopy(assembly)
  result={'action_id':action['transition_id'],'committed':False,'operation':action['operation']}
  try:
   if action['operation'] not in OPERATIONS:raise ValueError('Unknown operation')
   if not set(action['targets'])<=set(candidate.objects):raise ValueError('Unknown action object')
   allowed=assembly.spec['allowed_transitions']
   if action['process_id'] not in allowed:raise ValueError('Process not allowed for assembly')
   pre=action.get('preconditions',[])
   if validate and conditions(candidate,pre):raise ValueError('Preconditions not satisfied: '+str(conditions(candidate,pre)))
   p=action.get('params',{});ids=action['targets'];op=action['operation']
   if op in ['attach','connect']:
    candidate.relations.append({'source':ids[0],'target':ids[1],'type':p.get('relation',op),'source_anchor':p.get('source_anchor','center'),'target_anchor':p.get('target_anchor','center'),'offset':p.get('offset',[0,0,0])})
   elif op in ['detach','disconnect']:
    candidate.relations=[r for r in candidate.relations if not(r['source']==ids[0] and r['target']==ids[1] and r['type']==p.get('relation',op.replace('dis','')))]
   elif op=='transform_state':
    for oid,changes in p.get('visual_updates',{}).items():candidate.objects[oid]['visual_representation'].update(copy.deepcopy(changes))
    for oid,changes in p.get('property_updates',{}).items():candidate.objects[oid]['scientific_properties'].update(copy.deepcopy(changes))
   elif op=='move_along_path':
    for oid,path in p['paths'].items():
     geom=candidate.objects[oid]['visual_representation'];old=anchor(candidate.objects[oid],'center')
     target=path[-1];delta=[b-a for a,b in zip(old,target)]
     if 'points' in geom:geom['points']=[[x+d for x,d in zip(point,delta)] for point in geom['points']]
     geom['center']=target
   elif op=='extend':
    oid=ids[0];geom=candidate.objects[oid]['visual_representation'];geom['visible']=True
    geom['points']=copy.deepcopy(p['points']);geom['center']=[sum(x[i] for x in geom['points'])/len(geom['points']) for i in range(3)]
   elif op=='split':
    candidate.relations=[r for r in candidate.relations if r['type']!=p['remove_relation']]
    for oid in ids:candidate.objects[oid]['scientific_properties'].update(p.get('property_updates',{}))
   elif op=='merge':
    for oid in ids:candidate.objects[oid]['scientific_properties']['assembly_membership']=p['target_group']
   elif op=='replace_component':
    candidate.objects[ids[0]]['visual_representation']['visible']=False
    candidate.objects[ids[1]]['visual_representation']['visible']=True
   for oid,changes in p.get('visual_updates',{}).items():candidate.objects[oid]['visual_representation'].update(copy.deepcopy(changes))
   if op in ['attach','connect'] and p.get('draw_link'):candidate.relations[-1]['draw_link']=p['draw_link']
   candidate.state.update(p.get('state_updates',{}))
   for unused in range(2):
    for rel in candidate.relations:
     if rel['type'] in ['attachment','active_site']:
      source=candidate.objects[rel['source']]
      pos=anchor(candidate.objects[rel['target']],rel.get('target_anchor','center'))
      source['visual_representation']['center']=[x+y for x,y in zip(pos,rel.get('offset',[0,0,0]))]
     if rel.get('draw_link') in candidate.objects:
      geom=candidate.objects[rel['draw_link']]['visual_representation']
      geom['points']=[anchor(candidate.objects[rel['source']],rel.get('source_anchor','center')),anchor(candidate.objects[rel['target']],rel.get('target_anchor','center'))]
      geom['center']=[(x+y)/2 for x,y in zip(*geom['points'])]
   failures=conditions(candidate,assembly.spec['invariants']+action.get('invariants',[])+action.get('postconditions',[]),previous) if validate else []
   if failures:raise ValueError('Postcondition/invariant failed: '+str(failures))
   assembly.objects=candidate.objects;assembly.state=candidate.state;assembly.relations=candidate.relations
   result.update(committed=True,state=assembly.get_state())
  except Exception as exc:
   result.update(error_type=type(exc).__name__,error=str(exc),state=assembly.get_state())
   assert assembly.snapshot()==previous.snapshot(),'Failed transition polluted state'
  self.events.append(copy.deepcopy(result));return result
