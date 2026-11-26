from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway
from biology_expert.agent import BiologyExpertAgent
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':12,'qwen':0});A=BiologyExpertAgent(E/'recovered_workflow',G);m=json.loads((E/'recovered_candidate.json').read_text());review=json.loads((E/'recovered_review.json').read_text());task=json.loads((E/'task.json').read_text());evidence=json.loads((E/'retrieval.json').read_text())['evidence']
issues=[];ids={x['semantic_id'] for x in m['entities']+m['relations']}|{p['process_semantic_id'] for p in m['processes']}
for n,x in enumerate(review['issues']):
 target=x['target_id'];targets=[target] if target in ids else []
 # State issues target the process that declares that state; no biological answer supplied.
 for state in m.get('states',[]):
  if state['state_id']==target:targets+=state.get('required_by_process_ids',[])+([state['producer_process_id']] if state.get('producer_process_id') else [])
 issues.append({'issue_id':'INDEPENDENT_'+str(n),'target_ids':list(set(targets)),'required_evidence':x['reason'],'evidence_ids':x['evidence_ids']})
try:write(E/'recovered_repair_result.json',A.repair_typed_science(task,m,issues,evidence,E/'recovered_automatic',max_attempts=3))
except Exception as ex:write(E/'recovered_repair_error.json',{'type':type(ex).__name__,'message':str(ex)[:1800]});print(type(ex).__name__,str(ex)[:200],flush=True)
