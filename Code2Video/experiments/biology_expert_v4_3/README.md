# BioVideo V4.3 离线工程检查点

本轮工作尚未完成真实实验。新增Schema、证据引用与类型化模型Builder/Reviewer、通用TypedContractCompiler、语义ID场景规划器及独立事件起止观察适配器；现有单BiologyExpertAgent注册建模/审核工具。没有新增主题名称分支，没有预置DNA/有丝分裂/新主题机制答案。

## 真实状态

新V4.3合成单元测试12/12通过；与V4.2.2合计31/31。完整旧+新回归日志见manifest.json。科学过程模型真实生成0，新增付费请求0，真实新视频0。所有模型、编译、渲染正式门禁仍未通过，未创建sample_video.mp4或虚假trace。

任务书明确“建议10次DeepSeek、3次Qwen并非新的消费授权”，此前预算用满，已向用户请求本轮授权，当前仍待回复。离线工程已完成并可检查，真实检索→模型生成→独立核验与未见主题实验未执行。不得把合成测试的科学内容当真实生成结果。

## 源码

- Code2Video/src/biology_expert/typed_science_builder.py：Schema/语义引用/真实引文核对，独立请求核验，哈希冻结，类型化谓词编译。
- Code2Video/src/biology_expert/schemas/typed_science_model.schema.json：实体、关系、过程、状态、参与者、作用区间及证据。
- Code2Video/src/scientific_scene/typed_planner.py：消费已审核模型，以语义ID生成对象、关系和独立起止事件，不加载旧Process Blueprint。
- Code2Video/src/scientific_scene/adapters/typed_manim_adapter.py：通用示意组件与逐帧状态/关系/事件起止；尚未正式渲染，不声称完整生物过程可视化能力已验证。
- agent.py、scene_compiler.py、contract_compiler.py：接原Agent/Planner，独立事件结束标记优先，旧入口保留历史。

## 复现离线测试

```bash
python -m pytest Code2Video/experiments/biology_expert_v4_3/tests/test_v43.py -q
```

完整回归添加V4.2.1与V4.2.2的测试文件。真实运行入口为run_experiment.py，输入任务路径及环境文件路径；只有存在明确用户授权的authorization.json才允许请求。成功步骤按输入哈希/模型文件保存检查点，不用模型文字宣告渲染成功。

## 尚需验证的能力

当前Planner只支持通用角色示意图及状态/关联表达，不保证能完整表现所有运输、分离、合成过程。独立审核可能拒绝过强科学约束；此时保留失败而非降门禁。真实样本、完整编译、真实Manim观察、视频独立审核及两类真实机制注错均待执行。第三个未见主题将在代码/主要测试固定后才引入，不将其答案用于调试。
