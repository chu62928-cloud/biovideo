# 项目约定

- 使用中文说明，专有名词必要时附英文。
- 本轮结果已冻结；后续操作先阅读 PROJECT_MEMORY.md，并以服务器文件和日志验证状态。
- 继续实验使用新输出目录；保留模型原始响应、失败与代码历史。

# Project Instructions

<!-- maintain-project-memory:start -->
## Project continuity

- At the start of a task, read `PROJECT_MEMORY.md` before planning or changing files.
- Treat its status as a handoff snapshot: verify important files, Git state, tests, artifacts, and external jobs before relying on them.
- Update `PROJECT_MEMORY.md` after material milestones, decisions, failures, or background-job transitions, and before a long-session handoff.
- Keep verified results separate from pending plans. Preserve frozen protocols, data splits, and explicit invariants.
- Never write passwords, tokens, private keys, cookies, or credential-bearing URLs into project memory.
<!-- maintain-project-memory:end -->
