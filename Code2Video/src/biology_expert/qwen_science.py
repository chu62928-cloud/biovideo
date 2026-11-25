"""V3-only structured science adapter; V2 legacy provider stays frozen."""
from pathlib import Path
import os,json,base64,hashlib
from openai import OpenAI
def request_qwen_science(prompt,video_path,image_path,log_id,profile,audit_dir):
 audit=Path(audit_dir);audit.mkdir(parents=True,exist_ok=True)
 video=Path(video_path);grid=Path(image_path)
 record={'model':os.environ['QWEN_MODEL'],'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'profile':profile,'retry_count':0}
 (audit/(log_id+'.request.json')).write_text(json.dumps(record,indent=2))
 content=[{'type':'text','text':prompt}]
 frames=profile.get('actual_frame_paths',[])
 if frames:
  for frame in frames:
   fp=Path(frame);content.append({'type':'text','text':'Actual decoded MP4 frame '+fp.name});content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(fp.read_bytes()).decode()}})
  record['decoded_frames']=[{'path':str(f),'sha256':hashlib.sha256(Path(f).read_bytes()).hexdigest()} for f in frames]
  (audit/(log_id+'.request.json')).write_text(json.dumps(record,indent=2))
 else:content.append({'type':'video_url','video_url':{'url':'data:video/mp4;base64,'+base64.b64encode(video.read_bytes()).decode()}})
 if profile.get('include_grid',True):content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(grid.read_bytes()).decode()}})
 client=OpenAI(api_key=os.environ['DASHSCOPE_API_KEY'],base_url=os.environ['QWEN_BASE_URL'],max_retries=0,timeout=180)
 response=client.chat.completions.create(model=os.environ['QWEN_MODEL'],messages=[{'role':'user','content':content}],max_completion_tokens=profile['max_completion_tokens'],response_format={'type':'json_object'},extra_body={'thinking_budget':profile['thinking_budget']})
 path=audit/(log_id+'.response.json');path.write_text(response.model_dump_json(indent=2));path.chmod(0o600)
 if response.choices[0].finish_reason!='stop':raise ValueError('Qwen incomplete output: '+str(response.choices[0].finish_reason))
 data=json.loads(response.choices[0].message.content)
 if not isinstance(data.get('science'),dict):raise ValueError('Missing structured science result')
 return response
