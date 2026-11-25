"""Generic editable structures; topic facts live in data, never in this engine."""
from pathlib import Path
import copy,json,hashlib
from jsonschema import Draft202012Validator
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def schema_validate(name,data):
 schema=json.loads((Path(__file__).parent/'schemas'/(name+'.schema.json')).read_text())
 Draft202012Validator(schema).validate(data)
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
class Assembly:
 def __init__(self,spec,objects):
  self.spec=copy.deepcopy(spec);self.objects={o['object_id']:copy.deepcopy(o) for o in objects if o['object_id'] in spec['component_ids']}
  self.state=copy.deepcopy(spec['state_variables']);self.relations=copy.deepcopy(spec['relations'])
 def get_state(self):return copy.deepcopy(self.state)
 def get_components(self):return copy.deepcopy(self.objects)
 def get_relations(self):return copy.deepcopy(self.relations)
 def get_anchor(self,name):
  link=self.spec['anchor_points'][name]
  return anchor(self.objects[link['object_id']],link['anchor'])
 def set_state(self,next_state):
  from .validation import conditions
  candidate=copy.deepcopy(self);candidate.state.update(next_state)
  errors=conditions(candidate,self.spec['invariants'])
  if errors:raise ValueError(str(errors))
  self.state=candidate.state
 def validate(self):
  from .validation import conditions
  return conditions(self,self.spec['invariants'])
 def snapshot(self):return {'objects':copy.deepcopy(self.objects),'state':copy.deepcopy(self.state),'relations':copy.deepcopy(self.relations),'assembly_id':self.spec['assembly_id']}
def anchor(obj,name):
 spec=obj.get('anchors',{}).get(name,{'kind':'center'})
 geom=obj['visual_representation']
 if spec['kind']=='point':
  points=geom['points'];return list(points[spec['index']])
 if spec['kind']=='between':
  points=geom['points'];return [(1-spec['alpha'])*x+spec['alpha']*y for x,y in zip(points[spec['a']],points[spec['b']])]
 if 'points' in geom:return [(min(p[i] for p in geom['points'])+max(p[i] for p in geom['points']))/2 for i in range(3)]
 return list(geom.get('center',[0,0,0]))
class AssemblyRegistry:
 def __init__(self):self.items={}
 def register(self,data):
  schema_validate('assembly',data)
  if data['assembly_type'] in self.items:raise ValueError('Duplicate assembly type')
  self.items[data['assembly_type']]=copy.deepcopy(data)
 def instantiate(self,kind,objects):return Assembly(self.items[kind],objects)
class SceneGraph:
 def __init__(self,data):
  schema_validate('scene_graph',data);self.data=copy.deepcopy(data)
 def content_hash(self):return digest(self.data)
class ProcessRegistry:
 def __init__(self):self.items={}
 def register(self,data):
  schema_validate('process_template',data);self.items[data['process_id']]=copy.deepcopy(data)
 def get(self,name):return copy.deepcopy(self.items[name])
