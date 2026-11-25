from pathlib import Path
import sys,copy,shutil
sys.path.insert(0,str(Path(__file__).parent))
import run as d
f=d.E/'groups/B4_expert_repair';g=d.load(f/'scene_graph.json');archive=f/'before_temporal_continuity';archive.mkdir(exist_ok=True)
for name in ['scene_graph.json','status.json','video.mp4','geometry_trace.json','approval_ir_review.json','approval_video_review.json']:
 if (f/name).exists():shutil.copy2(f/name,archive/name)
steps=g['state_transitions'];cont=next(t for t in steps if t['transition_id']=='connect_continuous_extension');steps.remove(cont)
first=next(i for i,t in enumerate(steps) if t['operation']=='extend' and t['targets']==['gap_fill'])
steps.insert(first,cont)
# Covalent extension starts at the adjacent pre-existing 3prime end before lengthening;
# separate ligase action occurs only once the other endpoint has been reached.
ev=g['events'][-1];ev['transition_ids'].remove(cont['transition_id']);firstid=steps[first+1]['transition_id'];ev['transition_ids'].insert(ev['transition_ids'].index(firstid),cont['transition_id'])
for ev in g['events']:
 if ev['event_id']=='event_2_priming':ev['caption']='RNA primase starts; a short Pol-alpha DNA handoff is simplified'
 if ev['event_id']=='event_4_two_modes':ev['caption']='After Pol-alpha handoff, Pol-delta extends fragments away from the fork'
g['scientific_simplifications']+=['Lagging fragments grow away from the advancing replication fork. This is the standard local fork teaching convention, not growth toward the fork.','Covalent continuity fragment2-to-gapfill is established before gapfill lengthens. Separate later ligase connect seals gapfill-to-fragment1 after lengthening finishes; no cycle exists in this chain.']
d.write(f/'scene_graph.json',g)
