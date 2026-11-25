from pathlib import Path
import sys,copy,shutil
sys.path.insert(0,str(Path(__file__).parent))
import run as d
f=d.E/'groups/M1_mitosis';g=d.load(f/'scene_graph.json');archive=f/'before_centromere_checkpoint';archive.mkdir(exist_ok=True)
for name in ['scene_graph.json','status.json','video.mp4','geometry_trace.json','approval_ir_review.json','approval_video_review.json']:
 if (f/name).exists():shutil.copy2(f/name,archive/name)
for o in g['objects']:
 if o['object_id'] in ['sister_A','sister_B']:
  o['anchors']['centromere']={'kind':'point','index':2}
  o['scientific_properties']['centromeric_region']='centromere anchor; persists after cohesion cleavage'
 if o['object_id'].startswith('kinetochore'):
  o['scientific_properties'].update(role='kinetochore at centromere',faces_pole='pole_left' if o['object_id'].endswith('A') else 'pole_right')
for rels in [g['relations'],g['assemblies'][0]['relations']]:
 for rel in rels:
  if rel['type']=='attachment' and rel['source'].startswith('kinetochore'):
   rel['target_anchor']='centromere';rel['scientific_relation']='kinetochore_at_centromere'
  if rel['type']=='sister_cohesion':rel.update(source_anchor='centromere',target_anchor='centromere',scientific_relation='sister_cohesion_via_cohesin')
 for k in ['A','B']:
  rels.append({'source':'kinetochore_'+k,'target':'sister_'+k,'type':'kinetochore_at_centromere','source_anchor':'center','target_anchor':'centromere'})
for ev in g['events']:
 if ev['event_id']=='metaphase':ev['caption']='Opposite-pole attachment; checkpoint assumed satisfied'
 else:ev['caption']='Sister cohesion is released; centromeres remain intact'
for t in g['state_transitions']:
 if t['params'].get('state_updates',{}).get('phase')=='aligned':t['params']['state_updates']['checkpoint_satisfied']=True
 if t['operation']=='split':t['preconditions'].append({'constraint_id':'checkpoint_satisfied','predicate':'state_is','key':'checkpoint_satisfied','value':True})
g['scientific_simplifications']+=['Kinetochore at centromere is explicitly represented by attachment relation and centromere anchor. Cohesin cleavage is abstracted as loss of sister cohesion; centromere and kinetochores remain.','Spindle checkpoint satisfaction is assumed, shown in the caption and encoded as gate; molecular checkpoint pathway is not taught.']
st=d.render(f.name,g,tag='centromere_checkpoint_clarity');assert st['render_success'],st
