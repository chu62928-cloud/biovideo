"""Deterministic process data preparation, not model-authored teaching output."""
from pathlib import Path
import copy,json,sys,math
sys.path.insert(0,'/autodl-tmp/code2biovideo/Code2Video/experiments/scientific_scene_v4_1/tools')
import run as d
from scientific_scene.state_machine import TransitionEngine
from scientific_scene.models import Assembly,write,anchor

def action(g,op,targets,params,process='advance_replication_fork',duration=.12,pre=None,post=None):
 return {'operation':op,'targets':targets,'params':params,'transition_id':'progress_'+str(len(g['state_transitions'])),'process_id':process,'assembly_id':g['assemblies'][0]['assembly_id'],'preconditions':pre or [],'postconditions':post or [],'invariants':[],'duration':duration,'evidence_ids':['X_7574276a','X_bf28604c']}

def motion_graph():
 source=d.annotated(d.load(d.V/'groups/A2_scene_graph_fsm/scene_graph.json'))
 a=Assembly(source['assemblies'][0],source['objects']);engine=TransitionEngine()
 # Start after priming and first leading synthesis, never invent invisible DNA.
 for t in source['state_transitions']:
  if t['process_id']=='fragment_synthesis':break
  assert engine.apply(a,t)['committed']
 g=copy.deepcopy(source);g['objects']=list(a.objects.values());g['assemblies'][0]['relations']=copy.deepcopy(a.relations);g['assemblies'][0]['state_variables']=a.state;g['relations']=copy.deepcopy(a.relations)
 g['assemblies'][0]['allowed_transitions'].append('advance_replication_fork')
 g['title']='A local replication fork advances';g['events']=[];g['state_transitions']=[];g['event_order']=[];g['constraints']=[c for c in g['constraints'] if c['predicate'] in ['count_kind','identity_unchanged']]
 objects={o['object_id']:o for o in g['objects']}
 # Map local progress to open-region paths; right chromosome endpoints stay fixed.
 for oid in ['template_leading','template_lagging']:
  objects[oid]['visual_representation']['points'][1][0]=.6
 lead=objects['new_leading'];lead['visual_representation']['points']=[[-3.7,.778,0],[.2,.232,0]]
 enzyme=copy.deepcopy(objects['primase']);enzyme['object_id']='helicase';enzyme['scientific_identity']={'name':'Helicase','kind':'enzyme','origin_id':'helicase'};enzyme['scientific_properties']={'role':'helicase','representation_precision':'schematic'};enzyme['visual_representation'].update(label='Helicase',visible=True,width=.38,center=[.6,.15,0]);g['objects'].append(enzyme);g['assemblies'][0]['component_ids'].append('helicase')
 relation={'source':'helicase','target':'template_leading','type':'active_site','target_anchor':'junction','offset':[0,.32,0]};g['assemblies'][0]['relations'].append(relation)
 refs=g['assemblies'][0]['evidence_ids'];enzyme['evidence_ids']=refs
 g['scene_id']='dna_fork_advance';g['progress_contract']={'process':'advance_replication_fork','coordinate_frame':'local polyline tangent; endpoint remains fixed','start':.6,'end':3.1,'expected_unwound_increase':2.5,'engine':'ProgressDrivenTransition','data_origin':'CODEX_PROCESS_ENGINEERING','duration':10}
 # Every small transition is rendered continuously by PathMorph; boundaries logged.
 from scientific_scene.path_geometry import ProgressDrivenTransition
 progress=ProgressDrivenTransition([.6],[3.1])
 primer1=objects['rna_primer_lagging_1'];primer2=objects['rna_primer_lagging_2']
 # primer1/fragment1 belong to an already exposed location; primer2 appears later.
 all_tids=[]
 for k in range(1,41):
  u=k/40;j=float(progress.at(u)[0]);updates={}
  for oid,sign in [('template_leading',1),('template_lagging',-1)]:
   updates[oid]={'points':[[-5,sign*1.2,0],[j,sign*.15,0],[6,sign*.15,0]],'center':[.5,sign*.675,0]}
  # Leading 3' tip follows exposed region, never crosses into unopened duplex.
  x=j-.4;y=1.2+(x+5)/(j+5)*(.15-1.2)-.25
  updates['new_leading']={'points':[[-3.7,.778,0],[x,y,0]],'visible':True}
  updates['primase']={'visible':False}
  params={'visual_updates':updates,'state_updates':{'progress':u,'phase':'elongating'}}
  t=action(g,'transform_state',list(updates),params,duration=.20)
  g['state_transitions'].append(t);all_tids.append(t['transition_id'])
  # Two separate local initiation/extension sequences, not complete strands popping in.
  if k in [8,22]:
   n=1 if k==8 else 2;pid=f'rna_primer_lagging_{n}';fid=f'fragment_{n}'
   # Primer is laid on an exposed lower template segment, 5' on right, 3' on left.
   right=-.6 if n==1 else 1.7;left=right-.6
   py=lambda z:-1.2+(z+5)/(j+5)*(1.2-.15)+.25
   for oid in [pid,fid]:objects[oid]['scientific_properties']['parent_template']='template_lagging'
   pre=[{'constraint_id':'primer_before_'+fid,'predicate':'visible','object_ids':[pid]}]
   prime=action(g,'transform_state',[pid],{'visual_updates':{pid:{'visible':True,'points':[[right,py(right),0],[left,py(left),0]]}}},duration=.18)
   g['state_transitions'].append(prime);all_tids.append(prime['transition_id'])
   for z in range(1,6):
    end=left-z*.22
    extend=action(g,'extend',[fid],{'points':[[left,py(left),0],[end,py(end),0]]},duration=.08,pre=pre)
    g['state_transitions'].append(extend);all_tids.append(extend['transition_id'])
 g['events']=[{'event_id':'advance_fork','caption':'Helicase opens parental DNA; the leading 3-prime end grows toward the fork','transition_ids':all_tids,'duration':sum(t['duration'] for t in g['state_transitions'])}]
 # Half a second of holds is not needed; target clip remains 11.16s.
 return g

