# 运行环境与步骤

服务器 SSH 主机别名为 motion-data。工作目录 `/autodl-tmp/code2biovideo` 指向实际数据盘 `/root/autodl-tmp/code2biovideo`，防止使用空间不足的系统盘。

独立环境：`/autodl-tmp/code2biovideo/env`，Python 3.11，Manim Community 0.19.0，OpenAI SDK 1.90.0，FFmpeg 7.1.1，Conda texlive-core 另见下方修复。安装来源 conda-forge；未安装完整上游锁定依赖，因为本轮禁用评估器、Gemini 和外部素材。

```sh
TMPDIR=/autodl-tmp/code2biovideo/tmp CONDA_PKGS_DIRS=/root/autodl-tmp/code2biovideo/conda-pkgs conda create -p /autodl-tmp/code2biovideo/env --override-channels -c conda-forge --solver libmamba --repodata-fn current_repodata.json python=3.11 manim=0.19.0 openai=1.90.0 requests psutil pillow ffmpeg texlive-core -y
cd /autodl-tmp/code2biovideo/Code2Video
/autodl-tmp/code2biovideo/env/bin/python -u /autodl-tmp/code2biovideo/run_deepseek_experiment.py
```

配置文件 `/autodl-tmp/code2biovideo/.env` 权限为 600，不在仓库中。包含 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、DEEPSEEK_MODEL。密钥来自用户指定的 FastAPI 配置，不输出、不复制到实验结果。

官方接口说明：https://api-docs.deepseek.com/ 。本轮实际 `/models` 响应留存在项目 logs/deepseek-models.json，选择 deepseek-flash；服务端标识以每次响应为准。

原生 CLI 可用：`PYTHONPATH=.. python agent.py --API deepseek --knowledge_point 'DNA replication in eukaryotic cells' --no_feedback --no_assets --no_parallel --max_fix_bug_tries 2 --max_regenerate_tries 2`。实际实验使用上方串行驱动器，附加隔离、日志、全局调用上限和阶段验证；请勿直接用无隔离 CLI 执行不可信代码。

## 运行隔离
服务器不允许 unshare 网络命名空间。改用 Linux Landlock ABI 1 限制文件访问，seccomp 禁止网络、跟踪其他进程与挂载，运行用户 UID/GID 62001。仅允许读取独立环境和系统运行库、字体；允许写入当前主题的输出目录。密钥不传给子进程；CPU、内存、文件大小与执行时间受限。

为该 UID 添加 /root 的仅遍历 ACL，不授予列目录或读文件权限；Landlock 进一步限定可访问路径。启动器 sandbox_exec.py 存在项目根目录。隔离失败将停止，不降级为 root 执行。

手写环境测试文件位于 experiments/biology_baseline/tests/environment/smoke.py，与 Agent 产物分开，不能视为 Code2Video 成果。

## 私有公式环境修复与最终命令
Conda texlive-core 未包含完整运行所需格式/宏包，最终改用 `/autodl-tmp/code2biovideo/texlive` 的项目私有 TeX Live 2026，基础方案 scheme-basic，再安装 standalone、preview、amsmath、amsfonts、babel-english、xcolor、dvisvgm。原始 profile 为项目根目录 texlive.profile，安装日志在 logs/texlive-*.log。

环境修复后执行 recover_math_environment.py 复测现有代码；finalize_dna_merge.py 只重新执行上游合并方法。collect_results.py 解码检查、提取关键帧、生成 metrics.csv。辅助脚本副本保存在本实验 tools/，运行时项目根目录版本为准。

DeepSeek 新增 DEEPSEEK_THINKING=disabled。默认思考模式首轮失败与关闭后结果分别保留，不混为同一配置。45 次调用上限通过现有审计累计检查；本实验实际 35 次。已有结果应冻结，后续运行使用新标签与独立目录，禁止覆盖本轮记录。
