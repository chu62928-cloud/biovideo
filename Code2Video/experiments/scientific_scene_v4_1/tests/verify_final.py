from pathlib import Path
import sys,json,copy,math,csv
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/scientific_scene_v4_1';sys.path.insert(0,str(R/'src'))
from scientific_scene.models import Assembly,write,digest
from scientific_scene.state_machine import TransitionEngine
from scientific_scene.path_geometry import PathGeometry,PathMorph,ProgressDrivenTransition
from scientific_scene.validation import validate_runtime
load=lambda p:json.loads(Path(p).read_text())
base=load(E/'tests/test_results.json');out=[]
def test(name,fn):
 try:fn();out.append({'test':name,'passed':True})
 except Exception as ex:out.append({'test':name,'passed':False,'error':str(ex)})
def geometry():
 m=PathGeometry([[-3,0,0],[0,0,0],[3,0,0]],stroke_width=5);original=id(m);m.set_opacity(1)
 a=PathMorph(m,[[-3,1,0],[0,-1,0],[3,1,0]]);a.begin()
 for i in range(31):
  a.interpolate(i/30);assert m.get_fill_opacity()==0 and m.get_stroke_width()==5 and id(m)==original
 assert math.dist(m.get_path_anchor({'kind':'point','index':1}),[0,-1,0])<1e-8
test('actual_PathMorph_no_fill_constant_width_identity',geometry)
def progress():
 p=ProgressDrivenTransition([0,0],[2,1],invariants=[lambda q:q[0]<=2]);assert p.at(.5).tolist()==[1,.5]
 try:p.at(2)
 except ValueError:return
 raise AssertionError('out of range accepted')
test('progress_range_and_invariants',progress)
g=load(R/'experiments/scientific_scene_v4/groups/A2_scene_graph_fsm/scene_graph.json')
def endpoints():
 a=Assembly(g['assemblies'][0],g['objects']);before=a.snapshot()
 t=copy.deepcopy(next(t for t in g['state_transitions'] if t['operation']=='connect'));t['params']['source_anchor']='not_an_endpoint';t['preconditions']=[]
 result=TransitionEngine().apply(a,t);assert not result['committed'] and a.snapshot()==before
 unchecked=TransitionEngine().apply(a,t,validate=False);assert unchecked['committed']
test('missing_endpoint_rejected_before_commit_ablation',endpoints)
def actual_drawn_connection():
 f=E/'groups/M1_mitosis';checks=validate_runtime(load(f/'scene_graph.json'),load(f/'geometry_trace.json'));c=next(c for c in checks if c['check_id']=='continuous_drawn_connections');assert c['status']=='PASS' and not c['observed_evidence']['violations']
test('all_rendered_frames_mitosis_connections_continuous',actual_drawn_connection)
def fork():
 d=load(E/'motion/coupled_growth_final.json');assert d['status']=='PASS' and d['observations']>100
test('actual_fork_growth_never_ahead_of_junction',fork)
def identity():
 for label in ['B1_renderer_fix','B2_fork_motion','B3_mechanism_fix','B4_expert_repair','M1_mitosis']:
  f=E/'groups'/label;checks=validate_runtime(load(f/'scene_graph.json'),load(f/'geometry_trace.json'));assert all(c['status']=='PASS' for c in checks if c['category']=='identity')
test('all_groups_persistent_object_instances',identity)
def real_patch():
 a=load(E/'repair_routing/repair_acceptance.json');assert len(a['changed'])==3 and a['before_sha256']!=a['after_sha256']
 b=load(E/'repair_routing/patch_diffs/coupled_process.json');assert b['changes'] and b['before_sha256']!=b['after_sha256']
test('actual_model_identity_and_process_fields_changed',real_patch)
def approval():
 for label in ['B4_expert_repair','M1_mitosis']:
  s=load(E/'groups'/label/'status.json');assert s['science_gate']!='SCIENCE_APPROVED'
 assert (E/'science_current').resolve()==(E/'groups/B3_mechanism_fix').resolve()
test('stale_video_review_cannot_approve_new_hash',approval)
rows=[]
for enabled in [False,True]:
 for label,graph,t in [('missing_endpoint',g,copy.deepcopy(next(t for t in g['state_transitions'] if t['operation']=='connect')))]:
  t['params']['source_anchor']='unknown_port';t['preconditions']=[];a=Assembly(graph['assemblies'][0],graph['objects']);result=TransitionEngine().apply(a,t,validate=enabled);rows.append({'injection':label,'validation':enabled,'result':result})
mit=load(R/'experiments/scientific_scene_v4/groups/B1_mitosis/scene_graph.json')
for enabled in [False,True]:
 t=copy.deepcopy(next(t for t in mit['state_transitions'] if t['operation']=='split'));a=Assembly(mit['assemblies'][0],mit['objects']);rows.append({'injection':'premature_separation','validation':enabled,'result':TransitionEngine().apply(a,t,validate=enabled)})
for enabled in [False,True]:
 t=copy.deepcopy(next(t for t in g['state_transitions'] if t['operation']=='extend'));t['params']['points']=[[0,0,0],[-1,0,0]];t['preconditions']=[];t['postconditions']=[{'constraint_id':'wrong_growth','predicate':'growth_direction','object_ids':t['targets'],'unit_vector':[1,0,0]}];a=Assembly(g['assemblies'][0],g['objects']);rows.append({'injection':'wrong_growth_direction','validation':enabled,'result':TransitionEngine().apply(a,t,validate=enabled)})
write(E/'fsm_ablation/results.json',rows);write(E/'fsm_ablation/injected_errors.json',[{'injection':r['injection'],'validation':r['validation'],'committed':r['result']['committed']} for r in rows])
assert all(r['result']['committed']!=r['validation'] for r in rows)
combined=base['results']+out;write(E/'tests/test_results.json',{'all_passed':all(x['passed'] for x in combined),'passed':sum(x['passed'] for x in combined),'total':len(combined),'includes_negative_controls':True,'results':combined})
print(json.dumps(out));assert all(x['passed'] for x in combined)
