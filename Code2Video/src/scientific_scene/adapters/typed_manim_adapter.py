"""Generic independently timed typed-scene execution using existing BiologyScene trace."""
from manim import *
from pathlib import Path
import json,copy
from biology_runtime import BiologyScene
class TypedScientificScene(BiologyScene):
 def setup(self):
  super().setup();self.typed_observations=[];self.typed_markers=[];self.active_typed_events=set();self.typed_relations=[];self.typed_state={}
 def render_typed(self,path='assets/scene_graph.json'):
  self.typed_graph=json.loads(Path(path).read_text());self.semantic_objects={}
  for obj in self.typed_graph['objects']:
   geom=obj['visual_representation']
   if geom.get('format')=='path':
    from ..path_geometry import PathGeometry
    mob=PathGeometry(geom['points'],color=geom['color'],stroke_width=geom.get('stroke_width',10))
   elif geom.get('format')=='ellipse':mob=Ellipse(width=geom.get('width',.5),height=geom.get('height',1),color=geom['color'],fill_opacity=.6).move_to(geom['center'])
   else:mob=Circle(radius=geom.get('radius',.15),color=geom['color'],fill_opacity=.6).move_to(geom['center'])
   mob.set_opacity(1 if geom.get('visible',True) else 0)
   self.register_object(obj['object_id'],mob,role=obj['scientific_identity']['kind'],entity_semantic_id=obj['entity_semantic_id']);self.semantic_objects[obj['object_id']]=obj;self.add(mob)
   text=Text(geom.get('label',''),font_size=16);text.scale_to_fit_width(min(2.0,max(.5,text.width)))
   offset=np.array(geom.get('label_offset',[0,.55,0]));text.add_updater(lambda m,target=mob,d=offset:m.move_to(target.get_center()+d).set_opacity(max(float(target.get_stroke_opacity()),float(target.get_fill_opacity()))))
   self.register_object('label_'+obj['object_id'],text,role='label');self.add(text)
  # Initialize each object at its first declared motion origin before the first frame.
  for oid in self.semantic_objects:
   motions=sorted([a for a in self.typed_graph.get('actions',[]) if a['object_id']==oid and not a.get('dynamic_path')],key=lambda a:a['start_time'])
   if motions:self.objects[oid].move_to(motions[0]['from'])
  caption=Text('Schematic process model',font_size=22).move_to([0,-3.1,0]);self.register_object('caption',caption,role='label');self.add(caption)
  def tick(dt):
   time=float(self.time)
   for action in self.typed_graph.get('actions',[]):
    if time>=action['start_time']:
     alpha=min(1,max(0,(time-action['start_time'])/max(.001,action['end_time']-action['start_time'])))
     self.objects[action['object_id']].move_to((1-alpha)*np.array(action['from'])+alpha*np.array(action['to']))
   # Sync declared visual relation endpoints after all object motions.
   for action in self.typed_graph.get('actions',[]):
    dynamic=action.get('dynamic_path')
    if dynamic and time>=action['start_time']:
     mob=self.objects[action['object_id']]
     from ..path_geometry import PathGeometry
     if isinstance(mob,PathGeometry):mob.set_path([self.objects[dynamic['source_object']].get_center(),self.objects[dynamic['target_object']].get_center()])
   for relation in self.typed_graph['relations']:
    name='relation_'+relation['semantic_id']+'_'+relation['source']+'_'+relation['target']
    if name in self.objects:self.objects[name].put_start_and_end_on(self.objects[relation['source']].get_center(),self.objects[relation['target']].get_center())
   for event in self.typed_graph['events']:
    eid=event['event_id']
    if time>=event['start_time'] and not any(m['id']==eid and m['phase']=='started' for m in self.typed_markers):
     self.typed_markers.append({'id':eid,'phase':'started','time':time,'process_semantic_id':event['process_semantic_id']});self.active_typed_events.add(eid)
     for rid in event['relation_semantic_ids']:
      matching=[r for r in self.typed_graph['relations'] if r['semantic_id']==rid]
      for r in matching:
       if r not in self.typed_relations:self.typed_relations.append({**copy.deepcopy(r),'type':r.get('model_relation_ref',r['type'])})
      if not matching:continue
      matching=[r for r in matching if r.get('draw_link',True)]
      if not matching:continue
      relation=matching[0]
      for linked in matching[1:]:
       lname='relation_'+rid+'_'+linked['source']+'_'+linked['target']
       if lname not in self.objects:
        edge=Line(self.objects[linked['source']].get_center(),self.objects[linked['target']].get_center(),stroke_width=3,color=YELLOW);self.register_object(lname,edge,role='decoration');self.add(edge)
      # A registered line visually expresses an association, not molecular structure.
      name='relation_'+rid+'_'+relation['source']+'_'+relation['target']
      if name not in self.objects:
       line=Line(self.objects[relation['source']].get_center(),self.objects[relation['target']].get_center(),stroke_width=3,color=YELLOW);self.register_object(name,line,role='decoration');self.add(line)
     self.typed_state.update(event['state_before'])
     caption.become(Text(event['caption'],font_size=22).scale_to_fit_width(11).move_to([0,-3.1,0]))
    if time>=event['end_time'] and eid in self.active_typed_events:
     self.active_typed_events.remove(eid);self.typed_markers.append({'id':eid,'phase':'ended','time':time,'process_semantic_id':event['process_semantic_id']});self.typed_state.update(event['state_after'])
   self.capture_typed_geometry()
  self.typed_observer_tick=tick
  self.wait(self.typed_graph['duration'])
  tick(0)
  del self.typed_observer_tick
  self.capture_typed_geometry()
 def update_mobjects(self,dt):
  super().update_mobjects(dt)
  if hasattr(self,'typed_graph') and hasattr(self,'typed_observer_tick'):self.typed_observer_tick(dt)
 def capture_typed_geometry(self):
  if not hasattr(self,'semantic_objects'):return
  objects={oid:{'instance_id':id(self.objects[oid]),'origin_id':obj['scientific_identity']['origin_id'],'entity_semantic_id':obj['entity_semantic_id'],'kind':obj['scientific_identity']['kind'],'visible':self.objects[oid] in self.mobjects,'center':self.objects[oid].get_center().tolist(),'anchors':{'center':self.objects[oid].get_center().tolist()}} for oid,obj in self.semantic_objects.items()}
  self.typed_observations.append({'time':float(self.time),'objects':objects,'relations':copy.deepcopy(self.typed_relations),'state_variables':copy.deepcopy(self.typed_state),'active_events':sorted(self.active_typed_events),'participants':{e['event_id']:e['participant_bindings'] for e in self.typed_graph['events'] if e['event_id'] in self.active_typed_events}})
 def tear_down(self):
  super().tear_down();p=Path('geometry_trace.json');data=json.loads(p.read_text());data.update(scientific_observations=self.typed_observations,events=[{'id':e['id'],'time':e['time']} for e in self.typed_markers if e['phase']=='started'],typed_event_markers=self.typed_markers,typed_model_hash=self.typed_graph['typed_model_hash'] if hasattr(self,'typed_graph') else None,adapter='generic_typed_scene_v43');p.write_text(json.dumps(data,indent=2))
