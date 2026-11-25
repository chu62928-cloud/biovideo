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
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/mitosis';m=json.loads((f/'candidate_before_repair.json').read_text());retrieval=json.loads((f/'retrieval.json').read_text())
prompt='Return JSON only {"patches":[{"process_semantic_id":"...","input_roles":["actual participant role"],"output_roles":["actual participant role"]}]}. Fix only input_roles/output_roles for every process in supplied candidate. They must reference the participant role strings already declared, not descriptive states or new IDs. No other scientific changes. Compact.'
patchfile=f/'role_reference_patch.json'
patch=json.loads(patchfile.read_text()) if patchfile.exists() else parse_json(g.request('deepseek','typed_role_reference_repair',prompt+json.dumps(m)));write(f/'role_reference_patch.json',patch)
for x in patch['patches']:
 p=next(p for p in m['processes'] if p['process_semantic_id']==x['process_semantic_id']);p['input_roles']=x['input_roles'];p['output_roles']=x['output_roles']
try:validate_typed_model(m,retrieval['evidence'])
except ValueError as error:
 fix=parse_json(g.request('deepseek','typed_temporal_reference_repair','Return JSON only {"patches":[{"process_semantic_id":"...","temporal_scope":{...}}]}. Fix all temporal references: after/concurrent_with may contain only defined process_semantic_ids. Prior out-of-scope context belongs in start_condition text, not after references. Preserve scientific scope, support and valid dependencies. Resolve contradiction if a process is declared concurrent with a process that depends on its completion. Do not invent facts. Error: '+str(error)+json.dumps(m)))
 write(f/'temporal_reference_patch.json',fix)
 for x in fix['patches']:next(p for p in m['processes'] if p['process_semantic_id']==x['process_semantic_id'])['temporal_scope']=x['temporal_scope']
 validate_typed_model(m,retrieval['evidence'])
write(f/'model_candidate.json',m)
review=TypedScienceModelReviewer(g).review(m,retrieval['evidence'],json.loads((E/'mitosis_task.json').read_text()));write(f/'typed_result.json',{'model':m,'review':review});print(review,flush=True)
if review['decision']=='PASS':
 freeze_model(m,review,f/'frozen');compiled=TypedContractCompiler().compile(m,review);write(f/'compiled_plan.json',compiled);write(f/'scene_graph.json',plan_typed_scene(m,review))
