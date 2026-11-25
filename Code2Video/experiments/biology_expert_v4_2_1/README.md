# BioVideo V4.2.1：契约与观测集成

本轮完成离线工程集成，三个主题最终仍为 `REVIEW_INCOMPLETE`。付费模型请求0，重新渲染0；历史V4.1/V4.2输入哈希未改变。

## 唯一正式入口

从仓库根目录运行 `python audit_contract.py audit --contract <契约路径> --scene <场景路径> --trace <轨迹路径> --output <输出目录>`。可选 `--review <VLM记录> --video <原视频> --model qwen3.8-27b --contract-review <契约核验>`。默认离线，不读取密钥，无付费入口；输出实际加载路径、Git commit和可识别错误。

实际生产模块在 `Code2Video/src/biology_expert/`。`development/v4.2/src/`仅是旧开发快照，已添加退役提示；旧默认科学流程不会静默加载。源码实现提交 `8b047b6743f4efb25af2a5dec6028586ce44cbad`，精确源码哈希见evidence_manifest.json。隔离分支 `integration/v4.2.1`；原服务器项目和用户未提交改动未触碰。

## 一条命令重现实验

```bash
python Code2Video/experiments/biology_expert_v4_2_1/run_offline.py --evidence-root /autodl-tmp/code2biovideo/Code2Video/experiments
```

路径是参数，用户可换为本地历史证据根目录；生产源码中无服务器绝对路径。真实大型轨迹与视频仅在服务器，GitHub提供路径和哈希，不伪造缺失输入。pytest命令：`python -m pytest Code2Video/experiments/biology_expert_v4_2_1/tests/test_integration.py -q`。

## 实际结果

|主题|绑定实体角色/过程|运行局部测量|完整运行科学约束通过|带时间VLM证据|有效身份注错（按约束）|去重对象|
|---|---:|---:|---:|---:|---:|---:|
|DNA|3/2|15|0|8|6/6检出|3|
|有丝分裂|4/2|17|0|7|8/8检出|3|
|蛋白质翻译|10/6|0|0|0|未测试|0|

准确数量以results.json为准。翻译有7项实际静态关系登记检查，无Runtime Trace，运行项NOT_MEASURED。菌种/真核起始机制范围在原契约中仍混合，不能靠绑定解决原科学契约缺陷。

**局部测量范围**：身份连续性，以及在明确对象配对时的已登记关系生命周期。父科学约束保持PARTIALLY_VERIFIED；这不证明催化反应、化学方向或完整科学机制。身份异常是科学参与对象一致性错误，注入到真实轨迹副本后由程序检出，颜色负对照无误报。同一对象被多个约束引用，不能把约束案例数当独立生物错误种类。

角色Binder只用明确ID/来源身份、元数据词集合与结构候选匹配；模糊词和A/B不能强配。可绑定对象集合，但未将“未显示的酶”猜成另一对象；无可靠过程匹配时只声明可见对象生命周期检查，不声称过程发生。现有契约的自然语言关系未被擅自改成运行关系名。

## 覆盖与VLM证据

覆盖实际有完整语义证据的约束由V4.2的0增至DNA8、mitosis7；身份局部检查另列，不代替父约束覆盖。只有逐约束文本、可解析时间和契约/视频哈希相符时回填。模型总体PASS不传播，缺时间和不确定项仍未测量。确定性FAIL优先；最终REVIEW_INCOMPLETE还受契约未批准、目标缺口与原VLM问题约束。

有丝分裂V4.2报告提到的末尾Grid可能来自审查时附带参考图；本轮仅重放原意见，不把它当已证实视频缺陷，也未新请求或重渲染来裁决。参考图干扰问题仍需独立验证。

## 真实与合成测试

pytest包含两项读取原始DNA/Mitosis轨迹的集成测试，其他为明确合成输入的负对照/版本/异常测试。无Mock响应冒充真实模型。输入版本改变使绑定或VLM证据失效；静态登记不等于可见观测。

## 未完成的科学目标

本轮证明统一引擎能自动绑定部分对象并检测参与对象身份错误；**尚未证明无需语义协助即可把任意科学契约编译成完整机制验证器**。DNA聚合酶简称与新链、部分过程映射仍有歧义，未增加主题同义词表来凑成功。持续关系的有效区间由历史登记生命周期界定，无法据此独立识别真实作用何时应开始/结束。尚未实现经独立验证的自然语言机制到DSL映射，不能声称完整科学错误检测已经达到目标。

最小交付：results.json、bindings.json、checks.json、mutations.json、comparison.csv、evidence_manifest.json及tests/test_integration.py。details/只保留可复现的逐主题机器结果和Agent工具记录。原V4.1批准不自动升级为V4.2.1批准。
