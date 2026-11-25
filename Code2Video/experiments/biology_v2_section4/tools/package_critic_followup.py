from pathlib import Path
import json,sys,subprocess,zipfile,time
from PIL import Image,ImageDraw
ROOT=Path('/autodl-tmp/code2biovideo').resolve();REPO=ROOT/'Code2Video';E=REPO/'experiments/biology_v2_section4';G=E/'groups/A3_critic_followup_two_rounds'
sys.path.insert(0,str(REPO/'src'))
from biology_v2_pipeline import sha,probe
S=json.loads((G/'summary.json').read_text());calls=json.loads((G/'api_calls.json').read_text())
checks=[]
for rn in [1,2]:
 v=G/f'versions/critic_round_{rn}';status=json.loads((v/'status.json').read_text());meta=probe(v/'video.mp4')
 assert sha(v/'rendered_code.py')==status['code_sha256'] and sha(v/'video.mp4')==status['video_sha256']
 subprocess.run([str(ROOT/'env/bin/ffmpeg'),'-v','error','-i',str(v/'video.mp4'),'-f','null','-'],check=True,capture_output=True)
 trace=json.loads((v/'geometry_trace.json').read_text());lay=json.loads((v/'layout_metrics.json').read_text())
 actual_pairs=[o for o in lay['label_overlaps'] if 'template_end_labels' not in o['objects']]
 rec={'round':rn,**status,'width':meta['streams'][0]['width'],'height':meta['streams'][0]['height'],'frame_rate':meta['streams'][0]['r_frame_rate'],'full_decode_pass':True,'bindings_violations':len(lay['binding_violations']),'out_of_frame':len(lay['out_of_frame']),'group_bbox_label_overlap_samples':len(lay['label_overlaps']),'label_pair_samples_excluding_composite_bbox':len(actual_pairs),'note':'Composite label bounding box creates false positives; label-line overlap still visually observed and NOT captured by label-label heuristic.'}
 f=min(trace['frames'],key=lambda f:abs(f['time']-16))
 rec['at_16sec']={k:f['objects'][k]['center'] for k in ['dna_polymerase_leading_label','new_leading_3prime','rna_primer_lead_3prime']}
 lig=[f for f in trace['frames'] if f['objects'].get('dna_ligase',{}).get('visible')]
 rec['ligase_first_visible']={'time':lig[0]['time'],'center':lig[0]['objects']['dna_ligase']['center'],'bbox':lig[0]['objects']['dna_ligase']['bbox']}
 checks.append(rec)
