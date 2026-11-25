from pathlib import Path
import sys,json,csv,hashlib,subprocess,shutil,zipfile,time
R=Path('/autodl-tmp/code2biovideo/Code2Video').resolve();E=R/'experiments/scientific_scene_v4';sys.path.insert(0,str(R/'src'))
from scientific_scene.models import write
from scientific_scene.validation import validate_runtime
from biology_v2_pipeline import sha,trace_metrics
from PIL import Image,ImageDraw
load=lambda p:json.loads(Path(p).read_text())
calls=load(E/'logs/model_calls.json');rows=[]
for folder in sorted((E/'groups').iterdir()):
 if not (folder/'status.json').exists():continue
 st=load(folder/'status.json');label=folder.name;checks=[];layout={}
 if (folder/'geometry_trace.json').exists():
  checks=validate_runtime(load(folder/'scene_graph.json'),load(folder/'geometry_trace.json'));write(folder/'validation_report.json',checks)
  layout=trace_metrics(load(folder/'geometry_trace.json'));write(folder/'layout_metrics.json',layout)
  st['video_science_gate']=load(folder/'scientific_video_review.json')['decision'] if (folder/'scientific_video_review.json').exists() else 'NOT_MEASURED'
  if st.get('ir_science_gate')!='PASS' or any(c['status']=='FAIL' for c in checks):st['science_gate']='REVISE'
  elif st['video_science_gate']!='PASS':st['science_gate']='NEEDS_HUMAN_REVIEW'
  st['scientifically_approved']=st['science_gate']=='PASS' and st.get('scientifically_committed',True)
  if label=='A3_expert_repair':st['unresolved_blockers']=[x['issue_id'] for x in load(E/'validation/dna_repaired_ir_review.json')['issues']]
  write(folder/'status.json',st)
 assigned=[c for c in calls if (label in c['purpose']) or (label=='A3_expert_repair' and ('A3' in c['purpose']))]
 if label=='A0_v3_baseline':assigned=[]
 def tok(k):return sum((c.get('usage') or {}).get(k,0) for c in assigned)
 count=lambda status:sum(c['status']==status for c in checks)
 row={'group':label,'model':st.get('model',load(folder/'config.json').get('model')),'generation_success':st.get('generation_attempted',False) and bool(st.get('code_sha256')),'render_success':st.get('render_success'),'science_gate':st.get('science_gate'),'constraints_checked':count('PASS')+count('FAIL'),'constraints_passed':count('PASS'),'constraints_failed':count('FAIL'),'identity_violations':sum(c['status']=='FAIL' and c['category']=='identity' for c in checks) if checks else None,'topology_violations':sum(c['status']=='FAIL' and c['category']=='topology' for c in checks) if checks else None,'invalid_transitions':sum(not x['committed'] for x in load(folder/'geometry_trace.json').get('transition_execution',[])) if checks else None,'repair_attempts':st.get('repair_attempts',0),'repairs_approved':int(st.get('status')=='APPROVED'),'deepseek_calls':sum(c['provider']=='deepseek' for c in assigned),'qwen_calls':sum(c['provider']=='qwen' for c in assigned),'input_tokens':tok('prompt_tokens'),'output_tokens':tok('completion_tokens'),'active_seconds':round(sum(c.get('elapsed_seconds',0) for c in assigned),3),'uncertain_checks':count('UNCERTAIN')+count('NOT_MEASURED'),'actual_execution_mismatch_count':sum(len(c['observed_evidence'].get('mismatches',[])) for c in checks) if checks else None,'label_overlap_samples':len(layout.get('label_overlaps',[])) if checks else None,'out_of_frame_samples':len(layout.get('out_of_frame',[])) if checks else None,'object_discontinuity_samples':len(layout.get('sudden_jumps',[])) if checks else None,'video_path':st.get('video_path'),'duration_seconds':st.get('duration_seconds')}
 rows.append(row)
 if checks:row['scientific_constraint_pass_rate']=count('PASS')/(count('PASS')+count('FAIL'))
 else:row['scientific_constraint_pass_rate']=None
 # Missing optional artifacts are explicitly null, never fabricated.
 st['optional_artifacts']={n:str(folder/n) if (folder/n).exists() else None for n in ['scene_graph.json','assembly_states.json','state_transitions.json','generated_code.py','rendered_code.py','geometry_trace.json','validation_report.json','video.mp4','preview.jpg']};write(folder/'status.json',st)
