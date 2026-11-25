from pathlib import Path
import sys,copy,json
import pytest
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.role_binder import ScientificRoleBinder
from biology_expert.contract_compiler import ScientificContractCompiler
from biology_expert.temporal_validator import TemporalMechanismValidator,MechanismMutationTester
from biology_expert.contracts import digest

def fixture(predicate='relation_holds_during'):
 c={'topic_id':'generic_fixture','scientific_entities':[{'role':'actor'},{'role':'target'}],'required_processes':[{'role':'active_process'},{'role':'release'}],'constraints':[{'constraint_id':'C','participant_roles':['actor','target'],'evidence_ids':['SYNTHETIC_TEST_SOURCE'],'exceptions':[],'verification_status':'INDEPENDENTLY_VERIFIED','verification':{'capability':'DETERMINISTIC'},'executable_predicate':{'predicate':predicate,'participant_roles':['actor','target'],'source_role':'actor','target_role':'target','relation_type':'bound','interval':{'event_role':'active_process'},'max_sample_gap':1.01}}]}
 scene={'objects':[{'object_id':x,'scientific_identity':{'name':x,'origin_id':x},'scientific_properties':{},'anchors':{}} for x in ['actor','target']],'events':[{'event_id':'active','role':'active_process','duration':5},{'event_id':'release','role':'release','duration':2}]}
 frames=[{'time':t,'current_event':'active' if t<7 else 'release','objects':{'actor':{'visible':True},'target':{'visible':True}},'relations':[{'source':'actor','target':'target','type':'bound'}] if t<7 else [],'state_variables':{'ready':True,'phase':'waiting' if t<5 else 'done'}} for t in range(2,10)]
 trace={'events':[{'id':'active','time':2},{'id':'release','time':7}],'scientific_observations':frames}
 return c,scene,trace
def execute(c,s,t):
 b=ScientificRoleBinder().bind(c,s,t);p=ScientificContractCompiler().compile(c,{'decision':'PASS'},s,b,t);return p,TemporalMechanismValidator().execute(p,c,s,t)

def test_full_relation():
 c,s,t=fixture();p,r=execute(c,s,t);assert r['checks'][0]['status']=='PASS' and r['checks'][0]['full_constraint_verified']
def test_early_end_detected_and_interval_fixed():
 c,s,t=fixture()
 for f in t['scientific_observations']:
  if f['time']>=5:f['relations']=[]
 p,r=execute(c,s,t);assert r['checks'][0]['status']=='FAIL' and r['checks'][0]['expected_interval']['end']==7
def test_legal_release_not_false_positive():
 c,s,t=fixture('connection_holds_until');assert execute(c,s,t)[1]['checks'][0]['status']=='PASS'
def test_unknown_interval_not_pass():
 c,s,t=fixture();t['events']=[];assert execute(c,s,t)[1]['checks'][0]['status']=='EXPECTED_INTERVAL_UNRESOLVED'
def test_gap_in_critical_interval():
 c,s,t=fixture();t['scientific_observations']=[f for f in t['scientific_observations'] if f['time'] not in [4,5]];assert execute(c,s,t)[1]['checks'][0]['status']=='REVIEW_INCOMPLETE'
def test_hidden_object_does_not_shorten_interval():
 c,s,t=fixture()
 for f in t['scientific_observations']:
  if f['time']>=5:f['objects']['actor']['visible']=False;f['relations']=[]
 _,r=execute(c,s,t);assert r['checks'][0]['status']=='FAIL' and r['checks'][0]['samples_checked']==5
def test_wrong_target_detected():
 c,s,t=fixture();t['scientific_observations'][2]['relations'][0]['target']='wrong';assert execute(c,s,t)[1]['checks'][0]['status']=='FAIL'
def test_event_order_positive_negative():
 c,s,t=fixture('event_precedes');c['constraints'][0]['executable_predicate'].update(participant_roles=['active_process','release'],ordered_event_roles=['active_process','release'])
 assert execute(c,s,t)[1]['checks'][0]['status']=='PASS'
 t['events'][0]['time'],t['events'][1]['time']=7,2;assert execute(c,s,t)[1]['checks'][0]['status']=='FAIL'
