# V4.3.1 科学模型可靠性与 Wan 视频实验

## 已执行与真实状态

按照用户选择，本轮只尝试 Wan3.0，不提交 Seedance。已使用服务器现有百炼密钥，向北京 DashScope 视频生成接口提交1次真实 wan3.0-video 首尾帧任务。HTTP403，错误码 AccessDenied.Unpurchased，任务编号为null，没有生成任务或MP4。请求编号223c94c4-9970-9519-ac3a-3d9e87c963f8。该错误表示当前账户对此模型无可用权限，不能用“密钥有效”替代开通。没有重复付费提交。当前官方文档也提供业务空间专属maas域名；后续应在账户控制台核对模型开通、所属空间与地域，再配置准确接口，不盲目切地区碰运气。

首尾参考来自已审核有丝分裂科学模型。历史截图审核存在动粒几何歧义，因此DeepSeek另生成可编辑状态图计划，开发者再将外侧锚点与纤维端点绑定。最后独立Qwen审核科学/视觉均PASS。参考图无标签、无第三方插图；原始失败参考审核保留。这里有明确开发者几何干预，不能当作全自主生成成功，更不证明中间视频机制。

## 科学可靠性

现有BiologyExpertAgent注册EvidenceSufficiencyAuditor和ScientificCausalGraphValidator。三主题使用同一通用实现。证据审核识别DNA5项、囊泡6项缺口，有丝分裂没有新增证据缺口；因果检查采用有限状态路径、完成依赖和并发冲突检查。旧模型未声明initial_states，因此报告待明确初态/生产者，不凭此推翻已限定的历史科学PASS。文本别名和状态语义等价仍需结构化升级，不能只靠字符串不同宣布科学错误。

DNA进行了两轮有界定向检索，取得一个新教材来源；候选经历原文引用修复和独立科学审核，仍REVISE：核酸酶身份、引物替换执行者及nick/gap区别未解决。囊泡得到一个缺少正文的Reactome页面，模型错误引用标题作机制证据，被精确原文检查拒绝；后续定向检索没有新进展，停止。没有删除原有过程/约束来提高通过率，没有批准或覆盖历史模型。

## 运行与争议复核

对历史同场景在新通用适配器中实际重新渲染/解码，124次观测中248条关系实例有运行端点观测、107条仅声明；这些是样本条数而不是不同科学关系数量。加入透明度、画面范围、有效尺寸、对象身份、实际端点与跳变观测。结果不等同像素可见性证明，不给抽象关系自动授予画面PASS。

旧视频重影意见依据原始解码帧、注册标签边框和既有独立观察记录标记NOT_CORROBORATED，非证明全部帧无缺陷；原意见不覆盖、不通过新投票求一致。

## 源码与复现

新增src/biology_expert/model_reliability.py、observation_fidelity.py、src/video_generation/providers.py；扩展agent.py与scientific_scene/adapters/typed_manim_adapter.py。无主题专用生产分支。

离线命令：`python -m pytest experiments/biology_expert_v4_3_1/tests experiments/biology_expert_v4_3/tests experiments/biology_expert_v4_2_2/tests experiments/biology_expert_v4_2_1/tests -q`，67/67通过；最后初态不确定性调整后20项新增测试再次通过。历史47项保持可执行。样本包括合成单元、历史回归和真实重渲染；没有Wan生成样本。

生产Provider支持准备、能力校验、估价、显式提交、任务锁/恢复、状态查询、立即下载与用量记录。Seedance仅保留未选中的dry-run占位适配器，不宣称真实API接入完成。真实权限失败不可自动重提交；不保存密钥、认证头或带凭证下载链接。

## 局限与未实现

尚未达到“两主题自动修复后独立批准”。修复补丁是完整候选更新加过程/约束保留门禁，尚非完整字段级最小补丁；没有进展时停止。缺少真人科学/教学审核，部分合成测试只验证结构。运行几何观察不是视频对象检测/跟踪。未生成wan.mp4、seedance.mp4或双模型比较图，不提供占位成功视频。Manim重放仅作为观测回归，不冒充Wan结果。

## 后续

先在百炼模型详情确认Wan3.0开通条件及业务空间/地域，再恢复真实生成；保留这次403记录。科学线优先获得真正专门的第二来源，解决状态生产链后再生成DNA/囊泡视频；暂不扩展六节。

本轮模型调用与词元：{"deepseek_calls": 16, "qwen_calls": 4, "input_tokens": 128194, "output_tokens": 37161, "failed_model_requests": 0, "reported_cost": null}。Wan成功前估价为5秒×0.3元/秒=1.5元，非实际账单；实际收费不可得。
