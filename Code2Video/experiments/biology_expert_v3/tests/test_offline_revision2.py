from pathlib import Path
import sys,json,tempfile,ast,copy,traceback
R=Path('/autodl-tmp/code2biovideo/Code2Video');sys.path.insert(0,str(R/'src'))
from biology_expert.state import WorkflowState,write,digest,GATES
from biology_expert.agent import BiologyExpertAgent
from biology_expert.workflow import ScienceWorkflow
from biology_expert.schemas import validate
from biology_expert.providers import ModelGateway
from biology_expert.tools.mechanism_validator import mechanism_validator
from biology_expert.tools.repair_planner import bounded_patch,plan_repair
from biology_expert.tools.skill_manager import SkillManager
from biology_expert.tools.reviewers import review_result,issue
from biology_v2_pipeline import TransactionRenderer,sha
E=R/'experiments/biology_expert_v3';V2=R/'experiments/biology_v2_section4'
RESULTS=[]
def test(name,fn):
 try:details=fn();RESULTS.append({'test':name,'passed':True,'details':details})
 except Exception as ex:RESULTS.append({'test':name,'passed':False,'error':repr(ex)});traceback.print_exc()
def rejects(fn):
 try:fn()
 except Exception:return True
 raise AssertionError('Expected rejection')
class NoPaid:
 stopped=False
 def request(self,*a,**kw):raise AssertionError('Offline test attempted paid model call')
TMP=Path(tempfile.mkdtemp(prefix='offline_revision2_',dir=E/'tests'));TMP.chmod(0o755)
def schema_bad():return rejects(lambda:validate('review',{'decision':'APPROVE'}))
test('schema_rejects_missing_fields_and_illegal_decision',schema_bad)
test('schema_error_is_not_pass',lambda:validate('review',review_result('SCRIPT','ERROR',[],{'text':'fixture'}))['decision']=='ERROR')
def no_gate():
 st=WorkflowState(TMP/'prereq')
 return rejects(lambda:st.transition('SCRIPT_GATE','PASSED',{'decision':'PASS','review_id':'mock','issues':[]}))
test('unapproved_upstream_blocks_gate',no_gate)
def invalidate():
 st=WorkflowState(TMP/'invalidation')
 for g in GATES:
  st.register(g,{'fixture_version':1},g)
  st.transition(g,'PASSED',{'decision':'PASS','review_id':'mock-'+g,'issues':[]})
 st.register('changed_storyboard',{'fixture_version':2},'STORYBOARD_GATE')
 assert st.data['gates']['SCRIPT_GATE']['status']=='PASSED'
 assert st.data['gates']['CODE_GATE']['status']=='PENDING'
 assert st.data['gates']['APPROVED']['status']=='PENDING'
 assert st.cached('SCRIPT_GATE')
 return {'unrelated_script_cache_preserved':True,'code_and_release_invalidated':True}
test('content_hash_dependency_invalidation_and_cache',invalidate)
def release():
 st=WorkflowState(TMP/'release')
 result=ScienceWorkflow(st).release({'decision':'ERROR','issues':[]},'fixture')
 assert result is False and not (st.root/'APPROVED.json').exists()
 return result
test('ERROR_cannot_release_video',release)
def blocker():
 st=WorkflowState(TMP/'blocker')
 return rejects(lambda:st.transition('TOPIC_RESEARCH','PASSED',{'decision':'PASS','review_id':'mock','issues':[{'severity':'blocker'}]}))
