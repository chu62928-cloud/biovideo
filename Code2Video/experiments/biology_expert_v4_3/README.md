# BioVideo V4.3 真实实验交付

已生成完整8秒有丝分裂示意短片，并通过完整解码。它表示一对姐妹染色单体的排列和分离，不是六章节DNA整片。

## 实际结果

三主题均真实检索并生成科学模型；有丝分裂独立科学模型审核通过。DNA模型经返工仍REVISE：产物/模板混淆已纠正，但引物替换状态、连接前置条件及来源中的核酸酶身份歧义尚未解决。未见主题囊泡运输审核REVISE：现有来源不足以支持马达蛋白依赖性及持续关系。未为它添加主题专用生产代码。

有丝分裂视频由DeepSeek生成的场景数据经通用Manim适配器实际执行。保留了静态节点初版、语义修复、失败渲染和成功候选。开发者提供过具体布局与返工指导，因此不能声称完全自主或公平单次消融。未手写完整教学动画冒充模型产物。

运行检查：1条完整关系约束PASS、3条部分验证，不能称所有机制执行已证明。真实轨迹副本中的持续关系提前断开、错误连接对象两类注错均从PASS变FAIL；负对照只改视觉元数据，不能代替真正的几何或合法并发负对照。科学模型独立审核是同供应商独立请求，不是真人人类专家。

Qwen完整视频两次科学PASS，视觉REVISE并指称重影；在0.2—7.8秒9张直接解码PNG独立审核中科学和视觉均PASS，未证实重影。两种审核均保留。帧审核不保证全部帧。因此视频作为真实候选交付，实验整体REVIEW_INCOMPLETE，不授予联合VIDEO_APPROVED。

## 源码和复现

新增/扩展src/biology_expert/typed_science_builder.py、schemas/typed_science_model.schema.json、agent.py、contract_compiler.py、qwen_science.py，src/scientific_scene/typed_planner.py、scene_compiler.py、adapters/typed_manim_adapter.py，以及集合关系运行检查temporal_validator.py。检索、工具注册、事务渲染、受限运行环境复用既有模块。

从Code2Video运行：`python -m pytest experiments/biology_expert_v4_3/tests experiments/biology_expert_v4_2_2/tests experiments/biology_expert_v4_2_1/tests -q`。实际47/47通过。先配置仓库外环境变量/API配置，再按run_experiment.py、模型返工脚本、render_candidate.py和review_decoded_frames.py复现；付费步骤不要盲目全重跑，先核对账本和输入哈希。渲染使用既有沙箱超时/资源/网络隔离。

## 交付文件

sample_video.mp4、sample_scene.json、sample_trace.json、keyframes.jpg同版；manifest.json有真实哈希。typed_models.json包含三个真实模型和独立审核；evidence.json含精确来源摘录对应；execution_results.json、evaluation.json含失败和覆盖边界。原始调用、修复候选及渲染版本在服务器同实验目录保留。ZIP包含最小结果、相关源码、测试和可复核审核/调用记录，不复制历史视频。

## 下一步

先修通用程序集绑定、前置条件真实执行门禁和几何观测覆盖；为DNA与囊泡补充独立来源，继续审核。当前不建议扩展六节：跨主题两组完整编译验收尚未达到。用户已取消建议调用上限，费用账本不重置；不调用Wan或Seedance。

真实API用量：{"deepseek_calls": 30, "qwen_calls": 4, "input_tokens": 216988, "output_tokens": 93467, "cost": null, "cost_note": "API does not report actual charged amount; no invented monetary cost", "failed_calls": 2}

源码提交：1553626b7589f8f8481dd1c8a4b3fdf7fcbc4b6e。交付清单在后续提交中绑定该源码版本。
