from pathlib import Path
import json,sys,hashlib,time,subprocess,collections,zipfile,shutil,ast
from PIL import Image,ImageDraw
R=Path('/autodl-tmp/code2biovideo/Code2Video');ROOT=R.parent;E=R/'experiments/biology_expert_v3';sys.path.insert(0,str(R/'src'))
from biology_expert.state import write,WorkflowState
from biology_expert.tools.reviewers import review_result
from biology_expert.tools.mechanism_validator import mechanism_validator
from biology_expert.providers import ModelGateway
from biology_v2_pipeline import sha,probe
tests=json.loads((E/'tests/test_results.json').read_text());assert tests['all_passed']
b=json.loads((E/'test_B_revalidated_result.json').read_text());review=json.loads((E/'reviews/video/final_retry_review.json').read_text())
assert review['decision']=='REVISE' and review['targeted_gap_direction']=='PASS'
rows=json.loads((E/'logs/models/model_calls.json').read_text())
stats={}
for provider in ['deepseek','qwen']:
 rr=[r for r in rows if r['provider']==provider]
 stats[provider]={'requests':len(rr),'successful_structured_responses':sum(r['status']=='ok' for r in rr),'input_tokens':sum(r.get('usage',{}).get('prompt_tokens',0) for r in rr),'output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in rr),'total_tokens':sum(r.get('usage',{}).get('total_tokens',0) for r in rr),'api_seconds':round(sum(r['elapsed_seconds'] for r in rr),3),'retries':0}
assert stats['deepseek']['requests']==8 and stats['qwen']['requests']==3
# Pair/decoding/AST verification of the actual quarantined candidate.
before=b['before'];candidate=Path(b['candidate_video']);code=Path(b['candidate_code']);trace=Path(b['candidate_trace'])
assert sha(before['code'])==before['code_sha256'] and sha(before['video'])==before['video_sha256']
assert sha(code)==b['candidate_manifest']['code_sha256'] and sha(candidate)==b['candidate_manifest']['video_sha256']
cp=subprocess.run([str(ROOT/'env/bin/ffmpeg'),'-v','error','-i',str(candidate),'-f','null','-'],capture_output=True,text=True)
assert cp.returncode==0 and not cp.stderr.strip()
pack=json.loads((E/'knowledge/dna_replication/knowledge_pack.json').read_text())
measured=mechanism_validator({'code':code.read_text(),'trace':json.loads(trace.read_text())},{'knowledge_pack':pack})
target=next(c for c in measured['checks'] if c['check_id']=='lagging_gap_growth');assert target['status']=='PASS'
write(E/'traces/final_candidate_mechanism.json',measured)
# Current production stage states reflect final scientific decision, not engineering replay.
state=WorkflowState(E/'state')
state.register('final_candidate_code',code,'CODE_GATE')
state.transition('VIDEO_SCIENCE_GATE','REVISION_REQUIRED',review)
state.transition('FINAL_SCIENCE_GATE','HUMAN_REVIEW_REQUIRED',review)
assert not (E/'state/APPROVED.json').exists()
# Do not silently accept a model's proposed upstream root cause without source provenance.
story=json.loads((R/'experiments/biology_v2_section4/specs/section4_storyboard_v2.json').read_text())
root_audit=[]
for i in review['issues']:
 if i['issue_id']=='SCI_LEADING_POL_IDENTITY':
  root_audit.append({'issue_id':i['issue_id'],'model_proposed_stage':i['root_cause_stage'],'earliest_observed_stage':'ANIMATION_CODE','basis':'Current storyboard names generic polymerase, no Pol delta/epsilon labels; the concrete Pol delta label is present in rendered code. Earlier script/cast provenance requires separate confirmation. Do not blindly route to SCRIPT.','decision':'NEEDS_HUMAN_REVIEW_FOR_UPSTREAM_ATTRIBUTION'})
write(E/'reviews/video/root_cause_provenance_audit.json',root_audit)
mit=json.loads((E/'knowledge/eukaryotic_mitosis/knowledge_pack.json').read_text())
c=json.loads((E/'reviews/script/test_C_revalidated.json').read_text())
normal=next(x for x in c['samples'] if x['sample_id']=='normal_control')
bad=next(x for x in c['samples'] if x['sample_id']=='injected_errors')
assert normal['decision']=='PASS' and not normal['issues'] and bad['decision']=='REVISE' and len(bad['issues'])==4
# Preserve all historical V2 files and original providers byte for byte.
frozen=json.loads((E/'frozen_inputs.json').read_text());mismatches=[]
for rel,expected in frozen.items():
 p=R/rel
 if not p.exists() or sha(p)!=expected:mismatches.append(rel)
assert not mismatches,'Historical files modified'
write(E/'historical_integrity.json',{'checked':len(frozen),'mismatches':mismatches,'all_preserved':True})
events=[json.loads(x) for x in (E/'state/events.jsonl').read_text().splitlines()]
selected=[e for e in events if e['event']=='tool_selected']
tool_counts=dict(collections.Counter(e['selected_tool'] for e in selected))
autonomy={'policy':'Bounded reactive state/observation policy, not unconstrained LLM tool orchestration','mode':'REAL_TOOL_CALLS; offline mocked autonomy branches separately labeled','tool_counts':tool_counts,'examples':[]}
for name in ['evidence_retriever','evidence_fetch','fact_verifier','mechanism_validator','video_reviewer','repair_planner']:
 row=next((x for x in selected if x['selected_tool']==name),None)
 if row:autonomy['examples'].append({'goal':row['goal'],'chosen_tool':name,'reason':row['reason'],'time':row['time']})
write(E/'traces/autonomy_summary.json',autonomy)
knowledge_stats={}
for p in [pack,mit]:
 knowledge_stats[p['topic_id']]={'facts':len(p['facts']),'verified':sum(f['verification']=='VERIFIED' for f in p['facts']),'unverified_or_conflicted':[f['fact_id'] for f in p['facts'] if f['verification']!='VERIFIED'],'sources':[{'title':v['title'],'url':v['url'],'publisher':v['publisher']} for v in p['evidence']],'limitations':'Retrieved-span checks + separately prompted same-provider semantic checking; not independent expert consensus. Multiple OpenStax pages are one publisher.'}
metrics={'date_beijing':'2026-11-24','status':'MVP_IMPLEMENTED_AND_TESTED_SCIENTIFIC_RELEASE_BLOCKED','offline_tests':tests,'knowledge':knowledge_stats,'test_A':{'direction_detected':True,'direction_qualified_by_template_and_nascent_polarity':True,'topology':'UNCERTAIN_FROM_GEOMETRY_THEN_SCIENTIFIC_VIDEO_BLOCKER','enzyme_contact':'Registered anchor checks plus measured proximity to actual nucleotide additions; does not prove chemical contact'},'test_B':{'coder_generation_attempts':2,'initial_format_rejections':2,'saved_second_candidate_format_replays':1,'new_generation_on_replay':False,'full_candidate_renders':1,'target_direction_check_passes':1,'scientific_publication_commits':0,'scientific_commit_success_rate':'0/1 full rendered candidate','rollback_pair_preserved':b['rollback_pair_preserved'],'final_video_review':review['decision'],'targeted_gap_direction':review['targeted_gap_direction'],'final_review_id':review['review_id']},'test_C':{'normal_samples':1,'normal_false_positives':0,'injected_samples':1,'injected_issue_count':4,'detected_issues':4,'initial_gate_error_preserved':True,'saved_model_response_revalidated_after_UTF8_fix':True,'new_model_request_for_revalidation':False},'model_usage':stats,'total_known_tokens':sum(v['total_tokens'] for v in stats.values()),'actual_bill_cost':None,'cost_note':'No account billing API access; tokens are measured, not a billed-cost claim','qwen_truncation_error':{'call_id':'v3_10','finish_reason':'length','total_output_tokens':9000,'reasoning_tokens':5664,'known_total_tokens':44275},'user_authorized_qwen_retry':{'additional_allowed':2,'used':1,'remaining':1,'last_call':'v3_11','last_call_valid':True,'profile':rows[-1]['request_profile']},'autonomy':autonomy,'historical_files_preserved':len(frozen),'approved_video':False,'candidate_video':str(candidate),'before_video':before['video'],'candidate_manifest':b['candidate_manifest']}
write(E/'metrics.json',metrics)
# Compare at exact actual timestamps, not storyboard planned timings.
out=E/'outputs/review';out.mkdir(exist_ok=True)
times=[28.6,29.0,30.2]
canvas=Image.new('RGB',(854*2,510*3),'#222222');draw=ImageDraw.Draw(canvas)
for col,(name,video) in enumerate([('Historical V2 input',Path(before['video'])),('V3 candidate - NOT APPROVED',candidate)]):
 for row,t in enumerate(times):
  p=out/f'frame_{col}_{row}.png'
  subprocess.run([str(ROOT/'env/bin/ffmpeg'),'-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-y',str(p)],check=True)
  canvas.paste(Image.open(p).convert('RGB'),(col*854,row*510));draw.text((col*854+10,row*510+483),f'{name} @ {t}s',fill='white')
canvas.save(out/'before_after_scientific_review.jpg',quality=92)
readme="""# Biology Expert Agent V3 MVP
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
"""
(E/'README.md').write_text(readme)
report=f"""# Biology-Aware Code2Video V3 实验报告
日期：2026-11-24（北京时间）。

## 结论
已实现并真实运行单一BiologyExpertAgent MVP：通用证据知识构建、分阶段审核、实际机制检查、最小代码返工、完整渲染与科学门禁回滚均接通。
本次方向目标修正通过，但最终科学审核为REVISE；未发布科学批准版视频。V1/V2共{len(frozen)}个冻结输入文件哈希全部保持不变。
这是Code2Video + DeepSeek + Qwen的模型替代实验，不是原论文模型配置的严格复现。

## 1. 架构与调用关系
主智能体BiologyExpertAgent提供prepare_topic、review、plan_repair、verify_revision、run_gate。一个Agent下挂12个工具：主题分析、资料检索、指定来源获取、知识构建、精确原文补充、支持摘录核验、事实语义核验、机制验证、阶段产物审核、视频科学审核、返工规划、候选修复经验管理。
选择策略是受状态和观察结果约束的反应式策略，不是无边界的LLM自主命令执行器。没有新增多Agent。模型负责证据综合/科学判断和Coder；程序控制白名单、预算、状态、版本和回滚。
主关系：证据缺口→检索/核验；真实运动可疑→机制验证；事实已知但画面含义不明→视频审核；已定位实现错误→结构化返工任务→原DeepSeek Coder→原V2完整渲染器→实际轨迹→重新科学审核。

## 2. 复用与新增
直接复用BiologyScene及对象/事件/绑定/采样，原DeepSeek和Qwen视频接口、8个SVG和V2 TransactionRenderer。没有重写事务渲染器，没有改动原agent.py/gpt_request.py/api_config.json/run_agent_single.sh。
新增src/biology_expert/包：Schema、内容哈希依赖图、统一审核、知识/证据工具、限额网关、局部AST范围约束、候选技能、命令行。Qwen截断诊断后新增仅V3使用的结构化接口适配器，保留原服务地址/密钥/模型/完整视频。

## 3. 自主决策证据
实际日志位于state/events.jsonl，简表位于traces/autonomy_summary.json。既有离线模拟分支也有真实工具调用，二者明确区分。
"""
for row in autonomy['examples']:report+=f"- {row['chosen_tool']}：{row['reason']}\n"
report+="""
并非对所有输入运行同一六步流程：SCRIPT直接依据知识做文本审查；ANIMATION_CODE使用实际轨迹；有画面歧义才进入完整视频科学审核；证据不足会补检索；已定位错误才生成返工任务。每步记录目标、白名单、选择、简短理由、真实输入/输出、终止原因，不交付内部思考文本。

## 4. 科学知识包
"""
for topic,ks in knowledge_stats.items():
 report+=f"\n### {topic}\n动态构建{ks['facts']}条事实，其中{ks['verified']}条满足当前证据与语义核验，未核实/冲突项：{ks['unverified_or_conflicted']}。VERIFIED只表示当前范围与来源核验，不等于跨物种无条件成立或专家共识。\n"
 for src in ks['sources']:report+=f"- [{src['title']}]({src['url']})。\n"
report+="""
每条事实关联实际获取的证据ID、标题、URL、可定位摘录/段落、访问时间、正文哈希。相同知识构建器用于两个主题，没有预置mitosis facts.json。
第一轮DNA教材发现有大小写匹配缺陷，导致仅取到综述、缺乏合成方向原始依据。最初检出记录保留，但不能作为已充分证据支持的结果。修正后真实补检索教材并独立核验，最后机制检查绑定具体方向事实，而非泛泛聚合酶角色。
HTML初次被错误按Latin1解码，造成有丝分裂摘录中的破折号乱码，门禁拒绝了原本有依据的事实。正确UTF8重新获取并验证全文哈希后，复用已保存的独立语义判断和脚本模型响应进行再校验；没有声称这是新的模型推理。
NCBI Bookshelf的HTTP200验证码页被标为UNVERIFIED。多页OpenStax属于一个出版社，不能当成多个独立来源。

## 5. 测试结果
- 离线测试最终28/28通过，真实API0；包括Schema、错误不放行、内容哈希依赖失效、缓存、不同工具分支、白名单/预算、持久两次返工上限、真实完整渲染后的科学回滚、未知引用、缩进解析、来源编码及用户明确增额不重置历史。
- Test A1：历史V2 A2的补缺DNA首次出现x为2.0917→2.2750→2.4583；结合下模板端点5′左/3′右、RNA引物和新链3′文字位置，测得相对模板读取方向投影为负，定位event_5_maturation与fill_dna_00..02。返工目标是核苷酸实际出现顺序，不是箭头或标签。
- Test A2：轨迹侧输出UNCERTAIN并要求视频科学审核；完整视频审核指出中央蓝色空心梯状体与两条模板不汇合，可能被读作额外DNA，且合成画在未解旋双链所占区域。属于机制/身份表达问题，不是简单移动图标。
- Test A3：注册酶与锚点距离及酶与实际新增核苷酸的接近性均检查；本样本没有明显距离超限。固定锚点本身可能错、身份标签可能混淆，故几何通过不能证明化学作用正确。
- Test C：正常脚本1例PASS、错误脚本1例REVISE。正常样本误报0/1；注错样本检出4/4：复制被放到后期、同源染色体配对/必需交换、错误的后期分离对象、一次有丝分裂产生四个单倍体核。样本极小，不作为泛化准确率结论。
- 有丝分裂初次ERROR及纠正后的保存响应重校验结果都保留；不是把错误无条件改为PASS。

## 6. 真实返工闭环
两次DeepSeek生成均返回带额外缩进/初始化语句的局部代码，最初被AST格式门禁拒绝。候选与异常完整保留。规范化解析后，只提取第二次响应本来生成的for循环，未手写任何目标动画。
抽象语法树比较证实只有目标补缺循环变化，其余模块、函数、事件、SVG和分镜不变。没有第三次Coder生成。
候选经完整Manim渲染和全视频解码，真实核苷酸首次出现x改为2.4583→2.2750→2.0917，局部方向检查PASS，聚合酶也随新增核苷酸移动。
科学审核首次响应被9,000输出词元截断，其中思考占5,664；finish_reason=length，JSON未闭合。该次费用用量仍计入，未记成零。
用户明确增加Qwen2次额度后，先保存原因核查，再以总输出12,000、思考预算4,096、JSON模式及最多3个主要问题重试同一完整视频。只用一次即取得有效JSON，耗时44.495秒，总词元38,796，方向PASS、整节REVISE。
剩余三项：复制叉/额外DNA拓扑、前导链聚合酶亚型呈现、连接酶所封位置并非真实相邻切口。Polδ不是“绝不能参与前导链”；这里的问题是未加说明地用于常规前导链教学模型。模型将亚型问题归为SCRIPT，但当前分镜未指定该标签，因此单独记录根因归属待核实，不能盲目要求上游重写。
最终科学提交0/1完整渲染候选；原成功代码/视频配对保持，APPROVED未生成。局部方向修正成功与整节科学失败分别记录。候选MP4供诊断，不能称为已批准教学成片。

## 7. 模型用量与预算
"""
for provider,st in stats.items():report+=f"- {provider}：{st['requests']}次请求，输入{st['input_tokens']}、输出{st['output_tokens']}、合计{st['total_tokens']}词元；接口累计{st['api_seconds']}秒；SDK自动重试0。\n"
report+=f"""
已知总词元{metrics['total_known_tokens']}。DeepSeek8/8；Qwen原上限2+用户新增2=4，实际3，尚余1，不为用满额度发请求。真实账单不可取得，不将价目估算冒充账单金额。Wan/Seedance0次。

## 8. 输出路径
代码：{R/'src/biology_expert'}
实验根目录：{E}
真实修复前视频：{before['video']}
修复候选视频（未通过最终科学门禁）：{candidate}
实际代码：{code}
实际轨迹：{trace}
完整审核：reviews/；返工任务：repair_tasks/；模型和网络账本：logs/；工具日志：state/events.jsonl；指标：metrics.json。
每次审核有review_id、输入内容哈希，每次返工有repair_id，候选实际代码与MP4另有SHA-256配对清单。

## 9. 局限与下一步
- 一个DNA局部事件和一组有丝分裂文本，不支持普遍性能结论。
- 来源检索当前是有限教材目录排名+真实PubMed检索，可接受白名单来源；不是覆盖全部生物主题的完整检索系统。
- 语义核验与文本生成使用同一模型供应商的独立调用，不能视为独立专家确认。物种、阶段和来源本身的措辞问题仍需复核。
- 机制适配器目前针对V2的平面DNA场景，依据静态代码极性文字与实际轨迹；没有通用三维拓扑/化学键验证，约0.2秒采样可能漏掉更快事件。
- 上游脚本/角色/素材/分镜审核接口和模拟返工路由已实现，尚未把所有上游生成器实际接通；当前只真实接通一个代码事件返工。
- 候选修复经验自动保存，但没有批准正式技能，也不会自动写入正式科学规则库。
- 可继续与Code2Video集成，但应先为复制叉拓扑、切口邻接、角色亚型建立可测验收，再接通上游返工；目前不宜自动扩展整部六节视频或自动发布。
"""
(E/'RESULTS.md').write_text(report)
# Durable project continuity, replacing stale top-level objective/state rather than only appending.
memory=R/'PROJECT_MEMORY.md';m=memory.read_text()
a=m.index('## Objective');z=m.index('## Verified results',a)
m=m[:a]+"""## Objective
当前V3：一个BiologyExpertAgent、多工具、通用证据知识包、科学审核与受预算/状态机约束的最小返工闭环。只修一个Section事件，不重跑六节。V1/V2冻结。用户2026-11-24追加Qwen2次额度，须先诊断再重试；已执行1次有效重试。

## Current state
VERIFIED：V3 MVP已实现并完成实验；28项离线测试通过。DNA方向候选实际渲染/解码及方向检查通过，完整科学视频复核REVISE，事务保持历史配对，无APPROVED。有丝分裂知识包动态构建，正常脚本PASS、4项注错均检出；初始编码/格式失败完整保留。详见experiments/biology_expert_v3/RESULTS.md和metrics.json。

"""+m[z:]
a=m.index('## Immediate continuation');z=m.index('## Blockers',a)
m=m[:a]+"""## Immediate continuation
本次V3已完成，无后台运行任务。先读experiments/biology_expert_v3/RESULTS.md、metrics.json、reviews/video/final_retry_review.json。若后续继续，优先处理真实复制叉拓扑与缺口/切口几何；聚合酶亚型根因不能仅信模型归为脚本。候选未批准，不自动发布整片。DeepSeek8/8；Qwen已用3/4（用户额外2中用1），保留账本，不擅自重置。原Qwen输出截断已经确认并通过V3专用JSON/思考预算适配恢复，不能再说接口不可用。

"""+m[z:]
m+='\n## 2026-11-24 V3交付\nsrc/biology_expert/与experiments/biology_expert_v3/：单一有界反应式Agent，12工具，证据检索/动态知识包/阶段审核/真实机制检查/最小AST返工/完整渲染/科学回滚/候选技能/CLI。历史冻结2451文件哈希无变化。DeepSeek8次62277词元，Qwen3次123413词元，合计185690；其中一次Qwen输出截断仍有已知44275词元。新增授权重试1次有效，方向PASS但整节REVISE，无科学批准视频。两次Coder生成仅第二次保存响应作格式重放，无手写动画。完整报告记录局限与失败。所有结果服务器保留，只下载交付件。\n'
memory.write_text(m)
# Safe delivery artifacts; preserve raw server logs, omit internal thought fields in distributed JSON.
delivery=ROOT/'delivery/Biology_Expert_V3';delivery.mkdir(parents=True,exist_ok=True)
for src,name in [(Path(before['video']),'before_V2.mp4'),(candidate,'candidate_V3_NOT_APPROVED.mp4'),(E/'RESULTS.md','RESULTS.md'),(E/'metrics.json','metrics.json'),(out/'before_after_scientific_review.jpg','before_after.jpg')]:shutil.copy2(src,delivery/name)
def sanitized(obj):
 if isinstance(obj,dict):return {k:sanitized(v) for k,v in obj.items() if k not in ['reasoning_content','encrypted_content','reasoning_summary']}
 if isinstance(obj,list):return [sanitized(v) for v in obj]
 return obj
secrets=[]
for line in (ROOT/'.env').read_text().splitlines():
 if '=' in line:
  k,v=line.split('=',1)
  if 'KEY' in k and len(v)>12:secrets.append(v.strip().strip('"').strip("'").encode())
archive=delivery/'Biology_Expert_V3_materials.zip';entries=[]
for p in (R/'src/biology_expert').rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:entries.append((p,'src/biology_expert/'+str(p.relative_to(R/'src/biology_expert'))))
for p in [R/'src/biology_runtime.py',R/'src/biology_v2_pipeline.py',R/'src/gpt_request.py',ROOT/'sandbox_exec.py']:entries.append((p,'reused_source/'+p.name))
for p in E.rglob('*'):
 if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or 'media' in p.parts or '.cache' in p.parts:continue
 rel=p.relative_to(E)
 if any(x.startswith('offline_') for x in rel.parts):continue
 if p.suffix.lower() in ['.mp4','.png','.jpg','.pyc']:continue
 entries.append((p,'experiment/'+str(rel)))
for folder in ['specs','assets']:
 for p in (R/'experiments/biology_v2_section4'/folder).rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.json','.md','.svg']:entries.append((p,'reused_inputs/'+folder+'/'+str(p.relative_to(R/'experiments/biology_v2_section4'/folder))))
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p,name in entries:
  data=p.read_bytes()
  if p.suffix=='.json':
   try:data=json.dumps(sanitized(json.loads(data)),ensure_ascii=False,indent=2).encode()
   except Exception:pass
  assert not any(s in data for s in secrets),'Secret detected in delivery'
  z.writestr(name.replace('\\','/'),data)
for p in (E/'logs/models').rglob('*response.json'):p.chmod(0o600)
# Manifest can be independently checked after download.
manifest={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in delivery.iterdir() if p.is_file()}
write(delivery/'delivery_manifest.json',manifest)
print(json.dumps({'tests':tests['passed'],'historical_preserved':len(frozen),'models':stats,'total_tokens':metrics['total_known_tokens'],'final_science':review['decision'],'target_direction':review['targeted_gap_direction'],'archive_bytes':archive.stat().st_size,'delivery':str(delivery)},ensure_ascii=False))
