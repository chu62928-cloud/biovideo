"""Evidence grading of actual runtime geometry; pixel visibility remains separate."""
import math

def review_execution(trace,max_jump=1.0):
 frames=trace.get('scientific_observations',[]);issues=[];levels={};previous={};identity={};counts={}
 for f in frames:
  t=f['time']
  for oid,o in f.get('objects',{}).items():
   if o.get('visible') and o.get('opacity') is None:levels[oid]='DECLARED_ONLY'
   else:levels[oid]=o.get('observation_level','DECLARED_ONLY')
   if o.get('visible') and (o.get('opacity',1)<=.001 or not o.get('in_frame',True) or not o.get('effective_size',True)):issues.append({'time':t,'object_id':oid,'issue':'VISIBILITY_CONFLICT'})
   if oid in identity and identity[oid]!=o.get('instance_id'):issues.append({'time':t,'object_id':oid,'issue':'IDENTITY_CHANGED'})
   identity[oid]=o.get('instance_id')
   if oid in previous:
    last,point=previous[oid];dt=t-last;distance=math.dist(point,o['center'])
    if dt>0 and distance>max_jump:issues.append({'time':t,'object_id':oid,'issue':'GEOMETRY_JUMP','distance':distance,'dt':dt})
   previous[oid]=(t,o['center'])
  for r in f.get('relations',[]):
   level=r.get('observation_level','DECLARED_ONLY');counts[level]=counts.get(level,0)+1
   if r.get('endpoint_matches') is False:issues.append({'time':t,'relation_id':r.get('semantic_id'),'issue':'DRAWN_ENDPOINT_MISMATCH','distance':r.get('target_distance')})
 return {'samples':len(frames),'issues':issues,'relation_evidence_counts':counts,'object_evidence_levels':levels,'pixel_verification':'NOT_MEASURED','claim':'Runtime geometry visibility and endpoints only; no pixel or biological PASS inferred.'}
