# Code2Video + DeepSeek 模型替代实验报告

**结论：DeepSeek 替换可行，真实数学与 DNA 视频均已生成；画面布局和生物机制覆盖仍有明显不足。** 本实验保持原始提示词、Storyboard 和 Manim 逻辑，关闭视觉 Critic 与素材下载；不是原论文模型配置的严格复现。未增加 RAG、知识库或其他 Agent，未用人工 Manim 代码冒充生成结果。

## A. 复现状态

- 服务器：motion-data；项目实际目录 `/root/autodl-tmp/code2biovideo`，兼容用户路径 `/autodl-tmp/code2biovideo`。
- 上游版本：`637509294e936b231d220bb555cf74eeedcb9dfd`，原始提示词文件经 Git 差异检查保持不变。
- 环境：Python 3.11、Manim 0.19.0、OpenAI SDK 1.90.0、FFmpeg 7.1.1；公式使用另装的项目私有 TeX Live 2026。圆形、矩阵公式、网络与密钥隔离测试均通过。
- Provider：标准 OpenAI 兼容接口，模型、Base URL、密钥来自环境变量；请求 `deepseek-flash`，响应也返回此模型名。`/models` 描述为 DeepSeek-V4.1-Flash，未获得可冻结的内部权重版本，不能假定将来同名端点完全不变。
- 首轮默认思考模式造成输出截断，失败记录全部保留；第二轮显式关闭思考模式。格式解析沿用原代码，无额外结构化输出强制模式。
- Critic、IconFinder、完整基准评估均跳过；没有新增配音或字幕功能。

## B. 视频产物

| 产物 | 服务器真实路径 |
|---|---|
| DNA MP4 | `/root/autodl-tmp/code2biovideo/Code2Video/src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells/DNA_replication_in_eukaryotic_cells.mp4` |
| 数学示例 MP4 | `/root/autodl-tmp/code2biovideo/Code2Video/src/CASES/A2_math_deepseek_nonthinking/0-Linear_transformations_and_matrices/Linear_transformations_and_matrices.mp4` |
| DNA 分镜与代码 | `/root/autodl-tmp/code2biovideo/Code2Video/src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells` 下的 outline.json、storyboard.json、section_1.py 至 section_6.py |
| DNA 预览 | `/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_baseline/previews/B2_dna_deepseek_nonthinking/contact_sheet.jpg` |
| 科学内容核对图 | `/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_baseline/previews/B2_dna_deepseek_nonthinking/scientific_evidence.jpg` |
| 原始日志与请求 | `/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_baseline/logs/` |
| 上游修改 | `/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_baseline/upstream.patch` 与 CHANGELOG.md |

DNA：136.266667 秒，854×480，15 帧/秒，H.264，仅视频流；3,617,039 字节。全片解码返回 0，无解码错误；6 个场景时长之和与成片一致。SHA-256：`37c4ac107a742656ffb7f58c24780e896ee6c236c61e85ad88b775456ed82076`。

数学：132.666667 秒，854×480，15 帧/秒；全片解码通过。场景文件和所有失败中间文件保留服务器，交付副本仅包含选定报告、视频、分镜与代码等必要文件。

## C. 技术观察与成本

| 尝试 | 状态 | API 尝试次数 | 总词元 | 壁钟秒数 | 最终场景 |
|---|---|---:|---:|---:|---|
| A_math_deepseek | failed | 3 | 25,642 | 92.611 | 0/6 |
| B_dna_deepseek | failed | 2 | 14,094 | 54.863 | 未进入渲染 |
| A2_math_deepseek_nonthinking | success | 21 | 140,214 | 1155.793 | 6/6 |
| B2_dna_deepseek_nonthinking | success | 9 | 45,059 | 327.107 | 6/6 |

全实验共 **35 次 API 尝试、225,009 词元**，包含首轮截断与环境问题导致的修复开销。接口层重试共 0 次。未获取账单数据，不推算实际金额。

DNA 第二轮输入 18,231、输出 26,828 词元，9 次调用包括 2 次 Planner、6 次初始 Coder、1 次代码修复。最终场景成功率 **6/6（100%）**；初次渲染通过 **5/6（83.3%）**；计入一次修复后的尝试成功率 **6/7（85.7%）**。外层重生成 0 次，代码修复及重渲染 1 次。生成约 326.84 秒，单独重新合并约 0.27 秒，共 327.107 秒，技术检查与人工检查时间不计入。

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
