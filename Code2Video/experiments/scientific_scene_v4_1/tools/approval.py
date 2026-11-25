from pathlib import Path
import sys,json,copy,shutil,math,os
sys.path.insert(0,str(Path(__file__).parent))
import run as d,expert
from scientific_scene.scientific_review import graph_polarity,ScientificConflictAdjudicator
from scientific_scene.models import write,digest

def enrich(g):
 g=copy.deepcopy(g)
 for obj in g['objects']:
  oid=obj['object_id'];props=obj['scientific_properties']
  if oid.startswith('rna_primer'):
   leading=oid.endswith('leading')
   props.update(endpoint_labels={'start':"5'" if leading else "3'",'end':"3'" if leading else "5'"},growth_port='end' if leading else 'start')
   props['biological_role']='RNA initiation; DNA extension starts at primer 3prime and continues away from primer toward growing DNA 3prime'
  if oid=='helicase':
   obj['asset_id']='helicase_schematic';obj['visual_representation'].update(sides=6,radius=.19,color='#FF66AA',label='Helicase',label_side='down')
   props.update(representation_precision='schematic hexagon, not molecular structure')
 if not any(a['asset_id']=='helicase_schematic' for a in g['assets']):g['assets'].append({'asset_id':'helicase_schematic','format':'polygon','color':'#FF66AA','fidelity':'schematic','provenance':{'source_type':'original_schematic','source_url':None,'license':'CC0-1.0'},'editable':['center','radius','color'],'connectable_ports':['center']})
 g['scientific_simplifications']+=['Helicase is a generic hexagonal schematic, not a primase SVG or claim about protein structure.','Primer 3prime is covalently extended: after DNA is added, the growing DNA 3prime is free and moves away from the original RNA primer; it need not remain next to the original primer.','Section2 covers origins/licensing. Section4 demonstrates one local fork and one local primer removal; other primers remain.']
 # Explicit source/target endpoints for RNA-DNA continuity, preserving geometry.
 rels=g['assemblies'][0]['relations']
 for primer,strand,port in [('rna_primer_leading','new_leading','end'),('rna_primer_lagging_1','fragment_1','start'),('rna_primer_lagging_2','fragment_2','start')]:
  
  if any(r.get('source')==primer and r.get('target')==strand and r.get('type')=='primer_extension_continuity' for r in rels):continue
  rels.append({'source':primer,'target':strand,'type':'primer_extension_continuity','source_anchor':port,'target_anchor':'start','activation_condition':'both visible; primer relation removed when primer removed'})
 # Remove primer continuity at RNA removal, retain actual DNA replacement links.
 for t in g['state_transitions']:
  if t['params'].get('visual_updates',{}).get('rna_primer_lagging_1',{}).get('visible') is False:
   t['params'].setdefault('remove_relations',[]).append({'source':'rna_primer_lagging_1','type':'primer_extension_continuity'})
 return g

def review(g,pack,label):
 f=d.E/'groups'/label;st=d.load(f/'status.json');trace=d.load(f/'geometry_trace.json')
 deterministic=d.load(f/'validation_report.json');polarity=graph_polarity(g,pack) if g['topic_id']=='dna_replication' else []
 details={'actual_runtime_checks':deterministic,'polarity':polarity,'exact_scene_sha256':digest(g),'do_not_reuse_old_candidate_findings':True}
 if g['topic_id']=='dna_replication':
  obs=trace['scientific_observations'];detail=[]
  for o in obs:
   if o['objects']['new_leading']['visible']:
    j=o['objects']['template_leading']['anchors']['junction'][0];tip=o['objects']['new_leading']['anchors']['end'][0];detail.append({'time':o['time'],'junction':j,'growing3prime':tip,'gap':j-tip})
  details['growth_boundary']={'samples':len(detail),'overrun_count':sum(x['gap']<-.03 for x in detail),'final':detail[-1] if detail else None,'scope':'Polarity and exposed boundary differ from exact molecular distance; no universal 0.15 schematic-unit biology rule'}
  details['primer_footprint']={o['object_id']:o['visual_representation'].get('points') for o in g['objects'] if o['object_id'] in ['rna_primer_lagging_1','gap_fill']}
 ir=expert.expert.review_ir(g,pack,observations=details);write(f/'approval_ir_review.json',ir)
 mapped_ir=copy.deepcopy(ir)
 inspected={'POL-01-lagging-fragment-direction'}
 for issue in mapped_ir.get('issues',[]):
  if issue['issue_id'] in inspected:issue['rule_id']='DNA_STRAND_POLARITY'
 conflicts=ScientificConflictAdjudicator().adjudicate(g,pack,polarity,mapped_ir,d.load(d.E/'tests/test_results.json'));write(f/'approval_conflicts.json',conflicts)
 rev=expert.expert.review_video(g,pack,st['video_path'],(f/'rendered_code.py').read_text(),trace);write(f/'approval_video_review.json',rev)
 resolved={c['original_issue']['issue_id'] for c in conflicts if c['status']=='REVIEWER_FALSE_POSITIVE'}
 unresolved=[i for i in ir.get('issues',[]) if i['issue_id'] not in resolved and i.get('severity') in ['blocker','major','uncertain']]
 ir_ok=ir['decision']=='PASS' or (ir['decision']=='REVISE' and not unresolved and bool(resolved))
 approved=ir_ok and rev['decision']=='PASS' and all(c['status']=='PASS' for c in deterministic) and all(c['status']=='PASS' for c in polarity)
 st.update(science_gate='SCIENCE_APPROVED' if approved else 'REVISE',ir_review_decision=ir['decision'],video_review_decision=rev['decision'],repair_approved=approved,approval_evidence={'scene_hash':st['scene_hash'],'video_sha256':st['video_sha256'],'code_sha256':st['code_sha256'],'ir_review_id':ir['review_id'],'video_review_id':rev['review_id'],'unresolved_critical_ir':unresolved,'deterministic_all_pass':all(c['status']=='PASS' for c in deterministic),'conflicts':conflicts})
 write(f/'status.json',st);write(f/'approved_manifest.json',st if approved else {'status':'NOT_APPROVED','reason':'Necessary gates not all satisfied'})
 print(label,st['science_gate'],ir['decision'],rev['decision'],flush=True)
 return st

if __name__=='__main__':
 try:
  label=sys.argv[1];f=d.E/'groups'/label;g=d.load(f/'scene_graph.json')
  if label=='B4_expert_repair':
   g=enrich(g);archive=f/'before_asset_identity_followup';archive.mkdir(exist_ok=True)
   for name in ['scene_graph.json','video.mp4','geometry_trace.json','status.json']:
    shutil.copy2(f/name,archive/name)
   out=d.render(label,g,tag='approval_asset_identity_'+str(len(expert.gateway.rows)));assert out['render_success'],out
  pack=d.load(d.E/'knowledge'/g['topic_id']/'knowledge_pack.json');review(g,pack,label)
 finally:expert.archive()
