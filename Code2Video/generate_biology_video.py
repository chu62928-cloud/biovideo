import argparse,fcntl,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway
from biology_expert.state import write

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--request','--topic',dest='request',required=True)
    p.add_argument('--duration',type=int,default=30)
    p.add_argument('--audience',default='grades 10-12')
    p.add_argument('--language',default='en')
    p.add_argument('--backend',choices=['auto','manim'],default='auto')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--budget',type=int,default=10)
    p.add_argument('--workflow',choices=['agent','fixed'],default='agent')
    p.add_argument('--evidence-cache',type=Path)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    if not 6<=args.duration<=120 or not 1<=args.budget<=10:p.error('duration 6–120, text requests 1–10')
    root=args.output.resolve()
    task={k:v for k,v in vars(args).items() if k not in ('output','resume','dry_run','evidence_cache')}
    if args.dry_run:print(json.dumps(task|{'external_video_submission':False}));return
    root.mkdir(exist_ok=True,parents=True)
    with (root/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (root/'task.json').exists():
            if not args.resume or task!=json.loads((root/'task.json').read_text()):raise ValueError('Existing task: resume with identical configuration')
        write(root/'task.json',task)
        if args.evidence_cache and not (root/'evidence.json').exists():
            write(root/'evidence.json',json.loads(args.evidence_cache.read_text()))
        g=ModelGateway(root/'calls',{'deepseek':args.budget,'qwen':2},qwen_profile={'include_grid':False,'max_completion_tokens':4200,'thinking_budget':1024})
        result=BiologyExpertAgent(root,g).generate_video(task)
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
