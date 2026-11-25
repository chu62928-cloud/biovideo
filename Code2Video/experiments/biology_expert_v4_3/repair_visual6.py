from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/mitosis';model=json.loads((f/'typed_result.json').read_text())['model'];scene=json.loads((f/'scene_graph.json').read_text());write(f/('scene_before_'+str(__import__('time').time_ns())+'.json'),scene)
prompt='Return JSON {objects,relations,events,actions,assemblies} complete five arrays. Current scene render FAILED TypeError relation source/target is a LIST. All relation source/target MUST be a SINGLE object_id string; instantiate one edge per pair; no list endpoints. Assembly may be represented via component_ids, but each relation source must concrete object string and parent role uses list of both components. Copy EXACT precondition metaphase_alignment value from approved OBS_two_daughter_chromatids_after_separation: Duplicated chromosome aligned at metaphase plate (schematic phase order). into event2.state_after and event3.state_before. Do not substitute aligned_at_metaphase_plate. Visual initialize all sister/kinetochore geometry at first actions from x=-1.68,-1.32 respectively; then end x=-.18,.18. Rod stroke_width14 not .18. Two sisters joined initial with slight angled arms toward shared midpoint -1.5, then separate smoothly to x=-3,+3. No new sister copies. Microtubule stroke3; draw_link=false all edges because paths already visible. Semantic relation model_relation_ref exact. Keep duration8. No string assurances, correct actual arrays. Under6000tokens.'

patch=parse_json(g.request('deepseek','typed_scene_semantic_repair',prompt+json.dumps({'model':model,'scene':scene})))
for k in ['relations','events','actions','objects','assemblies']:scene[k]=patch[k]
write(f/'scene_graph.json',scene);write(f/'semantic_repair_response.json',patch)
