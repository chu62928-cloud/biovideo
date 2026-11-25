# Biology-Aware Code2Video V3 实验报告
日期：2026-11-24（北京时间）。

## 结论
已实现并真实运行单一BiologyExpertAgent MVP：通用证据知识构建、分阶段审核、实际机制检查、最小代码返工、完整渲染与科学门禁回滚均接通。
本次方向目标修正通过，但最终科学审核为REVISE；未发布科学批准版视频。V1/V2共2451个冻结输入文件哈希全部保持不变。
这是Code2Video + DeepSeek + Qwen的模型替代实验，不是原论文模型配置的严格复现。

## 1. 架构与调用关系
主智能体BiologyExpertAgent提供prepare_topic、review、plan_repair、verify_revision、run_gate。一个Agent下挂12个工具：主题分析、资料检索、指定来源获取、知识构建、精确原文补充、支持摘录核验、事实语义核验、机制验证、阶段产物审核、视频科学审核、返工规划、候选修复经验管理。
选择策略是受状态和观察结果约束的反应式策略，不是无边界的LLM自主命令执行器。没有新增多Agent。模型负责证据综合/科学判断和Coder；程序控制白名单、预算、状态、版本和回滚。
主关系：证据缺口→检索/核验；真实运动可疑→机制验证；事实已知但画面含义不明→视频审核；已定位实现错误→结构化返工任务→原DeepSeek Coder→原V2完整渲染器→实际轨迹→重新科学审核。

## 2. 复用与新增
直接复用BiologyScene及对象/事件/绑定/采样，原DeepSeek和Qwen视频接口、8个SVG和V2 TransactionRenderer。没有重写事务渲染器，没有改动原agent.py/gpt_request.py/api_config.json/run_agent_single.sh。
新增src/biology_expert/包：Schema、内容哈希依赖图、统一审核、知识/证据工具、限额网关、局部AST范围约束、候选技能、命令行。Qwen截断诊断后新增仅V3使用的结构化接口适配器，保留原服务地址/密钥/模型/完整视频。

## 3. 自主决策证据
实际日志位于state/events.jsonl，简表位于traces/autonomy_summary.json。既有离线模拟分支也有真实工具调用，二者明确区分。
- evidence_retriever：Scientific evidence is missing; retrieve before making claims.
- evidence_fetch：The first pack has polymerase roles but lacks the actual synthesis-direction/antiparallel rules.
- fact_verifier：Conflicting or unsupported scientific statements need source entailment/scope checking.
- mechanism_validator：Motion claims require actual event/geometry evidence before a model judgment.
- video_reviewer：Facts are available but rendered scientific meaning is ambiguous; inspect complete video.
- repair_planner：Observed execution violates an evidence-backed rule; repair its earliest implementation source.

并非对所有输入运行同一六步流程：SCRIPT直接依据知识做文本审查；ANIMATION_CODE使用实际轨迹；有画面歧义才进入完整视频科学审核；证据不足会补检索；已定位错误才生成返工任务。每步记录目标、白名单、选择、简短理由、真实输入/输出、终止原因，不交付内部思考文本。

## 4. 科学知识包

