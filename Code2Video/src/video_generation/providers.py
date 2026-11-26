"""Provider-neutral asynchronous video task persistence; no scientific topic logic."""
from pathlib import Path
import os,json,hashlib,base64,time,fcntl
import requests

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2));tmp.replace(p)
def sanitized(data):
 if isinstance(data,dict):return {k:('[REDACTED_URL]' if k.endswith('_url') else sanitized(v)) for k,v in data.items() if k.lower() not in ['authorization','api_key']}
 if isinstance(data,list):return [sanitized(x) for x in data]
 return data

class VideoGenerationProvider:
 def __init__(self,root,config,session=None):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.config=config;self.http=session or requests.Session()
 def validate_capabilities(self,request):raise NotImplementedError
 def estimate_cost_if_available(self,request):return None
 def record_usage(self,data):write(self.root/'usage.json',sanitized(data))

class Wan3Provider(VideoGenerationProvider):
 def validate_capabilities(self,request):
  from PIL import Image
  errors=[]
  if self.config.get('model_id') not in ['wan3.0-video','wan3.0-video-prime']:errors.append('UNSUPPORTED_MODEL')
  if not self.config.get('base_url','').startswith('https://'):errors.append('INVALID_BASE_URL')
  if not os.environ.get('DASHSCOPE_API_KEY'):errors.append('API_KEY_MISSING')
  if not 2<=request['duration']<=30:errors.append('UNSUPPORTED_DURATION')
  mode=request.get('input_mode','first_last_frame')
  if mode not in ['first_last_frame','text_to_video']:errors.append('UNSUPPORTED_INPUT_MODE')
  if mode=='text_to_video' and (request.get('first_frame') or request.get('last_frame')):errors.append('TEXT_MODE_MUST_NOT_INCLUDE_FRAMES')
  for f in ([request['first_frame'],request['last_frame']] if mode=='first_last_frame' else []):
   im=Image.open(f)
   if im.mode not in ['RGB','L'] or min(im.size)<240 or max(im.size)>8000 or max(im.size)/min(im.size)>8 or Path(f).stat().st_size>20*1024*1024:errors.append('INVALID_IMAGE')
  return {'valid':not errors,'errors':errors,'entitlement':'REAL_SUBMISSION_REQUIRED','docs':self.config.get('documentation')}
 def prepare_request(self,request):
  check=self.validate_capabilities(request)
  if not check['valid']:raise ValueError(check['errors'])
  inputs={'prompt':request['prompt']}
  if request.get('input_mode','first_last_frame')=='first_last_frame':inputs['media']=[{'type':k,'url':'data:image/png;base64,'+base64.b64encode(Path(request[k]).read_bytes()).decode()} for k in ['first_frame','last_frame']]
  return {'model':self.config['model_id'],'input':inputs,'parameters':{'duration':request['duration'],'resolution':request.get('resolution','480P'),'ratio':'16:9','audio':False,'prompt_extend':False,'watermark':False,'seed':request.get('seed',431)}}
 def estimate_cost_if_available(self,request):return {'estimated_cny':request['duration']*self.config.get('price_cny_per_second',.3),'basis':'Official Beijing output seconds list price; actual billed cost may differ','actual_cost':None}
 def submit(self,request,dry_run=True,authorized=False):
  payload=self.prepare_request(request);signature=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest();statepath=self.root/'task.json'
  if dry_run:return {'submission_status':'DRY_RUN','submitted':False,'request_sha256':signature,'capabilities':self.validate_capabilities(request),'estimate':self.estimate_cost_if_available(request)}
  if not authorized or os.environ.get('ENABLE_WAN')!='1':raise PermissionError('PAID_EXECUTION_NOT_AUTHORIZED')
  with (self.root/'submit.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   if statepath.exists():
    state=json.loads(statepath.read_text())
    if state['request_sha256']!=signature:raise ValueError('Existing run request differs; use a new authorized run directory')
    return state # pending, uncertain, failed: never automatically resubmit
   state={'provider':'wan','model_id':self.config['model_id'],'request_sha256':signature,'first_frame_sha256':sha(request['first_frame']) if request.get('first_frame') else None,'last_frame_sha256':sha(request['last_frame']) if request.get('last_frame') else None,'input_mode':request.get('input_mode','first_last_frame'),'prompt_sha256':hashlib.sha256(request['prompt'].encode()).hexdigest(),'submission_status':'SUBMITTING','generation_status':'UNKNOWN','task_id':None,'submitted_at':time.time(),'estimate':self.estimate_cost_if_available(request)};write(statepath,state)
   headers={'Authorization':'Bearer '+os.environ['DASHSCOPE_API_KEY'],'X-DashScope-Async':'enable','Content-Type':'application/json'}
   try:
    response=self.http.post(self.config['base_url'].rstrip('/')+'/api/v1/services/aigc/video-generation/video-synthesis',json=payload,headers=headers,timeout=90);data=response.json();state.update(http_status=response.status_code,response=sanitized(data),task_id=data.get('output',{}).get('task_id'),submission_status='ACCEPTED' if data.get('output',{}).get('task_id') else 'REJECTED',generation_status=data.get('output',{}).get('task_status','NOT_STARTED'))
   except Exception as ex:state.update(submission_status='UNCERTAIN_DO_NOT_RESUBMIT',error_type=type(ex).__name__)
   write(statepath,state);return state
 def get_status(self):
  path=self.root/'task.json';state=json.loads(path.read_text())
  if not state.get('task_id'):return state
  response=self.http.get(self.config['base_url'].rstrip('/')+'/api/v1/tasks/'+state['task_id'],headers={'Authorization':'Bearer '+os.environ['DASHSCOPE_API_KEY']},timeout=30);data=response.json();state['generation_status']=data.get('output',{}).get('task_status','UNKNOWN');state['last_query']=time.time();state['query_http_status']=response.status_code;state['query_response']=sanitized(data)
  if data.get('usage'):state['usage']=data['usage'];self.record_usage(data['usage'])
  # Download signed result URL immediately; never persist credential-bearing URL.
  url=data.get('output',{}).get('video_url')
  if state['generation_status']=='SUCCEEDED' and url and not (self.root/'video.mp4').exists():self.download_result(url)
  if (self.root/'video.mp4').exists():state['video_sha256']=sha(self.root/'video.mp4')
  write(path,state);return state
 def download_result(self,url):
  with self.http.get(url,stream=True,timeout=90) as res:
   res.raise_for_status();tmp=self.root/'video.download'
   with tmp.open('wb') as f:
    for chunk in res.iter_content(1024*1024):f.write(chunk)
   tmp.replace(self.root/'video.mp4')

class SeedanceProvider(VideoGenerationProvider):
 def validate_capabilities(self,request):return {'valid':False,'status':'NOT_SELECTED','reason':'Current user selected Wan only; exact model/endpoint and key not configured.'}
 def prepare_request(self,request):return {'provider':'seedance','status':'API_ACCESS_NOT_READY','request':{k:v for k,v in request.items() if 'key' not in k.lower()}}
 def submit(self,request,dry_run=True,authorized=False):
  if dry_run:return {'submission_status':'DRY_RUN','submitted':False,'capabilities':self.validate_capabilities(request)}
  raise PermissionError('Seedance not selected or authorized')
 def get_status(self):return {'status':'NOT_SUBMITTED'}
 def download_result(self,url):raise RuntimeError('No selected Seedance task')
