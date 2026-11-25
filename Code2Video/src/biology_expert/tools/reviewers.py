"""Evidence-aware semantic tools. Model judgments remain separate from measured checks."""
from pathlib import Path
import json,uuid,ast
from ..state import write,digest
from ..providers import parse_json
from ..schemas import validate
def review_result(stage,decision,issues,artifacts,checks=None,**extra):
 result={'review_id':'REV-'+uuid.uuid4().hex[:12],'stage':stage,'decision':decision,'issues':issues,'next_action':{'PASS':'NONE','REVISE':'CREATE_REPAIR_TASK','NEEDS_HUMAN_REVIEW':'HUMAN_REVIEW','ERROR':'STOP'}[decision],'artifact_versions':{k:digest(v) for k,v in artifacts.items() if k not in ['video']},'checks':checks or [],**extra}
 if 'video' in artifacts:result['artifact_versions']['video']=digest(Path(artifacts['video']))
 validate('review',result);return result
def issue(id,description,objects,facts,stage='ANIMATION_CODE',category='scientific_mechanism',severity='blocker',evidence=None,scope='affected_event'):
 return {'issue_id':id,'severity':severity,'category':category,'description':description,'object_ids':objects,'evidence_ids':facts,'artifact_evidence':evidence or {},'root_cause_stage':stage,'suggested_repair_scope':scope}