### dna_replication
动态构建16条事实，其中15条满足当前证据与语义核验，未核实/冲突项：['F8']。VERIFIED只表示当前范围与来源核验，不等于跨物种无条件成立或专家共识。
- [The Initiation of Eukaryotic DNA Replication.](https://pubmed.ncbi.nlm.nih.gov/35320688/)。
- [Eukaryotic DNA Replication Fork.](https://pubmed.ncbi.nlm.nih.gov/28301743/)。
- [14.5 DNA Replication in Eukaryotes - Biology 2e | OpenStax](https://openstax.org/books/biology-2e/pages/14-5-dna-replication-in-eukaryotes)。
- [9.2 DNA Replication - Concepts of Biology | OpenStax](https://openstax.org/books/concepts-biology/pages/9-2-dna-replication)。
- [14.2 DNA Structure and Sequencing - Biology 2e | OpenStax](https://openstax.org/books/biology-2e/pages/14-2-dna-structure-and-sequencing)。

### eukaryotic_mitosis
动态构建8条事实，其中8条满足当前证据与语义核验，未核实/冲突项：[]。VERIFIED只表示当前范围与来源核验，不等于跨物种无条件成立或专家共识。
- [10.2 The Cell Cycle - Biology 2e | OpenStax](https://openstax.org/books/biology-2e/pages/10-2-the-cell-cycle)。
- [6.2 The Cell Cycle - Concepts of Biology | OpenStax](https://openstax.org/books/concepts-biology/pages/6-2-the-cell-cycle)。
- [Mitosis.](https://pubmed.ncbi.nlm.nih.gov/27587616/)。
- [Spindle scaling mechanisms.](https://pubmed.ncbi.nlm.nih.gov/32501481/)。

每条事实关联实际获取的证据ID、标题、URL、可定位摘录/段落、访问时间、正文哈希。相同知识构建器用于两个主题，没有预置mitosis facts.json。
第一轮DNA教材发现有大小写匹配缺陷，导致仅取到综述、缺乏合成方向原始依据。最初检出记录保留，但不能作为已充分证据支持的结果。修正后真实补检索教材并独立核验，最后机制检查绑定具体方向事实，而非泛泛聚合酶角色。
HTML初次被错误按Latin1解码，造成有丝分裂摘录中的破折号乱码，门禁拒绝了原本有依据的事实。正确UTF8重新获取并验证全文哈希后，复用已保存的独立语义判断和脚本模型响应进行再校验；没有声称这是新的模型推理。
NCBI Bookshelf的HTTP200验证码页被标为UNVERIFIED。多页OpenStax属于一个出版社，不能当成多个独立来源。

## 5. 测试结果
- 离线测试最终28/28通过，真实API0；包括Schema、错误不放行、内容哈希依赖失效、缓存、不同工具分支、白名单/预算、持久两次返工上限、真实完整渲染后的科学回滚、未知引用、缩进解析、来源编码及用户明确增额不重置历史。
- Test A1：历史V2 A2的补缺DNA首次出现x为2.0917→2.2750→2.4583；结合下模板端点5′左/3′右、RNA引物和新链3′文字位置，测得相对模板读取方向投影为负，定位event_5_maturation与fill_dna_00..02。返工目标是核苷酸实际出现顺序，不是箭头或标签。
- Test A2：轨迹侧输出UNCERTAIN并要求视频科学审核；完整视频审核指出中央蓝色空心梯状体与两条模板不汇合，可能被读作额外DNA，且合成画在未解旋双链所占区域。属于机制/身份表达问题，不是简单移动图标。
- Test A3：注册酶与锚点距离及酶与实际新增核苷酸的接近性均检查；本样本没有明显距离超限。固定锚点本身可能错、身份标签可能混淆，故几何通过不能证明化学作用正确。
- Test C：正常脚本1例PASS、错误脚本1例REVISE。正常样本误报0/1；注错样本检出4/4：复制被放到后期、同源染色体配对/必需交换、错误的后期分离对象、一次有丝分裂产生四个单倍体核。样本极小，不作为泛化准确率结论。
- 有丝分裂初次ERROR及纠正后的保存响应重校验结果都保留；不是把错误无条件改为PASS。

## 6. 真实返工闭环
两次DeepSeek生成均返回带额外缩进/初始化语句的局部代码，最初被AST格式门禁拒绝。候选与异常完整保留。规范化解析后，只提取第二次响应本来生成的for循环，未手写任何目标动画。
抽象语法树比较证实只有目标补缺循环变化，其余模块、函数、事件、SVG和分镜不变。没有第三次Coder生成。
候选经完整Manim渲染和全视频解码，真实核苷酸首次出现x改为2.4583→2.2750→2.0917，局部方向检查PASS，聚合酶也随新增核苷酸移动。
科学审核首次响应被9,000输出词元截断，其中思考占5,664；finish_reason=length，JSON未闭合。该次费用用量仍计入，未记成零。
用户明确增加Qwen2次额度后，先保存原因核查，再以总输出12,000、思考预算4,096、JSON模式及最多3个主要问题重试同一完整视频。只用一次即取得有效JSON，耗时44.495秒，总词元38,796，方向PASS、整节REVISE。
剩余三项：复制叉/额外DNA拓扑、前导链聚合酶亚型呈现、连接酶所封位置并非真实相邻切口。Polδ不是“绝不能参与前导链”；这里的问题是未加说明地用于常规前导链教学模型。模型将亚型问题归为SCRIPT，但当前分镜未指定该标签，因此单独记录根因归属待核实，不能盲目要求上游重写。
最终科学提交0/1完整渲染候选；原成功代码/视频配对保持，APPROVED未生成。局部方向修正成功与整节科学失败分别记录。候选MP4供诊断，不能称为已批准教学成片。

## 7. 模型用量与预算
- deepseek：8次请求，输入53363、输出8914、合计62277词元；接口累计40.96秒；SDK自动重试0。
- qwen：3次请求，输入104367、输出19046、合计123413词元；接口累计226.42秒；SDK自动重试0。

已知总词元185690。DeepSeek8/8；Qwen原上限2+用户新增2=4，实际3，尚余1，不为用满额度发请求。真实账单不可取得，不将价目估算冒充账单金额。Wan/Seedance0次。

## 8. 输出路径
代码：/autodl-tmp/code2biovideo/Code2Video/src/biology_expert
实验根目录：/autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v3
真实修复前视频：/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/groups/A2_mechanism_assets/versions/group_visibility_observer_replay/video.mp4
修复候选视频（未通过最终科学门禁）：/autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v3/outputs/REP-dd947104c24f/render/attempts/scientific_attempt_2_format_replay/media/videos/rendered_code/480p15/Section4Scene.mp4
实际代码：/autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v3/outputs/REP-dd947104c24f/render/attempts/scientific_attempt_2_format_replay/rendered_code.py
实际轨迹：/autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v3/outputs/REP-dd947104c24f/render/attempts/scientific_attempt_2_format_replay/geometry_trace.json
完整审核：reviews/；返工任务：repair_tasks/；模型和网络账本：logs/；工具日志：state/events.jsonl；指标：metrics.json。
每次审核有review_id、输入内容哈希，每次返工有repair_id，候选实际代码与MP4另有SHA-256配对清单。

## 9. 局限与下一步
- 一个DNA局部事件和一组有丝分裂文本，不支持普遍性能结论。
- 来源检索当前是有限教材目录排名+真实PubMed检索，可接受白名单来源；不是覆盖全部生物主题的完整检索系统。
- 语义核验与文本生成使用同一模型供应商的独立调用，不能视为独立专家确认。物种、阶段和来源本身的措辞问题仍需复核。
- 机制适配器目前针对V2的平面DNA场景，依据静态代码极性文字与实际轨迹；没有通用三维拓扑/化学键验证，约0.2秒采样可能漏掉更快事件。
- 上游脚本/角色/素材/分镜审核接口和模拟返工路由已实现，尚未把所有上游生成器实际接通；当前只真实接通一个代码事件返工。
- 候选修复经验自动保存，但没有批准正式技能，也不会自动写入正式科学规则库。
- 可继续与Code2Video集成，但应先为复制叉拓扑、切口邻接、角色亚型建立可测验收，再接通上游返工；目前不宜自动扩展整部六节视频或自动发布。
