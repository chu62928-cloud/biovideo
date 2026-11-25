# 最小适配记录

1. `src/gpt_request.py`：新增 request_deepseek_token，使用 OpenAI SDK；模型、Base URL、密钥均从环境变量读取。返回原生 `(completion, usage)`，无需改变 JSON/代码解析；保存原始请求与响应、实际模型、词元、耗时、结束原因。SDK 隐式重试设为 0，最多两次显式尝试；鉴权、余额、限流、格式错误立即停止。
2. `src/agent.py`：注册 deepseek Provider 和 CLI 选项；ScopeRefineFixer 初始化从未定义全局变量 api 改为 self.API；移除原生 Iconfinder 密钥明文打印。
3. `src/prompts`、`src/json_files`：符号链接修复上游目录解析不一致；`src/assets/icon` 建立空目录。
4. 仓库外辅助文件：run_deepseek_experiment.py 仅串行调度原生方法、记录指标并包装渲染进程；sandbox_exec.py 提供隔离，不改变生成的科学内容。关闭视觉反馈与素材增强。
5. 所有 prompts/*.py 与上游字节一致；api_config.json 和 run_agent_single.sh 保持原样，无密钥入库。完整差异见 upstream.patch。
6. 上游源码通过本地稀疏克隆再上传，保留 Git 对象和版本；直接服务器克隆与完整压缩包下载曾失败，未因此替换源码版本。Windows 换行转换已恢复为上游原始字节。

7. 第一轮默认思考模式下，数学代码和 DNA 分镜分别达到 10000 词元上限并截断。失败目录 A_math_deepseek / B_dna_deepseek 完整保留；第二轮 A2_math_deepseek_nonthinking / B2_dna_deepseek_nonthinking 显式传入 thinking.type=disabled，值由 DEEPSEEK_THINKING 环境变量控制。原始提示词与输出上限不变。官方依据：https://api-docs.deepseek.com/guides/thinking_mode/ 。
8. Conda texlive-core 仅有二进制，公式渲染发现缺少格式与宏包。暂停实验，安装项目私有 TeX Live；保留安装日志和误触发的模型修复调用，不把这些渲染失败归因于模型。增加独立矩阵公式冒烟测试。隔离允许只读访问私有 TeX 目录。

9. 实验驱动器日志包装遗漏 FFmpeg 转发已修复；保留修改前指标与错误日志。通过原生 merge_videos 重新合并，未修改视频内容或调用模型。
10. 分阶段恢复脚本只复测/重新合并现有 Agent 输出。第 4 节模型自动修复差异已独立保存；代码来源逐节审计完成。
