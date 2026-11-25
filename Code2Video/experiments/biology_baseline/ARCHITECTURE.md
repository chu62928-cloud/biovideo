# Code2Video + DeepSeek：架构与原始调用链

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
