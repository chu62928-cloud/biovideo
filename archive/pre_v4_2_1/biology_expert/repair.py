"""Automatic scoped repair, full-render verification, no release on failed science."""
from pathlib import Path
import json,shutil,time
from .state import write,digest
from .tools.repair_planner import CoderAdapter,bounded_patch
from .tools.mechanism_validator import mechanism_validator
from biology_v2_pipeline import TransactionRenderer,sha
class RepairExecutor:
 def __init__(self,agent,root,runtime,assets):
  self.agent=agent;self.root=Path(root);self.runtime=Path(runtime);self.assets=Path(assets)
 def execute(self,task,source,context):
  path=self.root/task['repair_id'];path.mkdir(parents=True,exist_ok=True)
  counter=path/'attempts.json'
  attempts=json.loads(counter.read_text()) if counter.exists() else []
  tx=TransactionRenderer(path/'render',self.runtime,self.assets,duration_range=(25,35))
  if not tx.state():
   dest=tx.group/'versions/baseline';dest.parent.mkdir(exist_ok=True)
   shutil.copytree(source['version'],dest)
   (tx.group/'current').symlink_to(dest.relative_to(tx.group),target_is_directory=True)
   for n in ['rendered_code.py','video.mp4','status.json']:(tx.group/n).symlink_to('current/'+n)
  before=tx.state()
  if sha(before['code'])!=task['input_hash']:raise ValueError('Repair input version mismatch')
  coder=CoderAdapter(self.agent.gateway)
  outcome={'repair_id':task['repair_id'],'before':before,'attempts':attempts,'accepted':False,'targeted_direction_fixed':False,'global_science_approved':False}
  while len(attempts)<2:
   attempt_no=len(attempts)+1;d=path/f'attempt_{attempt_no}';d.mkdir()
   # Persist attempt before a model request so a restart cannot exceed the limit.
   record={'attempt':attempt_no,'status':'started'};attempts.append(record);write(counter,attempts)
   try:
    reply=coder.generate(task,Path(before['code']).read_text());(d/'model_reply.txt').write_text(reply)
    candidate,scope=bounded_patch(Path(before['code']).read_text(),reply)
    (d/'candidate_code.py').write_text(candidate);write(d/'scope_check.json',scope)
    gate={}
    def science_gate(stage,trace,layout):
     artifacts={'code':candidate,'trace':trace,'trace_ref':str(stage/'geometry_trace.json'),'video':str(stage/'media/videos/rendered_code/480p15/Section4Scene.mp4')}
     measured=self.agent._call('mechanism_validator',{'artifacts':artifacts,'context':context},'Verify scientific repair','Check the candidate actual execution before accepting a version.')
     write(d/'measured_checks.json',measured)
     target=next(c for c in measured['checks'] if c['check_id']=='lagging_gap_growth')
     gate['targeted_direction_fixed']=target['status']=='PASS'
     if target['status']!='PASS':raise ValueError('Scientific gap-growth gate did not pass')
     if any(c['status']=='FAIL' for c in measured['checks']):raise ValueError('New mechanism failure')
     # A full real scientific-video review, not cached layout feedback.
     reviewed=self.agent.verify_revision(task,artifacts,context)
     write(d/'science_review.json',reviewed);gate['review']=reviewed
     if reviewed['decision']!='PASS':raise ValueError('Full science gate not PASS: '+reviewed['decision'])
     if reviewed.get('targeted_gap_direction')!='PASS':raise ValueError('Video reviewer did not confirm the scoped repair')
    result=tx.attempt(candidate,f'scientific_attempt_{attempt_no}',extra_validator=science_gate)
    write(d/'transaction.json',result)
    outcome['targeted_direction_fixed']=gate.get('targeted_direction_fixed',False)
    outcome['latest_review']=gate.get('review')
    record.update(status='committed' if result['committed'] else 'rolled_back',transaction=result)
    if result['committed']:
     outcome.update(accepted=True,global_science_approved=True,after=result['after']);break
    assert tx.state()==before,'Scientific rejection must retain baseline exact matching pair'
    # Correct target + unresolved unrelated/global uncertainty: retrying the same event cannot solve it.
    if gate.get('targeted_direction_fixed'):
     outcome['stop_reason']='Target direction fixed, but whole-section science gate requires upstream/other-scope review; retain candidate and rollback publication.'
     break
   except Exception as exc:
    record.update(status='error',error_type=type(exc).__name__,error=str(exc)[:300])
    if self.agent.gateway.stopped:
     outcome['stop_reason']='API failure/uncertain billing state';break
   finally:write(counter,attempts)
  outcome['attempts']=attempts
  outcome['decision']='PASS' if outcome['accepted'] else 'NEEDS_HUMAN_REVIEW'
  outcome.setdefault('stop_reason','Accepted' if outcome['accepted'] else 'At most two attempts; no verified release')
  outcome['rollback_pair_preserved']=tx.state()==before if not outcome['accepted'] else None
  write(path/'outcome.json',outcome)
  skill=self.agent._call('skill_manager',{'task':task,'result':{'targeted_direction_fixed':outcome['targeted_direction_fixed'],'scientific_commit':outcome['accepted'],'regression_tests':['bounded_target_AST','actual_growth_trace','scientific_rollback_pair'],'experiment_path':str(path)}},'Record reusable candidate experience','Save an inert candidate; only human-approved skills may run.')
  outcome['skill_candidate']=skill;write(path/'outcome.json',outcome)
  return outcome
