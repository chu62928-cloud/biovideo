# Biology Expert Agent V3 MVP
实现位置：src/biology_expert/；实验位置：experiments/biology_expert_v3/。
## 快速检查（不调用模型）
cd /autodl-tmp/code2biovideo/Code2Video/src
/autodl-tmp/code2biovideo/env/bin/python -m biology_expert tools
/autodl-tmp/code2biovideo/env/bin/python -m biology_expert status
## 离线回归（无收费请求，会在沙箱中真实渲染一个测试夹具）
/autodl-tmp/code2biovideo/env/bin/python /autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v3/tests/test_offline_revision2.py
## API
BiologyExpertAgent.prepare_topic / review / plan_repair / verify_revision / run_gate。ToolRegistry限制白名单与调用次数；ModelGateway持久预算并阻止未确认故障后的新付费调用；WorkflowState按内容哈希管理依赖。
命令行research/review默认DRY_RUN，只有--execute才运行实际工具；同run-root继承已有预算。不得用新目录绕过同一实验的成本限制。
本次DeepSeek8/8；Qwen原2+用户额外2，总上限4，实际3，剩余1；不应为用完预算继续请求。
## 真实实验链路
run_real.py保留首轮原始失败；correct_evidence_and_revalidate.py修正来源大小写与UTF8后，实际补检索和语义核验；replay_saved_candidate.py只规范化已生成的第二候选缩进并完整渲染；retry_science_after_diagnosis.py在用户增额后核实截断原因，限制思考预算并启用JSON模式重试；finalize_v3.py汇总验证。
这些是本次实验审计脚本，不是可随意重复收费的向导。模型原始响应、最初异常与修正过程都保留。
## 发布原则
TransactionRenderer的current是工程配对缓存，并不等于科学批准；外层科学门禁未通过时，不创建APPROVED.json。本次方向局部通过，但完整视频科学审核REVISE，事务保持历史配对。候选视频仅供诊断。
## 依赖与限制
复用原Manim/OpenAI/requests/BeautifulSoup，新增jsonschema（版本见环境记录）。上游SCRIPT/CAST/ASSETS/STORYBOARD返工有接口与离线根因路由测试，尚未全部接入真实生成器。技能只有候选，不自动批准。
