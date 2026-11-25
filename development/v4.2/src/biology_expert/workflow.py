"""Workflow owns gates and release, not a language-model response."""
from .state import DEPENDENCIES
STAGE_GATE={'KNOWLEDGE':'KNOWLEDGE_GATE','SCRIPT':'SCRIPT_GATE','CAST':'CAST_ASSET_GATE','ASSETS':'CAST_ASSET_GATE','STORYBOARD':'STORYBOARD_GATE','ANIMATION_CODE':'CODE_GATE','RENDERED_VIDEO':'VIDEO_SCIENCE_GATE','FINAL':'FINAL_SCIENCE_GATE'}
class ScienceWorkflow:
 def __init__(self,state):self.state=state
 def apply(self,stage,review):
  gate=STAGE_GATE[stage]
  mapping={'PASS':'PASSED','REVISE':'REVISION_REQUIRED','NEEDS_HUMAN_REVIEW':'HUMAN_REVIEW_REQUIRED','ERROR':'FAILED'}
  self.state.transition(gate,mapping[review['decision']],review)
 def request_upstream_repair(self,task,generator=None):
  if generator is None:return {'status':'NEEDS_HUMAN_REVIEW','reason':'Upstream generator adapter not integrated','repair_id':task['repair_id']}
  self.state.invalidate(STAGE_GATE[task['root_cause_stage']])
  return generator(task)
 def release(self,review,version):
  if review['decision']!='PASS' or any(i['severity']=='blocker' for i in review['issues']):return False
  self.state.transition('APPROVED','PASSED',review)
  from .state import write
  write(self.state.root/'APPROVED.json',{'version':version,'review_id':review['review_id']})
  return True
