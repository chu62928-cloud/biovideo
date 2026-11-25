from pathlib import Path
import sys,json,os,hashlib
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
os.environ['QWEN_MODEL']='qwen3.8-27b'
g=ModelGateway(E/'logs',{'deepseek':1000000,'qwen':1000000},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096,'include_grid':False})
f=E/'candidates/mitosis';model=json.loads((f/'typed_result.json').read_text())['model'];ret=json.loads((f/'retrieval.json').read_text())
prompt='Recheck actual decoded video pixels. Prior review alleged crossfade/garbled letters at1.2,2.2,4.2s; independent exact frame extraction at1.2 shows crisp single labels, and renderer uses no crossfade. Treat prior alleged issue as unconfirmed; check actual attached frames/video, avoid temporal interpolation artifacts from video sampling. Independently review ONLY attached actual 8-second MP4, evidence and scientific model. No reference image attached. Return JSON {science:{decision:PASS|REVISE|NEEDS_HUMAN_REVIEW,issues:[]},visual:{decision:PASS|REVISE,issues:[]},scope_review:...,visible_evidence:[{time:...,observation:...}]}. Check actual visible chromosome alignment, continuous existing sister identities, separation to opposite poles, microtubule attachment to correct moving kinetochores, clear labels, frame containment and honest schematic limitations. One chromosome is deliberate scope. Do not demand molecular cleavage if explicitly excluded; do not approve from labels or generator assurances. Interpret scene as schematic not molecular structure. No audio requirement. Include timestamp evidence for failures. '+json.dumps({'model':model,'sources':[{'url':v['url'],'passages':v['passages'][15:33]} for v in ret['evidence']]})
out=parse_json(g.request('qwen','independent_actual_video_review',prompt,video=E/'sample_video.mp4'));out['video_sha256']=hashlib.sha256((E/'sample_video.mp4').read_bytes()).hexdigest();out['scene_sha256']=hashlib.sha256((E/'sample_scene.json').read_bytes()).hexdigest();write(f/('video_review_'+str(len(g.rows))+'.json'),out);print(json.dumps(out))
