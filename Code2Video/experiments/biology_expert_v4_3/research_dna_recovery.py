from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contract_builder import ScientificEvidenceRetriever
from biology_expert.agent import BiologyExpertAgent
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000});f=E/'candidates/dna_replication';task=json.loads((E/'dna_replication_task.json').read_text())
plan=parse_json(g.request('deepseek','typed_research_replan','Original candidate textbook pages were inaccessible. Return JSON {candidate_urls:[2 likely direct OpenStax pages],scientific_queries:[one query]}. Use actual task, no prewritten scientific answers: '+json.dumps(task)))
write(f/'recovery_discovery_plan.json',plan);retrieval=ScientificEvidenceRetriever(E/'research',limit=30,visual_limit=0).retrieve(task,plan);write(f/'retrieval_recovery.json',retrieval)
if retrieval['evidence']:
 result=BiologyExpertAgent(E/'workflow_dna',g).build_typed_science_model(task,retrieval);write(f/'typed_result.json',result);print(result['review'])
else:print('UNRESOLVED_EVIDENCE')
