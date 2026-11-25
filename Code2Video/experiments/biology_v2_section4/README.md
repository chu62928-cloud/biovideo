# Biology-Aware Code2Video V2：Section4
独立实验目录，不覆盖旧实验。先读EXPERIMENT_PROTOCOL.md，再读RESULTS.md与metrics.json。
A0为真实历史基线复制；A1/A2完整动画代码由DeepSeek生成；A3仅从成功A2开始。Qwen第1轮超时后停止新增API，A3当前MP4是明确标记的A2初始复制，不是Critic改进结果。
密钥仅在仓库外服务器项目.env中。本目录没有密钥。
离线回归：tools/pipeline_tests_v2.py。
生成：tools/run_biology_v2.py；检查器修正后的无重新抽样恢复：tools/continue_after_checker_fix.py。
Wan：tools/run_wan_comparison.py，默认ENABLE_WAN=0，只有dry-run，无HTTP与收费生成。
