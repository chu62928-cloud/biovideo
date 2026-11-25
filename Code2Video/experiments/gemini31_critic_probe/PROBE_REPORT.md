# Gemini 3.1 Pro Critic 实测

日期：2026-11-23（北京时间）。用户已同意从 Gemini 3 Pro 改用 Gemini 3.1 Pro。

## 实际请求
- 端点：https://apiclaude.cc/v1/chat/completions
- 协议：OpenAI兼容；请求模型 gemini-3.1-pro-preview。
- 输入：基线DNA第1节的真实MP4，及固定上游版本的GRID.png；保持上游视频的image_url/data:video/mp4格式与原始布局Critic提示词。
- 最大输出2500词元，超时120秒，自动重试0次。

## 结果
HTTP503，服务端错误：All available accounts exhausted。耗时10.192秒。
没有模型响应正文、有效布局JSON或词元用量；接口没有报告计费数据，不能将用量记为0。
鉴权此前已通过，但本次上游模型账号池不可用。因此尚不能确认该中转站的视频协议兼容性，也不能确认Critic视觉分析能力。

没有继续改试图片：本次属于上游资源错误，而不是可证实的媒体格式错误。没有反复重试，没有启动DeepSeek修复或渲染，没有修改已冻结的基线代码或视频。

## 产物
- original_video_metrics.json：真实请求指标。
- original_video_error.json：脱敏错误正文。
- critic_original_prompt.txt：实际使用的上游布局提示词。
- probe_gemini31.py：不含密钥的探测脚本。
- 项目logs/gemini31-probe.log：执行日志。

配置在仓库外的项目私有.critic.env，权限600。恢复服务后应以新输出目录重测，保留本次失败。需要中转站运营方确认 gemini-3.1-pro-preview 的上游账号池可用性；不能据此认定用户自己的余额不足。
