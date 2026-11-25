from pathlib import Path
import sys,json,os
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'reference_logs',{'deepseek':100,'qwen':10});model=json.loads((E/'inputs/mitosis/typed_result.json').read_text())['model'];old=json.loads((E/'references/review.json').read_text());write(E/'references/review_cropped_no_labels.json',old)
prompt='Generate two reference state drawing plans from approved scientific model, fixing independent visual reviewer topology concerns. Return JSON {first_frame:[{id,shape:line|ellipse|polygon,coordinates:[x0,y0,x1,y1] for line/ellipse or [[x,y],...] polygon,color,width}],last_frame:[same]}. Canvas1280x720 black, no text. Model ONE pair with persistent IDs, poles and kinetochore attachments. Sisters should visually join initially at central centromere, two separate microtubules must visibly terminate at OUTWARD pole-facing yellow kinetochore sites on each chromatid, not through a chromatid. Last state same chromatid IDs apart toward respective poles. Explicitly distinct left and right fibers with no continuous line through central gap. Pink arm shapes with constriction; realistic molecular detail excluded. Keep scientific objects cardinality constant, no decorative scientific objects. Same IDs same colors. Draw order: plane/poles/fibers then chromatid polygons then yellow kinetochore disks. First aligned, last separated. No letters or teaching labels. Compact under2500tokens. '
plan=parse_json(G.request('deepseek','scientific_state_reference_plan',prompt+json.dumps({'model':model,'prior_visual_issue':old})));write(E/'references/state_drawing_plan.json',plan)
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
