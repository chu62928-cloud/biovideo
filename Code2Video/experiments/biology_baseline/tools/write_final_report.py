from pathlib import Path
import json,shutil,subprocess,time,hashlib,difflib
R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video';E=REPO/'experiments/biology_baseline'
ds=json.loads((E/'all_results.json').read_text());by={d['label']:d for d in ds}
a=by['A2_math_deepseek_nonthinking'];b=by['B2_dna_deepseek_nonthinking']
total=sum(d['usage']['total_tokens'] for d in ds);calls=sum(d['api_attempts'] for d in ds)
assert a['status']==b['status']=='success'
assert b['video_properties']['decode_returncode']==a['video_properties']['decode_returncode']==0

biology='''# 生物学内容核查：Code2Video + DeepSeek

核查对象为实际 DNA MP4、原始分镜、最终代码与多时点关键帧；未修改生成内容。时间戳均为合并视频全局时间。Correct 仅确认表中限定的表达，不代表整段机制都完整正确。下列未能证实的机制均保留 Needs Human Review。

| 检查项 | 状态 | 证据与边界 |
|---|---|---|
| 双链及碱基互补配对 | Missing / Unclear | 00:07、00:25 可辨认双螺旋简图；全部分镜与代码未明确展示 A–T、C–G，也未给出配对规则。第 5 节仅以颜色矩形表示错配，不能据此认定已讲清碱基互补。 |
| 半保留复制 | Correct（简化终态） | 02:04—02:07 出现两条双链，每条含蓝色 old 与绿色 new；02:06.7 的关键帧及 section_6.py 187—244 行相符。未持续追踪母链分开与两条子链形成全过程；02:09 后统一蓝色削弱了颜色连续性。 |
| 新链沿 5′→3′ 合成 | Correct（文字）；Missing / Unclear（完整动态） | 01:09.5 显示文字与方向箭头。section_4.py 133—145 行确认该箭头；后随链无对应端点标注，模板反向平行性未建立，不能只据静态截图确认两链动态方向正确。Needs Human Review。 |
| 前导链与后随链 | Correct（连续与分段对比）；Missing / Unclear（复制叉耦合） | 01:23.6 显示上方连续绿线、下方短片段，分镜及 section_4.py 178—264 行一致。没有持续运动的复制叉与端点方向共同参照，不能确认后随链生成顺序的完整机制。 |
| 解旋酶与 DNA 聚合酶功能 | Correct（基本功能） | 00:50.6—00:59.3 表现解旋及复制叉，01:09.5—01:23.6 表现聚合酶与新链延长；文字为正确的基础描述。蛋白质为简单几何图形，未展示真实分子结构。 |
| 示意与真实尺度是否区分 | Missing / Unclear | 全片没有比例尺或明确“非真实尺度”说明，也未声称真实尺度，因此不判为明确科学错误。建议人工确认高中生是否可能将位置与运动方式当作真实过程。 |

## 需要进一步人工判断的问题

1. **中等严重程度，01:23.6—01:32.5：引物去除与连接酶边界未讲清。** 橙色 RNA Primer 在展示连接酶封闭后的场景仍存在；section_4.py 97—113 行创建引物，302—335 行用绿线连接可见间隔，没有引物移除、DNA 补缺步骤。画面可能被理解为连接酶直接填补缺失核苷酸。当前定为 Missing / Unclear / Needs Human Review，不能仅凭几何线段长度断言模型声称了错误的催化机制。
2. **中等严重程度，00:07—00:20：“30 亿碱基对”缺少物种与倍性限定。** 主题为一般真核细胞，画面与讲义直接给出这个数字。未说明人类单倍体基因组，也没有区分 S 期复制的 DNA 总量。属于范围限定不足，需教师核对。
3. **中等严重程度，01:48—01:53：“十亿分之一”缺少误差口径。** 该数字紧随聚合酶校对演示出现，未交代是否包含其他修复机制、单位与适用对象，不能据此确认该数字可以单独归因于聚合酶校对。Needs Human Review。
4. **低至中等严重程度，00:40—00:45：许可与起始的简化。** “1x per cycle”可帮助表达防止重复复制，但没有区分已许可起点与实际激活起点，需人工检查是否让学习者误认为每个已许可起点都会被使用。
5. **内容缺项：** 未讲端粒/端粒酶及染色质重新装配；对有限时长科普不自动判错，但使“真核细胞”主题覆盖不完整。没有科学事实核查 Agent 或 Critic 参与本轮核查。

## 参考依据

半保留复制的判据是每个子代双链含一条母链与一条新链，见 [OpenStax：复制基础](https://openstax.org/books/biology-2e/pages/14-3-basics-of-dna-replication)。

核对新链合成方向、引物后续处理、片段连接与真核复制背景时参考 [OpenStax：真核复制](https://openstax.org/books/biology-2e/pages/14-5-dna-replication-in-eukaryotes)。本次仅做来源支持的有限核查，没有进行完整专家审稿；查到的资料未作为生成模型输入。

## 人工观看清单

- 连续观看 01:00.6—01:36.0，确认后随链片段方向、引物与连接酶演示是否可能误导。
- 连续观看 02:01.0—02:16.3，核对母链/新链颜色、图例与最后统一颜色之间的关系。
- 复核所有数量口径与真核细胞特有内容覆盖，再决定是否用于教学。
'''
(E/'BIOLOGY_REVIEW.md').write_text(biology,encoding='utf-8')

