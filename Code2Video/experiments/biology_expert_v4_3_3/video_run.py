from common import *
import subprocess,shutil,gzip
from biology_expert.typed_science_builder import TypedContractCompiler
from scientific_scene.typed_planner import bind_typed_plan
from biology_expert.temporal_validator import TemporalMechanismValidator
from video_generation.providers import Wan3Provider,SeedanceProvider
V=E/'videos'; V.mkdir(exist_ok=True)
old=R/'experiments/biology_expert_v4_3_2/inputs/mitosis'
result=read(old/'original.json'); model=result['model'];review=result['review']
scene=read(R/'experiments/biology_expert_v4_3_1/sample_scene.json')
assert review['decision']=='PASS' and scene['typed_model_hash']==digest(model)==review['model_hash']
for row in scene['actions']+scene['events']:
    for field in ('start_time','end_time'):row[field]*=3
scene['duration']*=3
for obj in scene['objects']:
    geom=obj['visual_representation']
    if geom['label'].startswith('Sister_'):
        side=-1 if geom['label'].endswith('A') else 1
        geom['label']='Copy '+geom['label'][-1]
        geom['points']=[[side*(0.16-abs(y)*0.14),y,0] for y in (-.92,-.45,-.10,0,.10,.45,.92)]
        geom['color']='#EF839C'
    if obj['object_id'].startswith('kinetochore'):
        geom.update(color='#FFDB74',radius=.13,width=.24,height=.24)
scene['events'][0]['caption']='Spindle fibers attach to kinetochores on the two sister chromatids.'
scene['events'][1]['caption']='The duplicated chromosome moves toward the middle of the cell.'
scene['events'][2]['caption']='The sisters separate. Each is now a chromosome moving toward its own pole.'
write(V/'final_scene.json',scene)
code="""from manim import Text
from scientific_scene.adapters.typed_manim_adapter import TypedScientificScene
class Candidate(TypedScientificScene):
    def construct(self):
        self.camera.background_color = '#11253B'
        self.add(Text('Mitosis   |   From alignment to separation',font_size=33).move_to([0,3.35,0]))
        self.add(Text('RESEARCH CANDIDATE     /     ONE DUPLICATED CHROMOSOME',font_size=16,color='#ACC8DA').move_to([0,2.82,0]))
        self.render_typed('final_scene.json')
"""
(V/'render.py').write_text(code)
env=dict(os.environ,PYTHONPATH=str(R/'src'))
subprocess.run(['manim','--disable_caching','--fps','24','-r','1280,720','--media_dir','media','render.py','Candidate'],cwd=V,env=env,check=True,timeout=480)
mp4=V/'CANDIDATE_mitosis.mp4';shutil.copy(next((V/'media').rglob('Candidate.mp4')),mp4)
subprocess.run(['ffmpeg','-v','error','-i',str(mp4),'-f','null','-'],check=True)
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(mp4),'-vf','fps=1/4,scale=480:-1,tile=2x3','-frames:v','1',str(V/'keyframes.jpg')],check=True)
trace=read(V/'geometry_trace.json')
with gzip.open(V/'final_trace.json.gz','wt') as f:json.dump(trace,f,separators=(',',':'))
plan=bind_typed_plan(model,TypedContractCompiler().compile(model,review),scene)
write(V/'runtime.json',TemporalMechanismValidator().execute(plan,model,scene,trace))
