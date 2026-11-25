from pathlib import Path
import sys,copy,shutil
sys.path.insert(0,str(Path(__file__).parent))
import run as d
from scientific_scene.models import Assembly,anchor
from scientific_scene.state_machine import TransitionEngine
f=d.E/'groups/B4_expert_repair';g=d.load(f/'scene_graph.json');archive=f/'before_explicit_nick';archive.mkdir(exist_ok=True)
for name in ['scene_graph.json','video.mp4','geometry_trace.json','status.json','approval_ir_review.json','approval_video_review.json']:
 if (f/name).exists():shutil.copy2(f/name,archive/name)
for o in g['objects']:
 geom=o['visual_representation']
 if 'points' in geom:geom['center']=[(min(p[i] for p in geom['points'])+max(p[i] for p in geom['points']))/2 for i in range(3)]
# Dedicated nick anchor is the same genuine shared molecular endpoint; not an offset layout anchor.
for o in g['objects']:
 if o['object_id']=='gap_fill':o['anchors']['ligation_nick']=copy.deepcopy(o['anchors']['end']);o['scientific_properties']['ligation_endpoint']='growing 3prime endpoint after gap fill, coincident with fragment1 5prime'
 if o['object_id'] in ['gap_fill','fragment_1','fragment_2']:
  o['visual_representation']['endpoint_label_offset']=[0,-.36,0]
for t in g['state_transitions']:
 updates=t['params'].get('visual_updates',{})
 for oid,patch in updates.items():
  if 'points' in patch:patch['center']=[(min(p[i] for p in patch['points'])+max(p[i] for p in patch['points']))/2 for i in range(3)]
 if t['operation']=='attach' and t['targets'][0]=='ligase':t['params']['target_anchor']='ligation_nick'
 if t['operation']=='connect' and t['params'].get('relation')=='sealed_nick':
  t['params']['scientific_interpretation']='seal actual 3prime gap_fill endpoint to adjacent 5prime fragment1 start; no DNA synthesis by ligase'
for ev in g['events']:
 if ev['event_id']=='event_5_maturation':ev['caption']='Remove RNA; extend the adjacent DNA 3-prime end; ligase seals the nick'
g['scientific_simplifications']+=['RNA primer footprints and DNA replacement occupy the same local gap. Centers are derived from paths, not independent coordinates.','The nick is an unsealed covalent bond at two coincident 3prime/5prime endpoints, not a missing nucleotide-sized interval. Ligase sits at this endpoint; removal/fill and sealing are separate events.']
g['scientific_simplifications']=list(dict.fromkeys(g['scientific_simplifications']))
a=Assembly(g['assemblies'][0],g['objects']);engine=TransitionEngine()
for t in g['state_transitions']:assert engine.apply(a,t)['committed']
d.write(f/'scene_graph.json',g)
