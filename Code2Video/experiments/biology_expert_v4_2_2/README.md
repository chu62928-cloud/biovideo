# BioVideo V4.2.2：严格契约编译与独立区间验证

本轮完成基础通用引擎与真实数据诊断，理想的真实机制验证目标未达到。付费请求0、整段视频生成0，原始契约/轨迹/历史结果未修改。

## 实际源码与入口
沿用仓库根 `python audit_contract.py audit --contract <contract.json> --scene <scene_graph.json> --trace <geometry_trace.json> --contract-review <contract_review.json> --output <new_directory>`。程序明确加载Code2Video/src，实现版本 `af35ab24877716e8fbf2794edaafb86535f3d659`，源码哈希见manifest.json。

修改role_binder.py：共享词只能提候选；只有明确过程role或Process Template过程标识可绑定，拒绝候选及原因保留。ENTITY/PROCESS/RELATION/ANCHOR分类保留；EVENT由所选event_ids表达。类型明确矛盾返回TYPE_MISMATCH；缺少动作/输入输出/状态定义时不以词汇补全。翻译polyribosome_formation不再绑定EV_peptide_bond_formation，其他明确过程角色仍绑定。

新增contract_compiler.py：将显式typed executable_predicate或等价原语编译为relation_holds_during、event_precedes、connection_holds_until、state_transition_allowed。编译器不将自然语言关系替换成active_site等易过关系；VLM-only、例外不明、缺绑定或未经完整源支持时拒绝或部分编译。原契约未通过时只诊断，不批准。

新增temporal_validator.py：事件区间来自事件图+实际事件标记，不读取待验关系生命周期。关系缺失/对象隐藏不缩短区间；采样缺口明确报告。期望结束无法确定时拒绝PASS。通用注错按谓词生成，只有真实baseline完整PASS才计有效。

observation_adapter.py删除自指关系区间路径；带时间VLM文本降为TIMESTAMP_MATCHED，不再单凭时间文本增加完整科学覆盖。frame提取与独立语义确认分开。contract_cli.py调用同一Agent和上述编译/验证路径，未新增平行Agent。

## 真实实验结果

|主题|实体绑定|过程绑定/拒绝|完整编译|完整机制PASS|真实有效机制注错|
|---|---:|---:|---:|---:|---:|
|DNA|3|0/2|0|未测量|未测试|
|有丝分裂|4|0/2|0|未测量|未测试|
|蛋白质翻译|10|5/1|0|无Trace|未测试|

不能把未测量写成成功0。results.json中的执行计数0表示本次没有可完整执行规则，mutations.json逐类记录NOT_TESTED及原因。三个主题最终均REVIEW_INCOMPLETE；DNA原契约REVISE、mitosis契约PASS、translation REVIEW_INCOMPLETE均保持。

关键阻塞：DNA规则全部为VLM型自然语言，顺序列表还混用实体与事件；有丝分裂connected_by、attached_to等契约角色关系缺可证明的运行关系等价映射，state aligned_at_metaphase_plate没有对应实际状态键，direction参数使用对象角色而非明确锚点；翻译nested primitive与菌种作用范围不明确且没有真实轨迹。编译器不能凭名称推断这些科学含义。需要在独立科学核验下补齐通用process_semantic_id、action_category、input/output_roles、state_before/after、relation_semantic_id及适用区间声明；本轮不修改冻结契约。

V4.2.1身份检查可作为局部前提保留，但本轮未把它们计入完整机制成绩。真实新机制错误没有被证明：没有满足完整PASS的基线，所以四类真实机制注错均NOT_TESTED，不冒充漏检0或检出100%。通用合成测试单独证明提前终止、错误目标、逆序、错误前置状态可检出。

## VLM与Grid核查

已有审核按契约/视频SHA-256核对，时间需在ffprobe实际视频长度内；有文本时间仍只是模型声明。提取实际有丝分裂尾段10、10.5、11、11.5秒及末帧，人工查看均是有丝分裂，没有Grid Visual。原请求确实另附空间网格图，符合输入参考混淆假设，但不能声称知道模型内部原因，也不以少量截图证明全视频每一帧均无该内容。核查材料与哈希记录checks.json、manifest.json。没有重新调用Qwen，未自动洗掉原REVISE。

## 测试与复现

```bash
python -m pytest Code2Video/experiments/biology_expert_v4_2_1/tests/test_integration.py Code2Video/experiments/biology_expert_v4_2_2/tests/test_v422.py -q
```

最终旧+新测试32/32通过。旧集成测试包含两份真实历史轨迹，新的谓词正反对照为明确合成场景；已知翻译误绑定测试使用旧真实生成场景。状态、关系、顺序错误检测不靠主题答案，源码无新增主题分支。历史视频与轨迹在服务器原目录，GitHub不复制大文件；复现路径从CLI参数提供，不写进生产逻辑。

## 局限
基础实现可运行，尚未取得真实完整机制约束；不能称为已实现任意生物契约自动编译。本轮避免通过改契约/注入主题映射取得漂亮指标，记录了旧数据缺少的通用语义契约。未证明轨迹注错等价于MP4像素错误检测，未做新增科学批准。
