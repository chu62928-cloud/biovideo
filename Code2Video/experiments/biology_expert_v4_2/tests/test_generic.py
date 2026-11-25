from pathlib import Path
import sys,json,copy,tempfile
R=Path('/autodl-tmp/code2biovideo/Code2Video-v4.2-workspace');E=R/'experiments/biology_expert_v4_2';sys.path.insert(0,str(R/'src'))
from biology_expert.contracts import *
from biology_expert.agent import BiologyExpertAgent
results=[]
def test(name,fn):
 try:fn();results.append({'test':name,'passed':True})
 except Exception as ex:results.append({'test':name,'passed':False,'error':repr(ex)})
contract={'contract_id':'OFFLINE_GENERIC_FIXTURE','topic_id':'synthetic','scope':{'user_request':'synthetic relationship fixture','audience':'test','included':['event sequence'],'excluded':[]},'scientific_entities':[{'role':'unit','description':'synthetic object','evidence_ids':['OFFLINE']}],'required_processes':[{'role':'finish','description':'synthetic transition','evidence_ids':['OFFLINE']}],'required_observations':['two objects'],'constraints':[],'evidence_refs':['OFFLINE'],'visual_references':[],'coverage_requirements':[],'unresolved_questions':[],'verification_plan':{'mode':'OFFLINE_MOCK_NOT_SCIENCE'}}
def c(cid,primitive,roles,args,kind='STRUCTURAL'):
 return {'constraint_id':cid,'type':kind,'participant_roles':roles,'applies_to':{},'when':{},'must_hold':args,'exceptions':[],'evidence_ids':['OFFLINE'],'support':[{'evidence_id':'OFFLINE','quote':'OFFLINE synthetic evidence fixture'}],'verification':{'methods':['runtime_trace'],'capability':'DETERMINISTIC','primitive':primitive},'severity':'critical','verification_status':'PROPOSED','disputed':False}
contract['constraints']=[c('exist','exists',['a'],{}),c('identity','identity',['a'],{}),c('relation','persistent_relation',['a','b'],{'relation':'bound'},'PERSISTENT_RELATION'),c('order','event_order',[],{'ordered_roles':['start','finish']},'TEMPORAL'),c('state','state',[],{'key':'phase','value':'active'},'STATE'),c('count','count',[],{'kind':'unit','value':2})]
contract['coverage_requirements']=[{'item_id':'a','kind':'entity','constraint_ids':['exist','identity'],'critical':True},{'item_id':'bound','kind':'persistent','constraint_ids':['relation'],'critical':True},{'item_id':'finish','kind':'process','constraint_ids':['order'],'critical':True}]
scene={'objects':[{'object_id':'a','visual_representation':{}},{'object_id':'b','visual_representation':{}}]}
frame={'time':0,'objects':{'a':{'instance_id':1,'origin_id':'a','kind':'unit','visible':True,'center':[0,0,0],'anchors':{'center':[0,0,0]}},'b':{'instance_id':2,'origin_id':'b','kind':'unit','visible':True,'center':[1,0,0],'anchors':{'center':[1,0,0]}}},'relations':[{'source':'a','target':'b','type':'bound'}],'state_variables':{'phase':'active'},'current_event':'start','completed_events':[]}
trace={'scientific_observations':[copy.deepcopy(frame),copy.deepcopy(frame)],'events':[{'id':'start'},{'id':'finish'}]};trace['scientific_observations'][1]['time']=1
def normal():schema_validate(contract);assert ConstraintExecutor().execute(contract,scene,trace)['decision']=='PASS'
test('generic_schema_and_normal_execution',normal)
def missing():
 t=copy.deepcopy(contract);t.pop('coverage_requirements')
 try:schema_validate(t)
 except Exception:return
 raise AssertionError('schema accepted missing coverage')
test('schema_missing_required_rejected',missing)
def unsupported():
 t=copy.deepcopy(contract);t['constraints'][0]['verification']['primitive']='unimplemented';assert ConstraintExecutor().execute(t,scene,trace)['checks'][0]['status']=='UNSUPPORTED_CONSTRAINT'
