from pathlib import Path
import sys,json,os,shutil
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.typed_science_builder import validate_typed_model,TypedScienceModelReviewer,freeze_model,TypedContractCompiler
from biology_expert.contracts import write
from scientific_scene.typed_planner import plan_typed_scene
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/mitosis';old=json.loads((f/'typed_result.json').read_text());retrieval=json.loads((f/'retrieval.json').read_text());write(f/('typed_result_before_repair_'+str(len(g.rows))+'.json'),old)
schema=json.loads((R/'Code2Video/src/biology_expert/schemas/typed_science_model.schema.json').read_text())
prompt='Revise the science model using the independent review and original actual source. Return COMPLETE compact JSON matching schema, under 5000 output tokens. Retain original user scope but explicitly delimit which narrow property each observable proves. Distinct persistent objects must represent sisters if separation is modeled. Do not assert molecular mechanisms absent sources. Limit to 4-8 entities and 2-3 processes. Keep the full requested alignment AND separation scope. Split sister chromatids explicitly; do not represent their post-separation identity using only the whole pair. Correct every specific independent reviewer concern in definitions, effects and scope text, not just a generic disclaimer. Retain directly entailed observable properties; do not invent strict causal requirements. Every core item needs exact short support quote/location. All input/output roles must be declared participant role names. after/concurrent_with only defined process IDs. This is not approved until separate review; no coordinates or animation code.'
m=parse_json(g.request('deepseek','typed_model_scientific_repair',prompt+json.dumps({'old_model':old['model'],'independent_review':old['review'],'schema':schema,'actual_evidence':[{**{k:e[k] for k in ['evidence_id','url','title']},'passages':e['passages'][15:33]} for e in retrieval['evidence']]},ensure_ascii=False)))
write(f/'scientific_repair_candidate.json',m);validate_typed_model(m,retrieval['evidence']);review=TypedScienceModelReviewer(g).review(m,retrieval['evidence'],json.loads((E/'mitosis_task.json').read_text()));write(f/'typed_result.json',{'model':m,'review':review});print(review,flush=True)
if review['decision']=='PASS':
 freeze_model(m,review,f/'frozen');write(f/'compiled_plan.json',TypedContractCompiler().compile(m,review));write(f/'scene_graph.json',plan_typed_scene(m,review))
