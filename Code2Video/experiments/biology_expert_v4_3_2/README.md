# BioVideo V4.3.2 收敛实验（当前交付检查点）

**当前结论：SCIENCE_PARTIALLY_VALIDATED。尚不能证明新机制问题可在冻结系统中自主修复并独立批准，因此不宣布进入稳定维护。目标仍在进行中。**

本轮延续同一个BiologyExpertAgent，扩展现有检索、科学模型、因果验证和修复事务。新增retrieval_quality.py、model_repair.py；修改contract_builder.py、model_reliability.py、typed_science_builder.py、typed_science_model.schema.json、agent.py、tools/repair_planner.py。视频Provider仅增加text_to_video输入模式。没有增加主题名称分支。仓库仍有历史DNA专用动画修复路径，未被本轮调用，详见topic_coupling_audit.json，不宣称整个仓库无硬编码。

## 已取得的证据

查询数组/上下文/单字符门禁在联网前执行；结构化EuropePMC检索区分题录、摘要与正文，标题不能作机制证据。新网页须独立逐缺口蕴含检查，不因新来源自动结束。HTTP缓存保留真实网络账本。真实囊泡研究取得正文/摘要但多个缺口仅部分支持，没有通过缩小任务来获得PASS。

通用1.1状态Schema提供subject/property/value、初态、生产者、必需过程和未知状态；有限状态搜索保留未穷尽状态。真实囊泡候选Schema、精确引用和因果可达性PASS，独立科学审核REVISE：马达与特定囊泡的结合缺少直接证据、把轨道能力建模为主动过程、旧范围声明与新增身份矛盾。事务回滚，未提交科学模型。这证明能防止假成功，不证明已会自主修好。

开发轮发现关系依赖漏列/action_category白名单遗漏，修复通用接口后重新冻结，首轮失败作为开发样本保留。正式轮科学源码哈希未变。正式囊泡第1次补丁schema_version数字1.1被拒，第2次进入独立审核但未通过，第3次模型API返回402 Insufficient Balance。调用网关停止，DNA和有丝分裂未完成本轮新模型迁移及独立复核。旧模型保留，三主题均运行同一离线因果验证，但这不等于三个真实闭环完成。不得重置账本绕过402，也不得悄悄换模型获取更容易PASS。

历史有丝分裂MP4重新提取1.2/2.2/4.2秒原始帧，与轨迹时间对齐；保留完整视频/帧审核分歧，重影意见NOT_CORROBORATED，并非证明每帧完美。实际轨迹重跑1完整PASS/3部分验证，两类真实轨迹副本注错PASS→FAIL；声明/运行/像素证据独立。没有新增人类科学或学生实验。

## 视觉线

科学规范、视觉规范、负约束和合成Prompt由模型从已审核模型及原检索图注生成，非固定人工主题Prompt；原始响应与截断失败保留。外部图片许可未确认，仅内部图注研究，未上传。Wan文生视频演练不含media首尾图，配置可准备但本轮付费0。Seedance仍未配置型号/密钥，dry-run明确不可用，不宣称完整接入。VIDEO_BENCHMARK_NOT_EXECUTED。历史首尾帧Wan成功片不是本轮文生视频结果。

## 复现与后续

从Code2Video运行：`python -m pytest experiments/biology_expert_v4_3_2/tests experiments/biology_expert_v4_3_1/tests experiments/biology_expert_v4_3/tests experiments/biology_expert_v4_2_2/tests experiments/biology_expert_v4_2_1/tests -q`。完整结果见tests。正式科学调用入口run_reliability_formal.py有缓存；恢复前必须检查logs/model_calls.json最后402、现存候选和provider状态，不重抽已成功步骤。

需要恢复DeepSeek账户余额/可用额度，才能继续DNA及有丝分裂新审核和囊泡剩余尝试。当前不需要给通用引擎增加主题补丁；已暴露问题分别属于检索证据不足、模型局部补丁遵循能力和科学表达错误。若恢复后仍达尝试上限则保留NEEDS_HUMAN_REVIEW，而非无限扩框架。尚未做真正独立新主题的冻结后成功验证，不能推广为任意机制能力。

所有候选、原文摘录、局部补丁、审核、回滚哈希和失败日志在包内相对路径可复核。无新视频或占位成功产物。

实际调用：{"deepseek_calls": 23, "qwen_calls": 0, "wan_tasks": 0, "seedance_tasks": 0, "input_tokens": 191720, "output_tokens": 63478, "actual_cost": null, "failed_requests": 2, "unknown_usage_requests": ["v42_21_ef4bacb6"]}。费用API不返回，未知不写零。

测试源码提交：3b1ece1fc3630d95a9071f409de9206200261e9f。最终93/93测试通过，用时109.54秒。
