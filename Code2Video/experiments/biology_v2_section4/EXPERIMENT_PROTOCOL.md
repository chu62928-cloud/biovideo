# Biology-Aware Code2Video V2 Section4 实验协议

## 范围与固定输入
只研究Section4，不重新生成六节大纲；不增加RAG或复杂多Agent。原始历史目录冻结，historical_inputs.json记录报告、反馈、代码与MP4哈希。
A0严格复制原始Section4；A1/A2使用同一机制JSON、五事件分镜、25–35秒目标和运行环境。A1只用基础几何；A2只额外提供独立SVG组件清单和用法。完整动画必须来自DeepSeek真实响应。
A3严格从成功A2代码/视频开始，不重新抽样初始Coder。Critic保留完整MP4、上游GRID和布局要求，追加稳定对象ID与分子关系。每轮保存Prompt Diff。第一轮新候选通过完整渲染/验证并提交后才考虑第二轮。

## 事务和修复
新入口src/biology_v2_pipeline.py：语法与导入白名单、安全检查、隔离目录完整Manim渲染、ffprobe与全片解码、对象和事件检查，成功才原子切换current目录指针；代码和视频由同一不可变版本发布。失败不改current，候选与日志保留。
对象建议必须包含object_id、issue_type、current_state、target_constraint、suggested_change。不存在ID直接拒绝，不按视觉模型行号修改代码。DeepSeek只生成construct函数，AST替换限定到Section4Scene.construct，不触及模块其他定义。
运行模型代码沿用Landlock/seccomp和普通UID62001，禁网、密钥不继承、180秒墙钟超时和资源限制。基础组件/观测器不是完整教学动画。

## 阶段门禁与基础设施干预
先离线测试通过才允许API。初版8项测试通过；真实生成中发现绑定检查把历史结合位点当当前位点，暂停了模型调用并修正观测器：同一酶换位时替换旧updater/绑定，逐帧记录当时的绑定关系，立即定位并保证等待时也能采样。新增换位与根组子对象可见性测试后最终10项均通过，再用原模型候选无API复测。所有此前失败结果保留。
该次改动是基础设施干预，不是人工改写A1/A2动画。A2中断时已完成的模型响应与代码保存，不重新索取密钥，不抹去消耗。

## 调用预算
本次独立上限DeepSeek8次、Qwen2次、Wan1个任务且默认禁用；每次HTTP尝试记账，SDK重试为0。旧45次保护来自旧实验脚本，不是高层全局限制。旧计数与日志不删除、不清零。API服务异常或达到新预算即停止新调用。

## 对照解释与不确定性
只做每组单个主题的小样本，独立Coder采样本身也是混杂因素；不能将所有质量差异都因果归于SVG。A0内容与时长不同，按教学事件对齐，不能强行按同秒数比较。
几何越界/重叠/跳跃检查是启发式；结合代码、逐帧轨迹与实际截图做pass/fail/uncertain，不能直接采信模型自评分。渲染通过不等于机制正确。阶段失败需明确标记，不将复制旧片段冒充新渲染结果。

## Wan
tools/run_wan_comparison.py参照官网media:first_frame、公开HTTPS参考图、北京Workspace端点、5秒720P参数。仅ENABLE_WAN=1且地域/Workspace/URL完整时可提交；默认dry-run不发生HTTP、上传或视频任务。

## 最终状态
DeepSeek6/8次，Qwen1/2次超时后停止，Wan0。A1/A2工程门禁通过，但机制未全通过；A3无有效反馈、无新修复。观测器最终复测没有改变动画代码和MP4哈希。原基线及历史哈希全部保持不变。
