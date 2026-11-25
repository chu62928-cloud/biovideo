from pathlib import Path
import sys,json,os
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
os.environ['QWEN_MODEL']='qwen3.8-27b'
G=ModelGateway(E/'reference_logs',{'deepseek':100,'qwen':10},qwen_profile={'include_grid':False,'actual_frame_paths':[str(E/'references/first_frame.png'),str(E/'references/last_frame.png')],'max_completion_tokens':10000,'thinking_budget':4096})
model=json.loads((E/'inputs/mitosis/typed_result.json').read_text())['model']
prompt='Independently review these TWO actual first/last state reference images for a generative educational animation. Image1 must depict ONE duplicated chromosome aligned at equator with two persistent sister chromatids and correct bipolar microtubule-kinetochore attachment. Image2 must depict same two sisters separated to opposite poles, each retaining correct attachment, no copies. Scientific scope is schematic one chromosome, no molecular cohesin cleavage depicted. Are the pixels adequate as scientifically consistent endpoints? Return JSON {science:{decision:PASS|REVISE|NEEDS_HUMAN_REVIEW,issues:[]},visual:{decision:PASS|REVISE,issues:[]},observations:[],limitations:[]}. No labels required; teaching labels added after generation. Do not approve from model metadata alone. '+json.dumps(model)
out=parse_json(G.request('qwen','independent_reference_state_review',prompt,video=Path('/autodl-tmp/code2biovideo/biovideo-v4.3/Code2Video/experiments/biology_expert_v4_3/sample_video.mp4')));write(E/'references/review.json',out);print(json.dumps(out),flush=True)
