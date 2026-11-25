from pathlib import Path
import json,sys,os,traceback,shutil
R=Path('/autodl-tmp/code2biovideo/Code2Video');E=R/'experiments/biology_expert_v3';V2=R/'experiments/biology_v2_section4'
sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway
from biology_expert.state import write,digest
from biology_expert.tools.repair_planner import bounded_patch
from biology_expert.tools.mechanism_validator import mechanism_validator
from biology_v2_pipeline import TransactionRenderer,sha,probe
for line in (R.parent/'.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v.strip().strip('"').strip("'")
agent=BiologyExpertAgent(E,ModelGateway(E/'logs/models'))
assert json.loads((E/'tests/test_results.json').read_text())['all_passed']
source=TransactionRenderer(V2/'groups/A2_mechanism_assets',R/'src/biology_runtime.py').state()
code=Path(source['code']).read_text();trace=json.loads((Path(source['version'])/'geometry_trace.json').read_text())
pack=json.loads((E/'knowledge/dna_replication/knowledge_pack.json').read_text())
context={'knowledge_pack':pack,'storyboard':json.loads((V2/'specs/section4_storyboard_v2.json').read_text())}
artifacts={'code':code,'trace':trace,'video':source['video'],'trace_ref':str(Path(source['version'])/'geometry_trace.json')}
review=agent.review('ANIMATION_CODE',artifacts,context)
write(E/'reviews/code/test_A_evidence_corrected.json',review)
assert any(i['issue_id']=='BIO-DIRECTION' for i in review['issues']),'No supported direction failure'
old_task=json.loads((E/'repair_tasks/test_B_task.json').read_text())
task=agent.plan_repair(review,{'input_hash':source['code_sha256']})
task['repair_id']=old_task['repair_id'];task['revision']=2;task['corrected_evidence_not_new_issue']=True
write(E/'repair_tasks/test_B_task_evidence_corrected.json',task)
outdir=E/'outputs'/task['repair_id'];d=outdir/'attempt_2_format_replay';d.mkdir(exist_ok=False)
raw=(outdir/'attempt_2/model_reply.txt').read_text()
candidate,scope=bounded_patch(code,raw);write(d/'scope_check.json',scope);(d/'candidate_code.py').write_text(candidate)
write(d/'provenance.json',{'original_model_call':'v3_05','original_generation_attempt':2,'new_generation_attempt':False,'new_deepseek_request':False,'adaptation':'Uniform dedent then AST-extract exact generated loop; preserve original exception and two-attempt count','source_response_sha256':sha(outdir/'attempt_2/model_reply.txt')})
tx=TransactionRenderer(outdir/'render',R/'src/biology_runtime.py',V2/'assets',(25,35));before=tx.state();gate={}
def science_gate(stage,newtrace,layout):
 current={'code':candidate,'trace':newtrace,'trace_ref':str(stage/'geometry_trace.json'),'video':str(stage/'media/videos/rendered_code/480p15/Section4Scene.mp4')}
 measured=agent._call('mechanism_validator',{'artifacts':current,'context':context},'Verify the already-generated repaired candidate','Use corrected evidence and actual newly rendered temporal geometry.')
 write(d/'measured_checks.json',measured);gate['measured']=measured
 target=next(c for c in measured['checks'] if c['check_id']=='lagging_gap_growth')
 if target['status']!='PASS':raise ValueError('Direction still not scientifically established')
 video=agent.verify_revision(task,current,context);gate['video_review']=video;write(d/'video_science_review.json',video)
 if video['decision']!='PASS':raise ValueError('Whole-section science gate not PASS: '+video['decision'])
 if video.get('targeted_gap_direction')!='PASS':raise ValueError('Video gap direction not confirmed')
result=tx.attempt(candidate,'scientific_attempt_2_format_replay',extra_validator=science_gate)
write(d/'transaction.json',result)
if not result['committed']:assert tx.state()==before,'Rollback failure'
stage=Path(result['after']['version']) if result['committed'] else tx.group/'attempts/scientific_attempt_2_format_replay'
mp4=stage/'media/videos/rendered_code/480p15/Section4Scene.mp4'
out={'repair_id':task['repair_id'],'generation_attempts':2,'format_replay_not_new_model_candidate':True,'accepted':result['committed'],'targeted_direction_fixed':next((c['status']=='PASS' for c in gate.get('measured',{}).get('checks',[]) if c['check_id']=='lagging_gap_growth'),False),'global_science_approved':result['committed'],'rollback_pair_preserved':tx.state()==before if not result['committed'] else None,'decision':'PASS' if result['committed'] else 'NEEDS_HUMAN_REVIEW','transaction':result,'science_review':gate.get('video_review'),'before':source,'candidate_video':str(mp4),'candidate_code':str(stage/'rendered_code.py'),'candidate_trace':str(stage/'geometry_trace.json'),'candidate_manifest':{'code_sha256':sha(stage/'rendered_code.py'),'video_sha256':sha(mp4),'duration_seconds':float(probe(mp4)['format']['duration']),'published_as_scientifically_approved':result['committed']}}
write(E/'test_B_revalidated_result.json',out)
write(stage/'scientific_candidate_manifest.json',out['candidate_manifest'])
agent._call('skill_manager',{'task':task,'result':{'targeted_direction_fixed':out['targeted_direction_fixed'],'scientific_commit':out['accepted'],'regression_tests':['real_indented_model_reply','actual_polarity_plus_growth_trace','non_target_AST_unchanged','full_science_rejection_retains_prior_pair'],'experiment_path':str(d)}},'Save candidate experience from the real repair','Candidate only; final science did not automatically approve a formal skill.')
print(json.dumps({'accepted':out['accepted'],'targeted_direction_fixed':out['targeted_direction_fixed'],'rollback_pair_preserved':out['rollback_pair_preserved'],'candidate_video':out['candidate_video'],'video_science_decision':out['science_review']['decision'] if out.get('science_review') else None},ensure_ascii=False),flush=True)
