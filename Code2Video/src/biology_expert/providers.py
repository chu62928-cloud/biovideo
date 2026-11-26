"""Reuse existing providers; persist budget before each actual request."""
from pathlib import Path
import json,os,time
from .state import write
class ModelGateway:
 def __init__(self,root,limits=None,qwen_profile=None):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  self.path=self.root/'model_calls.json'
  self.limits=limits or {'deepseek':8,'qwen':2}
  self.rows=json.loads(self.path.read_text()) if self.path.exists() else []
  self.qwen_profile=qwen_profile
  authpath=self.root/'budget_authorizations.json'
  auths=json.loads(authpath.read_text()) if authpath.exists() else []
  acknowledged=set()
  for auth in auths:
   self.limits[auth['provider']]+=auth['additional_requests']
   acknowledged.update(auth['acknowledged_failed_calls'])
  self.stopped=any(r['status'] in {'error','pending'} and r.get('call_id') not in acknowledged for r in self.rows)
 def resume_authorized(self,authorization):
  if authorization.get('source')!='explicit_user_message':raise ValueError('Explicit user authorization required')
  path=self.root/'budget_authorizations.json';rows=json.loads(path.read_text()) if path.exists() else []
  if any(a['authorization_id']==authorization['authorization_id'] for a in rows):raise ValueError('Authorization already applied')
  rows.append(authorization);write(path,rows)
  self.limits[authorization['provider']]+=authorization['additional_requests']
  acknowledged={cid for a in rows for cid in a['acknowledged_failed_calls']}
  self.stopped=any(r['status'] in {'error','pending'} and r.get('call_id') not in acknowledged for r in self.rows)
 def request(self,provider,purpose,prompt,video=None):
  import fcntl
  lock=self.root/'request.lock'
  with lock.open('a') as handle:
   fcntl.flock(handle,fcntl.LOCK_EX)
   try:return self._request_locked(provider,purpose,prompt,video)
   finally:fcntl.flock(handle,fcntl.LOCK_UN)
 def _request_locked(self,provider,purpose,prompt,video=None):
  self.rows=json.loads(self.path.read_text()) if self.path.exists() else []
  authpath=self.root/'budget_authorizations.json'
  auths=json.loads(authpath.read_text()) if authpath.exists() else []
  acknowledged={cid for a in auths for cid in a.get('acknowledged_failed_calls',[])}
  blocking=[r for r in self.rows if r['status'] in {'error','pending'} and r.get('call_id') not in acknowledged]
  if blocking:
   # A confirmed provider-specific 403 does not make other providers' state uncertain.
   if any((r['provider']==provider and r.get('requested_model')==os.environ.get('QWEN_MODEL' if provider=='qwen' else 'DEEPSEEK_MODEL')) or r.get('http_status')!=403 for r in blocking):raise RuntimeError('Prior uncertain/failed API state for this provider; paid requests stopped')
  if provider not in self.limits:raise ValueError('Unknown provider')
  if sum(r['provider']==provider for r in self.rows)>=self.limits[provider]:raise RuntimeError('Persisted model budget exhausted')
  prompts=Path(__file__).parent/'prompts'
  extra='knowledge_review.md' if 'knowledge' in purpose or 'fact_verification' in purpose else ('video_review.md' if provider=='qwen' else ('repair_planning.md' if 'repair' in purpose else 'artifact_review.md'))
  prompt=(prompts/'system.md').read_text()+'\n'+(prompts/extra).read_text()+'\n'+prompt
  from gpt_request import request_deepseek_token,request_qwen_video_img
  os.environ['CODE2VIDEO_AUDIT_DIR']=str(self.root/'deepseek_raw')
  os.environ['QWEN_CRITIC_AUDIT_DIR']=str(self.root/'qwen_raw')
  os.environ['CODE2VIDEO_STAGE']=purpose
  import uuid
  n=len(self.rows)+1;call_id=f'v42_{n:02d}_'+uuid.uuid4().hex[:8]
  rec={'call_id':call_id,'provider':provider,'purpose':purpose,'status':'pending','started':time.time(),'retries':0,'requested_model':os.environ['DEEPSEEK_MODEL' if provider=='deepseek' else 'QWEN_MODEL']}
  self.rows.append(rec);write(self.path,self.rows);start=time.monotonic()
  (self.root/(call_id+'_prompt.txt')).write_text(prompt)
  try:
   if provider=='deepseek':response,usage=request_deepseek_token(prompt,log_id=call_id,max_tokens=9000,max_retries=1,json_mode=purpose.startswith(('staged_model_', 'harness_')))
   else:
    grid=Path(__file__).resolve().parents[2]/'experiments/gemini3_critic_probe/GRID_upstream.png'
    if self.qwen_profile:
     from .qwen_science import request_qwen_science
     response=request_qwen_science(prompt,str(video),str(grid),call_id,self.qwen_profile,self.root/'qwen_raw')
     rec['request_profile']=self.qwen_profile
    else:response=request_qwen_video_img(prompt,str(video),str(grid),log_id=call_id,max_tokens=9000,max_retries=1)
    usage=response.usage.model_dump() if response.usage else None
   rec.update(status='ok',usage=usage,response_model=response.model)
   (self.root/(call_id+'_response.json')).write_text(response.model_dump_json(indent=2))
   print('MODEL_OK',call_id,purpose,flush=True)
   return response.choices[0].message.content
  except Exception as exc:
   self.stopped=True;rec.update(status='error',error_type=type(exc).__name__,http_status=getattr(exc,'status_code',None))
   raw_path=self.root/(provider+'_raw')/(call_id+'.response.json')
   if raw_path.exists():
    raw=json.loads(raw_path.read_text())
    rec.update(usage=raw.get('usage'),response_model=raw.get('model'),finish_reason=raw.get('choices',[{}])[0].get('finish_reason'))
    if rec.get('finish_reason')=='length':rec['root_cause']='MODEL_OUTPUT_TRUNCATED'

   raise
  finally:
   rec['elapsed_seconds']=round(time.monotonic()-start,3);write(self.path,self.rows)
def parse_json(text):
 import re
 m=re.search(r'\x60\x60\x60(?:json)?\s*([\s\S]*?)\x60\x60\x60',text)
 return json.loads(m.group(1) if m else text)
