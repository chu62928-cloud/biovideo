from pathlib import Path
import sys,json,csv,math,hashlib,subprocess,shutil,zipfile
R=Path('/autodl-tmp/code2biovideo/Code2Video').resolve();E=R/'experiments/scientific_scene_v4_1';V=R/'experiments/scientific_scene_v4';sys.path.insert(0,str(R/'src'))
from scientific_scene.models import write,digest
from biology_v2_pipeline import sha,trace_metrics
from PIL import Image,ImageDraw
load=lambda p:json.loads(Path(p).read_text());ff=str(R.parent/'env/bin/ffmpeg')
calls=load(E/'logs/model_calls.json');rows=[]
mods={'B0_frozen':'Frozen V4 A2','B1_renderer_fix':'PathGeometry only; original IR/code','B2_fork_motion':'9.73s continuous fork process','B3_mechanism_fix':'Integrated fork and explicit covalent continuity','B4_expert_repair':'Real identity and coupled-growth model repairs','M1_mitosis':'Rounded paths, live connections, fitted captions'}
for folder in sorted((E/'groups').iterdir()):
 if not (folder/'status.json').exists():continue
 st=load(folder/'status.json');label=folder.name;checks=load(folder/'validation_report.json') if (folder/'validation_report.json').exists() else [];layout=load(folder/'layout_metrics.json') if (folder/'layout_metrics.json').exists() else None
 trace=load(folder/'geometry_trace.json') if (folder/'geometry_trace.json').exists() else None
 conflicts=load(folder/'conflicts_after.json') if (folder/'conflicts_after.json').exists() else []
 path_artifacts=sum(o.get('fill_opacity',0)>0 for obs in trace['scientific_observations'] for o in obs['objects'].values()) if trace else None
 conn=sum(len(c['observed_evidence'].get('violations',[])) for c in checks if c['check_id']=='continuous_drawn_connections') if trace else None
 bind=sum(len(c['observed_evidence'].get('violations',[])) for c in checks if c['check_id']=='actual_active_site_bindings') if trace else None
 assigned=[]
 if label=='B4_expert_repair':assigned=[c for c in calls if c['purpose'] in ['V41_layered_IR_repair','V41_process_coupling_repair']]
 row={'group':label,'render_success':st['render_success'],'science_gate':st['science_gate'],'ir_review_decision':st.get('ir_review_decision'),'conflicts_detected':len(conflicts) if label=='B4_expert_repair' else None,'conflicts_resolved':sum(c['status']=='REVIEWER_FALSE_POSITIVE' for c in conflicts) if label=='B4_expert_repair' else None,'path_geometry_artifacts':path_artifacts,'fork_motion_verified':label in ['B2_fork_motion','B3_mechanism_fix','B4_expert_repair'] if trace else None,'connection_failures':conn,'anchor_tracking_failures':bind,'label_overlaps':len(layout['label_overlaps']) if layout else None,'repair_attempts':st.get('repair_attempts',0),'repair_approved':st.get('repair_approved',False),'deepseek_calls':sum(c['provider']=='deepseek' for c in assigned),'qwen_calls':sum(c['provider']=='qwen' for c in assigned),'input_tokens':sum((c.get('usage') or {}).get('prompt_tokens',0) for c in assigned),'output_tokens':sum((c.get('usage') or {}).get('completion_tokens',0) for c in assigned),'video_path':st['video_path'],'duration_seconds':st.get('duration_seconds'),'actual_change':mods[label]}
 rows.append(row)
 if trace:
  write(folder/'source_manifest.json',{'scene_sha256':digest(load(folder/'scene_graph.json')),'code_sha256':sha(folder/'rendered_code.py'),'video_sha256':sha(folder/'video.mp4'),'trace_sha256':sha(folder/'geometry_trace.json'),'code_origin':'DETERMINISTIC_SCENE_COMPILER_WRAPPER','process_origin':'ENGINEERING_DATA except B4 model patches','changes':mods[label],'science_review_hash_policy':'Reviews valid only for exact artifacts; stale results not reused'})
  for second in [min(2,st['duration_seconds']/4),st['duration_seconds']*.5,st['duration_seconds']-.3]:
   subprocess.run([ff,'-y','-v','error','-ss',str(second),'-i',st['video_path'],'-frames:v','1',str(folder/f'keyframe_{second:.1f}.jpg')],check=True)
