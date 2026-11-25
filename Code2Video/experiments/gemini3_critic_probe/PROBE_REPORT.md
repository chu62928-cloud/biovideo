# Gemini 3 Pro 中转接口探测

日期：2026-11-23（北京时间）。原 Code2Video + DeepSeek 基线保持冻结，本次单独记录，不替换已有视频。

- 请求地址：https://apiclaude.cc/v1 ，已去掉用户链接末尾的中文句号。
- 协议：OpenAI 兼容；认证配置在仓库外私有文件 .critic.env，权限600。
- GET /models 成功；模型列表包含 gemini-3.1-pro-preview，但未列出 gemini-3-pro-preview。
- 对 gemini-3-pro-preview 发起一次真实视觉请求：使用现有 DNA 第1节渲染画面及原始布局 Critic 提示词，最多1500输出词元，SDK重试0次，超时90秒。
- 实际响应：HTTP503，服务端提示 No available accounts: no available accounts。耗时1.799秒。
- 未获得模型回答、词元用量或有效Critic反馈。没有将错误当成“画面无问题”，没有更改任何生成代码。
- 该错误说明本次请求没有可用上游账号；不能据此判断视觉格式兼容或不兼容，也不能确认可接受MP4视频。
- 待用户选择是否改用列表中的 Gemini 3.1 Pro，再继续图片/视频输入兼容性测试。尚未启动完整视觉反馈重渲染。

证据：models.json、gemini3pro_frame_metrics.json、gemini3pro_error.json、critic_original_prompt.txt。
