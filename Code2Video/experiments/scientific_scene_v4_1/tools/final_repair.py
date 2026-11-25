from pathlib import Path
import sys,json,copy,shutil,os
sys.path.insert(0,str(Path(__file__).parent))
import run as d,expert
from scientific_scene.models import write,digest,Assembly
from scientific_scene.state_machine import TransitionEngine
from scientific_scene.scientific_review import graph_polarity
f=d.E/'groups/B4_expert_repair';g=d.load(f/'scene_graph.json')
task={'repair_id':'REP_coupled_growth','issue_id':'S1','root_cause_stage':'PROCESS_TEMPLATE','target_artifact':'scene_ir/dna_section4.json','target_object_ids':['new_leading','template_leading','polymerase_leading'],'target_fields':['state_transitions.params.visual_updates.new_leading.points'],'acceptance_criteria':['Leading 3-prime end never ahead of open template arm','Growing end continues during advancing fork after initiation','Polymerase remains bound to end'],'status':'PENDING'}
prompt='''Return JSON only {"process_patch":{"type":"couple_growth_to_fork","target":"new_leading","template":"template_leading","growth_anchor":"end","template_anchor":"junction","lag":1.1,"apply_after_process":"continuous_extension"},"reason":"..."}. This is a real PROCESS_TEMPLATE repair of the provided measured error, not a label change. The new template has an exposed horizontal arm ending one unit behind junction; choose lag >=1.05 to keep tip on exposed template, not in sloped opening or paired duplex. During initial continuous_extension preserve its existing 5prime origin and let 3prime extension advance monotonically. For subsequent fragment_synthesis and maturation steps, couple new_leading.end to junction minus lag along local template tangent; retain original 5prime start. Do not change events, identity or polarity. Patch interpreter will modify the real transition geometry, simulate and verify changes before rendering. No prose-only claims accepted.'''
response=expert.parse_json(expert.gateway.request('deepseek','V41_process_coupling_repair',prompt+json.dumps({'task':task,'video_issue':d.load(f/'video_review.json')['issues'],'current_processes':[(t['process_id'],t['operation']) for t in g['state_transitions']]},ensure_ascii=False)))
write(f/'process_repair_response.json',response)
patch=response['process_patch'];assert patch['type']=='couple_growth_to_fork' and patch['target']=='new_leading' and 1.05<=patch['lag']<=1.5
new=copy.deepcopy(g);changes=[];last_end=-3.68;last_x=None
for t in new['state_transitions']:
 updates=t['params'].get('visual_updates',{});template=updates.get('template_leading',{}).get('points')
 if not template:continue
 j=template[2][0]
 if t['process_id']=='continuous_extension' and t['operation']=='extend' and t['targets']==['new_leading']:
  pts=t['params']['points'];old=copy.deepcopy(pts)
  endpoint=min(pts[-1][0],j-patch['lag']);endpoint=max(last_end,endpoint);pts[-1]=[endpoint,.95,0];last_end=endpoint
  if pts!=old:changes.append({'transition_id':t['transition_id'],'field':'params.points','before':old,'after':copy.deepcopy(pts)})
 elif t['process_id'] in ['fragment_synthesis','maturation']:
  endpoint=max(last_end,j-patch['lag']);last_end=endpoint
  old=copy.deepcopy(updates.get('new_leading'));updates['new_leading']={'visible':True,'points':[[-3.7,.95,0],[endpoint,.95,0]]}
  changes.append({'transition_id':t['transition_id'],'field':'params.visual_updates.new_leading','before':old,'after':copy.deepcopy(updates['new_leading'])})
assert changes,'REPAIR_NOT_APPLIED'
pack=d.load(d.E/'knowledge/dna_replication/knowledge_pack.json');assert all(c['status']=='PASS' for c in graph_polarity(new,pack))
a=Assembly(new['assemblies'][0],new['objects']);engine=TransitionEngine()
for t in new['state_transitions']:assert engine.apply(a,t)['committed']
archive=f/'first_repair_candidate';archive.mkdir(exist_ok=True)
for name in ['scene_graph.json','status.json','video.mp4','geometry_trace.json','validation_report.json','ir_after.json','video_review.json']:
 if (f/name).exists():shutil.copy2(f/name,archive/name)
write(d.E/'scene_ir/dna_section4.json',new);write(d.E/'repair_routing/patch_diffs/coupled_process.json',{'task':task,'before_sha256':digest(g),'after_sha256':digest(new),'changes':changes,'model_patch':patch,'implementation_origin':'deterministic bounded process-patch interpreter'})
st=d.render(f.name,new,tag='process_repair_2')
ir=expert.expert.review_ir(new,pack);write(f/'ir_final.json',ir)
st.update(science_gate='NEEDS_HUMAN_REVIEW',ir_review_decision=ir['decision'],repair_attempts=2,repair_approved=False,video_review_decision='NOT_MEASURED_FOR_NEW_HASH',publish_pointer='B3_mechanism_fix',reason='Two Qwen requests already used; previous video review is bound to different candidate hash, cannot approve new candidate from stale review')
write(f/'status.json',st);history=d.load(d.E/'repair_routing/repair_history.json');history.append({'task':task,'changes':changes,'result':st,'scientific_publication_rolled_back':True});write(d.E/'repair_routing/repair_history.json',history)
expert.archive()
