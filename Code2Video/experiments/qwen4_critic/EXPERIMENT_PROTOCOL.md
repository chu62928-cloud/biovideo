# Qwen4 Critic 两轮记录协议
日期：2026-11-23（北京时间）。

## 用户约束
仅替换 Critic 为 qwen4-max，并做协议必要适配；不更改原项目其他配置、输入、提示词或原生反馈修复逻辑。Planner/Coder继续DeepSeek，素材开关保持关闭。

## 输入与流程
使用已生成DNA项目的相同知识点、outline.json、storyboard.json和6份初始Manim代码，经原生缓存加载路径读取；未重新写入教学内容、专业规则或提示词。输入哈希见 input_hashes.json。原始基线目录冻结。
逐节调用已有原生 generate_section_code 和 render_section，与上一轮串行运行方式相同。render_section 内部执行 get_mllm_feedback → optimize_with_feedback，feedback_rounds=2；修复器、GridCodeModifier、Manim渲染参数均不改。
记录器仅包装原生反馈/优化函数，保存每节每轮返回后的快照。最后将同一轮的6个快照用原生 merge_videos 合并，得到第一轮与第二轮视频。
配置沿用基线：max_code_token_length=10000，max_fix_bug_tries=2，max_regenerate_tries=2，max_feedback_gen_code_tries=1，max_mllm_fix_bugs_tries=1。必要启用use_feedback并记录两轮；未调整其他生成参数。
不强制成功：原生优化失败时可能保留上一个成功视频，round_events.json会明确标识，不能将保留视频算作修复成功。接口异常也不当作无布局问题。

## 唯一模型接口适配
src/gpt_request.py新增Qwen视觉请求及Critic路由；src/agent.py将原先固定Gemini请求改为该路由。其余Agent方法与prompts保持不变。
DASHSCOPE_API_KEY、QWEN_BASE_URL、QWEN_MODEL、CRITIC_PROVIDER在仓库外项目.env中，权限600。
Qwen视频输入按官方video_url字段传完整MP4，同时附原始GRID.png；这是必要协议变换，不使用自选关键帧替代视频。保持原提示词、默认10000词元上限，不覆盖Qwen思考模式或抽帧频率。
调用失败不进行自动重试，避免持续错误消耗；该接口错误控制单独记录，不作为模型能力调整。原生代码生成/修复的次数限制不变。

## 对照解释
第一轮反馈评价初始视频；第二轮反馈评价第一轮修复后或原生保留的视频。没有额外增加第三次评价来评价最终第二轮视频。因此不能把第二轮反馈中的问题数当成第二轮修复后的问题数。
本项目仍为Code2Video + DeepSeek生成、Qwen4 Critic替代实验，不是原论文模型配置的严格复现。

官方说明：
https://www.alibabacloud.com/help/en/model-studio/qwen4-max
https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions
