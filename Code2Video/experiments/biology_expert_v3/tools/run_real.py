from pathlib import Path
import sys,json,os,traceback,time,shutil
R=Path('/autodl-tmp/code2biovideo/Code2Video');ROOT=R.parent;E=R/'experiments/biology_expert_v3';V2=R/'experiments/biology_v2_section4'
sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway
from biology_expert.state import write,digest
from biology_expert.schemas import validate
from biology_expert.repair import RepairExecutor
from biology_v2_pipeline import TransactionRenderer,sha
assert json.loads((E/'tests/test_results.json').read_text())['all_passed'],'Offline tests must pass first'
for line in (ROOT/'.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v.strip().strip('"').strip("'")
required=['DEEPSEEK_API_KEY','DEEPSEEK_BASE_URL','DEEPSEEK_MODEL','DASHSCOPE_API_KEY','QWEN_BASE_URL','QWEN_MODEL']
assert all(os.environ.get(k) for k in required),'Missing protected provider configuration'
write(E/'logs/preflight.json',{'configuration_present':True,'models':{k:os.environ[k] for k in ['DEEPSEEK_MODEL','QWEN_MODEL']},'interface_probe':'First real task call counts toward budget; no extra paid ping','SDK_retries':0,'budget':{'deepseek':8,'qwen':2},'offline_test_total':20})
gw=ModelGateway(E/'logs/models');agent=BiologyExpertAgent(E,gw);progress={'started':time.time(),'status':'RUNNING'}
write(E/'progress.json',progress)
try:
 print('STEP DNA_RESEARCH',flush=True)
 packfile=E/'knowledge/dna_replication/knowledge_pack.json'
 if not packfile.exists():
  pack=agent.prepare_topic({'topic':'DNA replication in eukaryotic cells','topic_id':'dna_replication','audience':'high_school','video_goal':'Explain priming, leading and lagging synthesis and local Okazaki fragment maturation'})
 else:
  pack=json.loads(packfile.read_text())
  if not pack.get('build_report',{}).get('independent_verification'):raise RuntimeError('Partial research checkpoint requires explicit review; do not silently skip incomplete verification')
 validate('knowledge_pack',pack)
 progress['dna_research']=pack['build_report'];write(E/'progress.json',progress)
 source=TransactionRenderer(V2/'groups/A2_mechanism_assets',R/'src/biology_runtime.py').state()
 artifacts={'code':Path(source['code']).read_text(),'trace':json.loads((Path(source['version'])/'geometry_trace.json').read_text()),'trace_ref':str(Path(source['version'])/'geometry_trace.json'),'video':source['video']}
 write(E/'traces/historical_input_pair.json',source)
 write(E/'traces/historical_geometry.json',artifacts['trace'])
 context={'knowledge_pack':pack,'storyboard':json.loads((V2/'specs/section4_storyboard_v2.json').read_text())}
 print('STEP TEST_A_CODE',flush=True)
 codereview=agent.review('ANIMATION_CODE',artifacts,context)
 write(E/'reviews/code/test_A.json',codereview)
 if not any(i['issue_id']=='BIO-DIRECTION' for i in codereview['issues']):raise RuntimeError('Historical direction error not independently supported/detected; stop before repair')
 agent.state.register('historical_code',Path(source['code']),'CODE_GATE')
 agent.state.transition('CODE_GATE','REVISION_REQUIRED',codereview)
 print('STEP TEST_A_VIDEO',flush=True)
 video_review=agent.review('RENDERED_VIDEO',artifacts,context)
 write(E/'reviews/video/test_A.json',video_review)
 if video_review['decision']=='ERROR':raise RuntimeError('Initial video science review error; no further paid requests')
 print('STEP REPAIR_PLAN',flush=True)
 task=agent.plan_repair(codereview,{'input_hash':source['code_sha256']})
 write(E/'repair_tasks/test_B_task.json',task)
 executor=RepairExecutor(agent,E/'outputs',R/'src/biology_runtime.py',V2/'assets')
 print('STEP TEST_B_REAL_REPAIR',flush=True)
 outcome=executor.execute(task,source,context)
 write(E/'test_B_result.json',outcome)
 progress['test_B']=outcome;write(E/'progress.json',progress)
 if gw.stopped:raise RuntimeError('Paid model failure; retain completed artifacts and stop')
 print('STEP MITOSIS_RESEARCH',flush=True)
 pack=agent.prepare_topic({'topic':'Mitosis in eukaryotic cells','topic_id':'eukaryotic_mitosis','audience':'high_school','video_goal':'Explain S-phase preparation, prophase, metaphase, anaphase and telophase; distinguish nuclear division from cytokinesis'})
 samples=[
 {'sample_id':'normal_control','text':'Before mitosis, DNA replicates during S phase of interphase, producing sister chromatids. During prophase, chromosomes condense. At metaphase, duplicated chromosomes align at the metaphase plate. During anaphase, sister chromatids separate and move toward opposite poles. In telophase, nuclear envelopes form around the separated chromosome sets. Mitosis divides the nucleus; cytokinesis divides the cytoplasm.'},
 {'sample_id':'injected_errors','text':'DNA is first replicated during anaphase of mitosis. At metaphase of ordinary mitosis, homologous chromosomes pair and crossing over is required. During anaphase, homologous chromosome pairs separate while sister chromatids stay joined. A single ordinary mitotic division reduces a diploid nucleus to four haploid daughter nuclei.'}]
 write(E/'tests/fixtures/mitosis_samples.json',samples)
 print('STEP TEST_C_SCRIPT_REVIEW',flush=True)
 result=agent.review('SCRIPT',{'samples':samples},{'knowledge_pack':pack})
 write(E/'reviews/script/test_C.json',result)
 progress['test_C']=result
 progress['status']='COMPLETED_EXPERIMENTS'
except Exception as ex:
 progress.update(status='STOPPED_ERROR',error_type=type(ex).__name__,error=str(ex)[:600]);traceback.print_exc()
finally:
 progress['elapsed_seconds']=round(time.time()-progress['started'],3);progress['model_calls']=gw.rows
 write(E/'progress.json',progress)
 print('V3_RUN_END',progress['status'],'calls',len(gw.rows),flush=True)
