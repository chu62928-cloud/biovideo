"""Optional official Wan3.0 comparison. No network activity unless ENABLE_WAN=1."""
from pathlib import Path
import json,os,urllib.request,urllib.parse,time

ROOT=Path('/autodl-tmp/code2biovideo').resolve()
E=ROOT/'Code2Video/experiments/biology_v2_section4'
for line in (ROOT/'.env').read_text().splitlines():
    if line and not line.startswith('#'):
        key,value=line.split('=',1);os.environ.setdefault(key,value)
workspace=os.getenv('WAN_WORKSPACE_ID','')
reference=os.getenv('WAN_REFERENCE_URL','')
enabled=os.getenv('ENABLE_WAN','0')=='1'
out=E/'comparisons/wan';out.mkdir(parents=True,exist_ok=True)
mechanism=json.loads((E/'specs/section4_mechanism.json').read_text())
prompt='A five-second schematic continuation of the SAME eukaryotic DNA replication fork from the reference image. No camera cuts and no text or labels. Preserve every existing molecule identity and strand polarity. Blue templates remain separate from new green DNA. Cyan DNA polymerase stays at a growing 3-prime end, adding individual nucleotides in 5-prime to 3-prime direction from an existing orange RNA primer. Show only the primed-extension event; do not compress all maturation steps into this clip. Scientific constraints: '+json.dumps(mechanism['constraints'],ensure_ascii=False)
payload={'model':'wan3.0-video','input':{'prompt':prompt,'media':[{'type':'first_frame','url':reference or None}]},'parameters':{'resolution':'720P','ratio':'adaptive','duration':5,'prompt_extend':False}}
endpoint=f'https://{workspace}.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis' if workspace else None
diagnostic={'enabled':enabled,'dry_run':not enabled,'model':'wan3.0-video','new_jobs':0,
    'official_documentation':'https://help.aliyun.com/zh/model-studio/wan3-video-generation-guide',
    'endpoint':endpoint,'payload':payload,'local_reference':str(E/'comparisons/A2_fork_reference.png'),
    'missing_configuration':[name for name,value in [('WAN_WORKSPACE_ID',workspace),('WAN_REFERENCE_URL',reference)] if not value],
    'media_note':'Upload the actual A2 fork reference to a public HTTPS URL using an authorized storage service. No guessed upload API or credential-derived workspace ID.'}
(out/'dry_run.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2))
if not enabled:
    print('DRY_RUN: no HTTP request, no upload, no video job or charges.');raise SystemExit(0)
assert not diagnostic['missing_configuration'],'Official workspace and HTTPS image URL required'
assert urllib.parse.urlparse(reference).scheme=='https','A public HTTPS reference URL is required'
assert (E/'comparisons/A2_fork_reference.png').exists(),'A2 did not produce a reference frame'
ledger=out/'submitted_job.json'
assert not ledger.exists(),'MAX_WAN_JOBS=1: a job attempt already exists; do not resubmit'
ledger.write_text(json.dumps({'state':'submitting','max_jobs':1,'submitted_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
headers={'Authorization':'Bearer '+os.environ['DASHSCOPE_API_KEY'],'Content-Type':'application/json','X-DashScope-Async':'enable'}
request=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers=headers,method='POST')
try:
    with urllib.request.urlopen(request,timeout=60) as response:result=json.load(response)
    ledger.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    task_id=result['output']['task_id']
    for _ in range(120):
        req=urllib.request.Request(f'https://{workspace}.cn-beijing.maas.aliyuncs.com/api/v1/tasks/{task_id}',headers={'Authorization':headers['Authorization']})
        with urllib.request.urlopen(req,timeout=30) as response:status=json.load(response)
        (out/'task_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
        state=status.get('output',{}).get('task_status')
        if state in ('SUCCEEDED','FAILED','CANCELED'):
            print('WAN_TASK',state,'Actual usage, if returned, is in task_status.json.');break
        time.sleep(5)
except Exception as exc:
    (out/'error.json').write_text(json.dumps({'error_type':type(exc).__name__,'http_status':getattr(exc,'code',None),'new_generation_requests':1},indent=2))
    raise
