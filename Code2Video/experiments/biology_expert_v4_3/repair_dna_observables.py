from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.typed_science_builder import validate_typed_model,TypedScienceModelReviewer,freeze_model,TypedContractCompiler
from biology_expert.contracts import write
from scientific_scene.typed_planner import plan_typed_scene
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/dna_replication';m=parse_json((f/'build_candidate_raw.txt').read_text());retrieval=json.loads((f/'retrieval_publisher.json').read_text())
for x in json.loads((f/'role_reference_patch.json').read_text())['patches']:
 p=next(p for p in m['processes'] if p['process_semantic_id']==x['process_semantic_id']);p['input_roles']=x['input_roles'];p['output_roles']=x['output_roles']
prompt='Return JSON {patches:[{process_semantic_id,participants,input_roles,output_roles,observables,temporal_scope}]}. Correct ALL undefined observable source_role/target_role to actual participant role strings matching relation source_entity/target_entity. Preserve exact original evidence support and quotes. Only defined temporal refs, input/output roles declared. Do not replace science by metadata. Complete arrays for each process but not rest of model. Under4500tokens.'
patch=parse_json(g.request('deepseek','typed_dna_observable_reference_repair',prompt+json.dumps(m)))
write(f/'observable_reference_patch.json',patch)
for x in patch['patches']:
 p=next(p for p in m['processes'] if p['process_semantic_id']==x['process_semantic_id'])
 for k,v in x.items():
  if k!='process_semantic_id':p[k]=v
validate_typed_model(m,retrieval['evidence'])
write(f/'model_candidate.json',m)
review=TypedScienceModelReviewer(g).review(m,retrieval['evidence'],json.loads((E/'dna_replication_task.json').read_text()));write(f/'typed_result.json',{'model':m,'review':review});print(review,flush=True)
if review['decision']=='PASS':
 freeze_model(m,review,f/'frozen');compiled=TypedContractCompiler().compile(m,review);write(f/'compiled_plan.json',compiled);write(f/'scene_graph.json',plan_typed_scene(m,review))
