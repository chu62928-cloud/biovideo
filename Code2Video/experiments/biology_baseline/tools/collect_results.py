from pathlib import Path
import subprocess,json,csv,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('/autodl-tmp/code2biovideo').resolve()
REPO=ROOT/'Code2Video';EXP=REPO/'experiments/biology_baseline'
FF=str(ROOT/'env/bin/ffmpeg');FP=str(ROOT/'env/bin/ffprobe')

def probe(p):
 return json.loads(subprocess.check_output([FP,'-v','error','-show_format','-show_streams','-of','json',str(p)],text=True))

results=[]
for p in sorted((EXP/'logs').glob('*/metrics.json')):
 cached=p.parent/'analysis.json'
 if cached.exists() and cached.stat().st_mtime>p.stat().st_mtime:
  results.append(json.loads(cached.read_text()));continue
 d=json.loads(p.read_text());label=d['label']
 audit=p.parent/'api';records=[json.loads(l) for l in (audit/'requests.jsonl').read_text().splitlines()] if (audit/'requests.jsonl').exists() else []
 d['usage']={k:sum(r.get('usage',{}).get(k,0) or 0 for r in records) for k in ['prompt_tokens','completion_tokens','total_tokens']}
 d['render_success_rate']=d.get('successful_sections',0)/d['sections'] if d.get('sections') else None
 events=[json.loads(q.read_text()) for q in Path(d['output_dir']).glob('render_logs/*.json')]
 renders=[e for e in events if e.get('cmd',[None])[0]=='manim']
 if renders:
  d['render_attempts']=len(renders)
  d['render_attempt_successes']=sum(e.get('returncode')==0 for e in renders)
  d['render_retries']=len(renders)-len(set(tuple(e['cmd']) for e in renders))
 d['stages']={}
 for r in records:
  stage=r.get('stage','unknown');d['stages'][stage]=d['stages'].get(stage,0)+1
 previews=[];offset=0;segments=[]
 for sid,path in sorted(d.get('section_videos',{}).items()):
  vp=Path(path);meta=probe(vp);duration=float(meta['format']['duration'])
  segments.append({'section':sid,'start_seconds':offset,'duration_seconds':duration,'path':str(vp)})
  for frac in [0.25,0.65,0.9]:
   t=duration*frac;frame=EXP/'previews'/label/(sid+f'_{int(frac*100)}.png');frame.parent.mkdir(exist_ok=True,parents=True)
   subprocess.run([FF,'-v','error','-y','-ss',str(t),'-i',str(vp),'-frames:v','1',str(frame)],check=True)
   previews.append((frame,f'{sid} | total {offset+t:.1f}s | local {t:.1f}s'))
  offset+=duration
 d['segments']=segments
 if d.get('video') and Path(d['video']).exists():
  vp=Path(d['video']);meta=probe(vp)
  (p.parent/'ffprobe.json').write_text(json.dumps(meta,indent=2))
  dec=subprocess.run([FF,'-v','error','-i',str(vp),'-f','null','-'],capture_output=True,text=True)
  (p.parent/'decode.log').write_text(dec.stderr)
  d['video_properties']={'duration_seconds':float(meta['format']['duration']),'streams':[{'type':s['codec_type'],'codec':s['codec_name'],'width':s.get('width'),'height':s.get('height'),'fps':s.get('r_frame_rate')} for s in meta['streams']],
    'decode_returncode':dec.returncode,'decode_errors':dec.stderr,'segment_duration_sum':offset,'bytes':vp.stat().st_size,'sha256':hashlib.sha256(vp.read_bytes()).hexdigest()}
  black=subprocess.run([FF,'-hide_banner','-i',str(vp),'-vf','blackdetect=d=0.5:pix_th=0.10:pic_th=0.98','-an','-f','null','-'],capture_output=True,text=True)
  lines=[l for l in black.stderr.splitlines() if 'black_start:' in l]
  (p.parent/'blackdetect.log').write_text('\n'.join(lines))
  d['video_properties']['black_intervals']=lines
 if previews:
  cols=3;w,h=480,296;rows=(len(previews)+cols-1)//cols
  sheet=Image.new('RGB',(w*cols,h*rows),'#202020');draw=ImageDraw.Draw(sheet)
  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
  for i,(frame,caption) in enumerate(previews):
   x=i%cols*w;y=i//cols*h
   sheet.paste(Image.open(frame).convert('RGB').resize((480,270)),(x,y))
   draw.text((x+8,y+275),caption,font=font,fill='white')
  sheet.save(EXP/'previews'/label/'contact_sheet.jpg',quality=92)
  d['preview']=str(EXP/'previews'/label/'contact_sheet.jpg')
 (p.parent/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
 results.append(d)
(EXP/'all_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
fields=['label','requested_model','status','sections','successful_sections','render_success_rate','api_attempts','api_retries','render_attempts','render_retries','prompt_tokens','completion_tokens','total_tokens','elapsed_seconds','video']
with (EXP/'metrics.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for d in results:
  row={k:d.get(k,'') for k in fields};row.update(d['usage']);writer.writerow(row)
with (EXP/'upstream.patch').open('w') as f:subprocess.run(['git','-C',str(REPO),'diff','--','src'],stdout=f,check=True)
assert not subprocess.check_output(['git','-C',str(REPO),'diff','--','prompts']).strip()
print(json.dumps([{k:d.get(k) for k in ['label','status','sections','successful_sections','usage','elapsed_seconds','video','video_properties']} for d in results],ensure_ascii=False,indent=2))
