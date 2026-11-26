from pathlib import Path
import sys,json,os,copy
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway
from biology_expert.contracts import write,digest
from biology_expert.model_reliability import ScientificCausalGraphValidator
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'logs',{'deepseek':12,'qwen':4})
for name in ['vesicle_transport','dna_replication','mitosis']:
 f=E/'science'/name;f.mkdir(parents=True,exist_ok=True);inp=E/'inputs'/name;old=json.loads((inp/'original.json').read_text());model=old['model'];task=json.loads((inp/'task.json').read_text());evidence=json.loads((inp/'evidence.json').read_text());prior=json.loads((inp/'historical_audit.json').read_text())
 try:
  agent=BiologyExpertAgent(f/'workflow',G);auditfile=f/'audit.json'
  if not auditfile.exists():write(auditfile,agent.audit_typed_reliability(task,model,evidence,old['review']))
  audit=json.loads(auditfile.read_text());issues=audit['evidence']['issues']
  # Generic state model migration affects reference fields of each process; explicit task,
  # not permission for unrelated biological changes.
  issues.append({'issue_id':'STATE_MODEL_MIGRATION','issue_type':'INITIAL_STATE_UNSPECIFIED','affected_process_ids':[p['process_semantic_id'] for p in model['processes']],'required_evidence':'Identify supported pre-clip conditions, explicit subject/property/value states and missing state producers without omitting user-required mechanisms. Preserve actual user teaching scope.','evidence_ids':list({v for p in model['processes'] for v in p['evidence_ids']})})
  if name=='mitosis':
   from biology_expert.model_repair import ScientificModelRepairTransaction
   tx=ScientificModelRepairTransaction(G,f/'state_migration');result=tx.run(task,model,issues,evidence,attempt=0);write(f/'result.json',{'status':'COMMITTED' if result['accepted'] else 'NEEDS_HUMAN_REVIEW','repairs':[result],'research':{'stop_reason':'Existing independently reviewed evidence reused for state migration'}})
  else:
   result=agent.repair_typed_science(task,model,issues,evidence,f/'automatic',max_attempts=3);write(f/'result.json',result)
  print('TOPIC_DONE',name,result.get('status'),flush=True)
 except Exception as ex:write(f/'error.json',{'error_type':type(ex).__name__,'message':str(ex)[:1800],'stage':'SCIENCE_LOOP'});print('TOPIC_ERROR',name,type(ex).__name__,str(ex)[:100],flush=True)
