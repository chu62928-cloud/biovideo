from pathlib import Path
import sys,shutil,copy
sys.path.insert(0,str(Path(__file__).parent))
import run as d
f=d.E/'groups/M1_mitosis';g=d.load(f/'scene_graph.json');archive=f/'before_layout_followup';archive.mkdir(exist_ok=True)
for name in ['scene_graph.json','video.mp4','geometry_trace.json','status.json','ir_review.json','video_review.json']:
 if (f/name).exists():shutil.copy2(f/name,archive/name)
for o in g['objects']:
 if o['object_id']=='sister_A':o['visual_representation']['label_side']='down'
 if o['object_id']=='sister_B':o['visual_representation']['label_side']='up'
for rel in g['relations']:
 if rel['type']=='attachment' and rel['source'].startswith('kinetochore'):rel['target_anchor']='kinetochore_site'
for o in g['objects']:
 if o['object_id']=='kinetochore_A':o['visual_representation']['center']=[-.22,0,0]
 if o['object_id']=='kinetochore_B':o['visual_representation']['center']=[.22,0,0]
g['scientific_simplifications']=list(dict.fromkeys(g['scientific_simplifications']+['Spindle checkpoint is assumed satisfied before the depicted anaphase.']))
st=d.render(f.name,g,tag='layout_and_relation_followup');st.update(science_gate='NEEDS_HUMAN_REVIEW',ir_review_decision='NOT_MEASURED_FOR_NEW_HASH',video_review_decision='NOT_MEASURED_FOR_NEW_HASH',engineering_followup=True,previous_reviews_not_reused=True)
d.write(f/'status.json',st);shutil.copy2(f/'video.mp4',d.E/'mitosis/mitosis_revised.mp4')
d.write(d.E/'mitosis/connection_checks.json',[c for c in d.load(f/'validation_report.json') if c['category'] in ['connection','topology','execution']])
