from pathlib import Path
import sys,os,json,time,subprocess
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from video_generation.providers import Wan3Provider,SeedanceProvider,write,sha
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
review=json.loads((E/'references/review.json').read_text());assert review['science']['decision']=='PASS' and review['visual']['decision']=='PASS'
auth=json.loads((E/'authorization.json').read_text());assert auth['wan_real_tasks']==1;os.environ['ENABLE_WAN']='1'
config={'model_id':'wan3.0-video','region':'cn-beijing','base_url':'https://ws-t97wmnhtb5p967oq.cn-beijing.maas.aliyuncs.com','documentation':'https://help.aliyun.com/zh/model-studio/wan3-video-generation-api-reference','endpoint_note':'User supplied exact business workspace Beijing endpoint; corrected from legacy generic endpoint.','price_cny_per_second':.3}
prompt='固定镜头、黑色背景的高中生物教学示意动画。严格保持首尾图中的同一对粉色姐妹染色单体、两个黄色动粒、左右蓝色纺锤极和各自连接的灰色微管。起初姐妹染色单体排列在中央赤道位置，然后同一对姐妹连续分离并向左右相反的纺锤极移动，左右身份保持不变。微管一端固定在相应纺锤极，另一端持续接触其对应动粒，随运动缩短。只表示一条复制染色体的示意分离，不表现分子切割机制。不得复制、增加、消除科学对象，不得交换连接，不得让两条染色单体融合或无依据变形。保持平面示意风格、清晰边界和连续运动；无文字、无字幕、无声音，不改变视角。'
request={'prompt':prompt,'first_frame':str(E/'references/first_frame.png'),'last_frame':str(E/'references/last_frame.png'),'duration':5,'resolution':'480P','seed':431};write(E/'wan_workspace_config.json',config);write(E/'wan_workspace_input.json',request)
p=Wan3Provider(E/'providers/wan_workspace',config);write(E/'wan_workspace_dry_run.json',p.submit(request));write(E/'seedance_dry_run.json',SeedanceProvider(E/'providers/seedance',{}).submit({},dry_run=True))
state=p.submit(request,dry_run=False,authorized=True);print(json.dumps(state),flush=True)
if state.get('task_id'):
 for i in range(80):
  state=p.get_status();print('POLL',state['generation_status'],flush=True)
  if state['generation_status'] in ['SUCCEEDED','FAILED','CANCELED','UNKNOWN']:break
  time.sleep(15)
 if state['generation_status']=='SUCCEEDED':
  source=E/'providers/wan_workspace/video.mp4';(E/'videos').mkdir(exist_ok=True);import shutil;shutil.copy2(source,E/'videos/wan.mp4')
  result=subprocess.run(['/autodl-tmp/code2biovideo/env/bin/ffmpeg','-v','error','-i',str(source),'-f','null','-'],capture_output=True,text=True);write(E/'wan_decode.json',{'success':result.returncode==0,'stderr':result.stderr,'video_sha256':sha(source)})
previous=json.loads((E/'provider_runs.json').read_text());previous['runs']=[x for x in previous['runs'] if x.get('run_id')!='wan_workspace'];state['run_id']='wan_workspace';previous['runs'].append(state);write(E/'provider_runs.json',previous)
