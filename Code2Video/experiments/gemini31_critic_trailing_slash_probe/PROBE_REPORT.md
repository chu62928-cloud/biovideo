# 带末尾斜杠的请求地址测试
配置Base URL：https://apiclaude.cc/v1/
OpenAI SDK实际请求：https://apiclaude.cc/v1/chat/completions
模型：gemini-3.1-pro-preview
输入：真实DNA分镜MP4、上游GRID参考图、原始Critic布局提示词。自动重试0次。

结果：{
  "mode": "original_video",
  "requested_model": "gemini-3.1-pro-preview",
  "max_tokens": 2500,
  "retries": 0,
  "timestamp_utc": "2026-11-23T05:41:14Z",
  "status": "error",
  "error_type": "InternalServerError",
  "http_status": 503,
  "elapsed_seconds": 11.262,
  "configured_base_url": "https://apiclaude.cc/v1/",
  "actual_request_url": "https://apiclaude.cc/v1/chat/completions"
}
错误：{"message": "All available accounts exhausted", "type": "server_error"}
