from pathlib import Path
import sys,shutil,json
R=Path(__file__).resolve().parents[3];E=Path(__file__).parent;sys.path.insert(0,str(R/'Code2Video/src'))
from biology_expert.contracts import write,digest
from biology_expert.typed_science_builder import TypedContractCompiler
from scientific_scene.typed_planner import bind_typed_plan
from biology_expert.temporal_validator import TemporalMechanismValidator,MechanismMutationTester
from biology_v2_pipeline import TransactionRenderer
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--topic',required=True);args=parser.parse_args();folder=E/'candidates'/args.topic
load=lambda p:json.loads(Path(p).read_text());result=load(folder/'typed_result.json');model=result['model'];review=result['review'];scene=load(folder/'scene_graph.json')
assert review['decision']=='PASS' and review['model_hash']==digest(model)
assets=folder/'payload';assets.mkdir(exist_ok=True);(assets/'__init__.py').write_text('');write(assets/'scene_graph.json',scene)
shutil.copytree(R/'Code2Video/src/scientific_scene',assets/'scientific_scene',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
runtime=folder/'biology_runtime_typed.py';runtime.write_text((R/'Code2Video/src/biology_runtime.py').read_text()+'\nfrom assets.scientific_scene.adapters.typed_manim_adapter import TypedScientificScene\n')
code='from biology_runtime import TypedScientificScene\nclass Section4Scene(TypedScientificScene):\n def construct(self):\n  self.render_typed()\n'
renderer=TransactionRenderer(folder/'render',runtime,assets,duration_range=(5,10));out=renderer.attempt(code,'typed_visual6');write(folder/'render_result.json',out);assert out['committed'],out
shutil.copy2(out['after']['video'],E/'sample_video.mp4');shutil.copy2(Path(out['after']['version'])/'geometry_trace.json',E/'sample_trace.json');shutil.copy2(folder/'scene_graph.json',E/'sample_scene.json')
trace=load(E/'sample_trace.json');plan=bind_typed_plan(model,TypedContractCompiler().compile(model,review),scene);checks=TemporalMechanismValidator().execute(plan,model,scene,trace);write(folder/'runtime_checks.json',checks);write(folder/'mutation_results.json',MechanismMutationTester().run(plan,model,scene,trace,checks));print(json.dumps(checks))
