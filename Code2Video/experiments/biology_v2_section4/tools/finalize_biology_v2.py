from pathlib import Path
import json,hashlib,subprocess,shutil,zipfile,ast,difflib
from PIL import Image,ImageDraw,ImageFont

R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video';E=REPO/'experiments/biology_v2_section4'
m=json.loads((E/'metrics.json').read_text());groups={x['group']:x for x in m['groups']}
checks={}
names=['模板与新链可区分','RNA引物先于对应新链','新DNA延伸5′→3′','前导链连续生长','后随链分段生长','酶与DNA作用位置关系','分子身份前后连续','关键步骤因果连续']
states={
 'A0_baseline':['pass','pass','uncertain','uncertain','uncertain','uncertain','uncertain','fail'],
 'A1_mechanism':['pass','pass','fail','pass','pass','fail','pass','uncertain'],
 'A2_mechanism_assets':['pass','pass','fail','pass','pass','uncertain','pass','uncertain']}
evidence={
 'A0_baseline':[
  '原代码top_template/bottom_template与leading_strand/frag1/frag2是不同对象，灰色模板与绿色新链可区分。',
  '局部约6秒先出现橙色引物，约14秒已显示绿链；代码对应先创建primer_top/bottom，再创建leading_strand。',
  '只有上方5′→3′箭头，未标注上下模板完整极性，无法确认后随链方向。',
  '以整条Create(Line)及文字说明表达，缺少逐核苷酸和复制叉持续推进的共同证据。',
  '虽有两个绿色短片段，但没有与每段对应的新RNA引物过程，机制证据不足。',
  '无持续绑定或追踪，不能仅凭静态圈图确认酶一直在作用端。',
  '从两条独立线段开始，未建立上一节已打开复制叉的连续身份。',
  '约31.5秒演示连接酶连接间隔，但未先展示RNA去除与DNA补缺。'],
 'A1_mechanism':[
  '蓝色Y形模板与绿色逐个出现的核苷酸是独立对象，见event3/4对照。',
  '实际轨迹RNA最先3.60秒、DNA最先8.93秒；各冈崎片段有独立RNA与DNA子对象。',
  '主延伸方向与标注相符，但约19.53–19.80秒补缺DNA按x=0.68→1.49→2.30出现，与下模板左5′右3′要求的向左延长不符；代码np.linspace(gap_start,gap_end,n_fill)亦支持。',
  '多个独立核苷酸依次向右出现，聚合酶随活动锚点移动；不是单根绿线一次成形。',
  '两个独立RNA起点及两组冈崎片段，DNA子对象的出现顺序向左；见轨迹和event4。',
  '约8–17秒新链在水平带上生长，而蓝色模板为倾斜Y形，部分新链与聚合酶离开实际模板；仅满足自声明活动锚点距离并不足以满足DNA关系。',
  '同一Y形蓝色模板/复制叉贯穿五个事件，未在镜头切换中换成无关模板。',
  'RNA去除→DNA填入→Ligase到达顺序已分开，但补缺方向及实际模板关系失败；仍不能确认整段机制连续正确。'],
 'A2_mechanism_assets':[
  '蓝色模板、橙色RNA、绿色新DNA对象可区分；来源注册与实际图像相符。',
  '实际RNA最先3.87秒、DNA最先9.33秒；两个后随片段各有引物。',
  '主延伸方向可以辨认，但28.53→28.80→29.07秒补缺子块最终x=2.092→2.275→2.458，沿下模板从左向右，违背本坐标约定所需的向左合成。',
  '绿色核苷酸逐个沿上模板邻近位置出现，而非重新给模板上色。',
  '两个橙色引物与两组绿色片段，后随主延伸分段且远离复制叉侧；仍需教师核查叉拓扑。',
  '声明的聚合酶活动位点绑定距离均在门限内，但绘制的叉为水平上下模板和中间连接，非清晰展开Y；图形锚点不等于真实DNA作用位点，保留uncertain。',
  '固定蓝色模板和角色持续存在；SVG图标身份未在后续画面更换。',
  '已分开RNA去除、DNA补缺、Ligase封小切口；但仅处理一个片段、补缺方向失败，整体因果教学仍需复核。']}