total={p:{'requests':sum(c['provider']==p for c in calls),'input_tokens':sum((c.get('usage') or {}).get('prompt_tokens',0) for c in calls if c['provider']==p),'output_tokens':sum((c.get('usage') or {}).get('completion_tokens',0) for c in calls if c['provider']==p),'active_seconds':round(sum(c.get('elapsed_seconds',0) for c in calls if c['provider']==p),3)} for p in ['deepseek','qwen']}
frozen=load(E/'frozen_inputs.json');changed=[name for name,h in frozen.items() if not (R/name).exists() or sha(R/name)!=h]
write(E/'validation/frozen_input_verification.json',{'checked':len(frozen),'changed':changed})
write(E/'metrics.json',{'groups':rows,'providers':total,'all_requests':len(calls),'amount':None,'group_attribution_note':'Group counts include direct Coder requests only; shared compiler and IR/video reviews are separately listed in full ledger and provider totals, not silently charged to every group.','frozen':{'checked':len(frozen),'changed':changed}})
for dest in [E/'metrics.csv',E/'comparisons/comparison_table.csv']:
 with dest.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
write(E/'validation/mechanism_results.json',{r['group']:load(E/'groups'/r['group']/'validation_report.json') for r in rows if (E/'groups'/r['group']/'validation_report.json').exists()})
write(E/'validation/scientific_review_results.json',{str(p.relative_to(E)):load(p) for p in list((E/'validation').glob('*ir_review.json'))+list((E/'groups').glob('*/scientific_video_review.json'))})
ff=str(R.parent/'env/bin/ffmpeg');comp=E/'comparisons';comp.mkdir(exist_ok=True)
videos=[Path(r['video_path']) for r in rows if r['group'].startswith('A') and r.get('video_path')]
names=[r['group'] for r in rows if r['group'].startswith('A') and r.get('video_path')]
cmd=[ff,'-y','-v','error']
for v in videos:cmd+=['-i',str(v)]
filters=[]
for i,n in enumerate(names):filters.append(f"[{i}:v]scale=640:360,drawtext=text='{n} - NOT APPROVED':fontcolor=white:fontsize=16:x=8:y=8, tpad=stop_mode=clone:stop_duration=40,trim=duration=34,setpts=PTS-STARTPTS[v{i}]")
filters.append('[v0][v1][v2][v3]xstack=inputs=4:layout=0_0|640_0|0_360|640_360[out]')
subprocess.run(cmd+['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','24',str(comp/'A0_A1_A2_A3.mp4')],check=True)
for topic,selected,times in [('dna',[r for r in rows if r['group'].startswith('A')],[2,13,22,30]),('mitosis',[r for r in rows if r['group']=='B1_mitosis'],[1,5,9,12])]:
 canvas=Image.new('RGB',(4*427,len(selected)*265),'#111111');draw=ImageDraw.Draw(canvas)
 for y,row in enumerate(selected):
  for x,t in enumerate(times):
   dest=comp/f"{row['group']}_{t:02}.jpg"
   subprocess.run([ff,'-y','-v','error','-ss',str(t),'-i',row['video_path'],'-frames:v','1',str(dest)],check=True)
   if dest.exists():canvas.paste(Image.open(dest).resize((427,240)),(x*427,y*265+25))
   draw.text((x*427+6,y*265+6),row['group']+f' t={t}s',fill='white')
 canvas.save(comp/(topic+'_keyframes.jpg'),quality=92)