issues='''# 问题与证据

## 接口与环境
- 首轮 DeepSeek 默认开启思考模式，数学代码与 DNA 分镜均达到 10000 输出词元并截断。原始 finish_reason=length、usage 与响应保留在 A_math_deepseek / B_dna_deepseek 的 api 目录。显式关闭思考模式后通过结构化分镜测试；未修改提示词或强制 JSON 模式。
- Conda texlive-core 缺少格式文件及宏包，最初数学公式失败并触发多次无效的模型修复。后来补装私有 TeX Live 和 dvisvgm，矩阵冒烟测试成功；所有这些失败仍计入成本。数学运行曾暂停补环境，壁钟耗时不可作为纯模型性能比较。
- 自建日志包装器最初遗漏非渲染命令的转发，导致合并没有执行；已修正并通过原生 merge_videos 重新合并，两次合并失败日志和修改前指标保留。该问题属于实验驱动器，不归因于上游或模型。
- 数学场景 2 的原始调用被记为超时，但已留下完整场景文件；环境复测发现该文件，经最终解码后纳入成片。因此数学最终 6/6 与渲染进程正常返回 5/12 并不矛盾，不能将后者冒充完整模型成功率。

## 模型生成代码
- DNA 第 4 节首次渲染失败，原因 `Mobject.__init__() got an unexpected keyword argument 'stroke_dash'`。原生 ScopeRefine 调用 DeepSeek 将 Line/stroke_dash 改为 DashedLine/dash_length，第二次渲染成功。精确差异见 logs/B2_dna_deepseek_nonthinking/section_4_agent_fix.diff。
- DNA 代码来源审计见 code_provenance.json：其余 5 节与原始响应经上游基类替换后的文本完全相同。第 4 节仅出现上述模型修复差异，没有人工写代码替代结果。

## 可见画面问题
| 时间戳 | 问题 | 证据 | 初步严重程度 |
|---|---|---|---|
| 00:07.1—00:08.5 | 30 亿碱基对的数字标签被右边界截断 | contact_sheet 第 1 行、early_preview；section_1 动画定位 | 中 |
| 00:18.5—00:20.0 | Speed / Accuracy 文本重叠 | contact_sheet 第 1 行第 2 格 | 中 |
| 00:40.6—00:45.3 | 多个起点下的计数标签过密，字很小 | contact_sheet 第 2 行 | 低至中 |
| 00:59.3 | Replication Fork 与 Origin 标注拥挤 | contact_sheet 第 3 行第 3 格 | 中 |
| 01:09.5—01:32.5 | Primase、RNA Primer、DNA Pol 与片段标签重叠；部分文字倾斜或难辨 | scientific_evidence.jpg、contact_sheet 第 4 行 | 中至高 |
| 02:01.6—02:02.6、02:07.8—02:08.4 | 自动黑屏检测报警，但关键帧仍有标题与讲义 | blackdetect.log；121.9 / 127.9 / 128.2 秒证据图 | 属于内容稀疏的过渡，非全帧黑屏；低 |

DNA 成片仅 136.27 秒，原始 Planner 提示要求约 5 分钟，说明时长约束未落地。全片没有音轨、配音或独立字幕轨；左侧讲义是烧录文字。不同章节保持黑底白字和右侧几何动画的大体风格，但蛋白质主要为圆、环、矩形，无法据此辨识真实分子结构。

## 生物学边界
科学内容的确认与待审项见 BIOLOGY_REVIEW.md。尤其缺少明确 A–T/C–G 配对、后随链方向参照与引物去除。未把这些缺失或疑点直接写成已证实的科学错误。
'''
(E/'ISSUES.md').write_text(issues,encoding='utf-8')

rows=[]
for label in ['A_math_deepseek','B_dna_deepseek','A2_math_deepseek_nonthinking','B2_dna_deepseek_nonthinking']:
 d=by[label];rate=f"{d.get('successful_sections',0)}/{d.get('sections','—')}" if d.get('sections') else '未进入渲染'
 rows.append(f"| {label} | {d['status']} | {d['api_attempts']} | {d['usage']['total_tokens']:,} | {d['elapsed_seconds']:.3f} | {rate} |")
