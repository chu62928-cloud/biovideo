from pathlib import Path
import subprocess, json
root=Path('/autodl-tmp/code2biovideo/Code2Video')
exp=root/'experiments/biology_baseline'
docs={
'ARCHITECTURE.md':'''# Code2Video + DeepSeek：架构与原始调用链

本项目是模型替代实验，不是原论文模型配置的严格复现。上游版本：637509294e936b231d220bb555cf74eeedcb9dfd。

## 源码核对
- `src/run_agent_single.sh` 默认选择 gpt-41，开启素材、视觉反馈和主题并发，生成代码上限 10000 词元，修复和重生成上限各 10。
- `src/api_config.json` 原有 GPT/Gemini 配置为 Azure 服务占位项；Claude 使用 OpenAI 兼容端点。配置读取优先采用服务名加字段名的环境变量。
- `src/gpt_request.py` 的 GPT/Gemini 请求使用 AzureOpenAI；Claude 使用 OpenAI。带 `_token` 的接口返回 `(completion, usage)`。
- `src/agent.py:get_api_and_output` 选择接口；同一 `RunConfig.api` 供 Planner、Coder 与 ScopeRefine 修复器使用。

## 工作流程
`generate_outline` → `generate_storyboard` → `generate_section_code` → `render_section` / `debug_and_fix_code` → `merge_videos`。

Planner 使用原始 `prompts/stage1.py` 和 `stage2.py`，直接生成 JSON，大纲和分镜分别保存为 outline.json / storyboard.json。分镜保留原始 sections、id、title、lecture_lines、animations 格式。

Coder 使用 `prompts/stage3.py` 和原始 `base_class.py`。原生 `replace_base_class` 会替换生成代码的 TeachingScene，这属于上游设计。代码保存为 section_N.py。渲染命令为 `manim -ql section_N.py SectionNScene`，预期输出为 media/videos/section_N/480p15/SectionNScene.mp4。

失败时调用原始 ScopeRefineFixer，尝试局部修复，再回退为整体修复；其内部还有最多三次修复，外层限制不等于实际模型请求次数，因此另设全局 45 次调用上限。保留全部请求和各次渲染前代码快照，不手工修复生成内容。

原生 `generate_codes` 和 `render_all_sections` 使用分镜级线程/进程池；`--no_parallel` 仅控制不同主题。本次驱动器逐个调用原始方法，确保串行并保留统一用量记录，避免工作进程遗漏 section_codes 与 token 统计。

Critic 原生使用 Gemini 视频加网格参考图；素材增强使用 IconFinder。两者本轮均关闭，未添加替代 Agent、知识库或 RAG。原项目不含实际配音合成与独立字幕轨；lecture_lines 用 Manim Text 展示，不能视为语音。

## 资源路径
上游将 prompts、json_files 放在仓库根目录，但运行时按 src 路径解析。本实验用 src/prompts、src/json_files 两个相对符号链接解决，src/assets/icon 仅为空目录；未下载外部素材。参考图仅在开启 Critic 后才有实际需要。

## 实验配置
DeepSeek OpenAI 兼容接口，模型/URL/密钥来自环境变量；原始提示词、教学时长要求、分镜、Manim 质量参数均保持不变。未额外注入高中生物约束，target_audience 由 Planner 原生生成，报告将如实记录。
''',
'SETUP.md':'''# 运行环境与步骤

服务器 SSH 主机别名为 motion-data。工作目录 `/autodl-tmp/code2biovideo` 指向实际数据盘 `/root/autodl-tmp/code2biovideo`，防止使用空间不足的系统盘。

独立环境：`/autodl-tmp/code2biovideo/env`，Python 3.11，Manim Community 0.19.0，OpenAI SDK 1.90.0，FFmpeg 7.1.1，TeX Live 2026。安装来源 conda-forge；未安装完整上游锁定依赖，因为本轮禁用评估器、Gemini 和外部素材。

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
''',
'CHANGELOG.md':'''# 最小适配记录

1. `src/gpt_request.py`：新增 request_deepseek_token，使用 OpenAI SDK；模型、Base URL、密钥均从环境变量读取。返回原生 `(completion, usage)`，无需改变 JSON/代码解析；保存原始请求与响应、实际模型、词元、耗时、结束原因。SDK 隐式重试设为 0，最多两次显式尝试；鉴权、余额、限流、格式错误立即停止。
2. `src/agent.py`：注册 deepseek Provider 和 CLI 选项；ScopeRefineFixer 初始化从未定义全局变量 api 改为 self.API；移除原生 Iconfinder 密钥明文打印。
3. `src/prompts`、`src/json_files`：符号链接修复上游目录解析不一致；`src/assets/icon` 建立空目录。
4. 仓库外辅助文件：run_deepseek_experiment.py 仅串行调度原生方法、记录指标并包装渲染进程；sandbox_exec.py 提供隔离，不改变生成的科学内容。关闭视觉反馈与素材增强。
5. 所有 prompts/*.py 与上游字节一致；api_config.json 和 run_agent_single.sh 保持原样，无密钥入库。完整差异见 upstream.patch。
6. 上游源码通过本地稀疏克隆再上传，保留 Git 对象和版本；直接服务器克隆与完整压缩包下载曾失败，未因此替换源码版本。Windows 换行转换已恢复为上游原始字节。
''',
'RUN_LOG.md':'''# 真实运行记录

- 2026-11-23（北京时间）：通过 motion-data SSH 登录。服务器默认 root；生成代码另以普通 UID 执行。
- 直接 GitHub 克隆失败：GnuTLS recv error (-110)。本地首次完整克隆遇到 TLS EOF；随后 `git clone --depth 1 --filter=blob:none --no-checkout` 成功，稀疏检出 src、prompts、json_files，上传至服务器。未下载上游演示视频冒充结果。
- `/autodl-tmp` 位于系统盘，仅余约 1.4 GB；实际数据盘是 `/root/autodl-tmp`，当时剩余约 166 GB。通过项目目录符号链接保留用户指定路径。
- 首次 conda 安装因多通道元数据获取耗时中止；改为单 conda-forge 通道并独立缓存后安装成功，原始日志均保存在项目 logs/ 下。
- `/models` 鉴权成功；实际模型列表保存在 logs/deepseek-models.json。
- 环境冒烟测试返回码 0；隔离测试输出 ISOLATION_OK。详见项目 logs/experiment-console.log 与 tests/environment/render_logs/。
- 实验命令：独立环境运行项目根目录的 run_deepseek_experiment.py。A 数学主题完成后串行启动 B DNA 主题；不运行全量主题、评估器、视觉反馈或素材下载。
- 分主题完整日志：experiments/biology_baseline/logs/{A_math_deepseek,B_dna_deepseek}/run.log；请求及用量：各目录 api/；指标：metrics.json。
- 实际状态和最终视频以 RESULTS.md、metrics.csv 及主题 metrics.json 为准。
'''
}
for name,content in docs.items(): (exp/name).write_text(content,encoding='utf-8')
env=Path('/autodl-tmp/code2biovideo/env')
with (exp/'environment-explicit.txt').open('w') as f:
 subprocess.run(['/root/miniconda3/bin/conda','list','-p',str(env),'--explicit'],stdout=f,check=True)
with (exp/'upstream.patch').open('w') as f:subprocess.run(['git','-C',str(root),'diff','--','src'],stdout=f,check=True)
print('Initial documentation written')