def section_graph(motion):
 base=d.annotated(d.load(d.V/'groups/A2_scene_graph_fsm/scene_graph.json'))
 # Keep all original five teaching events, insert a separate clearly named progression event.
 # The fixed geometry after progression must not jump backward for maturation: the motion clip
 # is the controlled B2/B3 experiment; Section4 integration is held until it passes.
 return motion

def add_connectivity(g):
 g=copy.deepcopy(g);g['mechanism_stage']='B3_scientific_connectivity'
 # The motion clip has initiation and extension, not maturation. Build full Section4 for B3
 # from original processes with a progress event after existing local maturation.
 base=d.annotated(d.load(d.V/'groups/A2_scene_graph_fsm/scene_graph.json'))
 for t in base['state_transitions']:
  if t['operation']=='connect' and t['params'].get('relation')=='sealed_nick':
   idx=base['state_transitions'].index(t)
   connect=copy.deepcopy(t);connect['transition_id']='connect_continuous_extension';connect['targets']=['fragment_2','gap_fill'];connect['params'].update(relation='covalent_continuity',source_anchor='end',target_anchor='start');connect['preconditions']=[{'constraint_id':'extension_endpoints_touch','predicate':'anchor_coincident','object_ids':['fragment_2','gap_fill'],'anchors':['end','start'],'tolerance':.03}]
   base['state_transitions'].insert(idx,connect)
   ev=base['events'][-1];ev['transition_ids'].insert(ev['transition_ids'].index(t['transition_id']),connect['transition_id']);break
 # New fork advance is added as its own process event, after local nick maturation, without
 # claiming the old five-event semantics were replaced. It advances only template geometry;
 # primer/fragments remain at their own material positions.
 a=Assembly(base['assemblies'][0],base['objects']);engine=TransitionEngine()
 for t in base['state_transitions']:assert engine.apply(a,t)['committed']
 base['assemblies'][0]['allowed_transitions'].append('advance_replication_fork')
 ids=[]
 for k in range(1,33):
  j=2.5+1.3*k/32;updates={}
  for oid,sign in [('template_leading',1),('template_lagging',-1)]:updates[oid]={'points':[[-5,sign*1.2,0],[j,sign*.15,0],[6,sign*.15,0]]}
  t=action(base,'transform_state',list(updates),{'visual_updates':updates,'state_updates':{'progress':k/32}},duration=.16);base['state_transitions'].append(t);ids.append(t['transition_id'])
 base['events'].append({'event_id':'advance_fork','caption':'The local fork advances; the parental duplex ahead becomes shorter','transition_ids':ids,'duration':5.12});base['event_order'].append([base['events'][-2]['event_id'],'advance_fork'])
 base['scientific_simplifications'].append('Additional final advance isolates template opening; synthesis was demonstrated in the preceding events, not claimed coupled during this final hold.')
 base['constraints'].append({'constraint_id':'covalent_extension','predicate':'relation_exists','object_ids':['fragment_2','gap_fill'],'relation':'covalent_continuity','after_event':'event_5_maturation','category':'connection','evidence_ids':['X_7574276a']})
 return base

