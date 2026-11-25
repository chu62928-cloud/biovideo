# 逐文件迁移

|原位置|归档/最终位置|原因|正式调用|可恢复|历史影响|
|---|---|---|---|---|---|
|src/scientific_scene/scientific_review.py|archive/retired_topic_checks/src/scientific_scene/scientific_review.py；新入口保留原路径|主题提示/规则退出通用生产链路|旧版否；新版契约接口是|原目录及快照均保留|历史实验原目录不改|
|src/scientific_scene/adapters/biology_expert_adapter.py|archive/retired_topic_checks/src/scientific_scene/adapters/biology_expert_adapter.py；新入口保留原路径|主题提示/规则退出通用生产链路|旧版否；新版契约接口是|原目录及快照均保留|历史实验原目录不改|
|src/biology_expert/tools/evidence_retriever.py|archive/retired_topic_checks/src/biology_expert/tools/evidence_retriever.py；新入口保留原路径|主题提示/规则退出通用生产链路|旧版否；新版契约接口是|原目录及快照均保留|历史实验原目录不改|
|src/biology_expert/tools/mechanism_validator.py|archive/retired_topic_checks/src/biology_expert/tools/mechanism_validator.py；新入口保留原路径|主题提示/规则退出通用生产链路|旧版否；新版契约接口是|原目录及快照均保留|历史实验原目录不改|
|src/biology_expert/tools/reviewers.py|archive/retired_topic_checks/src/biology_expert/tools/reviewers.py；新入口保留原路径|主题提示/规则退出通用生产链路|旧版否；新版契约接口是|原目录及快照均保留|历史实验原目录不改|
|experiments/scientific_scene_v4_1/groups/B4_expert_repair/scene_graph.json|examples/dna_replication/scene_graph.json|可审计例子，不作为Builder输入|否|是|复制不移动|
|experiments/scientific_scene_v4_1/groups/B4_expert_repair/approved_manifest.json|examples/dna_replication/approved_manifest.json|可审计例子，不作为Builder输入|否|是|复制不移动|
|experiments/scientific_scene_v4_1/groups/B4_expert_repair/validation_report.json|tests/regression/legacy_dna_replication/expected_checks.json|旧机制评价基准|仅回归测试|是|无|
|experiments/scientific_scene_v4_1/groups/M1_mitosis/scene_graph.json|examples/mitosis/scene_graph.json|可审计例子，不作为Builder输入|否|是|复制不移动|
|experiments/scientific_scene_v4_1/groups/M1_mitosis/approved_manifest.json|examples/mitosis/approved_manifest.json|可审计例子，不作为Builder输入|否|是|复制不移动|
|experiments/scientific_scene_v4_1/groups/M1_mitosis/validation_report.json|tests/regression/legacy_mitosis/expected_checks.json|旧机制评价基准|仅回归测试|是|无|