# 问题与证据

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
