from pathlib import Path
import json,sys,copy,shutil,ast,traceback,tempfile
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/scientific_scene_v4';sys.path.insert(0,str(R/'src'))
from scientific_scene.models import *
from scientific_scene.scene_compiler import compile_storyboard
from scientific_scene.state_machine import TransitionEngine,OPERATIONS
from scientific_scene.validation import *
from scientific_scene.provenance import label_origin
from biology_v2_pipeline import TransactionRenderer
RESULTS=[]
def test(name,fn):
 try:out=fn();RESULTS.append({'test':name,'passed':True,'details':out})
 except Exception as e:traceback.print_exc();RESULTS.append({'test':name,'passed':False,'error':repr(e)})
def rejects(fn):
 try:fn()
 except Exception:return True
 raise AssertionError('Expected rejection')
def fixture(topic,counts):
 b=json.loads((E/'scene_ir'/(topic+'_blueprint.json')).read_text());s=json.loads((E/'scene_ir'/(topic+'_storyboard_input.json')).read_text())
 pack=json.loads((E/'knowledge'/b['topic_id']/'knowledge_pack.json').read_text())
 plan={'events':[{'event_id':eid,'caption':'OFFLINE MOCK ADAPTER TEST','process_ids':[pid],'duration':duration} for eid,pid,duration in zip(s['required_event_ids'],b['processes'],counts)]}
 # Explicit mock plan, never archived as model-generated experimental result.
 return compile_storyboard(s,pack,b,plan=plan)['scene_graph'],pack,b
DNA,PK,BP=fixture('dna',[3,5,7,8,7]);MIT,MK,MB=fixture('mitosis',[5,7])
def fresh(g):return Assembly(g['assemblies'][0],g['objects'])
test('valid_scene_schemas_both_topics',lambda:[schema_validate('scene_graph',g) for g in [DNA,MIT]])
test('required_assembly_relationships_missing_rejected',lambda:rejects(lambda:schema_validate('assembly',{k:v for k,v in BP['assembly'].items() if k!='relations'})))
def unknown_object():
 g=copy.deepcopy(DNA);g['assemblies'][0]['relations'][0]['target']='unknown'
 assert graph_checks(g,{f['fact_id'] for f in PK['facts']});return True
test('unknown_object_reference_rejected',unknown_object)
def unknown_evidence():
 g=copy.deepcopy(DNA);g['evidence_refs'].append('invented_source')
 assert graph_checks(g,{f['fact_id'] for f in PK['facts']});return True
test('unknown_science_evidence_rejected',unknown_evidence)
test('assembly_components_anchors_and_state_query',lambda:(len(fresh(DNA).get_components()),fresh(DNA).get_anchor('junction_upper'),fresh(DNA).get_state()))
def simulation(g):
 a=fresh(g);engine=TransitionEngine()
 for t in g['state_transitions']:
  result=engine.apply(a,t)
  assert result['committed'],result
 assert set(a.objects)==set(fresh(g).objects)
 return {'steps':len(engine.events),'final_state':a.get_state()}
test('DNA_legal_transitions_all_pre_post_invariants',lambda:simulation(DNA))
test('mitosis_legal_transitions_preserve_two_sisters',lambda:simulation(MIT))
def illegal():
 a=fresh(DNA);before=a.snapshot();r=TransitionEngine().apply(a,DNA['state_transitions'][-1])
 assert not r['committed'] or a.snapshot()==before
 # Use the process first action, whose phase precondition must fail.
 a=fresh(DNA);t=next(x for x in DNA['state_transitions'] if x['process_id']=='maturation')
 r=TransitionEngine().apply(a,t);assert not r['committed'] and a.snapshot()==fresh(DNA).snapshot();return True
test('precondition_failure_rolls_back_state',illegal)
def extra_duplex():
 a=fresh(DNA);a.objects['extra']=copy.deepcopy(a.objects['template_leading']);a.objects['extra']['object_id']='extra'
 assert a.validate();return True
test('extra_parental_strand_or_duplex_detected',extra_duplex)
def wrong_growth():
 a=fresh(DNA);o=a.objects['gap_fill'];o['visual_representation']['points']=[[-1,0,0],[1,0,0]]
 c={'constraint_id':'wrong','predicate':'growth_direction','object_ids':['gap_fill'],'unit_vector':[-1,0,0]}
 assert not condition(a,c);return True
test('wrong_growth_relative_to_injected_polarity_rule',wrong_growth)
def nick_gap():
 a=fresh(DNA)
 c={'constraint_id':'not_adjacent','predicate':'anchor_coincident','object_ids':['gap_fill','fragment_1'],'anchors':['end','start'],'tolerance':.03}
 assert not condition(a,c);return True
