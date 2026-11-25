from pathlib import Path
import copy,json,sys,os
import pytest

REPO=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO/'Code2Video/src'))
from biology_expert.role_binder import ScientificRoleBinder
from biology_expert.observation_adapter import RuntimeObservationAdapter,SemanticObservationAdapter,ObservationMutationTester,merged_coverage
from biology_expert.contracts import digest

def fixture():
 contract={'contract_id':'offline_test','topic_id':'generic_test','scope':{},'scientific_entities':[{'role':'moving_unit'}],'required_processes':[],'constraints':[{'constraint_id':'C','type':'STRUCTURAL','participant_roles':['moving_unit'],'evidence_ids':['TEST_SOURCE'],'verification':{'primitive':'identity'},'applies_to':{}}],'coverage_requirements':[{'item_id':'unit','kind':'entity','constraint_ids':['C'],'critical':True}]}
 scene={'objects':[{'object_id':'obj','scientific_identity':{'name':'Moving unit','kind':'unit','origin_id':'obj'},'scientific_properties':{},'anchors':{'center':{}}}],'events':[]}
 frame={'time':0,'current_event':'event','objects':{'obj':{'visible':True,'instance_id':1,'origin_id':'obj','center':[0,0,0],'anchors':{'center':[0,0,0]}}},'relations':[]}
 trace={'scientific_observations':[copy.deepcopy(frame),copy.deepcopy(frame)]};trace['scientific_observations'][1]['time']=1
 return contract,scene,trace

def test_explicit_metadata_binding():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,t);assert b['bindings'][0]['object_ids']==['obj']

def test_ambiguous_role_not_bound():
 c,s,t=fixture();c['scientific_entities'][0]['role']='unit_a';c['constraints'][0]['participant_roles']=['unit_a']
 for i in ['x','y']:s['objects'].append({'object_id':i,'scientific_identity':{'name':'unit a','origin_id':i},'anchors':{}})
 b=ScientificRoleBinder().bind(c,s,t);assert b['bindings'][0]['status']=='AMBIGUOUS'

def test_unknown_not_pass():
 c,s,t=fixture();s['objects']=[];b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b);assert r['checks'][0]['status']=='NOT_MEASURED'

def test_no_trace_not_measured():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,{});r=RuntimeObservationAdapter().execute(c,s,{},b);assert r['checks'][0]['status']=='NOT_MEASURED' and r['checks'][0]['static_evidence']['status']=='PASS'

def test_actual_identity_subcheck_not_whole_semantics():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b);assert r['measured_observations'][0]['status']=='PASS';assert r['checks'][0]['status']=='PARTIALLY_VERIFIED'

def test_mutation_executor_detects_and_preserves_original():
 c,s,t=fixture();h=digest(t);b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b);m=ObservationMutationTester().run(c,s,t,b,r)
 assert m['valid_scientific_mutations']==1 and m['detected']==1 and m['cases'][0]['mutated_status']=='FAIL';assert digest(t)==h

def test_irrelevant_color_control():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b);assert not ObservationMutationTester().run(c,s,t,b,r)['negative_control']['false_positive']

def test_overall_video_pass_insufficient():
 c,s,t=fixture();r={'decision':'PASS','checks':[],'contract_hash':digest(c),'video_sha256':'HASH'};o=SemanticObservationAdapter().adapt(c,r,'HASH');assert o[0]['status']=='NOT_MEASURED'

def test_timestamped_video_observation_and_contract_change():
 c,s,t=fixture();r={'checks':[{'constraint_id':'C','status':'PASS','observation':'0.0-1.0 s unit remains visible'}],'contract_hash':digest(c),'video_sha256':'HASH'}
 assert SemanticObservationAdapter().adapt(c,r,'HASH')[0]['status']=='PASS'
 c['scope']['modified']=True;assert SemanticObservationAdapter().adapt(c,r,'HASH')[0]['evidence_status']=='VERSION_CONFLICT'

def test_deterministic_failure_not_overridden():
 c,s,t=fixture();b=ScientificRoleBinder().bind(c,s,t);t['scientific_observations'][1]['objects']['obj']['origin_id']='changed';b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b)
 semantic=[{'constraint_id':'C','status':'PASS'}];cov=merged_coverage(c,r,semantic,{'decision':'PASS'});assert r['checks'][0]['status']=='FAIL'

def test_no_topic_names_in_new_modules():
 for filename in ['role_binder.py','observation_adapter.py','contract_cli.py']:
  source=(REPO/'Code2Video/src/biology_expert'/filename).read_text()
  assert not any(name in source for name in ['dna_replication','protein_translation','mitosis','template_leading','kinetochore_A'])

@pytest.mark.parametrize('label,topic',[('B4_expert_repair','dna_replication'),('M1_mitosis','mitosis')])
def test_actual_historical_trace_measurement_and_mutation(label,topic):
 root=Path(os.environ.get('BIOVIDEO_HISTORICAL_ROOT','/autodl-tmp/code2biovideo/Code2Video/experiments'))
 if not root.exists():pytest.skip('Historical evidence unavailable; no fabricated trace')
 c=json.loads((root/'biology_expert_v4_2/contracts'/topic/'scientific_contract.json').read_text());f=root/'scientific_scene_v4_1/groups'/label;s=json.loads((f/'scene_graph.json').read_text());t=json.loads((f/'geometry_trace.json').read_text())
 b=ScientificRoleBinder().bind(c,s,t);r=RuntimeObservationAdapter().execute(c,s,t,b);assert r['measured_observations'];m=ObservationMutationTester().run(c,s,t,b,r);assert m['detected']>=1 and m['missed']==0