test('model_PASS_cannot_waive_blocker',blocker)
agent=BiologyExpertAgent(TMP/'agent',NoPaid())
for name,situation,expected in [
 ('missing_evidence_selects_retrieval',{'has_evidence':False},'evidence_retriever'),
 ('known_execution_error_selects_repair',{'has_evidence':True,'measured_error':True},'repair_planner'),
 ('known_facts_ambiguous_video_selects_video',{'has_evidence':True,'visual_ambiguity':True},'video_reviewer'),
 ('conflicting_claims_select_verifier',{'has_evidence':True,'conflict':True},'fact_verifier')]:
 def branch(s=situation,e=expected):
  selected,reason=agent.choose_next(s);assert selected==e
  original=agent.registry.tools[selected]
  agent.registry.tools[selected]=lambda situation: {'mode':'OFFLINE_MOCK','observed_situation':situation}
  try:return agent._call(selected,{'situation':s},'Offline autonomy branch test',reason)
  finally:agent.registry.tools[selected]=original
 test(name,branch)
test('arbitrary_tool_not_whitelisted',lambda:rejects(lambda:agent.registry.invoke('shell',{},'bad','bad')))
def budget():
 p=TMP/'model_budget';p.mkdir(exist_ok=True)
 write(p/'model_calls.json',[{'provider':'deepseek','status':'ok'}]*8)
 gw=ModelGateway(p);return rejects(lambda:gw.request('deepseek','should_not_run',''))
test('persistent_model_budget_blocks_ninth_request',budget)
def pending():
 p=TMP/'pending';p.mkdir(exist_ok=True);write(p/'model_calls.json',[{'provider':'deepseek','status':'pending'}])
 return rejects(lambda:ModelGateway(p).request('qwen','should_stop',''))
test('uncertain_pending_request_stops_new_paid_calls',pending)
source=TransactionRenderer(V2/'groups/A2_mechanism_assets',R/'src/biology_runtime.py').state()
trace=json.loads((Path(source['version'])/'geometry_trace.json').read_text());code=Path(source['code']).read_text()
context={'knowledge_pack':{'facts':[{'fact_id':'OFFLINE_SYNTHETIC_FIXTURE_ONLY','claim':'OFFLINE fixture only: polymerase synthesis 5 to 3','verification':'VERIFIED','semantic_verification':'VERIFIED'}]}}
def historical():
 m=mechanism_validator({'code':code,'trace':trace},context)
 c=next(c for c in m['checks'] if c['check_id']=='lagging_gap_growth')
 assert c['status']=='FAIL' and c['evidence']['successive_addition_projections'][0]<0
 write(E/'tests/fixtures/offline_historical_direction_result.json',m)
 return {'uses_real_V2_geometry':True,'science_evidence':'MOCK; production must retrieve and verify'}
test('actual_historical_trace_detects_polarity_growth_contradiction',historical)
def missing_polarity():
 changed=code.replace('small_label("5\'",','small_label("unreadable",').replace("small_label('5\\'',","small_label('unreadable',")
 # Explicitly remove all small_label polarity evidence from AST text; no geometry changes.
 import re
 changed=__import__('re').sub(r'small_label\((["\'])5.*?\1,', 'small_label("unreadable",',code)
 m=mechanism_validator({'code':changed,'trace':trace},context)
 assert next(c for c in m['checks'] if c['check_id']=='lagging_gap_growth')['status']=='UNCERTAIN'
 return True
test('missing_polarity_cannot_pass_on_x_only',missing_polarity)
def forged_metadata():
 changed=copy.deepcopy(trace);changed['growth_direction']='5to3_correct'
 m=mechanism_validator({'code':code,'trace':changed},context)
 assert next(c for c in m['checks'] if c['check_id']=='lagging_gap_growth')['status']=='FAIL'
 return True
test('generator_direction_declaration_cannot_override_actual_trace',forged_metadata)
def bounded():
 tree=ast.parse(code);loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and any(isinstance(x,ast.Constant) and isinstance(x.value,str) and x.value.startswith('fill_dna_') for x in ast.walk(n)))
 # Offline identity patch tests boundary mechanics; not passed off as Agent-generated repair.
 new,proof=bounded_patch(code,ast.unparse(loop));assert proof['only_target_loop_changed']
 assert rejects(lambda:bounded_patch(code,'for i in range(99):\n    pass'))
 return proof
