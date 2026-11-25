# Biology-Aware Code2Video V2：Section4 实验报告

**工程链路修复已通过离线测试，A1/A2真实生成并完整渲染；生物机制仍有明确失败项，A3因Qwen超时未完成。** 这是一轮模型替代与机制约束实验，不是原论文模型配置的严格复现。

## 一、工程改动

- 新增src/biology_v2_pipeline.py：对象标识建议校验、construct函数级AST替换、导入/基本安全检查、隔离完整渲染与解码、不可变代码/视频配对版本和原子指针提交。失败候选保留，成功版本不被失败代码污染。
- 新增src/biology_runtime.py：通用组件/SVG加载、稳定对象ID、活动位点绑定与实际逐帧几何轨迹，不包含完整教学动画。
- V2使用该事务入口，旧GridCodeModifier保留作历史复现；旧脚本不会自动获得V2保护。没有庞大改造原Agent，也没有增加RAG或新Agent。
- 历史Section2/4旧行号修改均实际复现缩进错误。历史Section3两版动画重放后，DNA/Helicase包围盒分离从0.0增至2.3125场景单位。
- 最终离线测试10项全部通过，API=0；8个原创独立SVG加载渲染通过。SVG为CC0示意图，不是真实蛋白质结构。
- 真实运行发现观测器误计旧绑定及VGroup根对象可见性，两项基础设施问题已修正并补测；使用相同模型候选重新渲染，未手工改动画。最后一次纯观测器复测的A1/A2动画源码与MP4哈希均未改变。

## 二、实验完成状态

| 组 | 状态 | 新渲染 | 时长 | 说明 |
|---|---|---|---:|---|
| A0 | 已保留 | 否 | 35.400s | 精确复制历史代码与MP4；不调用模型 |
| A1 | 工程门禁通过 | 是 | 26.867s | 3次真实Coder调用，最终接受已保存候选2；机制检查未全通过 |
| A2 | 工程门禁通过 | 是 | 33.467s | 3次真实Coder调用，最终候选3通过；实际使用4类SVG |
| A3 | Critic阶段失败 | 否 | 33.467s（A2复制） | Qwen第一轮180秒超时；无反馈、无候选、无修复视频，第二轮未执行 |

A3初始复制符合实验设计，**但不得称为Critic生成或改进的视频**。API异常没有被转换为“没有布局问题”。收到超时后停止了全部新增模型请求；DeepSeek剩余2次、Qwen剩余1次没有继续使用。

所有可播放视频均通过FFmpeg全片解码，854×480、15帧/秒、无音轨。A1/A2完整场景代码与保存的DeepSeek响应逐字一致，见model_provenance.json。手写极小动画仅用于测试，不算A1/A2成果。

## 三、主要发现

1. 结构化机制与分镜促成了独立模板/新链、逐核苷酸添加、重复引物和分开显示的加工步骤；但输入规格不是严格的科学执行器，不能保证关系都被正确落地。
2. A1把平行排列的新链画在倾斜Y形模板之外；A2采用了更容易分辨的酶SVG和短标签，但把叉简化成了上下水平模板与中部连接，拓扑表达仍不理想。仍应专注Section4，不扩展六节。
3. **A1/A2的后随链补缺均按左→右新增绿色子块，与本图下模板极性不一致，判fail。** 证据在biological_checks.json、nucleotide_observations.json、实际第5事件与源代码。不能只凭字幕“5′→3′”判通过。
4. 本轮无法判断Critic是否改善机制或布局，因为没有得到有效的Qwen反馈；A3与A2哈希一致只是初始复制，并非成功修复。
5. 自动布局指标没有注册文字覆盖，因此标签重叠“0”并不可靠。对照图和人工检查清单仍必要。各项pass/fail/uncertain及依据见manual_review_checklist.md。
6. A1/A2为独立Coder采样，且存在基础设施修正/重放，单样本不能严格分离SVG的因果效应。只报告可见变化，不宣称因果归因已经成立。

## 四、运行成本与工程指标

- DeepSeek：6/8次，输入62,468、输出38,899，合计101,367词元。
- Qwen：1/2次，API超时，未返回词元用量；记录为未知，不能写0。未自动重试。
- Wan：0个任务；默认dry-run没有HTTP、上传或视频生成。官方Workspace和参考图公开HTTPS URL尚未配置，不臆造上传接口或地域。
- 未取得账单，实际金额未知。旧历史调用计数完整保留，旧45上限仅来自旧脚本，本次使用明确授权的独立8/2/1预算。
- 已完成且可核实的完整渲染调用：A1 5/5、A2 3/4；这些包含无API重放，不能冒充初始Coder一次成功率。首次代码两组均未直接通过全部门禁。
- A3候选修复次数0，修复成功率不可计算；正式实验没有失败更新覆盖成功版本，事务拒绝与中断均另存。离线测试证明了旧成功配对在渲染失败时回滚，不能声称已完成一次真实A3修复。
- 每组已记录API与事务耗时之和在metrics.json的measured_active_seconds；暂停、人工检查和中断缺失时间不虚构为精确总耗时。

## 五、产物路径

实验根目录：/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4

- A0_baseline：`/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/groups/A0_baseline/video.mp4`；SHA256：`c19f6640b5839d5eb0ffbb843884e82b98e2ccbc20406509955b6872cacc5469`。

- A1_mechanism：`/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/groups/A1_mechanism/video.mp4`；SHA256：`539370b925ceb5b83062235a710dd7afa6d69f6b203485fd4b5382a4c9684782`。

- A2_mechanism_assets：`/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/groups/A2_mechanism_assets/video.mp4`；SHA256：`4154b5fef41c8552ea8fe42b06d346a1a3fb2b02888b66db35238b3bd4cb5459`。

- A3_mechanism_assets_critic：`/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/groups/A3_mechanism_assets_critic/video.mp4`；SHA256：`4154b5fef41c8552ea8fe42b06d346a1a3fb2b02888b66db35238b3bd4cb5459`。

- 对照图：/root/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/comparisons/all_groups_by_event.jpg，以及5张同事件对照图。
- 机制规格、统一分镜、旁白：specs/section4_mechanism.json、specs/section4_storyboard_v2.json、narration.md。
- 资产与许可：assets/asset_registry.json及8个SVG；加载测试assets/svg_loading_test.json。
- 真实调用、错误、失败候选与事务：logs/、failure_reasons.json、groups/*/attempts/。
- pipeline_tests.json、metrics.json/csv、model_provenance.json、source_changes.patch记录工程证据。
- Wan脚本tools/run_wan_comparison.py；dry-run见comparisons/wan/dry_run.json，参考帧见comparisons/A2_fork_reference.png。该图拓扑仍需人工确认，不建议直接用于收费对照。

## 六、下一步建议

先继续优化Section4。优先将新链与酶的实际几何关系绑定到模板路径与真实3′末端，而非仅依赖模型声明的锚点；再约束补缺的逐核苷酸方向与最终残留RNA的解释。之后补上所有文本的注册与几何检测。查明Qwen超时原因后，另设明确预算重跑A3；本轮不增加API、不扩展六节、不启动Wan。
