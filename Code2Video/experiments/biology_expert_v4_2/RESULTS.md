# V4.2 阶段报告
日期：2026-11-25，北京时间。

状态：实际开发与实验部分执行，尚未达到完整验收。不能宣称通用科学审核升级已成功。

## 文件治理
扫描11741个文件，分类建议{"KEEP": 1241, "ARCHIVE": 9978, "DELETE_CANDIDATE": 514, "REFACTOR": 8}。实际删除0。原Git分支main、commit637509294e936b231d220bb555cf74eeedcb9dfd，有大量用户未提交修改，已保存binary diff/哈希，未重置。独立源码在/autodl-tmp/code2biovideo/Code2Video-v4.2-workspace/src。首次worktree因部分克隆缺blob远端拉取阻塞，停止仅新checkout后改为实际工作源码隔离副本。历史10404文件哈希变化0。

## 移除主题硬编码
旧scientific_review.py的DNA极性/增长端规则、固定检索目录、DNA/有丝分裂系统提示与机制检查在新入口退出；原样归档及examples/regression保留。不是把旧规则放JSON再默认加载。生产新核心不含主题名分支，原历史路径未被伪装成新版。

## 三主题真实契约
[
  {
    "topic": "dna_replication",
    "constraints": 8,
    "contract_review": "REVISE",
    "frozen": false,
    "coverage": "REVIEW_INCOMPLETE",
    "critical_gaps": 19,
    "actual_checks_measured": 0,
    "valid_science_mutations": 0,
    "detected": 0,
    "missed": 0,
    "false_positives": 0,
    "final_gate": "REVIEW_INCOMPLETE"
  },
  {
    "topic": "mitosis",
    "constraints": 8,
    "contract_review": "REVIEW_INCOMPLETE",
    "frozen": false,
    "coverage": "REVIEW_INCOMPLETE",
    "critical_gaps": 10,
    "actual_checks_measured": 0,
    "valid_science_mutations": 0,
    "detected": 0,
    "missed": 0,
    "false_positives": 0,
    "final_gate": "REVIEW_INCOMPLETE"
  },
  {
    "topic": "protein_translation",
    "constraints": 9,
    "contract_review": "REVIEW_INCOMPLETE",
    "frozen": false,
    "coverage": "REVIEW_INCOMPLETE",
    "critical_gaps": 21,
    "actual_checks_measured": 0,
    "valid_science_mutations": 0,
    "detected": 0,
    "missed": 0,
    "false_positives": 0,
    "final_gate": "REVIEW_INCOMPLETE"
  }
]

DNA8条、翻译9条真实自动契约已独立请求复核但不通过；有丝分裂真实生成契约有枚举格式错误，保存原始响应，RELATION/DIRECTION仅归类为STRUCTURAL后Schema通过，尚未完成独立科学核验。无契约冻结或新科学批准。翻译无人工facts、规则或预制Scene，实际生成新抽象Scene和正常/错误分镜；同次模型出题/自评不算独立准确率，独立事实依据和运行检测仍有缺口。

## 真实外部证据与视觉参考
有效来源和图片数见metrics.json和references。NCBI的HTTP200验证页拒绝，错误教材URL保留，通过通用邻近章节发现真实正文。所有契约引文逐条核对原文，精确匹配不等于蕴涵成立。真实参考图已下载，但图片语义未独立核实、许可未确认，无外部素材导入；未获取参考视频，不冒充视频科学对照完成。

## 覆盖与注错
覆盖率分母来自契约实体/过程/关系需求。系统报告多项关键科学约束只能VLM或部分验证、缺实际观测，均REVIEW_INCOMPLETE。合成通用测试可检出对象/身份/持续关系/顺序/状态/数量错误且颜色负对照不误报；真实主题科学错误注入有效样本0，仅颜色负对照有效，不能报告真实检出率100%。这证明当前契约到可执行观察映射仍不足。原始失败、NOT_TESTED、模型结构错误均保存。

## API阻塞和真实用量
{
  "deepseek": {
    "requests": 11,
    "input_tokens": 78852,
    "output_tokens": 28004
  },
  "qwen": {
    "requests": 2,
    "known_tokens": 0,
    "token_usage_unknown": true,
    "errors": [
      "403 AccessDenied.Unpurchased (qwen4-max)",
      "400 Arrearage (qwen3.8-27b)"
    ]
  }
}
Qwen4-max真实403 AccessDenied.Unpurchased。用户要求换qwen3.8-27b后真实请求400 Arrearage，官方错误指向账户欠费/余额状态。两次都没有模型审核结果，不记为PASS。停止新增付费请求，未拿Mock冒充。真实金额/失败请求词元未知。Wan/Seedance0。

## 测试与未完成项
11项离线通用测试通过，均标记合成/模拟。尚需：完成独立有丝分裂契约审核、充分的可执行语义映射、真实主题有效科学注错、参考图语义核查与完整视频科学审核、更多输出Schema门禁。异常/例外约束报告UNSUPPORTED，不忽略后通过。账户恢复前继续离线工程，不能发布新版科学批准。

## 版本同步
已按用户授权推送https://github.com/chu62928-cloud/biovideo.git，首次4a20c1a，重要修改后更新；无定时自动任务。服务器独立部署密钥保留本机，不入库。密钥和环境/大视频不上传，证据摘要及哈希保留。

## 建议
当前不宜接入六章节自动生成或启动Wan/Seedance对照。先恢复账户，补足契约审查与实际观察能力，证明新主题至少一个独立科学错误能被自动检出。V4.1批准不代表V4.2通过。
