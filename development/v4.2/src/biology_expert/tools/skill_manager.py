"""Candidates are inert JSON-compatible YAML until explicit human approval."""
from pathlib import Path
import json,re
from ..state import write,digest
class SkillManager:
 def __init__(self,root,approved_root=None):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
  self.approved_root=Path(approved_root) if approved_root else None
 def propose(self,task,result):
  candidate={'skill_id':'fix_'+re.sub('[^a-z0-9]+','_',task['issue_id'].lower()),'status':'CANDIDATE_NOT_APPROVED','scope':'Instrumented antiparallel DNA gap-fill schematics only; not a universal x-direction rule','trigger':'Actual trace direction disagrees with observed template and nascent polarity','problem_type':task['category'],'repair_method':'Request a minimal Coder loop patch; compare unaffected AST; render completely; revalidate real temporal geometry','preserve_scientific_constraints':task['preserve']+['template polarity','extension at3prime','RNA removal before DNA fill before ligation'],'verification_tools':task['verification'],'regression_tests':result.get('regression_tests',[]),'experiment':{'repair_id':task['repair_id'],'review_id':task['source_review_id'],'result':result},'approval_required':True}
  # JSON is valid YAML1.2, so no parser-specific executable YAML tags.
  p=self.root/(candidate['skill_id']+'_'+task['repair_id']+'_'+digest(result)[:8]+'.yaml');write(p,candidate)
  return {'candidate_path':str(p),'status':'CANDIDATE_NOT_APPROVED'}
 def approved(self):
  if not self.approved_root or not self.approved_root.exists():return []
  return [json.loads(p.read_text()) for p in self.approved_root.glob('*.yaml') if json.loads(p.read_text()).get('status')=='APPROVED']
