from pathlib import Path
import ast,json,sys,subprocess,csv,hashlib,collections,time,shutil
from PIL import Image,ImageDraw,ImageFont

ROOT=Path('/autodl-tmp/code2biovideo').resolve();REPO=ROOT/'Code2Video';E=REPO/'experiments/biology_v2_section4'
sys.path.insert(0,str(REPO/'src'))
from biology_v2_pipeline import probe,sha
FF=str(ROOT/'env/bin/ffmpeg');FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
ledger=[json.loads(x) for x in (E/'logs/api_calls.jsonl').read_text().splitlines()]
labels=['A0_baseline','A1_mechanism','A2_mechanism_assets','A3_mechanism_assets_critic']
events=['event_1_fork','event_2_priming','event_3_extension','event_4_two_modes','event_5_maturation']
data=[];frame_paths={};failures=[]
for label in labels:
 g=E/'groups'/label
 state=json.loads((g/'status.json').read_text())
 prefix=label[:2]
 calls=[x for x in ledger if x['stage'].startswith(prefix)]
 transactions=[]
 for p in sorted(g.glob('*_transaction.json')):
  item=json.loads(p.read_text());transactions.append(item)
  if not item['committed']:failures.append({'group':label,'tag':item['tag'],'reason':item.get('error'),'log':str(p)})
 interrupted=[]
 for p in (g/'attempts').glob('*'):
  if not (p/'failure.json').exists() and not (p/'status.json').exists():
   interrupted.append(str(p))
   (p/'interruption_record.json').write_text(json.dumps({'committed':False,'reason':'Controller interruption during infrastructure diagnosis; no success assumed','new_code_video_pair_published':False},indent=2))
 meta=probe(g/'video.mp4');duration=float(meta['format']['duration'])
 decode=subprocess.run([FF,'-v','error','-i',str(g/'video.mp4'),'-f','null','-'],capture_output=True,text=True)
 (g/'decode.log').write_text(decode.stderr)
 row={'group':label,'experiment_success':state['success'],'valid_video':decode.returncode==0 and not decode.stderr.strip(),
      'new_render':label in ['A1_mechanism','A2_mechanism_assets'],'video':str(g/'video.mp4'),'code':str(g/'rendered_code.py'),
      'video_sha256':sha(g/'video.mp4'),'code_sha256':sha(g/'rendered_code.py'),'duration_seconds':duration,
      'resolution':str(meta['streams'][0]['width'])+'x'+str(meta['streams'][0]['height']),'fps':meta['streams'][0]['r_frame_rate'],
      'audio_present':any(x['codec_type']=='audio' for x in meta['streams']),
      'coder_calls':sum(x['provider']=='deepseek' for x in calls),'critic_calls':sum(x['provider']=='qwen' for x in calls),
      'known_prompt_tokens':sum((x.get('usage') or {}).get('prompt_tokens',0) or 0 for x in calls),
      'known_completion_tokens':sum((x.get('usage') or {}).get('completion_tokens',0) or 0 for x in calls),
      'unknown_usage_calls':sum('usage' not in x for x in calls),
      'transaction_attempts':len(transactions),'transaction_commits':sum(x['committed'] for x in transactions),
      'failed_candidates_or_rollbacks':sum(not x['committed'] for x in transactions),'interrupted_attempts':interrupted,
      'measured_active_seconds':round(sum(x.get('elapsed_seconds',0) for x in calls)+sum(x.get('elapsed_seconds',0) for x in transactions),3),
      'time_definition':'Sum of recorded API and transaction wall times; excludes human inspection/pauses; interrupted attempt time may be unavailable.',
      'human_animation_code_edits':False}
 if label=='A0_baseline':
  row['measured_active_seconds']=None
  row['note']='Exact frozen copy; no new API or render. Copy duration was not timed.'
 if label.startswith('A3'):
  row['note']='Critic API timeout; video is the explicitly allowed A2 initial copy, not a Critic-refined result.'
  row['critic_rounds']=json.loads((g/'critic_rounds.json').read_text())
 version=(g/'current').resolve() if (g/'current').exists() else None
 trace=json.loads((version/'geometry_trace.json').read_text()) if version and (version/'geometry_trace.json').exists() else None
 if trace:
  layout=json.loads((version/'layout_metrics.json').read_text())
  label_count=sum(x.get('role')=='label' for x in trace['object_metadata'].values())
  row['layout_metrics']={k:len(v) for k,v in layout.items() if isinstance(v,list)}
  row['registered_labels']=label_count
  row['label_detection_status']='uncertain: generated code did not register text labels' if label_count==0 else 'heuristic, inspect frames'
  visibility={}
  for name in [x['id'] for x in json.loads((E/'specs/section4_mechanism.json').read_text())['objects']]:
   samples=[fr['objects'][name] for fr in trace['frames'] if name in fr['objects']]
   visible=[x for x in samples if x['visible']]
   fractions=[]
   for x in visible:
    lo,hi=x['bbox'];area=max(hi[0]-lo[0],0)*max(hi[1]-lo[1],0)
    inside=max(min(hi[0],7.111)-max(lo[0],-7.111),0)*max(min(hi[1],4)-max(lo[1],-4),0)
    if area>0:fractions.append(min(inside/area,1))
   visibility[name]={'visible_samples':len(visible),'observed_samples':len(samples),'minimum_in_frame_bbox_fraction':min(fractions) if fractions else None}
  (g/'object_visibility.json').write_text(json.dumps(visibility,indent=2))
  nts=[]
  for name,info in trace['object_metadata'].items():
   if info.get('role')!='nucleotide':continue
   seen=[(fr['time'],fr['objects'][name]['center']) for fr in trace['frames'] if name in fr['objects'] and fr['objects'][name]['visible']]
   if seen:nts.append({'id':name,**info,'first_visible':seen[0][0],'last_visible':seen[-1][0],'final_x':seen[-1][1][0]})
  (g/'nucleotide_observations.json').write_text(json.dumps(nts,indent=2))
  row['mechanism_evidence']={'first_RNA':min((x['first_visible'] for x in nts if x.get('material')=='RNA'),default=None),
    'first_DNA':min((x['first_visible'] for x in nts if x.get('material')=='DNA'),default=None),
    'fill_nucleotides':[x for x in nts if 'fill' in x['id']],
    'actual_event_markers':trace['events']}
  starts={x['id']:x['time'] for x in trace['events']}
  times=[starts.get(event,0) for event in events]
  ends=times[1:]+[duration]
  sample_times=[(a+b)/2 for a,b in zip(times,ends)]
 else:sample_times=[1.7,6,14,23,31.5]
 frame_paths[label]=[]
 for i,t in enumerate(sample_times,1):
  p=E/'comparisons'/f'{label}_event_{i}.png'
  subprocess.run([FF,'-v','error','-y','-ss',str(t),'-i',str(g/'video.mp4'),'-frames:v','1',str(p)],check=True)
  frame_paths[label].append(p)
 row['comparison_frame_times']=dict(zip(events,sample_times))
 row['SVG_asset_types_in_code']=[]
 tree=ast.parse((g/'rendered_code.py').read_text())
 for n in ast.walk(tree):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['try_load','load_bio_asset'] and n.args and isinstance(n.args[0],ast.Constant):
   row['SVG_asset_types_in_code'].append(n.args[0].value)
 row['SVG_asset_types_in_code']=sorted(set(row['SVG_asset_types_in_code']))
 complete,successful,rollbacks=0,0,0
 details=[]
 for tx in transactions:
  loc=Path(tx['after']['version']) if tx['committed'] else g/'attempts'/tx['tag']
  if (loc/'stdout.log').exists():
   complete+=1
   vp=loc/'media/videos/rendered_code/480p15/Section4Scene.mp4'
   valid=False
   if vp.exists():
    cp=subprocess.run([FF,'-v','error','-i',str(vp),'-f','null','-'],capture_output=True,text=True)
    valid=cp.returncode==0 and not cp.stderr.strip()
   successful+=valid
   details.append({'tag':tx['tag'],'full_video_decodes':valid,'committed':tx['committed']})
  if not tx['committed'] and tx.get('before'):rollbacks+=1
 row.update(completed_full_render_attempts=complete,verified_full_render_outputs=successful,
            render_success_rate=successful/complete if complete else None,
            experiment_failed_update_rollbacks=rollbacks,render_attempt_details=details)
 data.append(row)
 (g/'final_group_summary.json').write_text(json.dumps(row,ensure_ascii=False,indent=2))
 if (g/'generation_summary.json').exists():
  old=g/'generation_summary_before_final_evaluation.json'
  if not old.exists():shutil.copy2(g/'generation_summary.json',old)

