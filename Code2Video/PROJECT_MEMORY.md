# 项目记忆

## Last verified
2026-11-23，北京时间；SSH motion-data。最近完成Biology-Aware Code2Video V2 Section4，实际状态以报告/清单为准。

## Objective
当前V3：一个BiologyExpertAgent、多工具、通用证据知识包、科学审核与受预算/状态机约束的最小返工闭环。只修一个Section事件，不重跑六节。V1/V2冻结。用户2026-11-24追加Qwen2次额度，须先诊断再重试；已执行1次有效重试。

## Current state
VERIFIED：V3 MVP已实现并完成实验；28项离线测试通过。DNA方向候选实际渲染/解码及方向检查通过，完整科学视频复核REVISE，事务保持历史配对，无APPROVED。有丝分裂知识包动态构建，正常脚本PASS、4项注错均检出；初始编码/格式失败完整保留。详见experiments/biology_expert_v3/RESULTS.md和metrics.json。

## Verified results and evidence
- 上游commit637509294e936b231d220bb555cf74eeedcb9dfd。
- V2路径experiments/biology_v2_section4/。pipeline_tests.json最终10/10通过、API0；历史Section3真实重放分离间距0.0→2.3125；8个原创独立SVG加载渲染通过。
- A0精确复制35.4秒；A1真实DeepSeek候选2通过工程门禁，26.866667秒；A2候选3通过，33.466667秒；全部可解码854x480/15FPS/无音轨。
- A3精确复制成功A2作为初始对照，但Qwen第1轮180秒超时。没有有效反馈、候选或新渲染，第二轮未运行；A3/video.mp4只是明确标注的初始复制，不是Critic改进。
- 新独立预算DeepSeek8/Qwen2/Wan1默认禁用；实际DeepSeek6次，输入62468/输出38899/合计101367词元；Qwen1次超时用量未知；Wan0，dry-run无HTTP/上传/视频任务。
- 原始A1/A2完整动画源代码分别与deepseek_02和deepseek_06响应逐字一致。基础设施观测器修正后无API重放，未手工改写动画；最终观测器复测的MP4与代码哈希均不变。
- 生物检查并未全部通过：两组下模板补缺DNA都向右出现，与该图极性约定不一致；A1新链与倾斜Y模板关系弱；A2叉拓扑仍不够清楚。建议继续Section4，暂不扩展六节。
- 文本未注册到几何监测器，标签重叠0不等于全部布局无问题。见manual_review_checklist.md及biological_checks.json。

## Decisions and invariants
保留所有旧历史与输入哈希，V2历史清单已逐一核验。仅成功完整渲染/解码/门禁才原子发布配对代码和视频；未知对象建议拒绝，AST只替换construct，禁止按视觉模型行号改任意代码。候选与成功视频代码区分。
src/biology_v2_pipeline.py和src/biology_runtime.py是V2入口；旧GridCodeModifier保留用于历史复现，旧脚本不自动获得V2事务保护。未增加新的完整动画手写代码作为Agent成果。
密钥在仓库外项目.env（600），不进入报告/代码/日志/交付包。普通UID62001、Landlock/seccomp禁网/限制文件，180秒渲染超时及资源限制。Wan必须ENABLE_WAN=1才允许任务。
旧45上限仅旧实验脚本，用户本次已授权独立8/2/1预算，不重置历史。API失败后停止新增请求，不能因未用满预算而继续请求。

