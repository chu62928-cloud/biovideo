from pathlib import Path
import sys,json,os,hashlib
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway
from biology_expert.agent import BiologyExpertAgent
from biology_expert.contract_builder import ScientificEvidenceRetriever,ScientificContractBuilder
from biology_expert.contracts import write,digest
from biology_expert.model_reliability import ScientificCausalGraphValidator
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':12,'qwen':0});task=json.loads((E/'task.json').read_text());A=BiologyExpertAgent(E/'workflow',G)
freeze=json.loads((R/'experiments/science_scope_maintenance/science_code_freeze.json').read_text());assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze.items())
try:
 retriever=ScientificEvidenceRetriever(E/'research',limit=30,visual_limit=0);builder=ScientificContractBuilder(G,E,retriever)
 if not (E/'discovery.json').exists():write(E/'discovery.json',builder.plan(task))
 if not (E/'retrieval.json').exists():write(E/'retrieval.json',retriever.retrieve(task,json.loads((E/'discovery.json').read_text())))
 retrieval=json.loads((E/'retrieval.json').read_text())
 if not retrieval['evidence']:raise ValueError('UNRESOLVED_EVIDENCE')
 if not (E/'initial_model.json').exists():write(E/'initial_model.json',A.build_typed_science_model(task,retrieval))
 result=json.loads((E/'initial_model.json').read_text());model=result['model'];review=result['review'];write(E/'initial_causal.json',ScientificCausalGraphValidator().validate(model))
 if not (E/'audit.json').exists():write(E/'audit.json',A.audit_typed_reliability(task,model,retrieval['evidence'],review))
 audit=json.loads((E/'audit.json').read_text());issues=audit['evidence']['issues']
 for n,x in enumerate(review.get('issues',[])):
  target=x.get('target_id');issues.append({'issue_id':'REVIEW_'+str(n),'target_ids':[target] if target else [],'issue_type':'SCOPE_MISMATCH' if target=='scope' else 'INSUFFICIENT_EVIDENCE','required_evidence':x['reason'],'evidence_ids':x.get('evidence_ids',[])})
 if not issues:write(E/'result.json',{'status':'NO_REPAIR_REQUIRED','note':'Initial model approval alone does not establish repair capability','review':review})
 else:write(E/'result.json',A.repair_typed_science(task,model,issues,retrieval['evidence'],E/'automatic',max_attempts=3))
except Exception as ex:write(E/'error.json',{'error_type':type(ex).__name__,'message':str(ex)[:3000],'science_code_changed':not all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in freeze.items())});print('ERROR',type(ex).__name__,str(ex)[:300],flush=True)