assert checks[0]['video_sha256']!=checks[1]['video_sha256']
original=json.loads((G/'round_1/input_pair.json').read_text())
assert sha(original['code'])==original['code_sha256'] and sha(original['video'])==original['video_sha256']
known=sum(x['usage']['total_tokens'] for x in calls);deep=sum(x['usage']['total_tokens'] for x in calls if x['provider']=='deepseek');qwen=sum(x['usage']['total_tokens'] for x in calls if x['provider']=='qwen')
start=S['rounds'][0]['result']['started']-calls[0]['elapsed_seconds'];end=S['rounds'][1]['result']['started']+S['rounds'][1]['result']['elapsed_seconds']
S.update(completed_rounds=2,status='two_rounds_rendered_quality_partially_improved',new_requests=3,new_request_retries=0,new_tokens=known,new_deepseek_tokens=deep,new_qwen_tokens=qwen,full_render_success_rate='2/2',function_format_rejections=1,elapsed_to_final_render_seconds=round(end-start,3),verification=checks,final_video=str(G/'round_2/video.mp4'),no_final_round2_critic_request=True)
(G/'summary.json').write_text(json.dumps(S,ensure_ascii=False,indent=2))
(G/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
videos=[('A2 input',Path(original['video'])),('Round 1',G/'round_1/video.mp4'),('Round 2',G/'round_2/video.mp4')]
review=G/'review';times=[16,29,30.13]
canvas=Image.new('RGB',(854*3,510*3),'#222222');draw=ImageDraw.Draw(canvas)
for col,(label,video) in enumerate(videos):
 for row,tm in enumerate(times):
  p=review/f'comparison_{col}_{row}.png'
  subprocess.run([str(ROOT/'env/bin/ffmpeg'),'-v','error','-ss',str(tm),'-i',str(video),'-frames:v','1','-y',str(p)],check=True)
  canvas.paste(Image.open(p).convert('RGB'),(col*854,row*510));draw.text((col*854+10,row*510+482),f'{label} @ {tm}s',fill='white')
canvas.save(review/'before_round1_round2.jpg',quality=92)
report=f"""# Code2Video + DeepSeek：Qwen评价反馈两轮生成报告

核验日期：2026-11-23（北京时间）。本次为模型替代实验，不是原论文模型配置的严格复现。
范围延续 Biology-Aware V2，只处理 DNA replication in eukaryotic cells 的第4节，不是重新生成六节完整成片。

## 实际完成结果

|结果|时长|尺寸/帧率|完整渲染与解码|
|---|---|---|---|
|第一轮反馈修复视频|33.466667秒|854×480 / 15帧每秒|通过|
|第二轮反馈修复视频（最终）|33.466667秒|854×480 / 15帧每秒|通过|

两轮均有真实、独立的新MP4及对应代码，不是复制初始视频。均无音轨。
服务器主目录：{G}
两轮完整渲染成功率2/2；这是本次两次渲染的统计，不代表历史所有候选的成功率。

## 实际执行链路

1. 起点为已验证的A2视频与代码。第一轮复用用户此前要求重试后成功返回的Qwen反馈，核对代码和视频SHA-256完全相同；未重复调用Qwen。
2. DeepSeek根据三项对象问题生成修复函数。按抽象语法树替换construct，经完整Manim渲染、完整视频解码、对象注册、五个事件、酶与锚点关系、边界及补缺方向检查，提交第一轮。
3. 将真实第一轮新视频及其真实对象清单送给Qwen，取得新的三项问题；第二次DeepSeek修复以第一轮代码为输入。
4. 第二次DeepSeek返回完整模块，而非要求的函数。首次格式门禁拒绝，保留原始异常。确认函数以外的导入、辅助函数和类结构在抽象语法树层面一致后，自动提取模型原本生成的construct，再经过相同完整渲染门禁提交第二轮。该适配没有额外API调用，没有手工编写或替换动画内容。
5. 第二轮成片没有再发起第三次评价；本报告中的第二轮质量复核来自实际轨迹和关键帧，不冒充Qwen对最终成片的认可。

## 反馈内容及实际质量

第一轮反馈指出：酶标签未随酶移动、滞后链相关标签与中间梯状结构重叠，以及新链端点标签被误认成模板端点。第一轮代码为标签增加跟随更新器并注册文本，实际视频中标签跟随改善，但前导链酶标签仍压在中间梯状线条上。

第二轮评价明确发现上述残留遮挡、新生前导链3′标记压在模板上，以及连接酶远离缺口。第二轮实际代码调整前导链酶标签颜色/间距、新生链3′位置及连接酶位置。但并未落实“前导链阶段结束后隐藏酶及标签”的建议，前导链酶标签仍与中间线条相交。

实际几何证据：
- 新生前导链3′标记中心y：第一轮1.31 → 第二轮0.73，已从蓝色上模板附近移开。
- 前导链酶标签中心y（16秒）：第一轮0.02284 → 第二轮-0.00716，仍接近中间梯状结构y=0；遮挡没有解决。
- 连接酶中心从(3.00,-1.58)移至(2.65,-1.35)，更接近缺口(2.55,-1.03)，但尚不能据此宣称其形状边界已可靠接触缺口。
- 引物3′标记仍在y=1.31；滞后链3′标记第二轮又靠近蓝色下模板。部分端点标识混淆仍存在。
- V2已知的叉拓扑不清、前导链标作Pol δ以及只演示局部引物移除等问题仍需生物学与教学复核。本次没有改写整个分镜消除这些问题。

为遵守既有机制约束，修复提示还明确加入“补缺DNA必须从右向左出现”和真实文本注册。这是预先已发现的问题及观测补充，不应全部归功于Qwen反馈。
两轮实际填补核苷酸首次出现x依次2.4583→2.2750→2.0917，方向检查通过。
两轮均无注册对象越界、无注册酶-锚点距离违规；这些工程门禁不等于完整科学正确性。

文本观测器中的template_end_labels是涵盖四个角落标记的组合对象，其大包围盒会制造大量标签重叠误报。因此不把原始重叠样本336/337解释为真实遮挡次数，也不据此宣称第二轮整体优于第一轮。关键帧和实际残留问题优先。

## 模型、用量、耗时与重试

模型保持环境变量中的deepseek-flash和qwen4-max；Qwen继续原有OpenAI兼容接口。未更改模型、服务地址、密钥、超时、输出上限、视频采样参数、外部素材或分镜配置。本次仅增加独立续跑脚本和交付记录。
新调用：DeepSeek两次、Qwen一次，均成功；自动API重试0次。
第一轮评价沿用上次成功响应：输入20783、输出4878、合计25661词元，耗时131.618秒，本次没有重复计费调用。

|本次新调用|输入词元|输出词元|总词元|耗时|
|---|---:|---:|---:|---:|
"""
for c in calls:
 u=c['usage'];report+=f"|{c['provider']} 第{c['round']}轮|{u['prompt_tokens']}|{u['completion_tokens']}|{u['total_tokens']}|{c['elapsed_seconds']}秒|\n"
report+=f"""
本次新增合计{known}词元，其中DeepSeek {deep}、Qwen {qwen}。从首轮修复调用至最终二轮渲染结束约{S['elapsed_to_final_render_seconds']}秒，含格式拒绝后的核对适配与渲染。
V2累计DeepSeek 8次，已知137532词元；Qwen累计3次（首次超时、用户重试成功、本次第二轮评价成功），已知50740词元，首次超时用量未知，不记为0。原历史账本未覆盖；续跑独立记录用户新增授权。本次没有额外素材下载、万相请求、检索增强或其他智能体。

## 修改与证据

- 新增tools/run_critic_followup.py：复用已验证反馈、记录独立账本、按对象反馈调用原Coder、两轮事务渲染。
- 新增tools/finish_critic_followup_format.py：核对模型返回模块的非目标部分不变，仅提取生成的目标函数；原始格式异常保留。
- 新增tools/package_critic_followup.py：完整解码复核、配对哈希、关键帧、报告与不含密钥的材料包。
- 原有gpt_request.py、agent.py、api_config.json、run_agent_single.sh、本次之前的V2运行结果与分镜/素材均未修改。
- 每轮round_N下保存输入配对、评价提示和结构化反馈、原始模型函数、候选/实际代码、事务日志、真实MP4。
- versions/critic_round_N下保存完整渲染日志、几何轨迹、布局指标与状态。
- logs和api_calls.json保留所有本次模型响应、用量、耗时。失败格式原样保存。

第一轮视频SHA-256：{checks[0]['video_sha256']}
第二轮视频SHA-256：{checks[1]['video_sha256']}

结论：已完成真实“评价→反馈→重新生成→新视频再评价→再次生成”的两轮闭环。工程链路可行，部分布局和机制问题改善，但最终第4节仍存在明显教学呈现问题，不能作为已通过科学审核的成片。
"""
(G/'REPORT_zh.md').write_text(report)
memory=REPO/'PROJECT_MEMORY.md';m=memory.read_text()
a=m.index('## Current state');z=m.index('## Verified results',a)
m=m[:a]+'## Current state\nVERIFIED：用户最新要求的Critic反馈两轮实际生成已完成。新目录groups/A3_critic_followup_two_rounds；两轮各33.466667秒，完整渲染/解码/配对通过，最终round_2/video.mp4。实际质量仅部分改善，不能宣称科学审核通过。\n\n'+m[z:]
a=m.index('## Immediate continuation');z=m.index('## Blockers',a)
m=m[:a]+'## Immediate continuation\n本次两轮已完成，无后台运行任务。先读experiments/biology_v2_section4/groups/A3_critic_followup_two_rounds/REPORT_zh.md及summary.json，观看round_2/video.mp4和review/before_round1_round2.jpg。若后续要求改进，针对仍存的前导酶标签压线、引物/滞后链端点标记、叉拓扑、连接酶接触建立验收后继续，保留两轮现有结果。\n\n'+m[z:]
m+='\n## 2026-11-23 两轮Critic续跑已完成\n第一轮复用上次Qwen成功反馈，DeepSeek真实修复并全渲染；第二轮将新第一轮视频送Qwen，再经DeepSeek修复全渲染。新增DeepSeek2/Qwen1，API重试0，新增61244词元。V2累计DeepSeek8次137532词元；Qwen3次已知50740词元，首次超时用量未知。第二次Coder错误返回完整模块，保留格式拒绝，只自动提取生成函数，非目标AST一致，无手写动画。两次渲染2/2成功；两轮均33.466667秒，最终视频SHA b67043cfabdb71d27aebdd5e31cd73644117419ebeecfb68d97f82bfe7b3cb0a。修复补缺方向已通过实际轨迹，布局仍有缺陷；没有第三次Critic对最终成片背书。续跑目录及REPORT_zh.md为最新证据，旧正式A3超时报告保留作历史，不能当作当前无视频。\n'
memory.write_text(m)
delivery=ROOT/'delivery';delivery.mkdir(exist_ok=True);archive=delivery/'Biology_V2_Critic_Two_Rounds_materials.zip'
candidates=[]
for p in G.rglob('*'):
 if p.is_file() and not p.is_symlink() and p.suffix.lower() not in ['.mp4','.png','.jpg','.pyc'] and 'initial_A2_copy' not in p.parts and 'media' not in p.parts and '__pycache__' not in p.parts:candidates.append((p,Path('followup')/p.relative_to(G)))
for p in [REPO/'src/biology_runtime.py',REPO/'src/biology_v2_pipeline.py',REPO/'src/gpt_request.py',E/'tools/run_critic_followup.py',E/'tools/finish_critic_followup_format.py',E/'tools/package_critic_followup.py']:
 if p.exists():candidates.append((p,Path('source')/p.name))
for folder in ['specs','assets']:
 for p in (E/folder).rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.json','.md','.svg','.py']:candidates.append((p,Path(folder)/p.relative_to(E/folder)))
secrets=[]
for line in (ROOT/'.env').read_text().splitlines():
 if '=' in line:
  k,v=line.split('=',1)
  if 'KEY' in k and len(v)>12:secrets.append(v.strip().strip('"').strip("'").encode())
for p,name in candidates:
 data=p.read_bytes();assert not any(k in data for k in secrets),'Secret detected: '+str(name)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zipout:
 for p,name in candidates:zipout.write(p,str(name))
print(json.dumps({'completed_rounds':2,'new_tokens':known,'new_call_seconds':sum(c['elapsed_seconds'] for c in calls),'elapsed_to_final_render_seconds':S['elapsed_to_final_render_seconds'],'archive':str(archive),'archive_bytes':archive.stat().st_size,'report':str(G/'REPORT_zh.md'),'video_hashes':[c['video_sha256'] for c in checks]},ensure_ascii=False))
