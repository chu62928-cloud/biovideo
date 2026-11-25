"""Generic trusted Manim component library. No scientific topic names or teaching timeline."""
from manim import *
from pathlib import Path
import json,copy,math
from biology_runtime import BiologyScene
from ..models import Assembly
from ..state_machine import TransitionEngine
def visible_opacity(mob):
 values=[]
 for part in mob.get_family():
  for method in ['get_fill_opacity','get_stroke_opacity']:
   try:values.append(float(getattr(part,method)()))
   except (AttributeError,TypeError,ValueError):pass
 return max(values or [0.0])
class ScientificScene(BiologyScene):
 def setup(self):
  super().setup()
  self.scientific_observations=[];self.completed_events=[];self.current_event=None
  self.expected_snapshots=[];self.bound_sources=set();self.extra_registered=[]
 def make_component(self,obj):
  geom=obj['visual_representation'];style=self.asset_map[obj['asset_id']]
  kind=style['format'];color=geom.get('color',style.get('color',WHITE))
  if kind=='polyline':
   mob=VMobject(color=color,stroke_width=geom.get('stroke_width',5));mob.set_points_as_corners([np.array(p) for p in geom['points']])
  elif kind=='svg':mob=SVGMobject(str(Path('assets')/style['path'])).set_width(geom.get('width',.45)).move_to(geom['center'])
  elif kind=='circle':mob=Circle(radius=geom.get('radius',.12),color=color,fill_color=color,fill_opacity=1).move_to(geom['center'])
  elif kind=='polygon':mob=RegularPolygon(n=geom.get('sides',5),radius=geom.get('radius',.2),color=color,fill_opacity=.85).move_to(geom['center'])
  else:raise ValueError('Unsupported generic representation '+kind)
  return mob
 def actual_anchor(self,oid,name):
  mob=self.objects[oid];obj=self.assembly.objects[oid];spec=obj['anchors'].get(name,{'kind':'center'})
  if spec['kind']=='point':
   points=list(mob.get_start_anchors())+[mob.get_end()]
   return np.array(points[spec['index']])
  if spec['kind']=='between':
   points=list(mob.get_start_anchors())+[mob.get_end()]
   return (1-spec['alpha'])*points[spec['a']]+spec['alpha']*points[spec['b']]
  return mob.get_center()
 def create_assembly(self,graph):
  self.graph=copy.deepcopy(graph);self.asset_map={a['asset_id']:a for a in graph['assets']}
  self.assembly=Assembly(graph['assemblies'][0],graph['objects']);self.engine=TransitionEngine()
  for oid,obj in self.assembly.objects.items():
   mob=self.make_component(obj)
   self.register_object(oid,mob,role=obj['scientific_identity']['kind'],scientific_identity=obj['scientific_identity'],scientific_properties=obj['scientific_properties'])
   mob.set_opacity(1 if obj['visual_representation'].get('visible',False) else 0);self.add(mob)
   label=obj['visual_representation'].get('label')
   if label:
    text=Text(label,font_size=obj['visual_representation'].get('label_size',16),color=obj['visual_representation'].get('label_color',WHITE))
    direction=UP if obj['visual_representation'].get('label_side','up')=='up' else DOWN
    text.add_updater(lambda m,target=mob,d=direction: m.next_to(target,d,buff=.10).set_opacity(visible_opacity(target)))
    self.register_object('label__'+oid,text,role='label');self.add(text)
   for port,word in obj.get('scientific_properties',{}).get('endpoint_labels',{}).items():
    text=Text(word,font_size=14,color=obj['visual_representation'].get('color',WHITE))
    offset=np.array(obj['visual_representation'].get('endpoint_label_offset',[0,.28,0]))
    text.add_updater(lambda m,o=oid,p=port,d=offset,target=mob:m.move_to(self.actual_anchor(o,p)+d).set_opacity(visible_opacity(target)))
    self.register_object('polarity__'+oid+'__'+port,text,role='label');self.add(text)
  for rel in self.assembly.relations:self.update_relation(rel)
  return self.assembly
 def update_relation(self,rel):
  # Generic attachments track real target anchors. Visual links are editable registered lines.
  if rel['type'] in ['attachment','active_site']:
   source,target=rel['source'],rel['target'];name='site__'+source+'__'+target
   if name not in self.objects:
    dot=Dot(radius=.01).set_opacity(0)
    port=rel.get('target_anchor','center')
    dot.add_updater(lambda m,t=target,p=port:m.move_to(self.actual_anchor(t,p)))
    dot.move_to(self.actual_anchor(target,port));self.register_object(name,dot,role='anchor');self.add(dot)
   self.bind_near(source,name,offset=rel.get('offset',[0,0,0]),max_distance=.8);self.bound_sources.add(source)
  if rel.get('draw_link'):
   name=rel['draw_link']
   if name not in self.objects:
    line=Line(self.actual_anchor(rel['source'],rel.get('source_anchor','center')),self.actual_anchor(rel['target'],rel.get('target_anchor','center')),color=rel.get('color',GRAY),stroke_width=2)
    self.register_object(name,line,role='decoration');self.add(line)
   line=self.objects[name]
   if not hasattr(line,'_scientific_link'):
    line.add_updater(lambda m,r=copy.deepcopy(rel):m.put_start_and_end_on(self.actual_anchor(r['source'],r.get('source_anchor','center')),self.actual_anchor(r['target'],r.get('target_anchor','center'))))
    line._scientific_link=True
 def apply_transition(self,action,full_validation=True):
  before=copy.deepcopy(self.assembly.objects)
  result=self.engine.apply(self.assembly,action,validate=full_validation)
  if not result['committed']:raise ValueError('State transition rejected: '+result['error'])
  animations=[]
  for oid,obj in self.assembly.objects.items():
   if before[oid]['visual_representation']!=obj['visual_representation']:
    target=self.make_component(obj);target.set_opacity(1 if obj['visual_representation'].get('visible',False) else 0)
    animations.append(Transform(self.objects[oid],target))
    if obj['visual_representation'].get('label')!=before[oid]['visual_representation'].get('label') and 'label__'+oid in self.objects:
     self.objects['label__'+oid].become(Text(obj['visual_representation']['label'],font_size=16))
  # Detachment removes only the adapter's own persistent binding updater.
  active={r['source'] for r in self.assembly.relations if r['type'] in ['attachment','active_site']}
  for source in self.bound_sources-active:
   old=self._binding_updaters.get(source)
   if old:self.objects[source].remove_updater(old)
   self.bindings=[b for b in self.bindings if b['object_id']!=source]
  self.bound_sources=active
  for rel in self.assembly.relations:self.update_relation(rel)
  if animations:self.play(*animations,run_time=action['duration'],rate_func=linear)
  else:self.wait(action['duration'])
  self.expected_snapshots.append({'time':float(self.time),'transition_id':action['transition_id'],'expected':self.assembly.snapshot()})
  self.capture_geometry()
  return result
 def render_scene(self,path='assets/scene_graph.json',validation_mode='full'):
  graph=json.loads(Path(path).read_text());self.create_assembly(graph)
  title=Text(graph.get('title',graph['topic_id'].replace('_',' ')),font_size=23).move_to([0,3.55,0])
  caption=Text('Scientific schematic',font_size=19,color=YELLOW).move_to([0,-3.35,0])
  self.register_object('scene_title',title,role='label');self.register_object('scene_caption',caption,role='label');self.add(title,caption)
  steps={t['transition_id']:t for t in graph['state_transitions']}
  for ev in graph['events']:
   self.current_event=ev['event_id'];self.mark_event(ev['event_id'])
   caption.become(Text(ev['caption'],font_size=19,color=YELLOW).move_to([0,-3.35,0]))
   for tid in ev['transition_ids']:self.apply_transition(steps[tid],full_validation=validation_mode=='full')
   self.completed_events.append(ev['event_id']);self.capture_geometry()
 def update_mobjects(self,dt):
  super().update_mobjects(dt)
  if hasattr(self,'assembly'):
   for rel in self.assembly.relations:
    if rel['type'] in ['active_site','attachment']:
     self.objects[rel['source']].move_to(self.actual_anchor(rel['target'],rel.get('target_anchor','center'))+np.array(rel.get('offset',[0,0,0])))
 def capture_geometry(self):
  if hasattr(self,'assembly'):
   for rel in self.assembly.relations:
    if rel['type'] in ['active_site','attachment']:
     self.objects[rel['source']].move_to(self.actual_anchor(rel['target'],rel.get('target_anchor','center'))+np.array(rel.get('offset',[0,0,0])))
  super().capture_geometry()
  if not hasattr(self,'assembly'):return
  objects={}
  for oid,obj in self.assembly.objects.items():
   mob=self.objects[oid]
   objects[oid]={'instance_id':id(mob),'visible':visible_opacity(mob)>.05,'kind':obj['scientific_identity']['kind'],'origin_id':obj['scientific_identity']['origin_id'],'center':mob.get_center().tolist(),'anchors':{name:self.actual_anchor(oid,name).tolist() for name in obj['anchors']},'scientific_properties':copy.deepcopy(obj['scientific_properties'])}
  self.scientific_observations.append({'time':float(self.time),'current_event':self.current_event,'completed_events':list(self.completed_events),'objects':objects,'relations':copy.deepcopy(self.assembly.relations),'state_variables':copy.deepcopy(self.assembly.state)})
 def tear_down(self):
  super().tear_down()
  p=Path('geometry_trace.json');data=json.loads(p.read_text())
  known={id(part) for mob in self.objects.values() for part in mob.get_family()}
  unknown=[{'class':type(m).__name__,'center':m.get_center().tolist()} for m in self.mobjects if id(m) not in known and any(part.get_num_points()>0 and visible_opacity(part)>.05 for part in m.get_family())]
  data.update(scientific_observations=self.scientific_observations,expected_snapshots=self.expected_snapshots,transition_execution=self.engine.events if hasattr(self,'engine') else [],unregistered_visible=unknown,adapter='generic_scientific_scene_v4')
  p.write_text(json.dumps(data,indent=2))