report=f'''# Code2Video + DeepSeek 模型替代实验报告

**结论：DeepSeek 替换可行，真实数学与 DNA 视频均已生成；画面布局和生物机制覆盖仍有明显不足。** 本实验保持原始提示词、Storyboard 和 Manim 逻辑，关闭视觉 Critic 与素材下载；不是原论文模型配置的严格复现。未增加 RAG、知识库或其他 Agent，未用人工 Manim 代码冒充生成结果。

## A. 复现状态

- 服务器：motion-data；项目实际目录 `{R}`，兼容用户路径 `/autodl-tmp/code2biovideo`。
- 上游版本：`637509294e936b231d220bb555cf74eeedcb9dfd`，原始提示词文件经 Git 差异检查保持不变。
- 环境：Python 3.11、Manim 0.19.0、OpenAI SDK 1.90.0、FFmpeg 7.1.1；公式使用另装的项目私有 TeX Live 2026。圆形、矩阵公式、网络与密钥隔离测试均通过。
- Provider：标准 OpenAI 兼容接口，模型、Base URL、密钥来自环境变量；请求 `deepseek-flash`，响应也返回此模型名。`/models` 描述为 DeepSeek-V4.1-Flash，未获得可冻结的内部权重版本，不能假定将来同名端点完全不变。
- 首轮默认思考模式造成输出截断，失败记录全部保留；第二轮显式关闭思考模式。格式解析沿用原代码，无额外结构化输出强制模式。
- Critic、IconFinder、完整基准评估均跳过；没有新增配音或字幕功能。

## B. 视频产物

| 产物 | 服务器真实路径 |
|---|---|
| DNA MP4 | `{b['video']}` |
| 数学示例 MP4 | `{a['video']}` |
| DNA 分镜与代码 | `{b['output_dir']}` 下的 outline.json、storyboard.json、section_1.py 至 section_6.py |
| DNA 预览 | `{b['preview']}` |
| 科学内容核对图 | `{E}/previews/B2_dna_deepseek_nonthinking/scientific_evidence.jpg` |
| 原始日志与请求 | `{E}/logs/` |
| 上游修改 | `{E}/upstream.patch` 与 CHANGELOG.md |

DNA：136.266667 秒，854×480，15 帧/秒，H.264，仅视频流；3,617,039 字节。全片解码返回 0，无解码错误；6 个场景时长之和与成片一致。SHA-256：`{b['video_properties']['sha256']}`。

数学：{a['video_properties']['duration_seconds']:.6f} 秒，854×480，15 帧/秒；全片解码通过。场景文件和所有失败中间文件保留服务器，交付副本仅包含选定报告、视频、分镜与代码等必要文件。

## C. 技术观察与成本

| 尝试 | 状态 | API 尝试次数 | 总词元 | 壁钟秒数 | 最终场景 |
|---|---|---:|---:|---:|---|
{chr(10).join(rows)}

全实验共 **{calls} 次 API 尝试、{total:,} 词元**，包含首轮截断与环境问题导致的修复开销。接口层重试共 0 次。未获取账单数据，不推算实际金额。

DNA 第二轮输入 {b['usage']['prompt_tokens']:,}、输出 {b['usage']['completion_tokens']:,} 词元，9 次调用包括 2 次 Planner、6 次初始 Coder、1 次代码修复。最终场景成功率 **6/6（100%）**；初次渲染通过 **5/6（83.3%）**；计入一次修复后的尝试成功率 **6/7（85.7%）**。外层重生成 0 次，代码修复及重渲染 1 次。生成约 326.84 秒，单独重新合并约 0.27 秒，共 {b['elapsed_seconds']:.3f} 秒，技术检查与人工检查时间不计入。

数学第二轮最终场景 6/6，但经历环境缺失、暂停、一次超时与恢复，1155.793 秒为主题壁钟及恢复用时之和，包含环境修复暂停，不适合作为干净的模型耗时对照。渲染进程正常返回成功 5/12，另一个场景由超时调用留下的文件恢复并验证；完整记录见 ISSUES.md。

Planner 的六节 DNA 教学顺序基本连贯，原生生成的受众是高中 10—12 年级。Coder 可以生成并执行数百行 Manim 代码；第 4 节的参数错误可被原生 ScopeRefine 修复。Critic 未运行，无法比较视觉反馈修复效果。单个主题、一次成功重试轮次不足以估计一般成功率。

原始系统仅把约 5 分钟作为提示词要求，最终 DNA 视频约 2 分 16 秒，未形成实际时长保证。可渲染也不等于科学内容完整或画面可直接教学。

## D. 生物领域问题

- 明确缺项：没有 A–T/C–G 配对规则。半保留复制在 02:06.7 有一旧一新的图例和双链终态，可确认这一简化表达。
- 01:09.5 有正确的 5′→3′ 文字和箭头，但后随链模板方向与复制叉耦合未明确，标为 Needs Human Review。
- 01:23.6—01:32.5 未展示引物去除或 DNA 补缺，连接酶画面可能引起误解；保留为证据不足或机制缺项，未直接判定为确定科学错误。
- 00:07—00:20 的“30 亿”缺少物种与倍性限定；01:48—01:53 的“十亿分之一”缺少误差口径。
- 文字裁切、重叠使若干关键标签难以阅读。逐项状态、依据与严重程度见 BIOLOGY_REVIEW.md 和 ISSUES.md。

核查依据见 [半保留复制基础](https://openstax.org/books/biology-2e/pages/14-3-basics-of-dna-replication)、[真核复制](https://openstax.org/books/biology-2e/pages/14-5-dna-replication-in-eukaryotes)。这些资料仅用于生成后的有限核查，没有注入模型。

## E. 下一步建议（本轮未实现）

1. 先针对现有生成结果完善文字边界、标签碰撞和字号检查，再评估是否恢复原生视觉 Critic；保留与当前视频的独立对照。
2. 为生物动画定义可人工核验的表达清单，例如链方向、互补配对、引物去除、连接酶作用边界；先由教师检查本轮片段，再决定下一阶段是否需要知识约束。
3. 将生成、渲染与环境预检分开，保留阶段用量和内容来源审计；使用多个独立运行评估成功率与时长偏差，避免把这次单样本成功当成稳定能力。

本轮到此停止模型调用。请先观看视频，再决定改进方向。
'''
(E/'RESULTS.md').write_text(report,encoding='utf-8')