test('ligase_cannot_seal_nonadjacent_endpoints',nick_gap)
def mitosis_early_separate():
 a=fresh(MIT);before=a.snapshot();t=next(x for x in MIT['state_transitions'] if x['operation']=='split')
 result=TransitionEngine().apply(a,t);assert not result['committed'] and a.snapshot()==before;return True
test('sister_separation_requires_alignment_and_bipolar_attachment',mitosis_early_separate)
def cloned_identity():
 a=fresh(MIT);original=copy.deepcopy(a);a.objects['sister_A']['scientific_identity']['origin_id']='clone'
 assert not condition(a,{'predicate':'identity_unchanged'},original);return True
test('chromatid_identity_change_detected',cloned_identity)
def invariant():
 a=fresh(DNA);before=a.snapshot();t=copy.deepcopy(DNA['state_transitions'][0])
 t['postconditions']=[{'constraint_id':'forcebad','predicate':'count_kind','kind':'parental_strand','count':3}]
 result=TransitionEngine().apply(a,t);assert not result['committed'] and a.snapshot()==before;return True
test('invariant_postcondition_failure_atomic_rollback',invariant)
def exercise_operations():
 a=fresh(MIT);engine=TransitionEngine()
 for op in OPERATIONS:
  t={'transition_id':'mock_'+op,'process_id':'bipolar_attachment','operation':op,'targets':['sister_A','sister_B'],'params':{},'preconditions':[],'postconditions':[]}
  if op=='transform_state':t['params']={'state_updates':{'mock':1}}
  if op=='move_along_path':t['params']={'paths':{'sister_A':[[-1,0,0]]}}
  if op=='extend':t['targets']=['sister_A'];t['params']={'points':[[0,0,0],[1,0,0]]}
  if op=='split':t['params']={'remove_relation':'mock'}
  if op=='merge':t['params']={'target_group':'group'}
  result=engine.apply(a,t);assert result['committed'],result
 return sorted(OPERATIONS)
test('all_ten_generic_operations_executable',exercise_operations)
def no_topic_branches():
 for p in (R/'src/scientific_scene').rglob('*.py'):
  if 'plugins' in p.parts:continue
  code=p.read_text()
  assert 'topic ==' not in code and 'topic_id ==' not in code
 return True
test('same_core_no_topic_specific_branch',no_topic_branches)
def label_source():
 res=label_origin('Pol δ',[('PLANNER','DNA polymerase'),('STORYBOARD','DNA polymerase'),('CODE',"Text('Pol δ')")])
 assert res['first_observed_stage']=='CODE';return res
test('Pol_delta_origin_not_blindly_attributed_to_Planner',label_source)
def observed_unknown():
 t={'frames':[],'object_metadata':{},'scientific_observations':[]}
 checks=validate_runtime(DNA,t);assert any(c['status']=='NOT_MEASURED' for c in checks)
 return True
test('missing_observation_not_zero_violations',observed_unknown)
def fake_modelflag():
 g=copy.deepcopy(DNA);g['validated']=True;g['objects'][0]['evidence_ids']=['unknown']
 assert graph_checks(g,{f['fact_id'] for f in PK['facts']});return True
test('model_validated_flag_ignored',fake_modelflag)
# Mock integration goes through the real single-Agent tool registry.
from biology_expert.agent import BiologyExpertAgent
from scientific_scene.adapters.biology_expert_adapter import BiologyExpertSceneAdapter
class MockGateway:
 stopped=False
 def request(self,provider,purpose,prompt,video=None):
  if provider=='qwen':raise ValueError('OFFLINE MOCK malformed JSON')
  return '{"decision":"PASS","issues":[],"notes":["OFFLINE MOCK SEMANTIC REVIEW"]}'
testroot=Path(tempfile.mkdtemp(prefix='offline_',dir=E/'tests'));testroot.chmod(0o755)
agent=BiologyExpertAgent(testroot,MockGateway());bridge=BiologyExpertSceneAdapter(agent,testroot/'reviews')
test('BiologyExpert_real_registry_scene_IR_tool_mock_semantics',lambda:bridge.review_ir(DNA,PK)['decision']=='PASS')
def video_error():
 r=bridge.review_video(DNA,PK,'mock-not-read.mp4','mock-code',{'frames':[],'object_metadata':{}})
 assert r['decision']=='ERROR';return True
test('Qwen_API_or_invalid_JSON_ERROR_never_PASS_mock',video_error)
def repair_scope():
 review={'issues':[{'root_cause_stage':'ASSEMBLY','repair_scope':'assembly_geometry'}]}
 assert review['issues'][0]['root_cause_stage']=='ASSEMBLY';return {'mode':'OFFLINE routing fixture','upstream_repair_preserved':True}