class ReviewTools:
 def __init__(self,gateway,root):self.gateway=gateway;self.root=Path(root)
 def verify_facts(self,pack):
  prompt="""Independently check the proposed scientific facts AGAINST the actual source passages. Return JSON {"facts":[{"fact_id":"...","status":"VERIFIED|CONFLICTED|INSUFFICIENT_EVIDENCE","reason":"brief source entailment and organism/stage scope judgment","evidence_ids":["..."]}],"conflicts":[]}.
Do not use self-confidence scores. Exact quotation matching has already been checked by code, but does not prove entailment. Flag ungrounded extensions, specific details absent from passages, and misleading source statements. Textbooks may contain errors (e.g. do not conflate RNase H and FEN1). Restrict to appropriate topic scope. Validate claim meaning, not merely shared keywords. Multiple pages of the same publisher are not independent cross-validation. If insufficient, retain uncertainty.
PACK:\n"""+json.dumps(pack,ensure_ascii=False)
  data=parse_json(self.gateway.request('deepseek','independent_fact_verification_'+pack['topic_id'],prompt))
  by={f['fact_id']:f for f in data['facts']}
  for fact in pack['facts']:
   verdict=by.get(fact['fact_id'],{})
   v=verdict.get('status','INSUFFICIENT_EVIDENCE')
   linked=set(verdict.get('evidence_ids',[]))<=set(fact['evidence_ids']) and bool(verdict.get('evidence_ids'))
   fact['semantic_verification']=v if linked and fact['verification']=='VERIFIED' else 'INSUFFICIENT_EVIDENCE'
   fact['semantic_reason']=verdict.get('reason','No independent verdict')
   if fact['semantic_verification']!='VERIFIED':fact['verification']=fact['semantic_verification']
  pack['build_report'].update(independent_verification=data,semantic_verified_count=sum(f.get('semantic_verification')=='VERIFIED' for f in pack['facts']),status='VERIFIED_WITH_SCOPE_LIMITS' if all(f['verification']=='VERIFIED' for f in pack['facts']) else 'PARTIALLY_VERIFIED')
  write(self.root/(pack['topic_id']+'_fact_verification.json'),data)
  return pack
 def artifact_review(self,stage,artifacts,context):
  pack=context.get('knowledge_pack')
  if not pack:return review_result(stage,'NEEDS_HUMAN_REVIEW',[],artifacts,[{'status':'UNCERTAIN','reason':'Missing evidence-backed knowledge'}])
  if stage=='ANIMATION_CODE':
   ast.parse(artifacts['code'])
   checks=context.get('mechanism_result',{}).get('checks',[])
   issues=[]
   for c in checks:
    if c['status']=='FAIL':
     issues.append(issue('BIO-DIRECTION' if c['check_id']=='lagging_gap_growth' else 'BIO-CONTACT',c['check_id']+' failed on actual execution evidence',c.get('object_ids',[]),c.get('fact_ids',[]),evidence={'trace_ref':artifacts.get('trace_ref','geometry_trace.json'),'check':c}))
   return review_result(stage,'REVISE' if issues else 'NEEDS_HUMAN_REVIEW',issues,artifacts,checks)
  prompt="""Scientifically review intermediate artifacts at the specified stage using the supplied verified facts and evidence only. Return JSON {"samples":[{"sample_id":"...", "decision":"PASS|REVISE|NEEDS_HUMAN_REVIEW|ERROR","issues":[{"issue_id":"...","severity":"blocker|major|minor|uncertain","category":"...","description":"...","object_ids":[],"evidence_ids":["fact id"],"artifact_evidence":{"quote":"exact artifact span"},"root_cause_stage":"SCRIPT|CAST|ASSETS|STORYBOARD|ANIMATION_CODE","suggested_repair_scope":"..."}],"checks":[]}]}.
Evaluate each supplied sample independently, including a normal negative control. Detect actual factual contradictions, not omissions outside the stated narrow scope. Do not flag a correct sample just to find an issue. CAST checks scientific role/action/identity/continuity; ASSETS checks scientific identity/schematic-vs-real/source/license; STORYBOARD checks events/causality/polarity/topology; SCRIPT checks terms and causal order. Unsupported claims remain uncertain.
""" + json.dumps({'stage':stage,'knowledge_pack':pack,'samples':artifacts.get('samples',[artifacts])},ensure_ascii=False)
  data=parse_json(self.gateway.request('deepseek','artifact_review_'+stage,prompt))
  results=[]
  for sample in data['samples']:
   out=review_result(stage,sample['decision'],sample.get('issues',[]),artifacts,sample.get('checks',[]),sample_id=sample.get('sample_id'))
   known={f['fact_id'] for f in pack['facts'] if f['verification']=='VERIFIED'}
   if any(set(i['evidence_ids'])-known for i in out['issues']):return review_result(stage,'ERROR',[],artifacts,[{'reason':'Unknown/unverified fact cited by reviewer'}])
   if out['decision']=='PASS' and any(i['severity']=='blocker' for i in out['issues']):out['decision']='REVISE';out['next_action']='CREATE_REPAIR_TASK'
   results.append(out)
  return {'samples':results}
 def video_review(self,artifacts,context):
  pack=context['knowledge_pack']
  prompt="""You are the SINGLE BiologyExpertAgent's scientific video-review TOOL, not the visual-layout critic. Watch the COMPLETE MP4. GRID image is only a coordinate reference. Assess biological meaning, identity, template/new-strand topology, primer removal then polymerase gap filling then ligase nick sealing. Combine actual trajectory and visible polarity; do not trust the generator's intended direction. Report unreadable/ambiguous objects as UNCERTAIN. In particular inspect the central blue hollow ladder: is it parental duplex or an apparent additional DNA? Identify scientific root cause, not just moving icons.
Return JSON with compatibility wrapper "layout":{"has_issues":true/false,"improvements":[]} AND "science":{"decision":"PASS|REVISE|NEEDS_HUMAN_REVIEW|ERROR","targeted_gap_direction":"PASS|FAIL|UNCERTAIN","issues":[{"issue_id":"...", "severity":"blocker|major|minor|uncertain","category":"scientific_mechanism|scientific_identity|scientific_ambiguity","description":"...", "object_ids":["ACTUAL KNOWN ID"],"evidence_ids":["FACT ID"],"artifact_evidence":{"video_timestamp":0.0,"observation":"what is actually seen"},"root_cause_stage":"SCRIPT|CAST|ASSETS|STORYBOARD|ANIMATION_CODE","suggested_repair_scope":"affected_event|scene_geometry|upstream_script"}],"checks":[]}.
Separate the event5 direction repair target from other existing issues. A correct growth order does not imply the whole video PASS. Do not invent precise timestamps you cannot observe. If ambiguous, targeted direction UNCERTAIN; trajectory evidence can establish direction even if sparse frames cannot.
""" + json.dumps({'facts':[f for f in pack['facts'] if f['verification']=='VERIFIED'],'storyboard':context.get('storyboard'),'mechanism_evidence':context.get('mechanism_result'),'actual_code':artifacts['code'],'actual_object_inventory':artifacts['trace']['object_metadata']},ensure_ascii=False)
  if getattr(self.gateway,'qwen_profile',None):
   prompt+='\nCONCISE STRUCTURED RESPONSE: JSON only, no markdown. At most 3 most important issues and 4 short checks. Each description/reason <=80 words. Avoid repeating full source or trajectory tables. Preserve scientific standards; do not hide remaining blockers. Use FACT IDs (not PMID IDs) in evidence_ids and only actual registered object IDs. Output science.targeted_gap_direction separately from overall decision. Overall PASS requires all necessary checks, not just the repaired direction.'
  data=parse_json(self.gateway.request('qwen','science_video_review',prompt,video=artifacts['video']))
  science=data['science'];known=set(artifacts['trace']['object_metadata']);facts={f['fact_id'] for f in pack['facts'] if f['verification']=='VERIFIED'}
  if any(set(i['object_ids'])-known or set(i['evidence_ids'])-facts for i in science.get('issues',[])):return review_result('RENDERED_VIDEO','ERROR',[],artifacts,[{'reason':'Video reviewer cited unknown object or fact ID'}])
  out=review_result('RENDERED_VIDEO',science['decision'],science.get('issues',[]),artifacts,science.get('checks',[]),mode='FULL_MP4',targeted_gap_direction=science.get('targeted_gap_direction','UNCERTAIN'))
  if any(i['severity']=='blocker' for i in out['issues']) and out['decision']=='PASS':out.update(decision='REVISE',next_action='CREATE_REPAIR_TASK')
  write(self.root/(out['review_id']+'.json'),out)
  return out
