from pathlib import Path
import json,sys,os,hashlib
E=Path(__file__).resolve().parent
R=E.parents[1]
U=R/'experiments/science_unseen_mechanism'
sys.path.insert(0,str(R/'src'))
from biology_expert.contracts import write,digest
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.repair_harness import compile_task,preflight
def read(path):return json.loads(Path(path).read_text())
def gateway():
    for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k,v=line.split('=',1)
            os.environ[k]=v
    os.environ['DEEPSEEK_THINKING']='disabled'
    return ModelGateway(E/'logs',{'deepseek':22,'qwen':3})
def material():
    return read(U/'recovered_candidate.json'),read(U/'retrieval.json')['evidence']