text='''# 高中教学人工复核表

本表尚待真实教师或高中生填写；模型审核不能冒充观众研究。

|检查|定位证据|人工结论|
|---|---|---|
|每次引入对象数量是否适中|DNA 第2/4事件；有丝分裂第1事件|待复核|
|字幕是否对应正在发生的动作|完整视频与事件时间|待复核|
|关键事件是否可见且有足够停留|引物去除、补缺与连接|待复核|
|身份和方向是否容易辨认|端点标签；姐妹染色单体移动|待复核|
|标签是否遮挡结构或出框|layout_metrics.json 的重叠/出框采样|待复核|
|修复是否肉眼可辨|A2/A3关键帧，主要为Primase标签差异|待复核|
|科学简化是否说明清楚|scientific_assumptions.md|待复核|
''';(E/'pedagogical_review_checklist.md').write_text(text)
table='\n'.join('|'+ '|'.join(str(r[k]) for k in ['group','render_success','science_gate','constraints_passed','constraints_failed','duration_seconds'])+'|' for r in rows)
report=f'''# V4 实验报告
日期：2026-11-24，北京时间。

## 完成状态
通用框架与两个主题组合已实现，27项离线测试通过，包括错误注入、真实完整渲染和失败回滚。A1/A2各完成真实Coder生成与完整渲染；A3执行两轮真实返工，B1完成13秒真实生成与完整渲染。工程实验已执行，最终科学批准0组。V1—V3冻结文件{len(frozen)}个，哈希变化{len(changed)}个。

|组|完整渲染|联合科学门禁|确定性通过|失败|秒|
|---|---|---|---|---|---|
{table}

## 架构与生成归因
详见architecture.md。知识证据、组合数据、过程数据、场景IR、实际观测分开。通用引擎支持十类动作与事务条件。模型生成事件计划、薄封装教学代码与返工补丁；大量几何及科学过程来自Codex准备的可编辑蓝图，不能说成模型自行构建完整动画。A1/A2同一模型计划和蓝图，分别关闭/开启完整状态验证。二者有效视频哈希相同，不能据此证明状态机减少自然生成错误；它的增益证据来自注错拦截。

## DNA科学与视觉证据
两条蓝色亲代模板是同一组合中的两个持续存在的对象，开叉移动的是它们自己的点，不生成第三条独立亲代双链。真实实例ID连续，实际生长端轨迹、引物先于延伸、后随链补缺负向投影、实际切口邻接均有checks与锚点证据。Pol epsilon用于常见前导链教学模型，非绝对排除Pol delta。旧Pol δ标签首次可观察阶段为CODE，不盲目归责Planner。

新增预期/实际验证发现旧几何中心定义与Manim包围盒不一致、绑定存在一帧延迟。Codex修正通用适配器后，用相同保存模型代码重放A1/A2，工程修复前后均留档；这些不是Agent科学修复成果。最终A1/A2确定性检查通过，但IR审核仍REVISE，不能自动批准。

## Biology Expert返工
首轮A3返回标签/字幕修改，文字解释声称修中心与绑定却未实际实现，真实门禁拒绝并回滚。第二轮真实生成将Primase显示名分离并补充Pol-alpha交接省略说明，完整渲染/解码通过，全视频Qwen返回PASS但仍有轻微意见；IR复核REVISE，联合门禁拒绝，指针回滚到冻结A2来源。完整候选单独保留，正式科学修复批准0。

IR复核中的极性意见与实际事实相冲突：模板3′左/5′右，新链3′端向右生长符合反平行规则；不能为满足模型意见而翻转正确方向。该分歧原样保存，不把审核误判自动改成通过。Primase显示名已改但scientific_identity.name仍带Pol alpha，身份字段存在未解决一致性问题。Qwen还指出补缺段与原片段虽端点重合，却缺少显式连续链关系；这揭示几何邻接不等于完整科学拓扑。修复到达每问题两次上限，不再追加。

## 有丝分裂泛化
B1使用相同Schema、组合类、状态机、验证器和Manim适配器，无主题判断分支。已有两个染色单体对象持续移动，角色转为子染色体，不通过复制图标增加数量；排列后才允许去除凝聚关系和分离。13秒视频完整解码。

科学复核REVISE：移动期间纺锤丝端点与动粒短暂脱开，末帧重合不能代表全程连接；染色单体尖端朝向和字幕出框也有问题。已将逐时刻drawn_connection检查补入通用验证器，真实B1检出FAIL，未手改其完整教学动画。跨主题可执行性成立，跨主题科学质量未达标。

## 视觉与教学
comparisons包含四组并排诊断视频和按相同秒数的关键帧；事件时间并非全部严格匹配，不能从同一秒截图推断效应大小。统计标签重叠/出框是约0.2秒采样启发式，真实教师复核表尚未填写。没有高中生实测，也不声称显著改善。最终关键帧人工查看确认：DNA模板蓝线在开叉后变为楔形粗带，属于适配器几何变换显示伪影，不能称为已解决全部结构可读性；B1字幕出框明显，染色单体三角形仍是高度抽象示意。这些额外问题没有被确定性通过率充分反映，应保留人工复核。

## 模型用量与失败
{json.dumps(total,ensure_ascii=False,indent=2)}

DeepSeek10/10、Qwen3/3，全部请求原始响应留存，自动重试0；Wan/Seedance0。真实金额未知。共享编译/科学审核调用不重复摊入每个组，完整总数与provider totals为准。第一轮A3科学运行门禁失败不是API失败。没有伪造缺失视频或模拟真实调用。

## 局限与建议
单样本、工程准备蓝图强约束、薄封装Coder、非盲法、共享模型科学审核、二维示意、轨迹采样及元数据角色不能替代科学观测。没有通用3D拓扑/化学验证，没有完整六节生成，没有真实观众试验。A3不支持任意结构自动返工，只对明确边界的表示补丁生效；结构根因需回到数据层，未自动泛化修复。

建议先修正连续链关系、动粒与微管逐帧连接、IR科学意见冲突与标签可读性，并增加多样本对照，再考虑六节扩展。当前不宜自动扩展或发布科学成片。
'''
(E/'RESULTS.md').write_text(report)
(E/'README.md').write_text('# V4 状态化科学动画\n\n工程实验已执行；联合科学门禁无批准组。先读 RESULTS.md 与 metrics.json。诊断视频不用于未经复核的教学发布。\n\n入口：tools/run_experiment.py、tools/continue_experiment.py。预算已用满，不直接重复运行真实请求。\n')
for p in [comp/'A0_A1_A2_A3.mp4']:
 subprocess.run([ff,'-v','error','-i',str(p),'-f','null','-'],check=True)
