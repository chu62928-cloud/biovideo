from pathlib import Path
import json,os,sys
E=Path(__file__).resolve().parent
sys.path.insert(0,str(E.parents[1]/'src'))
from biology_expert.product import critic,write,probe
from biology_expert.providers import ModelGateway
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1)
        os.environ[k]=v
os.environ['QWEN_MODEL']='qwen3.8-27b'
p=ModelGateway(E/'comparison_calls',{'deepseek':0,'qwen':2},qwen_profile={'include_grid':False,'max_completion_tokens':4200,'thinking_budget':1024})
old=E.parents[2].parent/'biovideo-v5/Code2Video/experiments/biovideo_v5'
for i,(name,request) in enumerate(json.loads((E/'protocol.json').read_text())['dev'],1):
    video=old/'comparison_videos'/f'T0{i}'/'video.mp4'
    try:
        review=critic(p,{'request':request,'duration':30,'audience':'grades 10-12','language':'en','backend':'manim'},video)
        write(E/'comparisons'/f'G0_{name}.json',{'review':review,'media':probe(video),'historical':True})
    except Exception as ex:
        write(E/'comparisons'/f'G0_{name}.json',{'error':str(ex)[:500]})
