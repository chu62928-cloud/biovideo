# 真实运行记录

- 2026-11-23（北京时间）：通过 motion-data SSH 登录。服务器默认 root；生成代码另以普通 UID 执行。
- 直接 GitHub 克隆失败：GnuTLS recv error (-110)。本地首次完整克隆遇到 TLS EOF；随后 `git clone --depth 1 --filter=blob:none --no-checkout` 成功，稀疏检出 src、prompts、json_files，上传至服务器。未下载上游演示视频冒充结果。
- `/autodl-tmp` 位于系统盘，仅余约 1.4 GB；实际数据盘是 `/root/autodl-tmp`，当时剩余约 166 GB。通过项目目录符号链接保留用户指定路径。
- 首次 conda 安装因多通道元数据获取耗时中止；改为单 conda-forge 通道并独立缓存后安装成功，原始日志均保存在项目 logs/ 下。
- `/models` 鉴权成功；实际模型列表保存在 logs/deepseek-models.json。
- 环境冒烟测试返回码 0；隔离测试输出 ISOLATION_OK。详见项目 logs/experiment-console.log 与 tests/environment/render_logs/。
- 实验命令：独立环境运行项目根目录的 run_deepseek_experiment.py。A 数学主题完成后串行启动 B DNA 主题；不运行全量主题、评估器、视觉反馈或素材下载。
- 分主题完整日志：experiments/biology_baseline/logs/{A_math_deepseek,B_dna_deepseek}/run.log；请求及用量：各目录 api/；指标：metrics.json。
- 实际状态和最终视频以 RESULTS.md、metrics.csv 及主题 metrics.json 为准。


## 最终核验
数学恢复 6/6，DNA 6/6；均经 FFmpeg 全片解码。汇总共 35 次请求、225009 词元，接口重试 0。
DNA 内容已与分镜、代码、多时间帧交叉核对；其中涉及复杂动态的问题保留 Needs Human Review。黑屏检测两段报警经画面检查属于稀疏过渡，仍有标题和讲义，未判为完整黑屏。
已停止进一步模型调用。最终命令：finalize_dna_merge.py → recover_math_environment.py → collect_results.py → write_final_report.py。所有命令在服务器独立环境中运行。