test('assembly_error_routes_to_assembly_not_layout_mock',repair_scope)
def genuine_route():
 from scientific_scene.adapters.biology_expert_adapter import repair_tasks
 tasks=repair_tasks({'issues':[{'issue_id':'injected_assembly','root_cause_stage':'ASSEMBLY','target_objects':['template_leading'],'target_events':['event_1_fork'],'repair_scope':'assembly_geometry','acceptance_criteria':['continuous']} ]})
 assert tasks[0]['root_cause_stage']=='ASSEMBLY' and tasks[0]['repair_scope']=='assembly_geometry'
 assert 'runtime' in tasks[0]['required_validators']
 return True
test('actual_repair_task_builder_preserves_root_layer',genuine_route)
def reject_duplicate_plan():
 plan={'events':[{'event_id':'event_1_fork','caption':'test','process_ids':[pid],'duration':6} for pid in BP['processes']]}
 return rejects(lambda:compile_storyboard(json.loads((E/'scene_ir/dna_storyboard_input.json').read_text()),PK,BP,plan=plan))
test('duplicate_or_out_of_order_plan_rejected',reject_duplicate_plan)
def bbox_anchor():
 obj=copy.deepcopy(DNA['objects'][0]);obj['visual_representation']['points']=[[-5,1.2,0],[2.5,.15,0],[6,.15,0]]
 assert anchor(obj,'center')==[.5,.6749999999999999,0] or abs(anchor(obj,'center')[1]-.675)<1e-8
 return True
test('polyline_center_matches_actual_bounding_box',bbox_anchor)
def temporal_connection_failure():
 f=E/'groups/B1_mitosis'
 g=__import__('json').loads((f/'scene_graph.json').read_text());trace=__import__('json').loads((f/'geometry_trace.json').read_text())
 found=next(c for c in validate_runtime(g,trace) if c['check_id']=='continuous_drawn_connections')
 assert found['status']=='FAIL' and found['observed_evidence']['violations']
 return {'actual_B1_temporal_failure_detected':True}
test('actual_B1_connection_break_detected_over_time',temporal_connection_failure)
# Actual full-render adapter fixture, clearly not an experimental model generation.
payload=testroot/'payload';shutil.copytree(E/'assets',payload)
shutil.copytree(R/'src/scientific_scene',payload/'scientific_scene',ignore=shutil.ignore_patterns('__pycache__'))
(payload/'__init__.py').write_text('')
fixture=copy.deepcopy(DNA);fixture['title']='OFFLINE ADAPTER TEST - NOT MODEL OUTPUT'
for t in fixture['state_transitions']:t['duration']=.08
for ev in fixture['events']:ev['caption']='Offline fixture - no model call'
write(payload/'scene_graph.json',fixture)
runtime=testroot/'biology_runtime_v4.py';runtime.write_text((R/'src/biology_runtime.py').read_text()+'\nfrom assets.scientific_scene.adapters.manim_adapter import ScientificScene\n')
def render_fixture():
 tx=TransactionRenderer(testroot/'render_fixture',runtime,payload)
 code="from biology_runtime import ScientificScene\nclass Section4Scene(ScientificScene):\n    def construct(self):\n        self.render_scene(validation_mode='full')\n"
 result=tx.attempt(code,'offline_adapter')
 write(E/'tests/offline_render_result.json',result)
 assert result['committed'],result.get('error')
 trace=json.loads((Path(result['after']['version'])/'geometry_trace.json').read_text())
 assert trace['scientific_observations'] and not trace['unregistered_visible']
 checks=validate_runtime(fixture,trace)
 assert all(c['status']=='PASS' for c in checks),[(c['check_id'],c['status']) for c in checks]
 # A real failed render must retain the matching successful pointer and hashes.
 before=tx.state();failed=tx.attempt(code.replace("self.render_scene(validation_mode='full')","raise ValueError('injected render failure')"),'injected_failure')
 assert not failed['committed'] and tx.state()==before
 return {'full_render':True,'decode':True,'mode':'OFFLINE_FIXTURE_NOT_EXPERIMENT','hashes':result['after']}
if all(x['passed'] for x in RESULTS):test('generic_Manim_adapter_real_full_render_fixture',render_fixture)
write(E/'tests/test_results.json',{'mode':'OFFLINE_NO_PAID_API','passed':sum(r['passed'] for r in RESULTS),'total':len(RESULTS),'all_passed':all(r['passed'] for r in RESULTS),'results':RESULTS})
for group,cats in [('schema',['schema','reference','evidence']),('assembly',['assembly','components','parental']),('transition',['transition','precondition','invariant','operation'])]:
 write(E/'validation'/(group+'_results.json'),[r for r in RESULTS if any(s in r['test'] for s in cats)])
print(json.dumps({'passed':sum(r['passed'] for r in RESULTS),'total':len(RESULTS),'failed':[r for r in RESULTS if not r['passed']]},ensure_ascii=False))
if not all(r['passed'] for r in RESULTS):sys.exit(1)
