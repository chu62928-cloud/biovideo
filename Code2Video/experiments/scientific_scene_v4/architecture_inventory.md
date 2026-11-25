# V4实际工程核查
2026-11-24，北京时间。历史上游commit637509294e936b231d220bb555cf74eeedcb9dfd，工作区已有V2/V3未提交实现，具体哈希见frozen_inputs.json。
## 直接复用
src/biology_runtime.py中的BiologyScene实际对象/可见性/绑定与事件轨迹；src/biology_v2_pipeline.py中的TransactionRenderer完整沙箱渲染、完整解码、哈希配对、原子提交与回滚；src/gpt_request.py的DeepSeek接口；src/biology_expert/的单Agent、工具白名单、Review Schema、持久调用预算和Qwen科学接口（12k总输出/4k思考预算、JSON模式）。
V3已有两个主题的真实证据知识包，本次精确复制，保留未核实事实；复用DNA的15条已支持事实及mitosis8条有范围限定事实，不重新假造引用。
V3最终候选仍NOT APPROVED；其蓝色第三体歧义、切口邻接问题、Polδ标签来源见reviews/video/final_retry_review.json与root_cause_provenance_audit.json。A0直接引用此候选不重渲染。
## 扩展接口
新增V4 BiologyExpert适配器，注册scene_ir_review/runtime_validation工具；原V3 Schema不支持SCENE_IR根因，新Schema在V4定义而非改动V3文件。
生成代码通过可信biology_runtime导出的通用ScientificScene调用可编辑对象/状态引擎。V2事务渲染器不改写；其runtime_file/assets注入口承载V4可信组件包。
## 新增
对象/组合/场景/过程/状态/审核Schema；数据驱动组合、10类通用操作与事务状态转移、条件DSL、静态/实际端点与身份检查、分镜编译器、实际状态轨迹、跨主题Manim适配器、来源溯源和教学复核。
## 限制
通用引擎不内置生物事实。DNA与mitosis的科学规则、组合蓝图和过程模板是人工工程准备的数据与插件，需与LLM输出区分。该准备本身是改进来源，不宣称全部来自模型自发发现。
几何轨迹只能验证示意关系，不能验证原子结构/化学反应；模型审核不是高中生实测。严格科学批准与工程可播放分开。V3原45/8等均为旧实验边界，本V4按用户新任务独立10/3计数，不重置旧账本。无更高层金额预算接口可查，真实账单未知。
