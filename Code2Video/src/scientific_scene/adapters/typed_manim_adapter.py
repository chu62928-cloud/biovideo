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
   geom=obj['visual_representation'];mob=Circle(radius=geom['radius'],color=geom['color'],fill_opacity=.6).move_to(geom['center']);self.register_object(obj['object_id'],mob,role=obj['scientific_identity']['kind'],entity_semantic_id=obj['entity_semantic_id']);self.semantic_objects[obj['object_id']]=obj;self.add(mob)
   text=Text(geom['label'],font_size=16);text.scale_to_fit_width(min(2.4,max(.5,text.width)));text.next_to(mob,UP,buff=.2);self.register_object('label_'+obj['object_id'],text,role='label');self.add(text)
  caption=Text('Schematic process model',font_size=22).move_to([0,-3.1,0]);self.register_object('caption',caption,role='label');self.add(caption)
  def tick(dt):
   time=float(self.time)
   for event in self.typed_graph['events']:
    eid=event['event_id']
    if time>=event['start_time'] and not any(m['id']==eid and m['phase']=='started' for m in self.typed_markers):
     self.typed_markers.append({'id':eid,'phase':'started','time':time,'process_semantic_id':event['process_semantic_id']});self.active_typed_events.add(eid)
     for rid in event['relation_semantic_ids']:
      relation=next(r for r in self.typed_graph['relations'] if r['semantic_id']==rid);self.typed_relations.append(copy.deepcopy(relation))
      # A registered line visually expresses an association, not molecular structure.
      name='relation_'+rid
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