for label,values in states.items():
 checks[label]=[{'criterion':name,'status':value,'evidence':why,'sources':['actual_video','rendered_code','geometry_trace_if_available']} for name,value,why in zip(names,values,evidence[label])]
checks['A3_mechanism_assets_critic']=[{**x,'inherited_from_A2_initial_copy':True,'critic_effect_not_evaluated':True} for x in checks['A2_mechanism_assets']]
(E/'biological_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
for row in m['groups']:
 row.update(engineering_success=row['experiment_success'],fully_mechanism_validated=False,
            ready_for_teaching_without_review=False,
            biological_check_summary={status:sum(x['status']==status for x in checks[row['group']]) for status in ['pass','fail','uncertain']})
 (E/'groups'/row['group']/'final_group_summary.json').write_text(json.dumps(row,ensure_ascii=False,indent=2))
m['group_success_definition']='Engineering full-render gate only; not a claim of biological correctness.'
(E/'metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
review=['# 机制与布局人工复核\n','状态基于实际画面、代码和轨迹交叉核对；不是接受LLM自评分。A3视频是未改动的A2初始复制，不能作为Critic效果证据。\n']
for label,items in checks.items():
 review+=['\n## '+label+'\n\n','| 检查项 | 状态 | 依据 |\n|---|---|---|\n']
 for x in items:review.append('| '+x['criterion']+' | '+x['status']+' | '+x['evidence']+' |\n')
review+=['''
## 布局结论与限制

- A0保留了左侧五行静态文字，并有Primase/RNA Primer/DNA Pol/Okazaki等局部重叠。
- A1/A2消除了固定左侧讲义；A1核苷酸画得很小，且新链与Y形模板的对应关系较弱。A2酶的轮廓更容易区分，标签更短，但复制叉拓扑仍不够清楚，不能说整体科学性已经提升。
- A1/A2绘制的文本都没有注册为role=label，故自动“重叠=0”不具备全标签覆盖，必须标为uncertain，不作为布局无问题的证明。当前监测能覆盖注册分子对象边界、绑定和部分突然跳跃。
- A1原始轨迹报告4个突然跳跃线索；这是启发式，可能含换位/淡入。A2为0，仍不等于绝对没有跳跃或遮挡。
- 成功代码的可见比例由实际对象几何估算，保存在各组object_visibility.json；根组通过子对象可见性判断，避免将未直接add到Scene的VGroup误判为完全不可见。

## 人工复核清单

- 连续观看A1约8–17秒：新链是否贴近对应模板，聚合酶是否在可辨认的实际合成端。
- 连续观看A2约18–27秒：固定叉与两种合成的相对方向是否清楚，第二引物位置是否有合理解释。
- 观看A1约19.5–20秒及A2约28.5–29.1秒，结合代码核查补缺合成方向；不要因为总字幕写了5′→3′就判正确。
- 观看最后事件：RNA先消失、DNA补入、连接酶最后到达，并确认最终残留橙色引物的教学范围说明。
- A2将前导酶也标作Pol δ（代码pol_lead_lbl）。这缺少正常前导合成主要由Pol ε承担、以及Pol δ可在某些情况下支持前导合成的范围说明；标为额外待人工核查，不武断地说Pol δ绝不可能合成前导链。可参考[重构复制体实验](https://pmc.ncbi.nlm.nih.gov/articles/PMC5222725/)。
- 请生物教师审查后再考虑扩大六节；本轮不建议直接作为已经科学验证的教学成片。

## 科学依据

冈崎片段成熟时引物加工与DNA补缺必须先于可连接切口的封闭；参见[人类冈崎片段成熟的机制研究](https://www.nature.com/articles/s41467-022-34751-2)。本文只用于确定加工和连接步骤边界，不将简化图形冒充真实结构。
''']
(E/'manual_review_checklist.md').write_text(''.join(review),encoding='utf-8')

# Verify animation source provenance, rather than assuming that any .py is model generated.
provenance=[]
for label,call in [('A1_mechanism','deepseek_02'),('A2_mechanism_assets','deepseek_06')]:
 raw=json.loads((E/'logs'/(call+'_response.json')).read_text())['choices'][0]['message']['content']
 source=raw.split('```python',1)[1].split('```',1)[0].strip()+'\n' if '```python' in raw else raw.strip()+'\n'
 actual=(E/'groups'/label/'rendered_code.py').read_text()
 provenance.append({'group':label,'accepted_source_response':call,'exact_animation_source_match':source==actual,'sha256':hashlib.sha256(actual.encode()).hexdigest(),'human_animation_code_edits':False,'infrastructure_changes_disclosed':True})
 assert source==actual,label+' source differs from the saved model output'
(E/'model_provenance.json').write_text(json.dumps(provenance,indent=2))

tests=m['pipeline_tests'];ds=m['token_usage']['deepseek'];report=f'''# Biology-Aware Code2Video V2：Section4 实验报告

**工程链路修复已通过离线测试，A1/A2真实生成并完整渲染；生物机制仍有明确失败项，A3因Qwen超时未完成。** 这是一轮模型替代与机制约束实验，不是原论文模型配置的严格复现。

## 一、工程改动

- 新增src/biology_v2_pipeline.py：对象标识建议校验、construct函数级AST替换、导入/基本安全检查、隔离完整渲染与解码、不可变代码/视频配对版本和原子指针提交。失败候选保留，成功版本不被失败代码污染。
- 新增src/biology_runtime.py：通用组件/SVG加载、稳定对象ID、活动位点绑定与实际逐帧几何轨迹，不包含完整教学动画。
- V2使用该事务入口，旧GridCodeModifier保留作历史复现；旧脚本不会自动获得V2保护。没有庞大改造原Agent，也没有增加RAG或新Agent。
- 历史Section2/4旧行号修改均实际复现缩进错误。历史Section3两版动画重放后，DNA/Helicase包围盒分离从0.0增至2.3125场景单位。
- 最终离线测试{len(tests['tests'])}项全部通过，API=0；8个原创独立SVG加载渲染通过。SVG为CC0示意图，不是真实蛋白质结构。
- 真实运行发现观测器误计旧绑定及VGroup根对象可见性，两项基础设施问题已修正并补测；使用相同模型候选重新渲染，未手工改动画。最后一次纯观测器复测的A1/A2动画源码与MP4哈希均未改变。

## 二、实验完成状态

| 组 | 状态 | 新渲染 | 时长 | 说明 |
|---|---|---|---:|---|
| A0 | 已保留 | 否 | {groups['A0_baseline']['duration_seconds']:.3f}s | 精确复制历史代码与MP4；不调用模型 |
| A1 | 工程门禁通过 | 是 | {groups['A1_mechanism']['duration_seconds']:.3f}s | 3次真实Coder调用，最终接受已保存候选2；机制检查未全通过 |
| A2 | 工程门禁通过 | 是 | {groups['A2_mechanism_assets']['duration_seconds']:.3f}s | 3次真实Coder调用，最终候选3通过；实际使用4类SVG |
| A3 | Critic阶段失败 | 否 | {groups['A3_mechanism_assets_critic']['duration_seconds']:.3f}s（A2复制） | Qwen第一轮180秒超时；无反馈、无候选、无修复视频，第二轮未执行 |

A3初始复制符合实验设计，**但不得称为Critic生成或改进的视频**。API异常没有被转换为“没有布局问题”。收到超时后停止了全部新增模型请求；DeepSeek剩余2次、Qwen剩余1次没有继续使用。

所有可播放视频均通过FFmpeg全片解码，854×480、15帧/秒、无音轨。A1/A2完整场景代码与保存的DeepSeek响应逐字一致，见model_provenance.json。手写极小动画仅用于测试，不算A1/A2成果。

## 三、主要发现

1. 结构化机制与分镜促成了独立模板/新链、逐核苷酸添加、重复引物和分开显示的加工步骤；但输入规格不是严格的科学执行器，不能保证关系都被正确落地。
2. A1把平行排列的新链画在倾斜Y形模板之外；A2采用了更容易分辨的酶SVG和短标签，但把叉简化成了上下水平模板与中部连接，拓扑表达仍不理想。仍应专注Section4，不扩展六节。
3. **A1/A2的后随链补缺均按左→右新增绿色子块，与本图下模板极性不一致，判fail。** 证据在biological_checks.json、nucleotide_observations.json、实际第5事件与源代码。不能只凭字幕“5′→3′”判通过。
4. 本轮无法判断Critic是否改善机制或布局，因为没有得到有效的Qwen反馈；A3与A2哈希一致只是初始复制，并非成功修复。
5. 自动布局指标没有注册文字覆盖，因此标签重叠“0”并不可靠。对照图和人工检查清单仍必要。各项pass/fail/uncertain及依据见manual_review_checklist.md。
6. A1/A2为独立Coder采样，且存在基础设施修正/重放，单样本不能严格分离SVG的因果效应。只报告可见变化，不宣称因果归因已经成立。

## 四、运行成本与工程指标

- DeepSeek：{m['call_counts']['deepseek']}/8次，输入{ds['prompt_tokens']:,}、输出{ds['completion_tokens']:,}，合计{ds['total_tokens']:,}词元。
- Qwen：{m['call_counts']['qwen']}/2次，API超时，未返回词元用量；记录为未知，不能写0。未自动重试。
- Wan：0个任务；默认dry-run没有HTTP、上传或视频生成。官方Workspace和参考图公开HTTPS URL尚未配置，不臆造上传接口或地域。
- 未取得账单，实际金额未知。旧历史调用计数完整保留，旧45上限仅来自旧脚本，本次使用明确授权的独立8/2/1预算。
- 已完成且可核实的完整渲染调用：A1 {groups['A1_mechanism']['verified_full_render_outputs']}/{groups['A1_mechanism']['completed_full_render_attempts']}、A2 {groups['A2_mechanism_assets']['verified_full_render_outputs']}/{groups['A2_mechanism_assets']['completed_full_render_attempts']}；这些包含无API重放，不能冒充初始Coder一次成功率。首次代码两组均未直接通过全部门禁。
- A3候选修复次数0，修复成功率不可计算；正式实验没有失败更新覆盖成功版本，事务拒绝与中断均另存。离线测试证明了旧成功配对在渲染失败时回滚，不能声称已完成一次真实A3修复。
- 每组已记录API与事务耗时之和在metrics.json的measured_active_seconds；暂停、人工检查和中断缺失时间不虚构为精确总耗时。

## 五、产物路径

实验根目录：{E}
'''
for label,row in groups.items():
 report+=f'\n- {label}：`{row["video"]}`；SHA256：`{row["video_sha256"]}`。\n'
report+=f'''
- 对照图：{E}/comparisons/all_groups_by_event.jpg，以及5张同事件对照图。
- 机制规格、统一分镜、旁白：specs/section4_mechanism.json、specs/section4_storyboard_v2.json、narration.md。
- 资产与许可：assets/asset_registry.json及8个SVG；加载测试assets/svg_loading_test.json。
- 真实调用、错误、失败候选与事务：logs/、failure_reasons.json、groups/*/attempts/。
- pipeline_tests.json、metrics.json/csv、model_provenance.json、source_changes.patch记录工程证据。
- Wan脚本tools/run_wan_comparison.py；dry-run见comparisons/wan/dry_run.json，参考帧见comparisons/A2_fork_reference.png。该图拓扑仍需人工确认，不建议直接用于收费对照。

## 六、下一步建议

先继续优化Section4。优先将新链与酶的实际几何关系绑定到模板路径与真实3′末端，而非仅依赖模型声明的锚点；再约束补缺的逐核苷酸方向与最终残留RNA的解释。之后补上所有文本的注册与几何检测。查明Qwen超时原因后，另设明确预算重跑A3；本轮不增加API、不扩展六节、不启动Wan。
'''
(E/'RESULTS.md').write_text(report,encoding='utf-8')

# Add explicit copy status to every A3 overview cell.
p=E/'comparisons/all_groups_by_event.jpg';im=Image.open(p).convert('RGB');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for row in range(5):
 y=row*296+270;draw.rectangle((1440,y,1920,y+26),fill='#202020')
 draw.text((1446,y+3),'A3 = A2 copy; Critic timed out',font=font,fill='white')
im.save(p,quality=94)

# Historical result hashes must remain unchanged.
historical=json.loads((E/'historical_inputs.json').read_text())
for name,expected in historical.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==expected['sha256'],name
# Preserve exact runtime/pipeline sources used in this completed experiment.
for name in ['biology_runtime.py','biology_v2_pipeline.py']:shutil.copy2(REPO/'src'/name,E/'tools'/name)
patch=[]
for name in ['biology_runtime.py','biology_v2_pipeline.py']:
 text=(REPO/'src'/name).read_text()
 patch.extend(difflib.unified_diff([],text.splitlines(True),fromfile='/dev/null',tofile='src/'+name))
(E/'source_changes.patch').write_text(''.join(patch))
inventory={str(p.relative_to(REPO)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
           for p in [REPO/'src/biology_runtime.py',REPO/'src/biology_v2_pipeline.py',*sorted((E/'tools').glob('*.py'))]}
(E/'source_inventory.json').write_text(json.dumps(inventory,indent=2))
env=dict(l.split('=',1) for l in (R/'.env').read_text().splitlines() if l and not l.startswith('#'))
for key in ['DEEPSEEK_API_KEY','DASHSCOPE_API_KEY']:
 secret=env[key].encode()
 assert not any(secret in p.read_bytes() for p in E.rglob('*') if p.is_file() and p.suffix not in ['.mp4','.png','.jpg']), 'Secret literal leaked'
bundle=R/'delivery/Biology_V2_Section4_materials.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 for p in E.iterdir():
  if p.is_file():z.write(p,p.name)
 for folder in ['specs','assets','tools','logs']:
  for p in (E/folder).rglob('*'):
   if p.is_file() and p.suffix not in ['.mp4','.png','.jpg'] and '__pycache__' not in p.parts:z.write(p,str(p.relative_to(E)))
 for label in groups:
  g=E/'groups'/label
  for name in ['generated_code.py','rendered_code.py','status.json','final_group_summary.json','object_visibility.json','nucleotide_observations.json','critic_rounds.json','initial_copy.json','checker_recovery.json']:
   p=g/name
   if p.exists():z.write(p,'groups/'+label+'/'+name)
  for p in (g/'round_1').glob('*'):
   if p.is_file():z.write(p,str(p.relative_to(E)))
  for p in g.glob('*_transaction.json'):z.write(p,str(p.relative_to(E)))
  for attempt in (g/'attempts').glob('*'):
   for name in ['candidate_code.py','stderr.log','stdout.log','failure.json','interruption_record.json']:
    p=attempt/name
    if p.exists():z.write(p,str(p.relative_to(E)))
  if (g/'current').exists():
   version=(g/'current').resolve()
   for name in ['geometry_trace.json','layout_metrics.json']:
    p=version/name
    if p.exists():z.write(p,'groups/'+label+'/verified_'+name)
 for p in (E/'comparisons/wan').glob('*.json'):z.write(p,str(p.relative_to(E)))
print('Final reports, provenance, historical hash and secret checks passed.')
print('MATERIALS',bundle,bundle.stat().st_size)
