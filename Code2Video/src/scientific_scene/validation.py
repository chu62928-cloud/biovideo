"""A small predicate DSL plus expected/observed checks. No topic-specific branches."""
import math,copy
from .models import anchor,digest
PREDICATES={'state_is','object_exists','visible','relation_exists','relation_absent','anchor_coincident','property_is','count_kind','growth_direction','all_visible','identity_unchanged'}
def condition(a,c,previous=None):
 op=c['predicate'];ids=c.get('object_ids',[])
 if op=='state_is':return a.state.get(c['key'])==c['value']
 if op=='object_exists':return all(i in a.objects for i in ids)
 if op=='visible':return bool(a.objects[ids[0]]['visual_representation'].get('visible',False))==c.get('value',True)
 if op=='all_visible':return all(a.objects[i]['visual_representation'].get('visible',False) for i in ids)
 if op in ['relation_exists','relation_absent']:
  match=any(r['type']==c['relation'] and r['source']==ids[0] and r['target']==ids[1] for r in a.relations)
  return match if op=='relation_exists' else not match
 if op=='anchor_coincident':return math.dist(anchor(a.objects[ids[0]],c['anchors'][0]),anchor(a.objects[ids[1]],c['anchors'][1]))<=c.get('tolerance',.06)
 if op=='property_is':return a.objects[ids[0]]['scientific_properties'].get(c['key'])==c['value']
 if op=='count_kind':return sum(o['scientific_identity']['kind']==c['kind'] for o in a.objects.values())==c['count']
 if op=='identity_unchanged':
  return previous is None or all(i in previous.objects and o['scientific_identity']['origin_id']==previous.objects[i]['scientific_identity']['origin_id'] for i,o in a.objects.items()) and set(a.objects)==set(previous.objects)
 if op=='growth_direction':
  obj=a.objects[ids[0]];start=anchor(obj,'start');end=anchor(obj,'end');v=c['unit_vector']
  return sum((y-x)*z for x,y,z in zip(start,end,v))>c.get('min_projection',.01)
 raise ValueError('Unknown predicate: '+op)
def conditions(a,rules,previous=None):
 errors=[]
 for c in rules:
  try:
   if not condition(a,c,previous):errors.append({'constraint_id':c['constraint_id'],'predicate':c['predicate'],'reason':'condition false'})
  except Exception as e:errors.append({'constraint_id':c.get('constraint_id'),'reason':type(e).__name__+': '+str(e)})
 return errors
def graph_checks(graph,evidence_ids):
 ids=[o['object_id'] for o in graph['objects']];known=set(ids);errors=[]
 if len(ids)!=len(known):errors.append('duplicate object identity')
 for obj in graph['objects']:
  if not set(obj['evidence_ids'])<=evidence_ids:errors.append('unknown evidence on '+obj['object_id'])
  if obj.get('asset_id') not in {a['asset_id'] for a in graph['assets']}:errors.append('unknown asset reference')
  if not obj['anchors']:errors.append('missing connectable anchors')
 for a in graph['assemblies']:
  if not set(a['component_ids'])<=known:errors.append('unknown assembly component')
  if len(a['component_ids'])!=len(set(a['component_ids'])):errors.append('duplicate component')
  for rel in a['relations']:
   if rel['source'] not in known or rel['target'] not in known:errors.append('unknown relation object')
 for c in graph['constraints']:
  if c['predicate'] not in PREDICATES:errors.append('unknown predicate')
  if not set(c.get('object_ids',[]))<=known:errors.append('unknown constraint object')
 for t in graph['state_transitions']:
  if not set(t['targets'])<=known:errors.append('unknown transition object')
  if not set(t['evidence_ids'])<=evidence_ids:errors.append('unknown evidence in transition')
 events={e['event_id']:i for i,e in enumerate(graph['events'])}
 if len(events)!=len(graph['events']):errors.append('duplicate event ID')
 for a,b in graph.get('event_order',[]):
  if a not in events or b not in events or events[a]>=events[b]:errors.append('invalid event order')
 for ref in graph['evidence_refs']:
  if ref not in evidence_ids:errors.append('unknown scientific evidence')
 return errors
