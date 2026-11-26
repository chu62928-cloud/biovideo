from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway
from biology_expert.typed_science_builder import TypedScienceModelReviewer
from biology_expert.model_reliability import ScientificCausalGraphValidator
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':12,'qwen':0});auth=E/'logs/budget_authorizations.json'
if not auth.exists():G.resume_authorized({'authorization_id':'known_truncation_complete_candidate_recovery','source':'explicit_user_message','provider':'deepseek','additional_requests':0,'acknowledged_failed_calls':['v42_03_c45d3765'],'reason':'Ongoing goal authorization; failed response contains complete candidate, developer extraction disclosed, no scientific edits'})
m=json.loads((E/'recovered_candidate.json').read_text());ev=json.loads((E/'retrieval.json').read_text())['evidence'];task=json.loads((E/'task.json').read_text());write(E/'recovered_causal.json',ScientificCausalGraphValidator().validate(m))
if not (E/'recovered_review.json').exists():write(E/'recovered_review.json',TypedScienceModelReviewer(G).review(m,ev,task))
print(json.loads((E/'recovered_review.json').read_text())['decision'],flush=True)
