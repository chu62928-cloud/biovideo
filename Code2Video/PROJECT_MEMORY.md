# 项目记忆

## Last verified
2026-11-25，北京时间；SSH motion-data，当前V4.3.1 worktree。最新状态以本文件末尾V4.3.1条目与实验报告为准。

## Objective
V4.3.2验证冻结后科学智能体能否自主定位缺口、检索、局部修复、独立复核，无主题专用补丁。目标未完成。

## Current state
VERIFIED 2026-11-26：独立worktree biovideo-v4.3.2。93测试通过，正式冻结科学源码不变、历史文件不变。真实囊泡局部补丁完成Schema/精确引文/状态可达性PASS，独立科学REVISE后回滚。DeepSeek第三次补丁请求402 Insufficient Balance；DNA与有丝分裂后续新审核被网关停止。SCIENCE_PARTIALLY_VALIDATED，不能宣布稳定版。视觉规范与Wan文生dry-run已完成，付费视频0；Seedance未配置。

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

## 2026-11-25 V4.3.1 / VP0已执行
VERIFIED：独立worktree /autodl-tmp/code2biovideo/biovideo-v4.3.1，基线aaee5ca。用户明确选择Wan3并授权真实试调用，Seedance0。Wan首尾图经DeepSeek计划和开发者锚点准备、独立Qwen科学/视觉PASS；真实POST一次返回403 AccessDenied.Unpurchased，request_id223c94c4-9970-9519-ac3a-3d9e87c963f8，无task_id、无Wan视频，禁止自动重提交。现有密钥有效但模型权限未就绪；需账户控制台核对开通/业务空间/北京地域。
通用可靠性审核/因果有限状态路径/定向检索/返工门禁接入现有Agent。DNA新候选精确引用修复后独立REVISE；囊泡候选精确引用失败且后续检索无进展；没有新增科学批准模型。新适配器真实重渲染124样本，关系观测248运行/107仅声明，像素仍未测量。67回归测试通过，最后20新增测试再过；冻结历史变化0。DeepSeek16、Qwen4，输入128194输出37161词元。Wan1次请求被拒，费用账单未知，Seedance仅dryrun stub。完整证据experiments/biology_expert_v4_3_1/README.md、evaluation.json、provider_runs.json。当前无必要后台任务。
下一步：先读取providers/wan/task.json，确认权限错误后在百炼模型页开通/核对空间地域，不能重复提交既有run。DNA需专门独立来源解决核酸酶与替换执行者、nick/gap；囊泡需真正含机制正文的证据。通用有限状态检查不推断自由文本别名，历史初态未声明为REVIEW_INCOMPLETE而非自动科学FAIL。保留所有历史模型、视频、审核和失败响应。

VERIFIED补充：用户提供业务空间域名后，已审核首尾图和用户原样纯文本示例各POST1次，均403 AccessDenied.Unpurchased，无task_id。累计3POST无生成。最后request_id39ad03bb-e778-991f-84d7-318140513158。后续先控制台核对空间/密钥权限，不能再说只试过旧域名。

VERIFIED权限恢复：Wan workspace retry任务2783b818-02d0-442c-ad9e-785fdcfe411c真实SUCCEEDED，5秒480P30fps，完整解码通过。用户后续希望360P先试；480P已提交且为官方最低档，现导出640x360预览，无额外高清生成。独立Wan视频审核正在进行，见v431_wan_review.log；科学批准未定。视频SHA4d433eb2815683d510802b4823fd94644b069944b4a6d97943564a24e1224009。

## 2026-11-26 V4.3.2续跑检查点
源码与产物 /autodl-tmp/code2biovideo/biovideo-v4.3.2/Code2Video。实验目录experiments/biology_expert_v4_3_2。当前没有后台运行任务。真实DeepSeek23请求（科学21+视觉2），2失败：一次9000输出截断，最后402余额不足；已知输入191720输出63478，402用量未知。Qwen/Wan/Seedance本轮0。93/93测试通过。正式科学文件hash固定见formal_science_code_freeze.json；早期开发轮通用依赖scope/action_category缺陷修后重冻结，开发失败不可当独立评测。

Immediate continuation：先读取logs/model_calls.json最后v42_21_ef4bacb6(402)和science_formal/vesicle_transport/automatic/repairs/attempt_1/{candidate.json,review.json,causal.json,result.json}。确认用户账户恢复后，保留账本并明确ack已知失败，再从既有patch/cache恢复，不能重跑成功模型步骤。当前run_reliability_formal.py没有topic级result跳过逻辑，需通过现存审计/repair缓存只恢复缺失步骤，避免多扣费。最高36为本次已有授权下界定的总调用ceiling，不重置已21。

还需完成DNA/有丝分裂正式迁移和独立复核、囊泡剩余一次有实质差异补丁；真正未见科学主题冻结后成功闭环尚无证据。若达尝试上限保留NEEDS_HUMAN_REVIEW，不为特定生物答案改通用引擎。Science总目标active，当前交付是检查点，不是完成。新无首尾帧视频没有新增付费授权，0提交。仓库旧DNA专用动画repair仍存在，topic_coupling_audit.json已披露；本轮新路径未用。