if __name__=='__main__':
 g=motion_graph();d.write(d.E/'motion/advance_replication_fork.json',g)
 st=d.render('B2_fork_motion',g);assert st['render_success'],st
 b3=add_connectivity(g);st=d.render('B3_mechanism_fix',b3);assert st['render_success'],st


def integrated_graph():
 base=d.annotated(d.load(d.V/'groups/A2_scene_graph_fsm/scene_graph.json'))
 for obj in base['objects']:
  geom=obj['visual_representation'];oid=obj['object_id']
  if oid in ['template_leading','template_lagging']:
   sign=1 if oid=='template_leading' else -1
   geom['points']=[[-5,sign*1.2,0],[-.4,sign*1.2,0],[.6,sign*.15,0],[6,sign*.15,0]]
   obj['anchors']['junction']['index']=2
   for port,spec in obj['anchors'].items():
    if port.startswith('pair_'):spec.update(a=2,b=3)
  elif 'points' in geom:
   y=.95 if oid in ['new_leading','rna_primer_leading'] else -.95
   geom['points']=[[v[0],y,0] for v in geom['points']]
   geom['center']=[sum(v[0] for v in geom['points'])/len(geom['points']),y,0]
  if oid=='primase':geom['center']=[-4,.95,0]
 enzyme=copy.deepcopy(next(o for o in base['objects'] if o['object_id']=='primase'))
 enzyme['object_id']='helicase';enzyme['scientific_identity']={'name':'Helicase','kind':'enzyme','origin_id':'helicase'};enzyme['scientific_properties']={'role':'helicase'};enzyme['visual_representation'].update(label='Helicase',width=.35,visible=True,center=[.6,.47,0])
 base['objects'].append(enzyme);base['assemblies'][0]['component_ids'].append('helicase');base['assemblies'][0]['relations'].append({'source':'helicase','target':'template_leading','type':'active_site','target_anchor':'junction','offset':[0,.32,0]})
 # The first opening event is replaced by a short hold in an already open local fork.
 steps=base['state_transitions'];count=len(steps)
 for i,t in enumerate(steps):
  if t['operation']=='extend':
   oid=t['targets'][0];y=.95 if oid=='new_leading' else -.95
   t['params']['points']=[[p[0],y,0] for p in t['params']['points']]
  updates=t['params'].setdefault('visual_updates',{})
  for oid,patch in updates.items():
   if 'points' in patch and oid not in ['template_leading','template_lagging']:
    y=.95 if oid in ['new_leading','rna_primer_leading'] else -.95
    patch['points']=[[p[0],y,0] for p in patch['points']]
  j=.6+2.8*(i+1)/count
  for oid,sign in [('template_leading',1),('template_lagging',-1)]:updates[oid]={'points':[[-5,sign*1.2,0],[j-1,sign*1.2,0],[j,sign*.15,0],[6,sign*.15,0]]}
  if t['process_id']=='open_fork':t['params']['state_updates']={'phase':'opened'}
 base['progress_contract']={'process':'advance_replication_fork','start':.6,'end':3.4,'coupled_to_original_actions':True,'scientific_difference':'Fork and exposed material lengths evolve during original five events, not whole-scene translation'}
 # Connect continuous polymerase extension before the separate ligase nick reaction.
 for idx,t in enumerate(base['state_transitions']):
  if t['operation']=='connect' and t['params'].get('relation')=='sealed_nick':
   connect=copy.deepcopy(t);connect['transition_id']='connect_continuous_extension';connect['targets']=['fragment_2','gap_fill'];connect['params'].update(relation='covalent_continuity',source_anchor='end',target_anchor='start');connect['preconditions']=[{'constraint_id':'extension_endpoints_touch','predicate':'anchor_coincident','object_ids':['fragment_2','gap_fill'],'anchors':['end','start'],'tolerance':.03}]
   connect['params']['visual_updates']={}
   base['state_transitions'].insert(idx,connect);ev=base['events'][-1];ev['transition_ids'].insert(ev['transition_ids'].index(t['transition_id']),connect['transition_id']);break
 base['constraints'].append({'constraint_id':'covalent_extension','predicate':'relation_exists','object_ids':['fragment_2','gap_fill'],'relation':'covalent_continuity','after_event':'event_5_maturation','category':'connection','evidence_ids':['X_7574276a']})
 return base