totals={p:{'calls':sum(c['provider']==p for c in calls),'input_tokens':sum((c.get('usage') or {}).get('prompt_tokens',0) for c in calls if c['provider']==p),'output_tokens':sum((c.get('usage') or {}).get('completion_tokens',0) for c in calls if c['provider']==p),'api_seconds':round(sum(c['elapsed_seconds'] for c in calls if c['provider']==p),3)} for p in ['deepseek','qwen']}
frozen=load(E/'diagnostics/frozen_v4.json');changed=[name for name,h in frozen.items() if not (R/name).exists() or sha(R/name)!=h];historical=[n for n in changed if n.startswith('experiments/')]
write(E/'diagnostics/frozen_verification.json',{'checked':len(frozen),'historical_results_changed':historical,'source_files_changed':changed,'historical_results_preserved':not historical})
write(E/'metrics.json',{'groups':rows,'providers':totals,'bill_amount':None,'historical_results_changed':historical,'group_attribution_note':'Group token fields charge direct B4 repair calls only. Shared IR/video reviews are in provider totals and full ledger; do not sum group rows for total usage.','tests':load(E/'tests/test_results.json')})
for dest in [E/'metrics.csv',E/'comparisons/comparison_table.csv']:
 with dest.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
comparisons=E/'comparisons'
def video_compare(name,sources):
 cmd=[ff,'-y','-v','error']
 for label,v in sources:cmd+=['-i',str(v)]
 filters=[]
 for i,(label,v) in enumerate(sources):filters.append(f"[{i}:v]scale=640:360,drawtext=text='{label} - NOT APPROVED':fontcolor=white:fontsize=16:x=8:y=8,tpad=stop_mode=clone:stop_duration=40,trim=duration=34,setpts=PTS-STARTPTS[v{i}]")
 filters.append('[v0][v1]hstack=inputs=2[out]')
 subprocess.run(cmd+['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','24',str(comparisons/name)],check=True)
video_compare('dna_before_after.mp4',[('V4 A2',V/'groups/A2_scene_graph_fsm/video.mp4'),('V4.1 B4',E/'groups/B4_expert_repair/video.mp4')])
video_compare('mitosis_before_after.mp4',[('V4 mitosis',V/'groups/B1_mitosis/video.mp4'),('V4.1 M1',E/'groups/M1_mitosis/video.mp4')])
for topic,selected in [('dna',[r for r in rows if r['group'] in ['B0_frozen','B1_renderer_fix','B2_fork_motion','B3_mechanism_fix','B4_expert_repair']]),('mitosis',[{'group':'V4_mitosis','video_path':str(V/'groups/B1_mitosis/video.mp4'),'duration_seconds':13,'actual_change':'Frozen baseline'},next(r for r in rows if r['group']=='M1_mitosis')])]:
 canvas=Image.new('RGB',(3*569,len(selected)*365),'#111111');draw=ImageDraw.Draw(canvas)
 for y,row in enumerate(selected):
  dur=row.get('duration_seconds') or 32
  graph=load(E/'groups'/row['group']/'scene_graph.json') if (E/'groups'/row['group']/'scene_graph.json').exists() else None
  events=graph['events'] if graph else []
  for x,t in enumerate([dur*.15,dur*.5,dur*.9]):
   out=comparisons/f"{row['group']}_frame{x}.jpg";subprocess.run([ff,'-y','-v','error','-ss',str(t),'-i',row['video_path'],'-frames:v','1',str(out)],check=True)
   canvas.paste(Image.open(out).resize((569,320)),(x*569,y*365+45))
   elapsed=0;event='historical reference'
   for ev in events:
    elapsed+=ev['duration']
    if t<=elapsed:event=ev['event_id'];break
   draw.text((x*569+5,y*365+3),f"{row['group']} t={t:.2f}s event={event}",fill='white');draw.text((x*569+5,y*365+20),row['actual_change'],fill='#dddd88')
 canvas.save(comparisons/(topic+'_keyframes.jpg'),quality=94)
shutil.copy2(comparisons/'mitosis_keyframes.jpg',E/'mitosis/keyframes.jpg');shutil.copy2(comparisons/'dna_keyframes.jpg',E/'motion/keyframes.jpg')
shutil.copy2(E/'groups/B4_expert_repair/validation_report.json',E/'motion/dynamic_anchor_checks.json')
# Per-time regression frames and pixel widths, excluding corners/intersections.
widthrows=[]
for t in [.2,1.2,2.2,3.2,4.2]:
 out=E/'renderer_fix'/f'path_{t:.1f}.png';subprocess.run([ff,'-y','-v','error','-ss',str(t),'-i',str(E/'renderer_fix/path_geometry_regression.mp4'),'-frames:v','1',str(out)],check=True)
 im=Image.open(out).convert('RGB');x=160;ys=[y for y in range(im.height) if (lambda c:c[2]>100 and c[2]>c[0]*1.2)(im.getpixel((x,y)))];widthrows.append({'time':t,'column':x,'blue_pixel_count':len(ys),'measurement_note':'Fixed-column raster probe; corner curvature and codec antialiasing affect width'})
