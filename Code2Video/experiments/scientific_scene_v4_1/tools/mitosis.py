from pathlib import Path
import sys,json,copy,shutil
sys.path.insert(0,str(Path(__file__).parent))
import run as d

def main():
 g=d.load(d.V/'groups/B1_mitosis/scene_graph.json');g['title']='Mitosis: sister chromatids separate'
 g['review_context']={'current_section':'Metaphase to anaphase only','required_concepts':['bipolar attachment','cohesion release','persistent chromatid identities'],'allowed_simplifications':['one duplicated chromosome','original schematic, not molecular shape']}
 # Rounded rod with a centromeric constriction. Editable curve, zero fill; two persistent
 # sisters are the two halves of one replicated chromosome, not cloned at separation.
 for obj in g['objects']:
  oid=obj['object_id'];geom=obj['visual_representation']
  if oid in ['sister_A','sister_B']:
   x=-.22 if oid=='sister_A' else .22
   geom.update(points=[[x-.10,.95,0],[x-.02,.48,0],[x,0,0],[x+.02,-.48,0],[x+.10,-.95,0]],center=[x,0,0],stroke_width=18,path_mode='curve',label='Sister A' if oid=='sister_A' else 'Sister B',label_side='up',label_size=16)
   obj['anchors']['kinetochore_site']={'kind':'point','index':2}
  if oid.startswith('kinetochore'):geom.update(radius=.08,color='#FFFFFF')
 for rel in g['assemblies'][0]['relations']:
  if rel['source'].startswith('kinetochore') and rel['type']=='attachment':rel['target_anchor']='kinetochore_site'
 for ev in g['events']:
  ev['caption']='Sister kinetochores attach to opposite poles' if ev['event_id']=='metaphase' else 'Cohesion is released; existing sisters move apart'
 for t in g['state_transitions']:
  if t['operation']=='split':
   t['params']['visual_updates']['sister_A']['label']='Daughter A';t['params']['visual_updates']['sister_B']['label']='Daughter B'
 g['scientific_simplifications']+=['Rounded rod-like chromatids are original editable schematics; shape alone is not evidence of molecular structure. Kinetochore site lies at the constriction, maintained during motion.']
 d.write(d.E/'mitosis/asset_registry.json',{'assets':[{'asset_id':'rounded_chromatid_schematic','object_name':'sister chromatid','format':'editable curve','author':'Project original schematic','source_url':None,'license':'CC0-1.0','editable':True,'scientific_accuracy_status':'NEEDS_VIDEO_REVIEW','representation_precision':'schematic'}]})
 # Record the explicit editable SVG reference without importing an unverified web image.
 (d.E/'mitosis/chromatid_reference.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 220"><path d="M40 15 C45 65 50 85 50 110 C50 135 55 155 60 205" fill="none" stroke="#68d9b0" stroke-width="18" stroke-linecap="round"/><circle cx="50" cy="110" r="6" fill="white"/></svg>')
 result=d.render('M1_mitosis',g);assert result['render_success'],result
 f=d.E/'groups/M1_mitosis'
 shutil.copy2(f/'video.mp4',d.E/'mitosis/mitosis_revised.mp4')
 checks=d.load(f/'validation_report.json');d.write(d.E/'mitosis/connection_checks.json',[c for c in checks if c['category'] in ['connection','topology','execution']])
 # Reuse the same persistent model budget, actual complete video review and original Agent.
 import expert
 pack=d.load(d.E/'knowledge/eukaryotic_mitosis/knowledge_pack.json')
 ir=expert.expert.review_ir(g,pack);d.write(f/'ir_review.json',ir)
 rev=expert.expert.review_video(g,pack,str(f/'video.mp4'),(f/'rendered_code.py').read_text(),d.load(f/'geometry_trace.json'));d.write(f/'video_review.json',rev)
 result.update(ir_review_decision=ir['decision'],video_review_decision=rev['decision'],science_gate='SCIENCE_APPROVED' if ir['decision']=='PASS' and rev['decision']=='PASS' and all(c['status']=='PASS' for c in checks) else 'REVISE')
 d.write(f/'status.json',result);expert.archive()

if __name__=='__main__':main()