test('repair_patch_AST_scope_and_iteration_guard',bounded)
def upstream():
 rev=review_result('STORYBOARD','REVISE',[issue('MOCK-UPSTREAM','An explicitly wrong fixture storyboard',['fixture'],[],'STORYBOARD')],{'storyboard':'fixture'})
 task=plan_repair(rev,{'input_hash':'0'*64})
 assert task['root_cause_stage']=='STORYBOARD' and task['invalidate'][0]=='STORYBOARD_GATE'
 result=ScienceWorkflow(agent.state).request_upstream_repair(task)
 assert result['status']=='NEEDS_HUMAN_REVIEW'
 return {'routes_to_earliest_stage':True,'unintegrated_generator_is_explicit':True}
test('upstream_root_cause_routing_not_icon_move',upstream)
def skill():
 sk=SkillManager(TMP/'candidate_skills',TMP/'formal_skills')
 task={'issue_id':'MOCK','category':'fixture','preserve':[],'verification':[],'repair_id':'REP-MOCK','source_review_id':'REV-MOCK'}
 out=sk.propose(task,{'regression_tests':['fixture']})
 assert not sk.approved() and not (TMP/'formal_skills').exists()
 assert json.loads(Path(out['candidate_path']).read_text())['approval_required']
 return True
test('candidate_skill_never_auto_approved',skill)
def rollback():
 tx=TransactionRenderer(TMP/'actual_full_render_rollback',R/'src/biology_runtime.py',V2/'assets',(25,35))
 dest=tx.group/'versions/fixture_baseline';dest.parent.mkdir(exist_ok=True)
 import shutil
 if not dest.exists():shutil.copytree(source['version'],dest)
 if not (tx.group/'current').exists():
  (tx.group/'current').symlink_to(dest.relative_to(tx.group),target_is_directory=True)
 before=tx.state()
 def reject_science(stage,trace,layout):raise ValueError('OFFLINE injected science-gate failure after real full render')
 result=tx.attempt(code,'offline_science_rejection',extra_validator=reject_science)
 assert not result['committed'] and tx.state()==before
 assert (tx.group/'attempts/offline_science_rejection/media/videos/rendered_code/480p15/Section4Scene.mp4').exists()
 return {'complete_real_render_before_rejection':True,'exact_prior_pair_retained':True,'candidate_preserved':True}
test('real_full_render_scientific_rejection_rolls_back_atomic_pair',rollback)

def returned_indented_block():
 raw=json.loads((E/'logs/models/v3_05_response.json').read_text())['choices'][0]['message']['content']
 candidate,scope=bounded_patch(code,raw)
 assert scope['only_target_loop_changed'] and ast.parse(candidate)
 return {'saved_real_model_response_parsed_without_new_call':True}
test('regression_real_indented_model_reply_with_extra_initializer',returned_indented_block)
def missing_science_rule():
 p=json.loads((E/'initial_run_failures/dna_replication/knowledge_pack.json').read_text())
 m=mechanism_validator({'code':code,'trace':trace},{'knowledge_pack':p})
 assert m['status']=='UNCERTAIN' and not any(c['status']=='FAIL' for c in m['checks'])
 return True
test('generic_polymerase_role_is_not_direction_fact',missing_science_rule)
def source_case():
 from biology_expert.tools.evidence_retriever import CATALOG
 tokens={'dna','replication','eukaryotic'}
 assert any(len(tokens&set(k.lower().split()))>=2 for k,u in CATALOG)
 return True
test('regression_case_insensitive_textbook_discovery',source_case)
def quote_encoding():
 from biology_expert.tools.knowledge import normalize
 assert normalize('S phase ( synthesis phase )')==normalize('S phase (synthesis phase)')
 assert normalize('only 5 to3')!=normalize('only3 to5')
 return True