# Source bundle excludes API credentials, duplicated payloads and bulky render intermediates.
bundle=E/'V4_代码规则审核日志.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 for base in [R/'src/scientific_scene',E]:
  for p in base.rglob('*'):
   if not p.is_file() or p==bundle or p.suffix in ['.mp4','.pyc'] or any(x in p.parts for x in ['payload','render','__pycache__']) or any(x.startswith('offline_') for x in p.parts):continue
   z.write(p,str(p.relative_to(R)))
write(E/'delivery_manifest.json',{str(p.relative_to(E)):sha(p) for p in [E/'RESULTS.md',E/'metrics.json',bundle,comp/'A0_A1_A2_A3.mp4',comp/'dna_keyframes.jpg',comp/'mitosis_keyframes.jpg']+[E/'groups'/x/'video.mp4' for x in ['A1_stateful_assembly','A2_scene_graph_fsm','A3_expert_repair','B1_mitosis']]})
memory=R/'PROJECT_MEMORY.md';old=memory.read_text();marker='\n## 2026-11-24 V4已执行\n'
if marker in old:old=old.split(marker)[0]
memory.write_text(old+marker+'通用src/scientific_scene实现，27/27离线测试；A1/A2实际生成渲染，A3两轮真实返工未获联合批准并回滚，B1实际13秒视频科学REVISE。DeepSeek10/10、Qwen3/3已用满，不追加调用。报告experiments/scientific_scene_v4/RESULTS.md，metrics.json和完整模型账本logs/model_calls.json。所有历史冻结文件哈希核查见validation/frozen_input_verification.json。无实验后台任务。下一步先读报告与validation/dna_repaired_ir_review.json，复核错误极性意见，修连续链关系和mitosis逐时刻微管连接；不自动扩展六节。\n')
print(json.dumps({'providers':total,'frozen_changed':changed,'groups':[(r['group'],r['science_gate']) for r in rows]},ensure_ascii=False))