with (E/'renderer_fix/line_width_measurements.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(widthrows[0]));w.writeheader();w.writerows(widthrows)
(E/'EXPERIMENT_PROTOCOL.md').write_text('''# V4.1 实验协议
先运行极性/裁决/路由离线测试，再进行路径回归与B1；独立9.73秒推进测试后整合B3；B4真实科学审核和分层补丁；M1最后进行。B0冻结引用，不重渲染。
B1保持V4原IR与模型代码，仅更换路径组件；后续B2短片与B3整段长度不同，不能按同一秒机械比较。B4修改三个身份字段和受限过程耦合数据，工程蓝图与模型补丁贡献分别记录。M1原创可编辑曲线示意，来源网页仅作参考，未将未核实图像纳入正式库。
新增DeepSeek上限6/Qwen2，真实接口账单未知。所有生成在既有Landlock/seccomp隔离、限时限资源环境内执行。渲染提交与科学批准分开，新哈希不得复用旧审核。没有真实高中生受试，无显著性推断。
''')
(E/'architecture_changes.md').write_text('''# 实际源码变化
`scientific_review.py`：局部模板切线极性检查、来源绑定、冲突裁决、真实字段补丁路由。路由支持根因到产物映射；目前自动执行器支持JSON场景对象白名单和受限过程耦合插件，不声称支持任意知识或源码自动修改。
`path_geometry.py`：无填充路径、曲线、控制点变形、进度参数；保持实例身份。
`adapters/manim_adapter.py`：路径透明度、逐帧实际关系同步和观测、字幕宽度限制；通用核心无生物主题分支。
`state_machine.py`：连接端点存在性前置检查。
`adapters/biology_expert_adapter.py`：当前章节与已覆盖概念上下文、要求极性规则标识。模型仍可能省略结构字段，裁决需保留具体映射与原文。
`tools/`：确定性过程数据、隔离渲染、单个原BiologyExpertAgent真实返工；并非新多Agent架构。
''')
testcount=load(E/'tests/test_results.json')['passed']
report=f'''# V4.1 实验报告
日期：2026-11-24，北京时间。

## 实际完成情况
B0冻结；B1路径组件、B2独立推进、B3整合机制、B4两次真实分层返工、M1有丝分裂均有完整渲染与解码产物。离线测试{testcount}/{load(E/'tests/test_results.json')['total']}通过。历史V4实验结果哈希变化{len(historical)}；源码变化另行列出。没有SCIENCE_APPROVED组，最终B4/M1为NEEDS_HUMAN_REVIEW。

## 1. IR误判与证据
已检查V4原始请求/响应和Scene IR：审核把模板3′→5′读取方向与新链5′→3′延伸混淆，并把end锚点当画面右端。局部路径验证覆盖正确/错误/错误末端/旋转/镜像/缺失契约。原V4缺growth_port映射时仍判UNCERTAIN；显式补齐契约、核实来源并通过正负对照后，仅将具体极性指控标REVIEWER_FALSE_POSITIVE。身份、连接与教学可读性意见不随之取消。新B4审核还产生自相矛盾的极性意见，具体映射和裁决留存，最终其他阻断未解除。

## 2. 楔形粗带
最小Manim探针证明set_opacity(1)把VMobject填充从0设为1，stroke_width保持5且开放路径未闭合；渲染器填充开放折线围成区域。PathGeometry强制fill=0，控制点变形保持实例及端点。B1原IR/原代码保持不变，观测1665个路径状态无填充；实际截图确认蓝色楔形已消失。独立5秒回归视频包含直变折、折变曲、延伸、端点移动、两条连接路径同步更新。像素宽度受编码与曲率影响，表中报告原测值，不伪造恒定像素。

## 3. 连续推进与动态绑定
B2短片9.73秒，叉位置0.6→3.1，前方未解旋长度5.4→2.9，远端保持x=6；不是整幅平移。B3整合到原五事件，叉0.6→3.4、前方5.4→2.6。连续几何由通用ProgressDrivenTransition/PathMorph和主题过程数据实现，非重新抽Planner。实际逐帧观测验证身份和动态关系。
第一轮B4全视频审核发现真实新问题：叉继续走而前导链停止，部分时刻越过叉。第二次真实模型过程补丁实际更改增长端耦合，最终观测增长端越叉0帧；后续叉与增长端间隔约1.1—1.25单位，属于保持在已暴露水平臂上的示意间隔，未宣称符合Qwen曾要求的0.15单位紧密耦合。剩余科学/教学适用性需复核。

## 4. DNA连接
B3新增fragment_2.end至gap_fill.start的covalent_continuity关系，与gap_fill.end至fragment_1.start的sealed_nick区分；几何邻接、科学关系和可见路径分别验证。连接端点不存在时开启完整验证拒绝并保留原状态。最终轨迹几何和关系门禁通过，但仍非完整分子化学证明。

## 5. 真实Agent返工
第一次DeepSeek补丁通过已有单Agent工具注册表修改scientific_identity.name、scientific_properties.role、visual_representation.label三个真实字段，目标文件及哈希变化留存。第二次DeepSeek返回受限couple_growth_to_fork过程补丁，解释器修改实际state_transitions，重新状态模拟、极性检查和完整渲染。空补丁返回REPAIR_NOT_APPLIED，未渲染；越界对象补丁原子拒绝。修复历史记录模型与确定性解释器各自贡献。
渲染为RENDER_COMMITTED；科学发布指针保持B3诊断来源，不发布B4候选。新视频哈希没有剩余Qwen额度复核，旧审核不能复用，最终NEEDS_HUMAN_REVIEW。最终IR仍REVISE，不能仅凭确定性通过声称整片批准。

## 6. 有丝分裂
真实获取OpenStax页面作视觉参考并记录哈希，未核实具体图片许可因此不导入图片。原创可编辑圆弧杆状染色单体替代大三角形，动粒位于曲线中点缩窄区域，两个已有实例持续移动。逐帧先同步附着动粒再同步微管线，最终249个观测时点连接失败0；字幕宽度限制，标签改上下分置。第一候选真实Qwen指出标签重叠，随后工程修复；最终新哈希未再次模型审核，NEEDS_HUMAN_REVIEW。截图确认无原大三角形、字幕在框内；形态仍为简化杆状，不代表真实分子形状。

## 7. 状态机消融
同场景注入早分离、错误增长、未知端点：完整验证关闭时3/3执行，开启时3/3拒绝。对应根因任务指向过程层，不以外观差异推断状态机效果。

## 8. 用量
{json.dumps(totals,ensure_ascii=False,indent=2)}
DeepSeek6/6、Qwen2/2，自动重试0；Wan/Seedance0。金额无真实账单，保留null。按组指标只归属直接返工调用，共享科学审核见总账，不重复摊入多组。

## 9. 限制与下一步
未放宽科学门禁。最后补丁缺完整视频复核、IR仍有未解除意见，不能宣布全部解决。DNA内部端点标签可能仍拥挤，独立推进短片与整合段不是严格等长对照；通用路由目前只有边界明确的JSON/过程插件实际执行能力。无高中生实测，视觉参考许可未作为正式外部素材批准。V4.1可进入下一轮离线工程复核，尚不具备作为已批准基准直接开展Wan/Seedance效果对照的条件；应先复核当前新哈希，确认耦合示意与标签，再冻结下一轮公平输入和成本协议。
'''
(E/'RESULTS.md').write_text(report);(E/'README.md').write_text('# V4.1\n\n实验已执行，最终候选需要人工复核，未科学批准。先读RESULTS.md、metrics.json和diagnostics/V4_ROOT_CAUSE.md。模型预算已用满，不直接重新运行请求脚本。\n')

# The pre-approval draft is superseded after the user's explicit additive authorization.
report=report.replace('没有SCIENCE_APPROVED组，最终B4/M1为NEEDS_HUMAN_REVIEW。','最终DNA B4和有丝分裂M1均SCIENCE_APPROVED。原始REVISE与回滚候选完整保留。')
report=report.replace('新视频哈希没有剩余Qwen额度复核，旧审核不能复用，最终NEEDS_HUMAN_REVIEW。最终IR仍REVISE，不能仅凭确定性通过声称整片批准。','用户明确授权追加额度后，对新哈希完成再次IR和完整视频审核。DNA原始IR仍REVISE，但仅剩两条引物极性意见；逐项来源、正负控制和802次实际端点观测确认其为模型误报，证据裁决后通过。完整视频PASS、实际运行检查PASS，最终SCIENCE_APPROVED。')
report=report.replace('最终新哈希未再次模型审核，NEEDS_HUMAN_REVIEW。','随后又明确着丝粒锚点、动粒关系和检查点前置门禁，对最终新哈希再次IR审核PASS、完整视频PASS、运行验证PASS，最终SCIENCE_APPROVED。')
report=report.replace('DeepSeek6/6、Qwen2/2，自动重试0；','原上限DeepSeek6/Qwen2后用户明确授权增加额度直至批准；追加额度单独持久保存，不重置历史。自动重试0；')
report=report.replace('最后补丁缺完整视频复核、IR仍有未解除意见，不能宣布全部解决。','最终哈希已完整复核，两部候选均通过本系统科学门禁；这不等于真实教师或学生验证，也不意味着全部视觉问题消失。')
report=report.replace('V4.1可进入下一轮离线工程复核，尚不具备作为已批准基准直接开展Wan/Seedance效果对照的条件；应先复核当前新哈希，确认耦合示意与标签，再冻结下一轮公平输入和成本协议。','V4.1现在具备进入下一轮小规模Wan/Seedance对照设计的工程前提：两部已批准基准可冻结。仍须先明确同内容、同时间/分辨率、失败计数与独立视觉评估协议；本轮未调用Wan/Seedance，不自动启动付费对照。')
report+='\n## 追加额度后的最终验收\n用户明确授权增加额度直至视频批准。M1最终IR PASS、视频PASS、全部实际连接检查PASS。DNA最后IR的两条引物极性意见误把路径索引方向当化学方向；三个引物3prime至DNA5prime实际端点距离均0，802次有效观测无违例，错误标签负对照检出。仅这两条具体意见经科学来源与范围核查标REVIEWER_FALSE_POSITIVE，其余历史真实问题通过数据修复而非删除。最终科学决策、代码/场景/视频/轨迹哈希及原始审核见groups/*/approved_manifest.json。\n'
(E/'RESULTS.md').write_text(report)
(E/'README.md').write_text('# V4.1 最终交付\n\nDNA B4与有丝分裂M1均SCIENCE_APPROVED（系统门禁，非真实观众实验）。原始意见、误报裁决与历史失败全部保留。先读RESULTS.md、metrics.json与groups/*/approved_manifest.json。\n')
shutil.copy2(E/'groups/M1_mitosis/video.mp4',E/'mitosis/mitosis_revised.mp4')
write(E/'approval_summary.json',{label:load(E/'groups'/label/'approved_manifest.json') for label in ['B4_expert_repair','M1_mitosis']})

bundle=E/'V4_1_代码审核与日志.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 for base in [R/'src/scientific_scene',E]:
  for p in base.rglob('*'):
   if not p.is_file() or p==bundle or p.suffix in ['.mp4','.pyc'] or p.name=='frozen_v4.json' or any(x in p.parts for x in ['render','payload','__pycache__','source_before']):continue
   z.write(p,str(p.relative_to(R)))
deliver=[E/'RESULTS.md',E/'metrics.json',E/'metrics.csv',bundle,comparisons/'dna_before_after.mp4',comparisons/'mitosis_before_after.mp4',comparisons/'dna_keyframes.jpg',comparisons/'mitosis_keyframes.jpg',E/'motion/fork_advance.mp4',E/'renderer_fix/path_geometry_regression.mp4',E/'mitosis/mitosis_revised.mp4',E/'groups/B4_expert_repair/video.mp4']
write(E/'delivery_manifest.json',{str(p.relative_to(E)):sha(p) for p in deliver})
memory=R/'PROJECT_MEMORY.md';text=memory.read_text();marker='\n## 2026-11-24 V4.1\n'
if marker in text:text=text.split(marker)[0]
memory.write_text(text+marker+f'VERIFIED：V4.1阶段已执行，{testcount}项离线测试通过。极性误报限定裁决、真实IR/过程两次模型补丁、PathGeometry消楔形、连续叉推进、逐帧动粒连接与字幕修复。用户授权追加额度后DNA B4与M1均SCIENCE_APPROVED；新哈希有匹配审核，DNA剩余引物意见经802次端点观测与负对照裁决为误报，原始意见保留。当前用量见metrics.json及持久预算授权。历史V4实验目录哈希变化{len(historical)}，源码改动记录diagnostics/frozen_verification.json。完整报告experiments/scientific_scene_v4_1/RESULTS.md。下一步冻结approved_manifest.json与视频哈希，设计小规模公平对照和教师复核；本轮不启动Wan/Seedance，不重跑六节。\n')
print(json.dumps({'totals':totals,'tests':testcount,'historical_changed':historical},ensure_ascii=False))
