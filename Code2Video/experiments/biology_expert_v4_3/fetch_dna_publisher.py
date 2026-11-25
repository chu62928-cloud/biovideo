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
plan={'candidate_urls':['https://openstax.org/books/biology-2e/pages/14-3-basics-of-dna-replication','https://openstax.org/books/biology-2e/pages/14-5-dna-replication-in-eukaryotes'],'scientific_queries':[]}
# Explicit researcher supplied publisher URLs, actual fetch still required; no supplied biological answers.
write(f/'researcher_source_plan.json',plan);retrieval=ScientificEvidenceRetriever(E/'research',limit=30,visual_limit=0).retrieve(task,plan);write(f/'retrieval_publisher.json',retrieval)
if retrieval['evidence']:
 result=BiologyExpertAgent(E/'workflow_dna',g).build_typed_science_model(task,retrieval);write(f/'typed_result.json',result);print(result['review'])
else:print('UNRESOLVED_EVIDENCE')
