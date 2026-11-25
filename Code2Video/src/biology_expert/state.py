"""Content-addressed artifacts and explicit scientific-gate dependencies."""
from pathlib import Path
import hashlib,json,time
GATES=['TOPIC_RESEARCH','KNOWLEDGE_GATE','SCRIPT_GATE','CAST_ASSET_GATE','STORYBOARD_GATE','CODE_GATE','RENDER','VIDEO_SCIENCE_GATE','VISUAL_CRITIC','FINAL_SCIENCE_GATE','APPROVED']
DEPENDENCIES={
 'TOPIC_RESEARCH':[], 'KNOWLEDGE_GATE':['TOPIC_RESEARCH'],
 'SCRIPT_GATE':['KNOWLEDGE_GATE'],'CAST_ASSET_GATE':['SCRIPT_GATE'],
 'STORYBOARD_GATE':['SCRIPT_GATE','CAST_ASSET_GATE'],'CODE_GATE':['STORYBOARD_GATE'],
 'RENDER':['CODE_GATE'],'VIDEO_SCIENCE_GATE':['RENDER','KNOWLEDGE_GATE'],
 'VISUAL_CRITIC':['VIDEO_SCIENCE_GATE'],'FINAL_SCIENCE_GATE':['VISUAL_CRITIC','VIDEO_SCIENCE_GATE'],
 'APPROVED':['FINAL_SCIENCE_GATE']}
STATUSES={'PENDING','RUNNING','PASSED','REVISION_REQUIRED','HUMAN_REVIEW_REQUIRED','FAILED'}
def digest(value):
 if isinstance(value,Path):data=value.read_bytes()
 else:data=json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()
 return hashlib.sha256(data).hexdigest()
def write(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
class WorkflowState:
 def __init__(self,root):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  self.path=self.root/'workflow.json'
  self.data=json.loads(self.path.read_text()) if self.path.exists() else {'artifacts':{},'gates':{g:{'status':'PENDING','input_hash':None} for g in GATES}}
  self.save()
 def log(self,event,**values):
  with (self.root/'events.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'event':event,**values},ensure_ascii=False,default=str)+'\n')
 def save(self):write(self.path,self.data)
 def register(self,name,content,owner_gate):
  value=digest(content);old=self.data['artifacts'].get(name)
  self.data['artifacts'][name]={'sha256':value,'owner':owner_gate}
  if not old or old['sha256']!=value:self.invalidate(owner_gate)
  self.log('artifact_registered',name=name,sha256=value,owner_gate=owner_gate);self.save()
  return value
 def invalidate(self,gate):
  queue=[gate];seen=set()
  while queue:
   cur=queue.pop()
   if cur in seen:continue
   seen.add(cur);self.data['gates'][cur]={'status':'PENDING','input_hash':None}
   queue.extend(g for g,deps in DEPENDENCIES.items() if cur in deps)
  self.log('invalidated',gates=sorted(seen));self.save()
 def input_hash(self,gate):
  relevant={k:v for k,v in self.data['artifacts'].items() if v['owner']==gate}
  deps={d:self.data['gates'][d] for d in DEPENDENCIES[gate]}
  return digest({'artifacts':relevant,'dependencies':deps})
 def transition(self,gate,status,review=None):
  if status not in STATUSES:raise ValueError('Unknown state')
  if status in {'RUNNING','PASSED'}:
   if any(self.data['gates'][d]['status']!='PASSED' for d in DEPENDENCIES[gate]):raise ValueError('Upstream science gate not passed')
  if status=='PASSED':
   if not review or review['decision']!='PASS':raise ValueError('Only a scientific PASS may pass a gate')
   if any(i['severity']=='blocker' for i in review.get('issues',[])):raise ValueError('Unresolved blocker')
  self.data['gates'][gate]={'status':status,'input_hash':self.input_hash(gate),'review_id':review.get('review_id') if review else None}
  self.log('gate_transition',gate=gate,status=status,review_id=review.get('review_id') if review else None);self.save()
 def cached(self,gate):
  row=self.data['gates'][gate]
  return row['status']=='PASSED' and row['input_hash']==self.input_hash(gate)
