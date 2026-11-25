"""One bounded reactive Agent. Policy branches on evidence and observations, not a fixed tool chain."""
from pathlib import Path
import json
from .state import WorkflowState,write,digest
from .tool_registry import ToolRegistry
from .schemas import validate
from .tools.knowledge import topic_analyzer,KnowledgeTools
from .contracts import generic_mechanism_validator as mechanism_validator
from .tools.evidence_retriever import EvidenceRetriever
from .tools.reviewers import ReviewTools,review_result
from .tools.repair_planner import plan_repair
from .tools.skill_manager import SkillManager
from .tools.extractive_builder import supplement
class BiologyExpertAgent:
 def __init__(self,root,gateway,registry=None):
  self.root=Path(root);self.state=WorkflowState(self.root/'state');self.gateway=gateway
  self.registry=registry or ToolRegistry(self.state,max_calls=64)
  self.knowledge=KnowledgeTools(gateway,self.root/'knowledge')
  self.review_tools=ReviewTools(gateway,self.root/'reviews')
  self.retriever=EvidenceRetriever(self.root/'logs/retrieval',max_requests=24)
  self.skills=SkillManager(self.root/'skill_candidates',self.root/'approved_skills')
  for name,callback in [('topic_analyzer',topic_analyzer),('evidence_fetch',self.retriever.fetch_source),('extractive_builder',supplement),('evidence_retriever',self.retriever.retrieve),('knowledge_builder',self.knowledge.build),('support_verifier',self.knowledge.verify),('fact_verifier',self.review_tools.verify_facts),('mechanism_validator',mechanism_validator),('artifact_reviewer',self.review_tools.artifact_review),('video_reviewer',self.review_tools.video_review),('repair_planner',plan_repair),('skill_manager',self.skills.propose)]:
   self.registry.register(name,callback)
 def _call(self,name,args,goal,reason):return self.registry.invoke(name,args,goal,reason)
 def choose_next(self,situation):
  # Explicit bounded action policy: evidence gaps, measured errors and visual ambiguity have different paths.
  if not situation.get('has_evidence'):return 'evidence_retriever','Scientific evidence is missing; retrieve before making claims.'
  if situation.get('conflict'):return 'fact_verifier','Conflicting or unsupported scientific statements need source entailment/scope checking.'
  if situation.get('measured_error'):return 'repair_planner','Observed execution violates an evidence-backed rule; repair its earliest implementation source.'
  if situation.get('code_or_motion_unchecked'):return 'mechanism_validator','Motion claims require actual event/geometry evidence before a model judgment.'
  if situation.get('visual_ambiguity'):return 'video_reviewer','Facts are available but rendered scientific meaning is ambiguous; inspect complete video.'
  return 'artifact_reviewer','Review this stage artifact against verified topic facts.'
 def prepare_topic(self,user_request):
  scope=self._call('topic_analyzer',{'user_request':user_request},'Prepare scientific topic','Identify scope and retrieval goal without inventing facts.')
  name,reason=self.choose_next({'has_evidence':False})
  retrieval=self._call(name,{'scope':scope},'Build topic knowledge',reason)
  if not retrieval['evidence']:
   self.state.log('agent_terminated',reason='UNVERIFIED: all retrieval failed');return {'topic_scope':scope,'facts':[],'status':'UNVERIFIED'}
  pack=self._call('knowledge_builder',{'scope':scope,'retrieval':retrieval},'Build topic knowledge','Extract atomic facts from actually retrieved sources.')
  pack=self._call('support_verifier',{'pack':pack},'Check factual grounding','Check exact source spans and evidence links programmatically.')
  name,reason=self.choose_next({'has_evidence':True,'conflict':True})
  pack=self._call(name,{'pack':pack},'Verify factual meaning',reason)
  self.knowledge.save(pack)
  self.state.register('knowledge_'+scope['topic_id'],pack,'TOPIC_RESEARCH')
  self.state.log('agent_terminated',reason='Knowledge pack built with explicit verification limits',topic_id=scope['topic_id'])
  return pack
 def review(self,stage,artifacts,context):
  try:return self._review(stage,artifacts,context)
  except Exception as exc:
   result=review_result(stage,'ERROR',[],artifacts,[{'tool_error_type':type(exc).__name__,'reason':str(exc)[:250]}])
   write(self.root/'reviews'/stage.lower()/(result['review_id']+'.json'),result)
   self.state.log('agent_terminated',stage=stage,reason='Tool failure; ERROR is never PASS',review_id=result['review_id'])
   return result
 def _review(self,stage,artifacts,context):
  pack=context.get('knowledge_pack',{})
  if not pack.get('facts'):
   if context.get('user_request'):
    pack=self.prepare_topic(context['user_request']);context={**context,'knowledge_pack':pack}
   if not pack.get('facts'):return review_result(stage,'NEEDS_HUMAN_REVIEW',[],artifacts,[{'reason':'No verified knowledge evidence'}])
  if stage in ['ANIMATION_CODE','RENDERED_VIDEO']:
   name,reason=self.choose_next({'has_evidence':True,'code_or_motion_unchecked':True})
   measured=self._call(name,{'artifacts':artifacts,'context':context},'Audit actual mechanism',reason)
   context={**context,'mechanism_result':measured}
   if stage=='ANIMATION_CODE':
    result=self._call('artifact_reviewer',{'stage':stage,'artifacts':artifacts,'context':context},'Review source and observed execution','Use measured evidence to locate a code-level scientific error.')
   else:
    name,reason=self.choose_next({'has_evidence':True,'visual_ambiguity':True})
    result=self._call(name,{'artifacts':artifacts,'context':context},'Review actual video science',reason)
    # Model cannot waive a deterministic violation or silently call missing measurements a PASS.
    failed=[c for c in measured.get('checks',[]) if c['status']=='FAIL']
    if failed:
     source=self.review_tools.artifact_review('ANIMATION_CODE',artifacts,context)
     result['issues']+=source['issues'];result.update(decision='REVISE',next_action='CREATE_REPAIR_TASK')
    elif result['decision']=='PASS' and any(c['status']=='UNCERTAIN' for c in measured.get('checks',[])):
     result.update(decision='NEEDS_HUMAN_REVIEW',next_action='HUMAN_REVIEW')
    result['measured_checks']=measured
  else:
   name,reason=self.choose_next({'has_evidence':True})
   result=self._call(name,{'stage':stage,'artifacts':artifacts,'context':context},'Review '+stage,reason)
  if 'samples' not in result:
   validate('review',result);write(self.root/'reviews'/stage.lower()/(result['review_id']+'.json'),result)
  self.state.log('agent_terminated',reason='Stage review completed',stage=stage,decision=result.get('decision','batch_samples'))
  return result
 def plan_repair(self,review_result,context):
  name,reason=self.choose_next({'has_evidence':True,'measured_error':True})
  task=self._call(name,{'review_result':review_result,'context':context},'Plan minimum scientific rework',reason)
  if 'repair_id' in task:write(self.root/'repair_tasks'/(task['repair_id']+'.json'),task)
  return task
 def verify_revision(self,repair_task,new_artifacts,context=None):
  if context is None:return review_result('RENDERED_VIDEO','ERROR',[],new_artifacts,[{'reason':'Verified knowledge context required'}])
  return self.review('RENDERED_VIDEO',new_artifacts,context)
 def run_gate(self,stage,artifacts,context):
  from .workflow import ScienceWorkflow
  result=self.review(stage,artifacts,context)
  if 'samples' in result:raise ValueError('Gate requires one version-bound artifact, not a sample batch')
  ScienceWorkflow(self.state).apply(stage,result);return result

 def enable_contract_workflow(self,root):
  from .contract_builder import ContractAgentTools
  self.contract_tools=ContractAgentTools(self,root)
  return self.contract_tools
 def build_contract(self,user_request):
  if not hasattr(self,'contract_tools'):self.enable_contract_workflow(self.root/'contract_workflow')
  return self.contract_tools.build_contract(user_request)
 def audit_contract(self,contract,scene,trace,bindings=None,goal_review=None):
  if not hasattr(self,'contract_tools'):self.enable_contract_workflow(self.root/'contract_workflow')
  return self.contract_tools.audit_contract(contract,scene,trace,bindings,goal_review)
 def choose_contract_tool(self,situation):
  if not situation.get('has_evidence'):return 'scientific_evidence_retriever'
  if situation.get('conflict'):return 'scientific_conflict_adjudicator'
  if not situation.get('contract_exists'):return 'scientific_contract_builder'
  if not situation.get('contract_verified'):return 'contract_verifier'
  if situation.get('coverage_gap'):return 'coverage_auditor'
  if situation.get('test_contract'):return 'mutation_tester'
  if situation.get('visual_ambiguity'):return 'reference_video_reviewer'
  return None
