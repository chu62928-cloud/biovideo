from pathlib import Path
import json,subprocess,zipfile,shutil,hashlib,time
R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video';E=REPO/'experiments/qwen4_critic'
m=json.loads((E/'metrics_analyzed.json').read_text());events=m['events']
cr=[json.loads(x) for x in (E/'logs/critic/requests.jsonl').read_text().splitlines()]
co=[json.loads(x) for x in (E/'logs/coder/requests.jsonl').read_text().splitlines()] if (E/'logs/coder/requests.jsonl').exists() else []
rows=[]
for sid in [f'section_{i}' for i in range(1,7)]:
 cells=[]
 for rn in [1,2]:
  e=next((x for x in events if x['section']==sid and x['round']==rn),None)
  if not e:
   feedback=E/f'round_{rn}/feedback'/(sid+'.json')
   cells.append('反馈已返回；优化中断' if feedback.exists() else '未执行')
  elif not e['has_issues']:cells.append('未报告布局问题；保留视频')
  elif e['native_optimize_success']:cells.append(f"修复渲染成功，建议{e['improvements']}条")
  else:cells.append(f"修复失败；保留上一成功视频，建议{e['improvements']}条")
 rows.append('| '+sid+' | '+' | '.join(cells)+' |')
runlog=(E/'logs/run.log').read_text()
stop_lines=[line for line in runlog.splitlines() if 'EXPERIMENT_ERROR' in line]
stop_reason=stop_lines[-1] if stop_lines else '无异常中断'
video_rows=[]
for rn,x in m['rounds'].items():
 video_rows.append(f"| 第{rn}轮 | {x['scenes']}/6 | {x['successful_optimizations']} | {x['failed_optimizations']} | {x['duration_seconds']:.3f} | {x['decode_returncode']} |")
usage_rounds={}
for rn in [1,2]:
 calls=[x for x in cr if x.get('stage','').startswith(f'round_{rn}:')]
 usage_rounds[str(rn)]={'calls':len(calls),'usage':{k:sum((x.get('usage') or {}).get(k,0) or 0 for x in calls) for k in ['prompt_tokens','completion_tokens','total_tokens']},'seconds':sum(x.get('elapsed_seconds',0) for x in calls)}
(E/'round_usage.json').write_text(json.dumps(usage_rounds,indent=2))
errs=[]
case=Path(m['output_dir'])
for p in sorted((case/'render_logs').glob('*.json')):
 d=json.loads(p.read_text())
 if d['cmd'][0]=='manim' and d.get('returncode')!=0:
  errs.append({'log':p.name,'cmd':d['cmd'],'stage':d.get('stage'),'error_tail':d.get('stderr','')[-1800:]})
