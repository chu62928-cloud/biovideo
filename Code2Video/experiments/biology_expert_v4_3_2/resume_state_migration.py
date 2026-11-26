from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.model_repair import ScientificModelRepairTransaction
from biology_expert.providers import ModelGateway
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
f=E/'science_formal/mitosis';inp=E/'inputs/mitosis';old=json.loads((inp/'original.json').read_text());task=json.loads((inp/'task.json').read_text());evidence=json.loads((inp/'evidence.json').read_text());audit=json.loads((f/'audit.json').read_text());issues=audit['evidence']['issues']+[{'issue_id':'STATE_MODEL_MIGRATION','affected_process_ids':[p['process_semantic_id'] for p in old['model']['processes']],'required_evidence':'Explicit supported initial and produced state references, preserve teaching scope','evidence_ids':list({e for p in old['model']['processes'] for e in p['evidence_ids']})}]
G=ModelGateway(E/'logs',{'deepseek':40,'qwen':4});tx=ScientificModelRepairTransaction(G,f/'state_migration');previous=json.loads((f/'state_migration/attempt_0/result.json').read_text());records=[previous]
for n in [1,2]:
 feedback={'previous_patch':previous.get('patch'),'error':previous.get('error'),'review':previous.get('review'),'causal_status':previous.get('causal_status')}
 result=tx.run(task,old['model'],issues,evidence,attempt=n,feedback=feedback);records.append(result);print('MIGRATION',n,result['status'],result.get('error'),flush=True)
 if result['accepted']:break
 previous=result
write(f/'result.json',{'status':'COMMITTED' if records[-1]['accepted'] else 'NEEDS_HUMAN_REVIEW','repairs':records,'research':{'stop_reason':'Existing independently reviewed evidence reused for state migration'}})