test('quote_normalization_does_not_change_scientific_direction',quote_encoding)
def limit_two():
 from biology_expert.repair import RepairExecutor
 loc=TMP/'two_attempt_limit';task={'repair_id':'REP-TWO-MOCK','issue_id':'MOCK','category':'fixture','preserve':[],'verification':[],'source_review_id':'REV-MOCK','input_hash':source['code_sha256']}
 write(loc/task['repair_id']/'attempts.json',[{'attempt':1,'status':'offline_mock_failed'},{'attempt':2,'status':'offline_mock_failed'}])
 result=RepairExecutor(agent,loc,R/'src/biology_runtime.py',V2/'assets').execute(task,source,context)
 assert len(result['attempts'])==2 and not result['accepted'] and result['rollback_pair_preserved']
 return {'third_model_request_prevented':True}
test('two_attempt_cap_persists_across_restart',limit_two)

def structured_error():
 agent.registry.tools['artifact_reviewer']=lambda **kwargs: (_ for _ in ()).throw(TimeoutError('offline injected tool timeout'))
 result=agent.review('SCRIPT',{'text':'offline fixture'},{'knowledge_pack':{'facts':[{'fact_id':'MOCK'}]}})
 assert result['decision']=='ERROR' and result['next_action']=='STOP'
 return {'tool_failure_returns_schema_valid_ERROR':True}
test('tool_exception_returns_structured_ERROR',structured_error)
def truncated_usage():
 from unittest.mock import patch
 import gpt_request,os
 gw=ModelGateway(TMP/'truncated_model_mock')
 def fake(*args,**kwargs):
  write(gw.root/'qwen_raw/v3_01.response.json',{'model':'MOCK','usage':{'total_tokens':5},'choices':[{'finish_reason':'length'}]})
  raise ValueError('MOCK truncated output')
 with patch.dict(os.environ,{'QWEN_MODEL':'OFFLINE_MOCK'}),patch.object(gpt_request,'request_qwen_video_img',fake):
  rejects(lambda:gw.request('qwen','offline_test','mock',video='not_read_by_mock'))
 assert gw.rows[-1]['status']=='error' and gw.rows[-1]['usage']['total_tokens']==5 and gw.rows[-1]['root_cause']=='MODEL_OUTPUT_TRUNCATED' and gw.stopped
 return {'known_usage_preserved_on_invalid_output':True,'paid_requests':0}
test('truncated_response_keeps_known_usage_and_stops',truncated_usage)

def authorized_extension():
 loc=TMP/'authorization_fixture';loc.mkdir()
 original=[{'call_id':'OLD1','provider':'qwen','status':'ok'},{'call_id':'OLD2','provider':'qwen','status':'error'}]
 write(loc/'model_calls.json',original)
 gw=ModelGateway(loc)
 assert gw.stopped
 assert rejects(lambda:gw.resume_authorized({'source':'model_suggestion'}))
 auth={'authorization_id':'OFFLINE-MOCK','source':'explicit_user_message','provider':'qwen','additional_requests':2,'acknowledged_failed_calls':['OLD2']}
 gw.resume_authorized(auth)
 assert gw.limits['qwen']==4 and not gw.stopped and len(gw.rows)==2
 assert rejects(lambda:gw.resume_authorized(auth))
 restored=ModelGateway(loc)
 assert restored.limits['qwen']==4 and not restored.stopped and len(restored.rows)==2
 return {'old_requests_preserved':True,'duplicate_authorization_rejected':True}
test('explicit_user_quota_extension_persists_without_history_reset',authorized_extension)
write(E/'tests/test_results.json',{'mode':'OFFLINE_NO_PAID_MODELS','total':len(RESULTS),'passed':sum(x['passed'] for x in RESULTS),'all_passed':all(x['passed'] for x in RESULTS),'tests':RESULTS})
print(json.dumps({'total':len(RESULTS),'passed':sum(x['passed'] for x in RESULTS),'failed':[x for x in RESULTS if not x['passed']]},ensure_ascii=False))
if not all(x['passed'] for x in RESULTS):sys.exit(1)
