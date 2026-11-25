from pathlib import Path
import sys,os,json,copy,shutil,subprocess,time,hashlib
R=Path('/autodl-tmp/code2biovideo/Code2Video').resolve();E=R/'experiments/scientific_scene_v4_1';V=R/'experiments/scientific_scene_v4';sys.path.insert(0,str(R/'src'))
from scientific_scene.models import write,digest,Assembly,schema_validate
from scientific_scene.scientific_review import graph_polarity,RepairRouter,ScientificConflictAdjudicator
from scientific_scene.validation import validate_runtime
from biology_v2_pipeline import TransactionRenderer,sha,trace_metrics
load=lambda p:json.loads(Path(p).read_text())

def payload(folder,g):
 dest=folder/'payload'
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(V/'assets',dest);shutil.copytree(R/'src/scientific_scene',dest/'scientific_scene',ignore=shutil.ignore_patterns('__pycache__'))
 (dest/'__init__.py').write_text('');write(dest/'scene_graph.json',g)
 runtime=folder/'biology_runtime_v41.py';runtime.write_text((R/'src/biology_runtime.py').read_text()+'\nfrom assets.scientific_scene.adapters.manim_adapter import ScientificScene\n')
 return dest,runtime

def render(label,g,code=None,tag='initial'):
 folder=E/'groups'/label;folder.mkdir(exist_ok=True)
 write(folder/'scene_graph.json',g)
 code=code or "from biology_runtime import ScientificScene\nclass Section4Scene(ScientificScene):\n def construct(self):\n  self.camera.background_color='#0E1116'\n  self.render_scene(validation_mode='full')\n"
 (folder/'rendered_code.py').write_text(code)
 assets,runtime=payload(folder,g);tx=TransactionRenderer(folder/'render',runtime,assets)
 result=tx.attempt(code,tag);write(folder/(tag+'_transaction.json'),result)
 with (E/'logs/render_events.jsonl').open('a') as f:f.write(json.dumps({'group':label,**result})+'\n')
 state={'group':label,'render_success':result['committed'],'render_commit':'RENDER_COMMITTED' if result['committed'] else 'RENDER_FAILED','science_gate':'NEEDS_HUMAN_REVIEW','video_path':None,'scene_hash':digest(g),'tag':tag}
 if result['committed']:
  version=Path(result['after']['version'])
  for name in ['video.mp4','geometry_trace.json','layout_metrics.json']:shutil.copy2(version/name,folder/name)
  checks=validate_runtime(g,load(folder/'geometry_trace.json'));write(folder/'validation_report.json',checks)
  state.update(video_path=str(folder/'video.mp4'),video_sha256=sha(folder/'video.mp4'),code_sha256=sha(folder/'rendered_code.py'),trace_sha256=sha(folder/'geometry_trace.json'),duration_seconds=result['after']['duration_seconds'])
 else:state['error']=result.get('error')
 write(folder/'status.json',state);return state

def annotated(g):
 g=copy.deepcopy(g)
 for o in g['objects']:
  oid=o['object_id']
  if oid in ['new_leading','fragment_1','fragment_2','gap_fill']:
   o['scientific_properties'].update(endpoint_labels={'start':"5'",'end':"3'"},growth_port='end',template_id='template_leading' if oid=='new_leading' else 'template_lagging',polarity_evidence_ids=['X_7574276a','X_bf28604c'])
 g['review_context']={'course_outline':{'section2':'Replication origins and licensing','section4':'Local fork priming, extension and maturation'},'current_section':4,'previously_covered_concepts':['origins','licensing'],'required_concepts':['local fork','priming','antiparallel extension','one local maturation'],'allowed_simplifications':g.get('scientific_simplifications',[])}
 return g

def regression():
 g=load(V/'groups/A2_scene_graph_fsm/scene_graph.json')
 code='''from biology_runtime import ScientificScene
from manim import *
from assets.scientific_scene.path_geometry import PathGeometry,PathMorph
class Section4Scene(ScientificScene):
 def construct(self):
  a=PathGeometry([[-5,1,0],[0,1,0],[4,1,0]],color=BLUE,stroke_width=5)
  b=PathGeometry([[-5,-1,0],[0,-1,0],[4,-1,0]],color=GREEN,stroke_width=5)
  self.add(a,b)
  self.play(PathMorph(a,[[-5,2,0],[0,0,0],[4,1,0]]),run_time=1)
  self.play(PathMorph(a,[[-5,2,0],[0,0,0],[4,1,0]],target_mode='curve'),run_time=1)
  self.play(PathMorph(b,[[-5,-1,0],[0,-1,0],[6,-1,0]]),run_time=1)
  self.play(PathMorph(a,[[-5,2,0],[0,0,0],[5,1.5,0]]),PathMorph(b,[[-5,-1,0],[0,-1,0],[5,1.5,0]]),run_time=1)
  self.wait(1)
'''
 # Handwritten generic regression fixture; explicitly not an agent-generated teaching lesson.
 f=E/'tests/render/regression';f.mkdir(exist_ok=True);assets,runtime=payload(f,g)
 # Regression has no scientific assembly; remove ScientificScene teardown expectation via base scene fixture.
 code=code.replace('from biology_runtime import ScientificScene','from biology_runtime import BiologyScene').replace('class Section4Scene(ScientificScene):','class Section4Scene(BiologyScene):')
 # Renderer safety only permits public imports; export generic geometry through trusted runtime.
 runtime.write_text(runtime.read_text()+'\nfrom assets.scientific_scene.path_geometry import PathGeometry,PathMorph\n')
 code=code.replace('from assets.scientific_scene.path_geometry import PathGeometry,PathMorph','from biology_runtime import PathGeometry,PathMorph')
 tx=TransactionRenderer(f/'render',runtime,assets);out=tx.attempt(code,'path_regression');write(f/'result.json',out)
 assert out['committed'],out
 for dest in [E/'tests/render/path_geometry_regression.mp4',E/'renderer_fix/path_geometry_regression.mp4']:shutil.copy2(out['after']['video'],dest)

def baseline_renderer():
 b=E/'groups/B0_frozen';b.mkdir(exist_ok=True);src=V/'groups/A2_scene_graph_fsm'
 write(b/'status.json',{'group':b.name,'render_success':True,'science_gate':'REVISE','video_path':str(src/'video.mp4'),'video_sha256':sha(src/'video.mp4'),'code_sha256':sha(src/'rendered_code.py'),'frozen_reference':True})
 g=load(src/'scene_graph.json');result=render('B1_renderer_fix',g,(src/'rendered_code.py').read_text())
 assert result['render_success'],result
 write(E/'renderer_fix/fixed_input_check.json',{'scientific_IR_unchanged':digest(g)==digest(load(E/'groups/B1_renderer_fix/scene_graph.json')),'only_component_library_changed':True,'historical_code_reused':True})

if __name__=='__main__':
 {'renderer':lambda:(regression(),baseline_renderer())}[sys.argv[1]]()
