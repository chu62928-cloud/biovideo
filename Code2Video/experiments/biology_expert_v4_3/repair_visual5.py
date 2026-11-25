from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/mitosis';model=json.loads((f/'typed_result.json').read_text())['model'];scene=json.loads((f/'scene_graph.json').read_text());write(f/('scene_before_'+str(__import__('time').time_ns())+'.json'),scene)
prompt='Return compact JSON with complete objects,relations,events,actions,assemblies arrays correcting current rendered scene. Do not change frozen model. Previous run failed: metaphase_alignment exact approved precondition value is missing; copy exact value from approved observable precondition into preceding state_after AND separation state_before. Avoid claiming partial rule full verification. Scene poles/plane must have explicit event participant bindings, assembly parent bind to both sister components, no aliases mapping parent to single sister. Preserve existing physical sister identities. Fix stroke_width: uses Manim pixel units so .18 is invisibly thin: rods 14, microtubules3, plate1. Initialize rods/kinetochores at FIRST action.from rather than at final plane to avoid teleport t1. Initial pair must be visibly joined at their central region; model a tiny connector via existing pair visual geometry, no unexplained new scientific object. No fake yellow extra lines from center of microtubule to kinetochore: set draw_link=false as the microtubule path already connects pole and kinetochore. Microtubule label_offset should be [0,.4,0], not +/-2.6 that pushes labels outside. Keep rod labels opposite above/below. Scope one chromosome, timing8s; same physical daughters move opposite poles. Preserve dynamic_path actions. Return all five arrays complete, under6000tokens.'

patch=parse_json(g.request('deepseek','typed_scene_semantic_repair',prompt+json.dumps({'model':model,'scene':scene})))
for k in ['relations','events','actions','objects','assemblies']:scene[k]=patch[k]
write(f/'scene_graph.json',scene);write(f/'semantic_repair_response.json',patch)
