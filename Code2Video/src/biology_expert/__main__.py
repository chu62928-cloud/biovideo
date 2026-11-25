"""Small executable interface; paid requests require explicit execution and share the persisted run budget."""
from pathlib import Path
import argparse,json,os
from .agent import BiologyExpertAgent
from .providers import ModelGateway
from .state import write
def main():
 parser=argparse.ArgumentParser(description='BiologyExpertAgent MVP: inspect, research, or scientifically review version-bound artifacts')
 parser.add_argument('action',choices=['tools','status','research','review'])
 parser.add_argument('--run-root',type=Path,default=Path(__file__).resolve().parents[2]/'experiments/biology_expert_v3')
 parser.add_argument('--topic')
 parser.add_argument('--stage',choices=['SCRIPT','CAST','ASSETS','STORYBOARD','ANIMATION_CODE','RENDERED_VIDEO'])
 parser.add_argument('--artifacts',type=Path)
 parser.add_argument('--knowledge-pack',type=Path)
 parser.add_argument('--execute',action='store_true',help='Permit real tools under the persisted 8/2 budget; default is inspection only')
 args=parser.parse_args()
 gateway=ModelGateway(args.run_root/'logs/models')
 agent=BiologyExpertAgent(args.run_root,gateway)
 if args.action=='tools':print(json.dumps({'tools':sorted(agent.registry.tools),'policy':'bounded reactive; whitelist, content hashes, source evidence, maximum two repairs'},indent=2));return
 if args.action=='status':print(json.dumps({'workflow':agent.state.data,'paid_requests_stopped':gateway.stopped,'model_counts':{p:sum(x['provider']==p for x in gateway.rows) for p in gateway.limits}},indent=2));return
 if not args.execute:
  print(json.dumps({'mode':'DRY_RUN','action':args.action,'paid_requests':0,'instruction':'Supply inputs and --execute only for an authorized run; existing budget is not reset.'}));return
 config=Path(__file__).resolve().parents[3]/'.env'
 if config.exists():
  for line in config.read_text().splitlines():
   if '=' in line and not line.startswith('#'):
    k,v=line.split('=',1);os.environ.setdefault(k,v.strip().strip('"').strip("'"))
 if args.action=='research':
  if not args.topic:parser.error('--topic required')
  out=agent.prepare_topic(args.topic)
 else:
  if not args.stage or not args.artifacts or not args.knowledge_pack:parser.error('review needs --stage, --artifacts and --knowledge-pack')
  out=agent.review(args.stage,json.loads(args.artifacts.read_text()),{'knowledge_pack':json.loads(args.knowledge_pack.read_text())})
 write(args.run_root/'cli_result.json',out);print(json.dumps({'result':str(args.run_root/'cli_result.json')},ensure_ascii=False))
if __name__=='__main__':main()
