from pathlib import Path
import json,subprocess,hashlib,csv
from PIL import Image,ImageDraw,ImageFont
R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video';E=REPO/'experiments/qwen4_critic'
FF=str(R/'env/bin/ffmpeg');FP=str(R/'env/bin/ffprobe')
def probe(p):return json.loads(subprocess.check_output([FP,'-v','error','-show_format','-show_streams','-of','json',str(p)],text=True))
m=json.loads((E/'metrics.json').read_text());events=m['events']
runlog=(E/'logs/run.log').read_text()
stop_lines=[line for line in runlog.splitlines() if 'EXPERIMENT_ERROR' in line]
if stop_lines:m['stop_reason']=stop_lines[-1]
for rn in [1,2]:
 feedback_dir=E/f'round_{rn}'/'feedback'
 for f in feedback_dir.glob('*.json'):
  if not any(x['section']==f.stem and x['round']==rn for x in events):
   candidate=Path(m['output_dir'])/(f.stem+'.py')
   if candidate.exists():
    dest=E/f'round_{rn}'/'interrupted_code';dest.mkdir(exist_ok=True)
    (dest/candidate.name).write_bytes(candidate.read_bytes())

tables=[]
for rn,info in m['rounds'].items():
 p=Path(info['video']);meta=probe(p);dur=float(meta['format']['duration'])
 decode=subprocess.run([FF,'-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
 (E/f'round_{rn}'/'decode.log').write_text(decode.stderr)
 round_events=[e for e in events if e['round']==int(rn)]
 info.update(duration_seconds=dur,width=meta['streams'][0].get('width'),height=meta['streams'][0].get('height'),fps=meta['streams'][0].get('r_frame_rate'),streams=[s['codec_type'] for s in meta['streams']],decode_returncode=decode.returncode,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
  issues_before_optimization=sum(e['has_issues'] for e in round_events),
  reported_improvements=sum(e['improvements'] for e in round_events),
  successful_optimizations=sum(e['native_optimize_success'] and e['has_issues'] for e in round_events),
  failed_optimizations=sum(not e['native_optimize_success'] for e in round_events),
  changed_code_sections=sum(e['code_changed'] for e in round_events))
 tables.append({'round':rn,**{k:v for k,v in info.items() if k not in ['note']}})
 (E/f'round_{rn}'/'ffprobe.json').write_text(json.dumps(meta,indent=2))
(E/'metrics_analyzed.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
base=REPO/'src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells'
preview=E/'previews';preview.mkdir(exist_ok=True)
for i in range(1,7):
 sheet=Image.new('RGB',(854*3,506*3),'#202020');draw=ImageDraw.Draw(sheet)
 variants=[('baseline',base/f'media/videos/section_{i}/480p15/Section{i}Scene.mp4'),('round_1',E/f'round_1/scenes/section_{i}.mp4'),('round_2',E/f'round_2/scenes/section_{i}.mp4')]
 for row,(label,p) in enumerate(variants):
  if not p.exists():continue
  dur=float(probe(p)['format']['duration'])
  for col,frac in enumerate([.25,.65,.9]):
   t=dur*frac;frame=preview/f'{label}_section_{i}_{int(frac*100)}.png'
   subprocess.run([FF,'-v','error','-y','-ss',str(t),'-i',str(p),'-frames:v','1',str(frame)],check=True)
   x=854*col;y=506*row
   sheet.paste(Image.open(frame),(x,y));draw.text((x+8,y+483),f'{label} | section {i} | {t:.2f}s',font=font,fill='white')
 sheet.save(preview/f'section_{i}_comparison.jpg',quality=92)
# Keep the code that actually produced a retained video separate from failed candidates.
for i in range(1,7):
 sid=f'section_{i}';last_good=(base/(sid+'.py')).read_text()
 for rn in [1,2]:
  event=next((x for x in events if x['round']==rn and x['section']==sid),None)
  if not event:continue
  if event['video_is_new_optimized_result']:
   last_good=(E/f'round_{rn}/code'/(sid+'.py')).read_text()
  dest=E/f'round_{rn}/rendered_code';dest.mkdir(exist_ok=True,parents=True)
  (dest/(sid+'.py')).write_text(last_good)
with (E/'metrics.csv').open('w',newline='') as f:
 fields=['round','scenes','all_scenes','duration_seconds','width','height','fps','issues_before_optimization','reported_improvements','successful_optimizations','failed_optimizations','changed_code_sections','decode_returncode','video']
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(tables)
print(json.dumps(m,ensure_ascii=False,indent=2))