2026-11-26 14:19北京时间免费GET/user/balance复核：is_available=false，总余额-0.04CNY。无新增付费请求。check_resume.py已实现并运行，确认科学源码freeze变化0、囊泡前两次结果缓存完好、DNA/mitosis未开始。恢复状态resume_status.json；仍需用户账户余额恢复，目标active。

## 账户恢复后的最终有界实验结果
2026-11-26账户余额恢复至19.95元后，复用缓存继续，未重复成功请求。囊泡、DNA、有丝分裂各三次正式候选尝试均已完成，没有新科学模型被批准。囊泡和DNA末次候选均状态可达性PASS但科学REVISE；有丝分裂迁移末次结果见science_results.json。全部失败候选和回滚保留。Science正式冻结代码无变化。

本轮问题的答案是：尚不能证明系统能自主可靠修复新的机制模型，因此结论SCIENCE_PARTIALLY_VALIDATED，不能进入稳定维护。该结论来自实际有界实验，不继续为特定问题改引擎或无限追求PASS。剩余问题分别归因于检索证据质量/相关性、模型补丁与科学语义能力、以及已有接口的范围修订表达限制。没有证据表明需要再次扩建一套Agent。后续优先改善研究资料和模型遵循能力，并用独立新任务评测；不把这些失败主题反复调参结果当未见泛化。

先前README中的402中断是历史检查点，现已恢复并执行完毕；当前无账户阻塞或后台任务。本轮视频仍只dry-run，未新增付费视频。

最终累计用量：{"deepseek_calls": 41, "qwen_calls": 0, "wan_tasks": 0, "seedance_tasks": 0, "input_tokens": 389013, "output_tokens": 105189, "actual_cost": null, "failed_requests": 2}

实验最终证据science_results.json；已完成有界实验，结论部分验证，不是成功证明。不要继续同一主题增加补丁或重置三次尝试。

2026-11-26实验后审计发现并修复两个通用实现缺陷：schema1.1缺失state-ref字段误PASS；维持已有初态identity effect误报。新增4测试。原formal freeze结果保留，post_audit_revalidation.json对三候选重验证结果未变。没有新增模型调用或主题补丁。当前代码不同于formal freeze，需新独立评测才能支持稳定发布。

## 完成性审计补充
经最小通用反例复现，当前局部补丁接口不允许更正scope，即使独立Reviewer指出旧范围与新增事实矛盾。此为已证明的通用表达限制，不应把所有失败都归因科学来源不足。新增repair_expression_audit.json和completion_audit.json逐Gate保留部分完成与未证明项。未重跑三主题、未新增付费调用、未扩大架构。本轮3次问题返工限制已耗尽；稳定维护成功结论仍不成立。未来若修scope接口，必须新版本及独立评测，不能回改本轮正式结果。

2026-11-26通用scope接口维护在独立worktree /autodl-tmp/code2biovideo/biovideo-science-maintenance，maintenance/science-repair-scope分支。允许明确scope任务纠正范围，禁止删包含过程/新增排除/换物种与主题，精确正文证据必需。无新付费调用，不重跑已耗尽3次的主题。不宣布稳定，仍需冻结后独立机制评测。

2026-11-26独立新任务评测science_unseen_mechanism：骨骼肌收缩舒张，新任务未预给机制答案。a4ffcbb科学代码hash不变。3次DeepSeek，初模型Undefined input/output role；Schema修复9000输出截断，独立审核/科学返工未执行。初候选与失败保留，无手改，无新增生产分支。未证明稳定候选，104工程测试不能代替端到端成功。

## 协助恢复阶段（不得冒充原完全自主评测）
截断响应中candidate对象实际完整，开发者使用JSONDecoder原样提取，未编辑科学字段。该候选Schema/精确引用PASS，但独立科学和状态检查REVISE。冻结引擎随后按审核意见定向研究并进行了3次局部补丁，分别因目标超出任务、字段越权、observable参与者类型不一致而回滚。没有独立批准新模型。原自主评测失败保留；这次格式协助不能算零人工介入。没有新增主题分支，也不重置3次限制继续追PASS。

证据science_unseen_mechanism/recovered_final_result.json，10次累计DeepSeek，原始截断1次。没有后台任务，尚未证明目标。

## 补丁失败的离线归因
patch_failure_diagnostics.json列出首个错误后的全部可检测接口问题：attempt0修改ENT_SR与PROC_EXCITATION超出任务；attempt1向3个关系写scientific_name（不在允许字段），并有observable角色关系端点不一致；attempt2仍有同一实体绑定不一致。未持久化绕过门禁的候选，未批准。新机制补丁失败不应全部解释为来源缺失：生成器接口遵循/一致性是直接阻塞。该诊断0新模型请求，0生产改动。

## 发布判定与执行停止
release_decision.json核对三主题各3次和新主题有界失败，0批准新模型。Science状态SCIENCE_PARTIALLY_VALIDATED，不建议稳定维护。当前无运行任务，科学源码freeze未变。目标尚未达到；依据任务书有限尝试与禁止无限扩框架要求，现有协议已耗尽，不再自动新增主题/重置次数。继续证明目标需要另定一轮模型/结构化输出策略与独立评测协议，不能把失败包装成完成。