def item(check_id,category,status,objects=None,events=None,evidence=None,observed=None,expected='',description='',stage='SCENE_IR'):
 return {'check_id':check_id,'category':category,'status':status,'object_ids':objects or [],'event_ids':events or [],'evidence_ids':evidence or [],'observed_evidence':observed or {},'expected_condition':expected,'description':description,'suggested_repair_stage':stage}
def validate_graph(graph,pack):
 verified={f['fact_id'] for f in pack['facts'] if f.get('verification')=='VERIFIED'}
 errors=graph_checks(graph,verified)
 return [item('schema_references','schema','FAIL' if errors else 'PASS',observed={'errors':errors},expected='All references exist and facts were verified')]
def validate_runtime(graph,trace):
 """All measured anchors come from actual Manim objects, not expected state values."""
 frames=trace.get('frames',[]);checks=[];expected_ids={o['object_id'] for o in graph['objects']}
 observed_ids=set(trace.get('object_metadata',{}))
 extras=[i for i in observed_ids-expected_ids if trace['object_metadata'][i].get('role') not in ['label','decoration','anchor']]
 checks.append(item('registered_scientific_identity','identity','PASS' if expected_ids<=observed_ids and not extras else 'FAIL',observed={'missing':sorted(expected_ids-observed_ids),'unexpected_scientific_ids':extras}))
 observations=trace.get('scientific_observations',[])
 if not observations:
  checks.append(item('actual_execution','execution','NOT_MEASURED',description='No adapter observation records'));return checks
 fingerprints={};violations=[]
 for obs in observations:
  for oid,o in obs['objects'].items():
   if oid in fingerprints and o['instance_id']!=fingerprints[oid]:violations.append({'time':obs['time'],'object_id':oid})
   fingerprints[oid]=o['instance_id']
 checks.append(item('object_instance_continuity','identity','FAIL' if violations else 'PASS',observed={'violations':violations,'tracked_objects':len(fingerprints)}))
 actual_events=[e['id'] for e in trace.get('events',[])]
 valid=all(a in actual_events and b in actual_events and actual_events.index(a)<actual_events.index(b) for a,b in graph.get('event_order',[]))
 checks.append(item('actual_event_order','event_order','PASS' if valid else 'FAIL',observed={'events':actual_events}))
 last=observations[-1]
 for c in graph['constraints']:
  if c.get('runtime_only') is False:continue
  relevant=[o for o in observations if (c.get('after_event') is None or c['after_event'] in o.get('completed_events',[])) and (c.get('during_event') is None or c['during_event']==o.get('current_event'))]
  if not relevant:
   checks.append(item(c['constraint_id'],'execution','NOT_MEASURED',c.get('object_ids'),evidence=c.get('evidence_ids'),description='Required event not observed'));continue
  obs=relevant[-1];objs=obs['objects'];status='UNCERTAIN';data={}
  op=c['predicate'];ids=c.get('object_ids',[])
  if op=='anchor_coincident' and all(i in objs for i in ids):
   a=objs[ids[0]]['anchors'][c['anchors'][0]];b=objs[ids[1]]['anchors'][c['anchors'][1]]
   distance=math.dist(a,b);status='PASS' if distance<=c.get('tolerance',.06) else 'FAIL';data={'measured_distance':distance,'a':a,'b':b,'time':obs['time']}
  elif op=='count_kind':
   count=sum(o['kind']==c['kind'] for o in objs.values());status='PASS' if count==c['count'] else 'FAIL';data={'count':count}
  elif op=='growth_direction':
   samples=[o for o in relevant if ids[0] in o['objects'] and o['objects'][ids[0]]['visible']]
   endpoints=[]
   for o in samples:
    p=o['objects'][ids[0]]['anchors']['end']
    if not endpoints or math.dist(endpoints[-1][1],p)>.01:endpoints.append((o['time'],p))
   projections=[sum((b-a)*v for a,b,v in zip(x[1],y[1],c['unit_vector'])) for x,y in zip(endpoints,endpoints[1:])]
   status='PASS' if projections and all(x>=-.015 for x in projections) and sum(projections)>.05 else ('FAIL' if any(x<-.015 for x in projections) else 'UNCERTAIN')
   data={'actual_endpoints':endpoints,'step_projections':projections,'coordinate_rule_fact_ids':c.get('evidence_ids',[]),'rule_polarity_basis':c.get('polarity_basis')}
  elif op=='identity_unchanged':status='PASS' if not violations else 'FAIL'
  elif op=='property_is':
   actual=objs[ids[0]].get('scientific_properties',{}).get(c['key'])
   status='PASS' if actual==c['value'] else 'FAIL';data={'observed_role_metadata':actual,'limitation':'Semantic role is not inferable from geometry alone'}
  elif op=='relation_exists':
   valid=any(r['type']==c['relation'] and r['source']==ids[0] and r['target']==ids[1] for r in obs['relations'])
   status='PASS' if valid else 'FAIL';data={'observed_relation_state':valid,'limitation':'Relation bookkeeping must be corroborated by endpoints'}
  checks.append(item(c['constraint_id'],c.get('category','mechanism'),status,ids,evidence=c.get('evidence_ids'),observed=data,expected=c.get('description',''),stage='ANIMATION_IMPLEMENTATION'))
 mismatches=[]
 for expected in trace.get('expected_snapshots',[]):
  observed=min(observations,key=lambda o:abs(o['time']-expected['time']))
  for oid,obj in expected['expected']['objects'].items():
   actual=observed['objects'].get(oid)
   if actual is None:
    mismatches.append({'object_id':oid,'time':expected['time'],'reason':'missing observation'});continue
   visible=bool(obj['visual_representation'].get('visible',False))
   if actual['visible']!=visible:mismatches.append({'object_id':oid,'time':expected['time'],'reason':'visibility differs'})
   for port in obj['anchors']:
    distance=math.dist(anchor(obj,port),actual['anchors'][port])
    if distance>.08:mismatches.append({'object_id':oid,'anchor':port,'distance':distance,'time':expected['time']})
 checks.append(item('expected_observed_states','execution','FAIL' if mismatches else ('PASS' if trace.get('expected_snapshots') else 'NOT_MEASURED'),observed={'mismatches':mismatches,'snapshot_count':len(trace.get('expected_snapshots',[]))},expected='Actual transformed anchors and visibility match committed expected states'))
 binding_errors=[]
 for obs in observations:
  for rel in obs['relations']:
   if rel['type'] not in ['active_site','attachment']:continue
   source=obs['objects'][rel['source']];target=obs['objects'][rel['target']]
   if not source['visible']:continue
   position=target['anchors'][rel.get('target_anchor','center')]
   desired=[x+y for x,y in zip(position,rel.get('offset',[0,0,0]))]
   distance=math.dist(source['center'],desired)
   if distance>.10:binding_errors.append({'object_id':rel['source'],'time':obs['time'],'distance':distance})
 checks.append(item('actual_active_site_bindings','connection','FAIL' if binding_errors else 'PASS',observed={'violations':binding_errors},expected='Visible bound objects follow actual target anchors including declared offset'))
 relation_gaps=[]
 objects_by_id={o['object_id']:o for o in graph['objects']}
 for obs in observations:
  for rel in obs['relations']:
   if not rel.get('draw_link') or rel['draw_link'] not in obs['objects']:continue
   line=obs['objects'][rel['draw_link']]
   if not line['visible']:continue
   for endpoint,oid,port in [('start',rel['source'],rel.get('source_anchor','center')),('end',rel['target'],rel.get('target_anchor','center'))]:
    if endpoint not in line['anchors']:continue
    distance=math.dist(line['anchors'][endpoint],obs['objects'][oid]['anchors'][port])
    if distance>.04:relation_gaps.append({'time':obs['time'],'line':rel['draw_link'],'target':oid,'distance':distance})
 checks.append(item('continuous_drawn_connections','topology','FAIL' if relation_gaps else 'PASS',observed={'violations':relation_gaps},expected='Every drawn connection endpoint follows its real target at every sampled time'))
 extra=trace.get('unregistered_visible',[])
 checks.append(item('visible_coverage','coverage','PASS' if not extra else 'UNCERTAIN',observed={'unregistered_visible':extra},description='All adapter-created scientific and decorative objects registered; arbitrary Coder-added objects checked separately'))
 return checks
