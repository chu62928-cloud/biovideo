from pathlib import Path
import os,json,sys,subprocess
E=Path(__file__).resolve().parent;R=E.parents[1]
sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write
from video_generation.providers import Wan3Provider,SeedanceProvider
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1);os.environ[k]=v
os.environ.update(DEEPSEEK_THINKING='disabled',QWEN_MODEL='qwen3.8-27b')
g=ModelGateway(E/'audit_calls',{'deepseek':3,'qwen':3},qwen_profile={'include_grid':False,'max_completion_tokens':4200,'thinking_budget':1024})
task=json.loads((E/'tasks/T02/task.json').read_text())
from biology_expert.video_controller import TOOLS
cases=[('Evidence chapter retrieved','HTTP 404, no evidence'),('Scene rendered cleanly','Render failed: geometry invalid in scene 2'),('Actual video and all claims reviewed PASS','Video review REVISE: misleading label in scene 2'),('Model schema and scientific verification complete','Optional typed model failed; verified facts and storyboard available')]
# Same goal and tools, change only observations. Evaluate proposed choices with deterministic mock tool dispatch.
for i in range(3):
    pair=cases[i:i+1]+(cases[3:] if i==2 else [])
    data=parse_json(g.request('deepseek','harness_behavior_probe','Controlled simulation. Select next registered action for each observation independently for same goal. Return JSON {cases:[{normal_tool,changed_tool,reason}]} in order. '+json.dumps(dict(task=task,tools=TOOLS,cases=pair))))
    write(E/('behavior_'+str(i)+'.json'),dict(inputs=pair,model=data,mock_dispatch=[{'normal':[x['normal_tool']] if x['normal_tool'] in TOOLS else [],'changed':[x['changed_tool']] if x['changed_tool'] in TOOLS else []} for x in data['cases']],fixed_workflow='next scheduled action independent of observation'))
for i in (1,2):
    folder=E/'comparison_videos'/('T%02d'%i);video=folder/'video.mp4'
    if video.exists():
        question=json.loads((E/'assignments.json').read_text())[i-1]
        prompt='Check actual educational video against goal. Return JSON {science:{decision:PASS|REVISE},visual:{decision:PASS|REVISE},coverage,issues:[{seconds,description}]}. '+question
        write(folder/'review.json',parse_json(g.request('qwen','blind_video_audit',prompt,video=video)))
p=E/'tasks/T02';spec={k:json.loads((p/(k+'.json')).read_text()) for k in ['task','fact_sheet','visual_design']}
req=dict(input_mode='text_to_video',prompt=json.dumps(spec)[:3000],duration=5,resolution='480P')
write(E/'providers.json',{k:v.submit(req,dry_run=True) for k,v in [('wan',Wan3Provider(E/'dryrun/wan',{'model_id':'wan3.0-video','base_url':'https://ws-t97wmnhtb5p967oq.cn-beijing.maas.aliyuncs.com'})),('seedance',SeedanceProvider(E/'dryrun/seedance',{}))]})
