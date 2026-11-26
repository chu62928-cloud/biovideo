"""Read-only provider balance and checkpoint inspection; never submits a model request."""
from pathlib import Path
import json,os,requests,hashlib,datetime
E=Path(__file__).parent

def inspect():
 env={}
 for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
  if '=' in line and not line.startswith('#'):
   k,v=line.split('=',1);env[k]=v.strip().strip('"').strip("'")
 base=env['DEEPSEEK_BASE_URL'].rstrip('/')
 try:
  response=requests.get(base+'/user/balance',headers={'Authorization':'Bearer '+env['DEEPSEEK_API_KEY']},timeout=20)
  balance=response.json();provider={'http_status':response.status_code,'available':balance.get('is_available'),'balance_infos':balance.get('balance_infos',[])}
 except Exception as ex:provider={'available':None,'error':type(ex).__name__}
 rows=json.loads((E/'logs/model_calls.json').read_text());topics=[]
 for topic in ['vesicle_transport','dna_replication','mitosis']:
  folder=E/'science_formal'/topic
  attempts=[]
  for result in sorted(folder.rglob('attempt_*/result.json')):
   data=json.loads(result.read_text());attempts.append({'path':str(result.relative_to(E)),'status':data.get('status'),'review':data.get('independent_review'),'candidate_hash':data.get('after_hash')})
  topics.append({'topic':topic,'audit_cached':(folder/'audit.json').exists(),'attempts':attempts,'error':json.loads((folder/'error.json').read_text()) if (folder/'error.json').exists() else None})
 code_root=E.parents[1];frozen=json.loads((E/'formal_science_code_freeze.json').read_text());changed=[name for name,h in frozen.items() if not (code_root/name).exists() or hashlib.sha256((code_root/name).read_bytes()).hexdigest()!=h]
 return {'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provider':provider,'model_calls_preserved':len(rows),'latest_call':rows[-1],'topics':topics,'science_code_changed_after_freeze':changed,'can_resume_paid_requests':provider.get('available') is True and not changed,'next_action':'Restore account balance, verify again, then acknowledge the confirmed 402 and resume only missing steps. No automatic retries or ledger reset.','paid_requests_submitted':0}
if __name__=='__main__':print(json.dumps(inspect(),ensure_ascii=False,indent=2))
