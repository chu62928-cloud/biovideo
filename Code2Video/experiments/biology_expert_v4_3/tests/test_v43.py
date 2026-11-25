from pathlib import Path
import sys,copy
import pytest
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.typed_science_builder import validate_typed_model,TypedContractCompiler,freeze_model
from biology_expert.contracts import digest
from scientific_scene.typed_planner import plan_typed_scene,bind_typed_plan
from biology_expert.temporal_validator import TemporalMechanismValidator,MechanismMutationTester
def fixture():
 support=[{'evidence_id':'TEST','quote':'A generic actor maintains contact during activity.','location':'p1'}]
 model={'model_id':'synthetic','schema_version':'1.0','scope':{'topic':'generic','organism_context':'synthetic test','audience':'test','included_processes':['activity'],'excluded_processes':[],'simplifications':[]},'entities':[{'semantic_id':i,'scientific_name':i,'entity_type':'unit','evidence_ids':['TEST'],'support':support} for i in ['A','B']],'relations':[{'semantic_id':'R','relation_type':'contact','definition':'contact during activity','source_entity':'A','target_entity':'B','evidence_ids':['TEST'],'support':support}],'processes':[{'process_semantic_id':'P','scientific_name':'Activity','action_category':'interaction','participants':[{'role':'actor','entity_ref':'A'},{'role':'target','entity_ref':'B'}],'input_roles':['actor'],'output_roles':['target'],'preconditions':{},'effects':{},'temporal_scope':{'start_condition':'activity begins','end_condition':'activity ends','after':[],'concurrent_with':[]},'observables':[{'constraint_id':'C','predicate':'relation_holds_during','relation_ref':'R','source_role':'actor','target_role':'target','capability':'DETERMINISTIC','evidence_ids':['TEST'],'support':support}],'evidence_ids':['TEST'],'support':support,'exceptions':[]}],'unresolved_questions':[]}
 evidence=[{'evidence_id':'TEST','passages':[{'location':'p1','text':support[0]['quote']}]}];review={'decision':'PASS','model_hash':digest(model)};return model,evidence,review
def test_schema_valid_and_invalid():
 m,e,r=fixture();assert validate_typed_model(m,e);m.pop('scope')
 with pytest.raises(Exception):validate_typed_model(m,e)
def test_unknown_entity_rejected():
 m,e,r=fixture();m['processes'][0]['participants'][0]['entity_ref']='missing'
 with pytest.raises(ValueError,match='entity'):validate_typed_model(m,e)
def test_quote_location_integrity():
 m,e,r=fixture();e[0]['passages'][0]['text']='unrelated'
 with pytest.raises(ValueError,match='UNRESOLVED_EVIDENCE'):validate_typed_model(m,e)
def test_wrong_relation_participant_type_rejected():
 m,e,r=fixture();m['relations'][0]['source_entity']='B'
 with pytest.raises(ValueError,match='mismatch'):validate_typed_model(m,e)
def test_scene_semantic_ids_and_no_blueprint():
 m,e,r=fixture();s=plan_typed_scene(m,r);p=TypedContractCompiler().compile(m,r);bound=bind_typed_plan(m,p,s);assert s['events'][0]['process_semantic_id']=='P' and bound['compiled_constraints'][0]['process_semantic_id']=='P'
def test_concurrent_independent_intervals():
 m,e,r=fixture();second=copy.deepcopy(m['processes'][0]);second['process_semantic_id']='P2';second['observables'][0]['constraint_id']='C2';second['temporal_scope']['concurrent_with']=['P'];m['processes'].append(second);r['model_hash']=digest(m);s=plan_typed_scene(m,r)
 assert s['events'][0]['start_time']==s['events'][1]['start_time'];assert s['events'][0]['end_trigger']!=s['events'][1]['end_trigger']
def execution():
 m,e,r=fixture();s=plan_typed_scene(m,r);p=bind_typed_plan(m,TypedContractCompiler().compile(m,r),s);ev=s['events'][0];a,b=ev['start_time'],ev['end_time'];trace={'events':[{'id':ev['event_id'],'time':a}],'scientific_observations':[{'time':a+(b-a)*i/30,'objects':{},'relations':s['relations'],'state_variables':{}} for i in range(30)]};return m,s,p,trace
def test_runtime_pass_and_early_end():
 m,s,p,t=execution();x=TemporalMechanismValidator().execute(p,m,s,t);assert x['checks'][0]['status']=='PASS'
 for f in t['scientific_observations'][15:]:f['relations']=[]
 assert TemporalMechanismValidator().execute(p,m,s,t)['checks'][0]['status']=='FAIL'
def test_mutation_different_mechanism_types_and_controls():
 m,s,p,t=execution();v=TemporalMechanismValidator().execute(p,m,s,t);mut=MechanismMutationTester().run(p,m,s,t,v);assert mut['distinct_valid_mutation_types']==2 and mut['detected']==2 and mut['false_positives']==0
def test_no_trace_no_pass():
 m,s,p,t=execution();assert TemporalMechanismValidator().execute(p,m,s,{})['checks'][0]['status']=='NOT_MEASURED'
def test_frozen_hash_rejects_scene_after_mutation(tmp_path):
 m,e,r=fixture();freeze_model(m,r,tmp_path);m['scope']['audience']='changed'
 with pytest.raises(ValueError,match='reviewed'):plan_typed_scene(m,r)
def test_no_topic_names_in_common_paths():
 for name in ['biology_expert/typed_science_builder.py','scientific_scene/typed_planner.py','scientific_scene/adapters/typed_manim_adapter.py']:
  text=(R/'Code2Video/src'/name).read_text();assert not any(topic in text for topic in ['dna_replication','mitosis','vesicle'])
def test_failed_science_review_blocks_planner():
 m,e,r=fixture();r['decision']='REVISE'
 with pytest.raises(ValueError):plan_typed_scene(m,r)

def test_explicit_role_binding_beats_shared_entity_type():
 m,e,r=fixture();s=plan_typed_scene(m,r);extra=copy.deepcopy(s['objects'][1]);extra['object_id']='other_B';s['objects'].insert(0,extra)
 plan=bind_typed_plan(m,TypedContractCompiler().compile(m,r),s)
 assert plan['compiled_constraints'][0]['participants']['target']==['object_2']
def test_all_relation_instances_checked():
 m,s,p,t=execution();rule=p['compiled_constraints'][0];rule['spec']['expected_pairs']=[{'source':'object_1','target':'object_2'},{'source':'second_A','target':'second_B'}]
 assert TemporalMechanismValidator().execute(p,m,s,t)['checks'][0]['status']=='FAIL'
def test_unknown_explicit_participant_rejected():
 m,e,r=fixture();s=plan_typed_scene(m,r);s['events'][0]['participant_bindings']['actor']='missing'
 with pytest.raises(ValueError,match='Unknown scene participant'):bind_typed_plan(m,TypedContractCompiler().compile(m,r),s)