def test_state_transition_positive_negative():
 c,s,t=fixture('state_transition_allowed');c['constraints'][0]['executable_predicate'].update(state_key='phase',to_value='done',precondition={'ready':True})
 assert execute(c,s,t)[1]['checks'][0]['status']=='PASS'
 t['scientific_observations'][2]['state_variables']['ready']=False;assert execute(c,s,t)[1]['checks'][0]['status']=='FAIL'
def test_no_trace_no_dynamic_pass():
 c,s,t=fixture();assert execute(c,s,{})[1]['checks'][0]['status']=='NOT_MEASURED'
def test_lexical_process_candidate_rejected():
 c,s,t=fixture();c['required_processes']=[{'role':'aggregate_formation'}];s['events']=[{'event_id':'different_formation','role':'bond_formation'}]
 b=ScientificRoleBinder().bind(c,s,t);row=next(x for x in b['bindings'] if x['kind']=='process');assert row['status']=='REJECTED' and row['rejected_candidates']
def test_explicit_process_and_sets_preserved():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,t);assert next(x for x in b['bindings'] if x['role']=='active_process')['status']=='BOUND'
def test_vlm_rule_not_forced_to_compile():
 c,s,t=fixture();c['constraints'][0]['verification']['capability']='VLM';assert execute(c,s,t)[0]['compiled_constraints'][0]['compile_status']=='AMBIGUOUS_SEMANTICS'
def test_exceptions_not_ignored():
 c,s,t=fixture();c['constraints'][0]['exceptions']=[{'condition':'unknown'}];assert execute(c,s,t)[0]['compiled_constraints'][0]['compile_status']=='UNSUPPORTED'
def test_contract_change_invalidates_plan():
 c,s,t=fixture();p,_=execute(c,s,t);c['topic_id']='changed'
 with pytest.raises(ValueError,match='VERSION_CONFLICT'):TemporalMechanismValidator().execute(p,c,s,t)
def test_three_mutation_types_synthetic():
 for predicate in ['relation_holds_during','event_precedes','state_transition_allowed']:
  c,s,t=fixture(predicate)
  if predicate=='event_precedes':c['constraints'][0]['executable_predicate'].update(participant_roles=['active_process','release'],ordered_event_roles=['active_process','release'])
  if predicate=='state_transition_allowed':c['constraints'][0]['executable_predicate'].update(state_key='phase',to_value='done',precondition={'ready':True})
  p,baseline=execute(c,s,t);m=MechanismMutationTester().run(p,c,s,t,baseline);assert m['valid_mutations']>=1 and all(x.get('detected') for x in m['cases'] if x['valid_sample']) and m['false_positives']==0
def test_translation_actual_misbinding_rejected():
 H=Path('/autodl-tmp/code2biovideo/Code2Video/experiments/biology_expert_v4_2/contracts/protein_translation')
 if not H.exists():pytest.skip('Historical data absent')
 c=json.loads((H/'scientific_contract.json').read_text());s=json.loads((H/'generated_scene_graph.json').read_text());b=ScientificRoleBinder().bind(c,s,{})
 row=next(r for r in b['bindings'] if r['role']=='polyribosome_formation');assert row['status']!='BOUND' and 'EV_peptide_bond_formation' not in row['selected_ids']
def test_generic_modules_no_topic_branches():
 for name in ['contract_compiler.py','temporal_validator.py','role_binder.py']:
  text=(R/'Code2Video/src/biology_expert'/name).read_text();assert all(x not in text for x in ['dna_replication','protein_translation','mitosis'])


def test_timestamp_claim_not_independent_visual_verification():
 from biology_expert.observation_adapter import SemanticObservationAdapter
 c,s,t=fixture();review={'contract_hash':digest(c),'video_sha256':'V','checks':[{'constraint_id':'C','status':'PASS','observation':'2.0-7.0 s relation holds'}]}
 x=SemanticObservationAdapter().adapt(c,review,'V')[0]
 assert x['evidence_level']=='TIMESTAMP_MATCHED' and not x['independently_frame_verified']
