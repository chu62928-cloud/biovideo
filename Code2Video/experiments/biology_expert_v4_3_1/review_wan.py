from pathlib import Path
import sys,json,os,hashlib
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
os.environ['QWEN_MODEL']='qwen3.8-27b'
g=ModelGateway(E/'wan_review_logs',{'deepseek':1000000,'qwen':1000000},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096,'include_grid':False})
f=E/'wan_review';f.mkdir(exist_ok=True);model=json.loads((E/'inputs/mitosis/typed_result.json').read_text())['model'];ret=json.loads((E/'inputs/mitosis/retrieval.json').read_text())
prompt='Independently review ONLY attached actual 5-second generative Wan MP4, evidence and scientific model. No reference image attached. Return JSON {science:{decision:PASS|REVISE|NEEDS_HUMAN_REVIEW,issues:[]},visual:{decision:PASS|REVISE,issues:[]},scope_review:...,visible_evidence:[{time:...,observation:...}]}. Check actual visible chromosome alignment, continuous existing sister identities, separation to opposite poles, microtubule attachment to correct moving kinetochores, no invented text, frame containment and honest schematic limitations. One chromosome is deliberate scope. Do not demand molecular cleavage if explicitly excluded; do not approve from labels or generator assurances. Interpret scene as schematic not molecular structure. No audio requirement. Labels intentionally absent. Evaluate object count/identity, continuous retained fibers, correct endpoints, direction, structural deformation and teaching clarity. This generative video has no scientific runtime trace: mark judgments Video Observed or VLM Inferred, never Runtime Verified. Do not approve merely because endpoints match. Include timestamp evidence for failures. '+json.dumps({'model':model,'sources':[{'url':v['url'],'passages':v['passages'][15:33]} for v in ret['evidence']]})
out=parse_json(g.request('qwen','independent_actual_video_review',prompt,video=E/'videos/wan.mp4'));out['video_sha256']=hashlib.sha256((E/'videos/wan.mp4').read_bytes()).hexdigest();out['scene_sha256']=hashlib.sha256((E/'references/state_drawing_plan.json').read_bytes()).hexdigest();write(f/('video_review_'+str(len(g.rows))+'.json'),out);print(json.dumps(out))
