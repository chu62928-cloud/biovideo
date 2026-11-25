from pathlib import Path
import sys,json,os
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'reference_logs',{'deepseek':100,'qwen':10});model=json.loads((E/'inputs/mitosis/typed_result.json').read_text())['model'];old=json.loads((E/'references/review.json').read_text());write(E/'references/review_before_plan_repair.json',old)
prompt='Correct the current two-state plan. Return complete JSON {first_frame:[...],last_frame:[...]} same generic shape schema. Deterministic defects: fiber_left ends610 but yellow kinetochore center585 in first (310 vs285 last); right fiber begins670 but yellow center695 (970 vs995 last). Each fiber endpoint MUST end at pole-facing yellow dot center; do not continue through chromatid. Initial sisters currently completely separated by40px, NOT a joined pair. Make their central centromere necks meet at x640,y360, arms left/right remain distinguishable; outer kinetochore sites face corresponding poles, not center. Last preserve the same shapes translated left/right with obvious gap, same number and identities. No extra new scientific object and no labels. Black1280x720. Fix both actual coordinates and draw order. Return only plan under2500tokens.'

plan=parse_json(G.request('deepseek','scientific_state_reference_plan',prompt+json.dumps({'model':model,'prior_visual_issue':old,'current_plan':json.loads((E/'references/state_drawing_plan.json').read_text())})));write(E/'references/state_drawing_plan.json',plan)
for name,items in plan.items():
 if name not in ['first_frame','last_frame']:continue
 image=Image.new('RGB',(1280,720));d=ImageDraw.Draw(image)
 for obj in items:
  co=obj['coordinates'];color=obj['color'];width=int(obj.get('width',3))
  if obj['shape']=='line':d.line(co,fill=color,width=width)
  elif obj['shape']=='ellipse':d.ellipse(co,fill=color)
  elif obj['shape']=='polygon':d.polygon([tuple(x) for x in co],fill=color)
 image.save(E/'references'/(name+'.png'))
print('state plans drawn',flush=True)