p=E/'SETUP.md';s=p.read_text().replace('TeX Live 2026。安装来源','Conda texlive-core 另见下方修复。安装来源')
s+='''
## 私有公式环境修复与最终命令
Conda texlive-core 未包含完整运行所需格式/宏包，最终改用 `/autodl-tmp/code2biovideo/texlive` 的项目私有 TeX Live 2026，基础方案 scheme-basic，再安装 standalone、preview、amsmath、amsfonts、babel-english、xcolor、dvisvgm。原始 profile 为项目根目录 texlive.profile，安装日志在 logs/texlive-*.log。

环境修复后执行 recover_math_environment.py 复测现有代码；finalize_dna_merge.py 只重新执行上游合并方法。collect_results.py 解码检查、提取关键帧、生成 metrics.csv。辅助脚本副本保存在本实验 tools/，运行时项目根目录版本为准。

DeepSeek 新增 DEEPSEEK_THINKING=disabled。默认思考模式首轮失败与关闭后结果分别保留，不混为同一配置。45 次调用上限通过现有审计累计检查；本实验实际 35 次。已有结果应冻结，后续运行使用新标签与独立目录，禁止覆盖本轮记录。
''';p.write_text(s,encoding='utf-8')
p=E/'CHANGELOG.md';p.write_text(p.read_text()+'''
9. 实验驱动器日志包装遗漏 FFmpeg 转发已修复；保留修改前指标与错误日志。通过原生 merge_videos 重新合并，未修改视频内容或调用模型。
10. 分阶段恢复脚本只复测/重新合并现有 Agent 输出。第 4 节模型自动修复差异已独立保存；代码来源逐节审计完成。
''',encoding='utf-8')
p=E/'RUN_LOG.md';p.write_text(p.read_text()+f'''

## 最终核验
数学恢复 6/6，DNA 6/6；均经 FFmpeg 全片解码。汇总共 {calls} 次请求、{total} 词元，接口重试 0。
DNA 内容已与分镜、代码、多时间帧交叉核对；其中涉及复杂动态的问题保留 Needs Human Review。黑屏检测两段报警经画面检查属于稀疏过渡，仍有标题和讲义，未判为完整黑屏。
已停止进一步模型调用。最终命令：finalize_dna_merge.py → recover_math_environment.py → collect_results.py → write_final_report.py。所有命令在服务器独立环境中运行。
''',encoding='utf-8')

tools=E/'tools'
for name in ['run_deepseek_experiment.py','sandbox_exec.py','collect_results.py','recover_math_environment.py','finalize_dna_merge.py','write_final_report.py']:
 if (R/name).exists():shutil.copy2(R/name,tools/name)
with (E/'upstream.patch').open('w') as f:subprocess.run(['git','-C',str(REPO),'diff','--','src'],stdout=f,check=True)
print('Final report written',E/'RESULTS.md')