for i,event in enumerate(events):
 sheet=Image.new('RGB',(854*4,510),'#202020');draw=ImageDraw.Draw(sheet)
 for col,label in enumerate(labels):
  sheet.paste(Image.open(frame_paths[label][i]),(col*854,0))
  qualifier='A2 copy; Critic timeout' if label.startswith('A3') else label
  draw.text((col*854+8,484),f'{qualifier} | {data[col]["comparison_frame_times"][event]:.2f}s',font=FONT,fill='white')
 sheet.save(E/'comparisons'/f'{event}_comparison.jpg',quality=94)
overview=Image.new('RGB',(480*4,296*5),'#202020');draw=ImageDraw.Draw(overview)
for row,event in enumerate(events):
 for col,label in enumerate(labels):
  overview.paste(Image.open(frame_paths[label][row]).resize((480,270)),(col*480,row*296))
  draw.text((col*480+6,row*296+273),f'{label[:2]} | event {row+1}',font=FONT,fill='white')
overview.save(E/'comparisons/all_groups_by_event.jpg',quality=94)
# Actual fork-reference candidate; explicitly requires human review of its schematic topology.
shutil.copy2(frame_paths['A2_mechanism_assets'][2],E/'comparisons/A2_fork_reference.png')
(E/'comparisons/wan/reference_selection.json').write_text(json.dumps({'source_group':'A2','event':events[2],'time_seconds':data[2]['comparison_frame_times'][events[2]],'human_review_required':True,'reason':'Actual A2 frame, but simplified fork topology and direction need review before any Wan comparison'},indent=2))
counts={p:sum(x['provider']==p for x in ledger) for p in ['deepseek','qwen','wan']}
tokens={p:{k:(sum((x.get('usage') or {}).get(k,0) or 0 for x in ledger if x['provider']==p) if all('usage' in x for x in ledger if x['provider']==p) else None) for k in ['prompt_tokens','completion_tokens','total_tokens']} for p in ['deepseek','qwen']}
metrics={'groups':data,'api_calls':ledger,'call_counts':counts,'token_usage':tokens,'limits':{'MAX_DEEPSEEK_CALLS':8,'MAX_QWEN_CALLS':2,'MAX_WAN_JOBS':1,'ENABLE_WAN':0},'actual_bill':None,'code_fix_success_rate':{'A3':None,'reason':'No Critic response or repair candidate was produced'},'pipeline_tests':json.loads((E/'pipeline_tests.json').read_text()),'note':'A3 copied video is not counted as a successful Critic render. Heuristic measurements are not scientific proof.'}
(E/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
(E/'failure_reasons.json').write_text(json.dumps({'transaction_rejections':failures,'API_errors':[x for x in ledger if x['status']=='error'],'interrupted_controller_attempts':[p for x in data for p in x['interrupted_attempts']]},ensure_ascii=False,indent=2))
fields=['group','experiment_success','new_render','duration_seconds','resolution','fps','coder_calls','critic_calls','known_prompt_tokens','known_completion_tokens','unknown_usage_calls','transaction_attempts','transaction_commits','completed_full_render_attempts','verified_full_render_outputs','render_success_rate','failed_candidates_or_rollbacks','experiment_failed_update_rollbacks','measured_active_seconds','video_sha256','video']
with (E/'metrics.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(data)
print(json.dumps({'call_counts':counts,'token_usage':tokens,'groups':[{k:x.get(k) for k in ['group','experiment_success','new_render','duration_seconds','SVG_asset_types_in_code','registered_labels']} for x in data]},ensure_ascii=False,indent=2))