(E/'render_failures.json').write_text(json.dumps(errs,ensure_ascii=False,indent=2))
report=f"""# Code2Video + DeepSeek + Qwen4 Critic：两轮实验
+
+日期：2026-11-23（北京时间）。
+
+**模型调用已通过，实际两轮状态见下表。视频文件可播放不等于每次修复成功：本报告明确区分新渲染与原生失败后保留的旧视频。** 本实验是模型替代实验，不是原论文模型配置的严格复现。
+
+## 配置与输入保持情况
+- Critic请求模型及响应标识为qwen4-max，Base URL为https://dashscope.aliyuncs.com/compatible-mode/v1。密钥仅存服务器仓库外.env，权限600；未打包、未写代码或日志。
+- Planner/Coder继续使用DeepSeek。未增加其他Agent、RAG、素材、专业规则或人工代码；原始布局提示词保持不变，Critic仅评价布局，不承担生物学事实核查。
+- 输入与冻结DNA基线一致：知识点、outline.json、storyboard.json、6份初始Manim代码，经原生缓存路径读取。原生render_section内部连续执行两轮反馈和优化；记录器只保存快照。
+- 除启用所请求的Critic并执行两轮外，现有基线生成/渲染配置保持不变。代码修改仅新增Qwen协议适配和Critic请求路由；视频使用官方video_url字段，仍传完整原MP4和上游GRID图，不用人为选帧替代输入。
+- 沿用10000输出词元上限，不覆盖Qwen思考模式或视频帧率。配置与源码检查见configuration_integrity.json；输入哈希见input_hashes.json；差异见critic_only.patch。
+
+## 一轮与二轮结果
+| 场景 | 第一轮 | 第二轮 |
+|---|---|---|
+{chr(10).join(rows)}
+
+| 成片 | 场景覆盖 | 实际修复渲染成功场景 | 修复失败场景 | 秒数 | 解码返回码 |
+|---|---:|---:|---:|---:|---:|
+{chr(10).join(video_rows)}
+
+第一轮快照是每节第一次原生反馈处理后的结果，第二轮快照是同次流程每节第二次处理后的结果；没有重新规划、重新抽样或人为补足失败场景。
+第二轮反馈评价的是第一轮修复后或保留的旧视频，**不能把第二轮反馈的问题数解释为第二轮修复后的剩余问题数**。没有额外插入第三轮评估。
+
+## 用量与运行时间
+实验状态：{m['status']}；主流程耗时{m['elapsed_seconds']:.3f}秒。
停止原因：{stop_reason}。
如出现45次上限，它是此前基线35次加本轮10次的既有DeepSeek累计限制；没有因本次实验扩大。达到上限后未继续修复，其后场景未执行，成片为已记录场景的局部视频，不是完整6节两轮成功视频。
+Qwen调用共{m['critic_attempts_including_probe']}次，含1次完整视频兼容性预检；用量{m['critic_usage']['total_tokens']:,}词元（输入{m['critic_usage']['prompt_tokens']:,}，输出{m['critic_usage']['completion_tokens']:,}，响应包含思考词元细目）。单独普通文本预检30词元，不计入该值。
+DeepSeek修复调用{m['coder_attempts']}次，用量{m['coder_usage']['total_tokens']:,}词元；Planner和初始Coder使用已有缓存，不增加规划调用。每轮Qwen用量见round_usage.json。未取得账单，不推算实际金额。
+接口、代码修复、渲染失败分别见logs/critic、logs/coder、render_failures.json，保留所有原始响应。
+
+## 已核实的技术观察
+1. 实际完整视频视觉请求成功，返回原layout JSON格式；Critic能指出裁切与标签重叠。第1节第一轮已缓解数字标签裁切和Speed/Accuracy重叠，第二轮继续调整大小和位置，证据见previews/section_1_comparison.jpg。
+2. 第2节原生位置提取器返回“No grid positions found in the code.”；Critic仍给出了行号与对象名。原生GridCodeModifier按行替换后产生IndentationError，两个轮次均失败。此记录不能写成视觉修复成功。
+3. 原生流程在优化渲染失败后可能留下尚未成功渲染的候选代码，同时保留旧视频；下一轮位置表来自候选代码，视频可能仍是旧版，存在对应关系不一致。未修改该流程。
+4. 原生修复器通过语法/干运行验证，不代表本轮实际全渲染成功；达到现有尝试限制后不人为追加重试。code/保存模型候选，rendered_code/单独保存对应实际视频的代码，避免将失败候选冒充成功产物。
+5. 本轮只检验布局反馈链路，不对原基线的生物知识缺项作修正。没有人工纠正Critic坐标、提示词或生成科学内容；更强的Critic不保证原生按行修复可靠，也不保证第二轮一定优于第一轮。
+
+## 实际产物
+"""
for rn,x in m['rounds'].items():report+=f"\n- 第{rn}轮MP4：{x['video']}\n"
report+=f"""
+- 分轮反馈、候选代码、已渲染代码、差异与逐场景视频：{E}/round_1/ 与 round_2/。
+- 对照图：{E}/previews/。
+- 日志与原始请求响应：{E}/logs/。
+- 原始DeepSeek基线完整保留，未覆盖。
+
+下一步应先观看两轮与基线对照，确认视觉收益和退化。按用户本次要求，没有修复原项目流程或增加其他模型配置。
+
+官方接口依据：[Qwen4-Max能力说明](https://www.alibabacloud.com/help/en/model-studio/qwen4-max)、[OpenAI兼容视频字段](https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions)。
+"""
report=report.replace('\n+','\n')
(E/'RESULTS.md').write_text(report,encoding='utf-8')
# Confirm all frozen baseline inputs remain identical.
source=REPO/'src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells'
hashes=json.loads((E/'input_hashes.json').read_text())
assert all(hashlib.sha256((source/name).read_bytes()).hexdigest()==expected for name,expected in hashes.items())
# Verify the configured secret literal is absent from all experiment deliverables.
env=dict(l.split('=',1) for l in (R/'.env').read_text().splitlines() if l and not l.startswith('#'))
for keyname in ['DASHSCOPE_API_KEY','DEEPSEEK_API_KEY']:
 key=env[keyname].encode()
 assert not any(key in p.read_bytes() for p in E.rglob('*') if p.is_file()),'Secret literal found'
for name in ['run_qwen4_two_rounds.py','collect_qwen4_rounds.py','finalize_qwen4_report.py']:shutil.copy2(R/name,E/'tools'/name)
with zipfile.ZipFile(R/'delivery/Qwen4_Critic_two_rounds.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in E.rglob('*'):
  if p.is_file() and p.suffix not in ['.mp4','.png','.jpg','.jpeg'] and p.name not in ['before_agent.py','before_gpt_request.py']:
   z.write(p,str(p.relative_to(E)))
print('Report and delivery package ready; frozen input and secret checks passed.')
