from pathlib import Path
import ast,json,sys,time
import numpy as np

ROOT=Path('/autodl-tmp/code2biovideo').resolve();REPO=ROOT/'Code2Video'
sys.path.insert(0,str(REPO/'src'))
from biology_v2_pipeline import TransactionRenderer,validate_issues,replace_construct,sha
from scope_refine import GridCodeModifier
E=REPO/'experiments/biology_v2_section4';T=E/'tests'/('run_'+str(time.time_ns()));T.mkdir(parents=True)
runtime=REPO/'src/biology_runtime.py'
results=[]
def record(name,passed,evidence):
    results.append({'name':name,'pass':bool(passed),'evidence':evidence})
    print(name,passed,flush=True)

# Reproduce the actual historical bug at the original call seam.
base=REPO/'src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells'
for section in [2,4]:
    source=(base/f'section_{section}.py').read_text()
    fb=json.loads((REPO/f'experiments/qwen4_critic/round_1/feedback/section_{section}.json').read_text())['suggested_improvements']
    bad=GridCodeModifier(source).parse_feedback_and_modify(fb)
    try: ast.parse(bad); caught=False
    except IndentationError: caught=True
    record(f'historical_indent_reproduced_section{section}',caught,'Exact historical source and feedback replayed against original GridCodeModifier')

fixture='from manim import *\nfrom biology_runtime import BiologyScene\nclass Section4Scene(BiologyScene):\n def construct(self):\n  obj=self.register_object("circle",Circle())\n  self.play(Create(obj),run_time=0.3)\n  self.wait(0.1)\n'
tx=TransactionRenderer(T/'transaction',runtime)
initial=tx.attempt(fixture,'initial_fixture')
assert initial['committed'],initial
old=tx.state()
bad=tx.attempt(fixture.replace('  obj=','   obj='),'bad_indent')
record('indentation_not_committed',not bad['committed'] and tx.state()==old,bad)
bad=tx.attempt(fixture.replace('  obj=', '  raise RuntimeError("injected rendering failure")\n  obj='),'render_exception')
record('render_failure_rolls_back_code_and_video',not bad['committed'] and tx.state()==old,bad)
record('paired_hashes_match_manifest',sha(old['code'])==old['code_sha256'] and sha(old['video'])==old['video_sha256'],old)
try:
 validate_issues([{'object_id':'not_existing','issue_type':'overlap','current_state':{},'target_constraint':{},'suggested_change':'move'}],{'circle'})
 unknown_rejected=False
except AssertionError:unknown_rejected=True
record('unknown_object_rejected',unknown_rejected and tx.state()==old,'No model or arbitrary line edit was called')
new=replace_construct(fixture,'def construct(self):\n obj=self.register_object("circle",Square())\n self.play(Create(obj),run_time=0.3)\n self.wait(0.1)\n')
success=tx.attempt(new,'valid_function_repair')
next_input=tx.state()
record('next_round_reads_new_verified_pair',success['committed'] and next_input['video_sha256']!=old['video_sha256'] and sha(next_input['code'])==next_input['code_sha256'],next_input)

switch_code='from manim import *\nfrom biology_runtime import BiologyScene\nclass Section4Scene(BiologyScene):\n def construct(self):\n  enzyme=self.register_object("enzyme",Circle(radius=0.1))\n  a=self.register_object("a",Dot(LEFT),role="anchor")\n  b=self.register_object("b",Dot(RIGHT),role="anchor")\n  self.add(a,b,enzyme)\n  self.bind_near("enzyme","a")\n  self.wait(0.4)\n  self.bind_near("enzyme","b")\n  self.wait(0.4)\n'
switch=TransactionRenderer(T/'binding_switch',runtime)
switch_result=switch.attempt(switch_code,'switch_fixture')
assert switch_result['committed']
switch_metrics=json.loads((Path(switch.state()['version'])/'layout_metrics.json').read_text())
record('binding_switch_only_checks_current_site',not switch_metrics['binding_violations'],switch_metrics)

group_code='from manim import *\nfrom biology_runtime import BiologyScene\nclass Section4Scene(BiologyScene):\n def construct(self):\n  a=Circle(radius=0.2).shift(LEFT)\n  b=Circle(radius=0.2).shift(RIGHT)\n  self.register_object("group",VGroup(a,b))\n  self.add(a,b)\n  self.wait(0.4)\n'
group_tx=TransactionRenderer(T/'group_visibility',runtime)
group_out=group_tx.attempt(group_code,'group_fixture')
assert group_out['committed']
group_trace=json.loads((Path(group_tx.state()['version'])/'geometry_trace.json').read_text())
record('group_visibility_tracks_drawn_children',any(f['objects']['group']['visible'] for f in group_trace['frames']),
       'A registered group can be visible via individually added children without being a top-level scene object')

class HistoricalInstrument(ast.NodeTransformer):
 def visit_ClassDef(self,node):
  if node.name=='TeachingScene':node.bases=[ast.Name(id='HistoryScene',ctx=ast.Load())]
  if node.name=='Section3Scene':node.name='Section4Scene'
  return self.generic_visit(node)
 def visit_Assign(self,node):
  self.generic_visit(node)
  names=[n.id for n in node.targets if isinstance(n,ast.Name)]
  watched={'helix':'dna','zipper':'helicase'}
  extra=[]
  for name in names:
   if name in watched:
    extra.append(ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id='self',ctx=ast.Load()),attr='observe_historical',ctx=ast.Load()),args=[ast.Constant(watched[name]),ast.Name(id=name,ctx=ast.Load())],keywords=[])))
  return [node,*extra]

gaps={}
for label,path in [('baseline',base/'section_3.py'),('regressed',REPO/'experiments/qwen4_critic/round_1/rendered_code/section_3.py')]:
 tree=HistoricalInstrument().visit(ast.parse(path.read_text()))
 tree.body.insert(1,ast.ImportFrom(module='biology_runtime',names=[ast.alias(name='HistoryScene')],level=0))
 code=ast.unparse(ast.fix_missing_locations(tree))
 hist=TransactionRenderer(T/('history_'+label),runtime)
 outcome=hist.attempt(code,'replay')
 assert outcome['committed'],outcome
 trace=json.loads((Path(hist.state()['version'])/'geometry_trace.json').read_text())
 values=[]
 for frame in trace['frames']:
  a=frame['objects'].get('dna');b=frame['objects'].get('helicase')
  if a and b and a['visible'] and b['visible'] and 2<frame['time']<9:
   al,ah=a['bbox'];bl,bh=b['bbox']
   dx=max(al[0]-bh[0],bl[0]-ah[0],0);dy=max(al[1]-bh[1],bl[1]-ah[1],0)
   values.append((dx*dx+dy*dy)**.5)
 gaps[label]=max(values) if values else None
record('historical_DNA_helicase_regression_detected',gaps['baseline'] is not None and gaps['regressed']>gaps['baseline']+.6,{'bbox_separation_scene_units':gaps,'method':'Full historical animations rendered under isolation, AST observer only; not a scientific correctness score'})
summary={'all_passed':all(x['pass'] for x in results),'api_calls':0,'fixture_note':'Handwritten tiny fixture animations are environment/transaction tests only, never A1/A2 Agent results.','tests':results}
(E/'pipeline_tests.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('ALL_PASSED',summary['all_passed'],flush=True)
assert summary['all_passed']
