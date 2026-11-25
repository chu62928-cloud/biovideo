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
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/dna_replication';old=json.loads((f/'typed_result.json').read_text());retrieval=json.loads((f/'retrieval_publisher.json').read_text());write(f/('typed_result_before_repair_'+str(len(g.rows))+'.json'),old)
schema=json.loads((R/'Code2Video/src/biology_expert/schemas/typed_science_model.schema.json').read_text())
prompt='Revise model per independent review using only supplied original passages. Complete compact JSON under4500 tokens; simplify item verbosity and support quotes, not scientific mechanisms. Preserve requested priming, extension and maturation scope. Fix product/template/substrate identities as reviewer requires, explicit DNA product and ligation substrate gap. No RNaseH/flap nuclease equivalence assertion. Unknown identities remain unresolved and cannot affect deterministic claims. All input/output roles and observable roles must match declared participants and relation source/target entity types. 6-10 entities,2-4 processes with exact concise quotes/location on every item. At least one narrowly source-supported continuous relation observable can be DETERMINISTIC, other unformalizable aspects PARTIAL. No scientific approval self-declaration.'

m=parse_json(g.request('deepseek','typed_model_scientific_repair',prompt+json.dumps({'old_model':old['model'],'independent_review':old['review'],'schema':schema,'actual_evidence':[{**{k:e[k] for k in ['evidence_id','url','title']},'passages':e['passages']} for e in retrieval['evidence']]},ensure_ascii=False)))
write(f/'scientific_repair_candidate.json',m);validate_typed_model(m,retrieval['evidence']);review=TypedScienceModelReviewer(g).review(m,retrieval['evidence'],json.loads((E/'dna_replication_task.json').read_text()));write(f/'typed_result.json',{'model':m,'review':review});print(review,flush=True)
if review['decision']=='PASS':
 freeze_model(m,review,f/'frozen');write(f/'compiled_plan.json',TypedContractCompiler().compile(m,review));write(f/'scene_graph.json',plan_typed_scene(m,review))