test('unsupported_never_pass',unsupported)
def noobs():assert ConstraintExecutor().execute(contract,scene,{})['decision']=='REVIEW_INCOMPLETE'
test('absent_observation_not_zero_errors',noobs)
def coverage():
 ex=ConstraintExecutor().execute(contract,scene,trace);a=ScientificCoverageAuditor().audit(contract,ex,{'decision':'PASS'});assert a['decision']=='PASS'
 reduced=copy.deepcopy(contract);reduced['constraints']=reduced['constraints'][:1];ex=ConstraintExecutor().execute(reduced,scene,trace);a=ScientificCoverageAuditor().audit(reduced,ex,{'decision':'PASS'});assert a['decision']=='REVIEW_INCOMPLETE' and a['critical_gaps']
test('deleted_rules_do_not_inflate_coverage',coverage)
def mutations():
 m=ScientificMutationTester().run(contract,scene,trace);assert m['detected']==6 and not m['false_positives'] and not m['missed'];assert trace['scientific_observations'][1]['objects']['a']['origin_id']=='a'
test('automatic_mutations_detected_color_control_not_error',mutations)
def freeze():
 store=ContractStore(Path(tempfile.mkdtemp(dir=E/'tests')));f=store.freeze(contract,{'decision':'PASS'});t=copy.deepcopy(contract);t['constraints'].pop()
 try:store.verify(t,f['contract_hash'])
 except ValueError:return
 raise AssertionError('frozen mutation accepted')
test('contract_change_invalidates_approvals',freeze)
def conflict():
 ex=ConstraintExecutor().execute(contract,scene,trace);a=ScientificConflictAdjudicator().adjudicate(contract,ex,{'issues':[{'constraint_id':'exist','description':'semantic uncertainty'}]});assert a[0]['status']=='NEEDS_HUMAN_REVIEW' and not a[0]['repair_allowed']
test('conflict_not_automatically_dismissed',conflict)
class MockGateway:
 def request(self,*a,**kw):raise AssertionError('OFFLINE tests must not call API')
def agent():
 a=BiologyExpertAgent(E/'tests/mock_agent',MockGateway());a.enable_contract_workflow(E/'tests/mock_workflow')
 assert a.choose_contract_tool({'has_evidence':False})=='scientific_evidence_retriever'
 assert a.choose_contract_tool({'has_evidence':True,'conflict':True})=='scientific_conflict_adjudicator'
 assert a.choose_contract_tool({'has_evidence':True,'contract_exists':True,'contract_verified':True,'coverage_gap':True})=='coverage_auditor'
 for n in ['mutation_tester','coverage_auditor','reference_video_reviewer','scientific_contract_builder']:assert n in a.registry.tools
 result=a.audit_contract(contract,scene,trace,goal_review={'decision':'PASS'});assert result['decision']=='PASS'
test('existing_single_agent_tools_and_different_routes_mock',agent)
def no_legacy():
 forbidden=['DNA_STRAND_POLARITY','polarity_check(','if topic ==','rna_primer','template_leading']
 for rel in ['biology_expert/contracts.py','biology_expert/contract_builder.py','scientific_scene/scientific_review.py','scientific_scene/adapters/biology_expert_adapter.py']:
  txt=(R/'src'/rel).read_text();assert not any(w in txt for w in forbidden),rel
test('new_production_path_no_legacy_topic_rules',no_legacy)
def infrastructure():
 from scientific_scene.models import Assembly
 from scientific_scene.state_machine import TransitionEngine
 from scientific_scene.path_geometry import PathGeometry,PathMorph
 import numpy as np
 m=PathGeometry([[0,0,0],[1,0,0]],stroke_width=5);m.set_opacity(1);a=PathMorph(m,[[0,0,0],[1,1,0]]);a.begin();a.interpolate(.5);assert m.get_fill_opacity()==0
 from biology_v2_pipeline import safety_check
 safety_check('from biology_runtime import BiologyScene\nclass Section4Scene(BiologyScene):\n def construct(self):\n  self.wait(1)\n')
test('generic_path_and_renderer_safety_preserved',infrastructure)
write(E/'tests/test_results.json',{'mode':'OFFLINE_SYNTHETIC_FIXTURES_NO_REAL_MODEL','results':results,'passed':sum(x['passed'] for x in results),'total':len(results),'all_passed':all(x['passed'] for x in results)})
print(json.dumps(results));assert all(x['passed'] for x in results)