## Important files and paths
实际项目/root/autodl-tmp/code2biovideo，兼容路径/autodl-tmp/code2biovideo。仓库Code2Video/，环境env/，TeX texlive/。
V2报告experiments/biology_v2_section4/RESULTS.md，metrics.json/csv、pipeline_tests.json、model_provenance.json、source_changes.patch、source_inventory.json、historical_inputs.json。
各组groups/*/generated_code.py为初始模型产物；rendered_code.py/video.mp4指向同一成功版本。A3 status.json明确Critic失败，即使存在A2复制的可播放视频。
机制specs/section4_mechanism.json，分镜specs/section4_storyboard_v2.json，8个SVG与asset_registry.json，comparisons按事件对齐。
过去基线仍在biology_baseline/与qwen4_critic/，原版完整DNA成片仍保留。

## External systems and background jobs
VERIFIED：两轮续跑脚本与打包脚本均结束，没有后台任务。原始Qwen180秒超时仍保留作历史，用量未知；随后重试和此次第二轮评价均成功。Wan继续禁用且未调用。本地两轮交付MP4的SHA-256已与服务器一致。

## Immediate continuation
本次V3已完成，无后台运行任务。先读experiments/biology_expert_v3/RESULTS.md、metrics.json、reviews/video/final_retry_review.json。若后续继续，优先处理真实复制叉拓扑与缺口/切口几何；聚合酶亚型根因不能仅信模型归为脚本。候选未批准，不自动发布整片。DeepSeek8/8；Qwen已用3/4（用户额外2中用1），保留账本，不擅自重置。原Qwen输出截断已经确认并通过V3专用JSON/思考预算适配恢复，不能再说接口不可用。

## Blockers and unknowns
当前交付无阻塞，真实两轮视频已完成。最终视频仍有标签压线、端点标识/复制叉拓扑与连接酶接触待复核；工程门禁不能证明科学教学质量。第一次Qwen超时原因与计费用量未知。最新用量与已完成状态见两轮续跑报告，旧A3超时条目仅作历史。

## Update history
2026-11-23：DeepSeek替代基线完成；Qwen Critic旧实验出现按行修复失败并在旧45上限停止。
2026-11-23：V2修复事务/对象接口，10项回归，机制与8SVG，A0/A1/A2产物及A3超时失败记录、Wan dry-run、完整评价和交付均已保存。

## 用户要求的Qwen单次重试
原V2超时后用户明确要求再试一次。保持同一模型/提示词/完整视频/180秒超时，独立日志位于 /root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/logs/qwen_retry_20261123_105828；结果见retry_report.json。未覆盖旧账本、未重渲染或修改动画。

## 用户授权的Qwen同输入重试最新结果
VERIFIED：2026-11-23同模型/URL/完整视频/提示词/10000输出上限/180秒超时重试成功，耗时131.618秒。请求ID 15e2fd60-6ab8-94d1-92c9-762aa1636317。输入20783、输出4878、合计25661词元（含思考3415）。
有效JSON含3个结构化对象问题，ID均真实存在：dna_polymerase_leading、dna_polymerase_lagging、new_leading_strand。尚未修改代码/视频，没有把反馈本身算作修复成功。
日志experiments/biology_v2_section4/logs/qwen_retry_20261123_105828/diagnostic_report.json与structured_feedback.json。
Qwen正式初次1+用户重试1=2次，原2次上限已用满；原超时用量未知，25661仅重试已知用量，不是完整总成本。DeepSeek仍6/8。
若用户要求继续，优先复用这份已验证反馈进行AST事务修复，避免再次调用Qwen。原正式RESULTS/metrics未被改写为成功，followup_qwen_status.json单独记录进展。上次超时原因尚未知，不能再把Qwen说成不可用。

## 2026-11-23 两轮Critic续跑已完成
第一轮复用上次Qwen成功反馈，DeepSeek真实修复并全渲染；第二轮将新第一轮视频送Qwen，再经DeepSeek修复全渲染。新增DeepSeek2/Qwen1，API重试0，新增61244词元。V2累计DeepSeek8次137532词元；Qwen3次已知50740词元，首次超时用量未知。第二次Coder错误返回完整模块，保留格式拒绝，只自动提取生成函数，非目标AST一致，无手写动画。两次渲染2/2成功；两轮均33.466667秒，最终视频SHA b67043cfabdb71d27aebdd5e31cd73644117419ebeecfb68d97f82bfe7b3cb0a。修复补缺方向已通过实际轨迹，布局仍有缺陷；没有第三次Critic对最终成片背书。续跑目录及REPORT_zh.md为最新证据，旧正式A3超时报告保留作历史，不能当作当前无视频。

## 2026-11-24 V3交付
src/biology_expert/与experiments/biology_expert_v3/：单一有界反应式Agent，12工具，证据检索/动态知识包/阶段审核/真实机制检查/最小AST返工/完整渲染/科学回滚/候选技能/CLI。历史冻结2451文件哈希无变化。DeepSeek8次62277词元，Qwen3次123413词元，合计185690；其中一次Qwen输出截断仍有已知44275词元。新增授权重试1次有效，方向PASS但整节REVISE，无科学批准视频。两次Coder生成仅第二次保存响应作格式重放，无手写动画。完整报告记录局限与失败。所有结果服务器保留，只下载交付件。

## 2026-11-24 V4已执行
通用src/scientific_scene实现，27/27离线测试；A1/A2实际生成渲染，A3两轮真实返工未获联合批准并回滚，B1实际13秒视频科学REVISE。DeepSeek10/10、Qwen3/3已用满，不追加调用。报告experiments/scientific_scene_v4/RESULTS.md，metrics.json和完整模型账本logs/model_calls.json。所有历史冻结文件哈希核查见validation/frozen_input_verification.json。无实验后台任务。下一步先读报告与validation/dna_repaired_ir_review.json，复核错误极性意见，修连续链关系和mitosis逐时刻微管连接；不自动扩展六节。

## 2026-11-24 V4.1
VERIFIED：V4.1阶段已执行，25项离线测试通过。极性误报限定裁决、真实IR/过程两次模型补丁、PathGeometry消楔形、连续叉推进、逐帧动粒连接与字幕修复。用户授权追加额度后DNA B4与M1均SCIENCE_APPROVED；新哈希有匹配审核，DNA剩余引物意见经802次端点观测与负对照裁决为误报，原始意见保留。当前用量见metrics.json及持久预算授权。历史V4实验目录哈希变化0，源码改动记录diagnostics/frozen_verification.json。完整报告experiments/scientific_scene_v4_1/RESULTS.md。下一步冻结approved_manifest.json与视频哈希，设计小规模公平对照和教师复核；本轮不启动Wan/Seedance，不重跑六节。

## 2026-11-25 V4.3真实实验续跑检查点
VERIFIED：worktree /autodl-tmp/code2biovideo/biovideo-v4.3。新8秒有丝分裂完整MP4、真实轨迹与关键帧已生成，sample_video.mp4 SHA256 c035449dc554645baf35a11b7855b8d0a85253ea2d06af39bf780bdde32e9f2d。模型独立审核PASS；运行1完整PASS/3部分验证；两类真实轨迹注错检出。Qwen完整视频科学PASS/视觉REVISE称重影，9张实际PNG审核双PASS；保留分歧，不联合批准。DNA/囊泡模型REVISE，整体REVIEW_INCOMPLETE。47测试通过，历史冻结文件变化0。真实DeepSeek30/Qwen4，输入216988输出93467词元，两次截断失败保留。用户最新取消建议次数上限，但不使用Wan/Seedance、不重置账本。细节以experiments/biology_expert_v4_3/{README.md,evaluation.json,manifest.json}为准。
下一步：先处理typed_planner程序集父角色绑定代理问题与前置条件实际门禁，补几何观测；DNA来源存在RNaseH/FEN1表述歧义、未见囊泡主题缺马达证据。禁止把样本帧PASS或一条窄约束PASS当作全实验成功。当前无必要付费后台任务。
