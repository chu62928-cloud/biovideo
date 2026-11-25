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
Do not use self-confidence scores. Exact quotation matching has already been checked by code, but does not prove entailment. Flag ungrounded extensions, specific details absent from passages, and misleading source statements. Textbooks may contain errors; require source entailment. Restrict to appropriate topic scope. Validate claim meaning, not merely shared keywords. Multiple pages of the same publisher are not independent cross-validation. If insufficient, retain uncertainty.
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
  service=context.get('contract_review_service')
  if service is None:raise ValueError('Scientific Contract review service required; legacy topic rules retired')
  return service.review(artifacts,context['scientific_contract'],context.get('evidence',[]))
