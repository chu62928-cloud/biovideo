"""Checkpointed real experiment. Model requests require explicit persisted authorization."""
from pathlib import Path
import sys,json,os,shutil,hashlib,subprocess
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.contracts import write,digest
from biology_expert.providers import ModelGateway
from biology_expert.agent import BiologyExpertAgent
from biology_expert.contract_builder import ScientificEvidenceRetriever,ScientificContractBuilder
from biology_expert.typed_science_builder import freeze_model,TypedContractCompiler
from scientific_scene.typed_planner import plan_typed_scene,bind_typed_plan
from biology_expert.temporal_validator import TemporalMechanismValidator,MechanismMutationTester
load=lambda p:json.loads(Path(p).read_text())

def run(task_path,env_path):
 authpath=E/'authorization.json'
 if not authpath.exists() or load(authpath).get('source')!='explicit_user_message':raise ValueError('PAID_AUTHORIZATION_REQUIRED: user task explicitly says suggested ceilings are not spending authorization')
 auth=load(authpath)
 for line in Path(env_path).read_text().splitlines():
  if line and not line.startswith('#') and '=' in line:
   k,v=line.split('=',1);os.environ[k]=v
 os.environ['QWEN_MODEL']='qwen3.8-27b'
 gateway=ModelGateway(E/'logs',{'deepseek':auth['deepseek_limit'],'qwen':auth['qwen_limit']},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096})
 agent=BiologyExpertAgent(E/'workflow',gateway);task=load(task_path);folder=E/'candidates'/task['topic_id'];folder.mkdir(parents=True,exist_ok=True)
 retriever=ScientificEvidenceRetriever(E/'research',limit=30,visual_limit=0);builder=ScientificContractBuilder(gateway,E,retriever)
 planfile=folder/'discovery_plan.json'
 if not planfile.exists():write(planfile,builder.plan(task))
 retrievalfile=folder/'retrieval.json'
 if not retrievalfile.exists():write(retrievalfile,retriever.retrieve(task,load(planfile)))
 retrieval=load(retrievalfile)
 resultfile=folder/'typed_result.json'
 if not resultfile.exists():write(resultfile,agent.build_typed_science_model(task,retrieval))
 result=load(resultfile);model=result['model'];review=result['review']
 write(folder/'checkpoint.json',{'stage':'CONTRACT_REVIEWED','model_hash':digest(model),'review':review['decision'],'next_allowed_tool':'typed_scene_planner' if review['decision']=='PASS' else 'independent_evidence_repair','real_sources':len(retrieval['evidence'])})
 if review['decision']!='PASS':return {'status':'REVISE','model':model,'review':review,'scene':None}
 freeze_model(model,review,folder/'frozen');compiled=TypedContractCompiler().compile(model,review);write(folder/'compiled_plan.json',compiled)
 if not any(r['compile_status']=='COMPILED' for r in compiled['constraints']):return {'status':'BLOCKED','reason':'No fully compiled scientific observable','model':model,'review':review}
 scene=plan_typed_scene(model,review);write(folder/'scene_graph.json',scene);write(folder/'checkpoint.json',{'stage':'SCENE_VALIDATED','model_hash':digest(model),'scene_hash':digest(scene),'next_allowed_tool':'transaction_renderer','compiled_constraints':sum(c['compile_status']=='COMPILED' for c in compiled['constraints'])})
 return {'status':'SCENE_VALIDATED','model':model,'review':review,'scene':scene,'compiled':compiled}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--env-file',required=True);args=p.parse_args()
 print(json.dumps(run(args.task,args.env_file),ensure_ascii=False))
