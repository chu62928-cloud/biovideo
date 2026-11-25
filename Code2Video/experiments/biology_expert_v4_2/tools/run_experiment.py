from pathlib import Path
import sys,json,os,copy,traceback
R=Path('/autodl-tmp/code2biovideo/Code2Video-v4.2-workspace');E=R/'experiments/biology_expert_v4_2';sys.path.insert(0,str(R/'src'))
from biology_expert.agent import BiologyExpertAgent
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import *
for line in (R.parent/'.env').read_text().splitlines():
 if line and not line.startswith('#') and '=' in line:
  k,v=line.split('=',1);os.environ[k]=v
gateway=ModelGateway(E/'logs',{'deepseek':12,'qwen':4},qwen_profile={'max_completion_tokens':12000,'thinking_budget':4096})
override=E/'logs/provider_override.json'
if override.exists():os.environ['QWEN_MODEL']=json.loads(override.read_text())['qwen_model']
agent=BiologyExpertAgent(E/'agent',gateway);tools=agent.enable_contract_workflow(E)
TASKS=[{'topic_id':'dna_replication','topic':'Eukaryotic DNA replication at one local fork','user_request':'Review a grades10-12 Section4 video showing local fork opening, RNA priming, leading/lagging extension, one local primer replacement and nick sealing. Origins/licensing are covered in Section2; no whole-genome completion claim.','audience':'grades_10_12'}, {'topic_id':'mitosis','topic':'Eukaryotic mitosis metaphase to anaphase','user_request':'Review a grades10-12 video of one duplicated chromosome aligning with opposite-pole kinetochore attachment, then cohesion release and existing sister separation. No replication, homolog pairing or cytokinesis in scope.','audience':'grades_10_12'}, {'topic_id':'protein_translation','topic':'Protein translation initiation and elongation','user_request':'Create and review an educational storyboard explaining how a ribosome reads mRNA, tRNA recognizes codons, and a polypeptide extends step by step; identify organism-specific initiation simplifications.','audience':'grades_10_12'}]

def archive():
 (E/'logs/api_calls.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in gateway.rows))
 p=E/'agent/state/events.jsonl'
 if p.exists():__import__('shutil').copy2(p,E/'logs/agent_tool_calls.jsonl')

def run(index):
 task=TASKS[index];folder=E/'contracts'/task['topic_id']
 if (folder/'build_result.json').exists():result=json.loads((folder/'build_result.json').read_text())
 else:
  result=agent.build_contract(task);write(folder/'build_result.json',result);archive()
 if result.get('contract') is None:return
 contract=result['contract'];review=result['review'];evidence=result['retrieval']['evidence']
 if index<2:
  label=['B4_expert_repair','M1_mitosis'][index];base=R/'experiments/scientific_scene_v4_1/groups'/label
  scene=json.loads((base/'scene_graph.json').read_text());trace=json.loads((base/'geometry_trace.json').read_text());video=str(base/'video.mp4')
 else:scene=None;trace=None;video=None
 prompt='''Act as a contract-to-observation binding and independent artifact review tool. Use only the supplied dynamic contract, current task, source excerpts and actual scene/trace inventory. Return JSON {"bindings":{"semantic role":"exact object/event ID or array of IDs"},"ir_review":{"decision":"PASS|REVISE|REVIEW_INCOMPLETE|NEEDS_HUMAN_REVIEW","issues":[],"contract_goal_coverage":{"decision":"PASS|REVIEW_INCOMPLETE","missing_goals":[]}},"scene":null,"normal_storyboard":null,"incorrect_storyboard":null,"storyboard_reviews":[],"reference_events":[]}. For an existing scene, bind roles to ACTUAL IDs; unresolved roles remain absent, never guess. Binding a molecular activity to a label is not proof it was observed. For a NEW topic with no supplied scene: generate a compact new abstract Scene Graph with objects:[{object_id,scientific_identity:{name,kind,origin_id},scientific_properties,anchors,visual_representation}], relations:[{source,target,type}], events:[{event_id,role,description,state_before,state_after}]. No prewritten topic blueprint exists. Also create one normal storyboard grounded in source facts, and a wrong storyboard by changing exactly one source-supported scientific relationship; list the altered claim, exact quote and expected violation. Review each separately with evidence. New scene is an abstract planned test, NOT a rendered observation, so do not invent runtime frames/positions/identity traces. Return reference_events extracted from actual source passages, with evidence IDs and exact supporting quote, not from generated scene. This single request must not be treated as independent test truth; deterministic mutations and source facts are separate evaluation evidence.'''
 sample={'task':task,'contract':contract,'source_support':[{'evidence_id':e['evidence_id'],'title':e['title'],'passages':[p for p in e['passages'] if any(s['quote'] in p['text'] and s['evidence_id']==e['evidence_id'] for c in contract['constraints'] for s in c['support'])]} for e in evidence],'existing_scene':scene,'runtime_events':trace.get('events',[]) if trace else None,'actual_inventory':trace.get('object_metadata',{}) if trace else None}
 cached=E/'reviews/ir_reviews'/(task['topic_id']+'.json')
 mapped=json.loads(cached.read_text()) if cached.exists() else parse_json(gateway.request('deepseek','contract_binding_and_artifact_review',prompt+json.dumps(sample,ensure_ascii=False)))
 write(E/'reviews/ir_reviews'/(task['topic_id']+'.json'),mapped)
 if scene is None:scene=mapped.get('scene') or {'objects':[],'events':[],'relations':[]};trace={};write(folder/'generated_scene_graph.json',scene);write(folder/'storyboard_tests.json',{'normal':mapped.get('normal_storyboard'),'incorrect':mapped.get('incorrect_storyboard'),'reviews':mapped.get('storyboard_reviews'),'generation_origin':'REAL_MODEL_NEW_TOPIC','limitation':'Same request proposed and reviewed scripts; independent truth relies on actual quoted sources and separate generic mutations, not score alone'})
 execution=ConstraintExecutor().execute(contract,scene,trace,mapped.get('bindings',{}));write(folder/'execution.json',execution)
 coverage=tools.call('coverage_auditor',{'contract':contract,'execution':execution,'goal_review':review['semantic_review'].get('goal_coverage')},'Some declared scientific requirements may have no measured realization; audit frozen denominator and user-goal completeness.')
 write(E/'coverage'/(['dna_coverage.json','mitosis_coverage.json','translation_coverage.json'][index]),coverage)
 mutation=tools.call('mutation_tester',{'contract':contract,'scene':scene,'trace':trace,'bindings':mapped.get('bindings',{})},'Test the proposed standards with generic isolated mutations and irrelevant appearance negative control; unmeasurable baseline is not successful testing.')
 write(E/'mutation_tests'/(task['topic_id']+'.json'),mutation)
 semantic=mapped['ir_review'];conflicts=tools.call('scientific_conflict_adjudicator',{'contract':contract,'deterministic':execution,'semantic':semantic},'Conflicting measured subset and semantic claims require evidence arbitration; never force approval.')
 write(E/'reviews/conflict_adjudications'/(task['topic_id']+'.json'),conflicts)
 video_review=None
 if video and any(c['provider']=='qwen' and c['status']=='error' and c.get('http_status')==403 and c.get('requested_model')==os.environ['QWEN_MODEL'] for c in gateway.rows):
  video_review={'decision':'ERROR','error':'AccessDenied.Unpurchased','reason':'Confirmed model access 403; no retry or fake review','checks':[]};write(E/'reviews/video_reviews'/(task['topic_id']+'.json'),video_review)
 elif video:
  video_review=tools.call('reference_video_reviewer',{'artifacts':{'video':video,'trace':trace,'scene_graph':scene,'execution':execution,'reference_events':review['semantic_review'].get('reference_events',[])},'contract':contract,'evidence':[{'evidence_id':e['evidence_id'],'title':e['title'],'url':e['url'],'passages':[p for p in e['passages'] if any(s['quote'] in p['text'] for c in contract['constraints'] for s in c['support'] if s['evidence_id']==e['evidence_id'])]} for e in evidence],'visual_references':result['visual']},'Actual video meaning cannot be inferred from registered metadata; compare complete MP4 to retrieved event/state evidence and record missing video references.')
  write(E/'reviews/video_reviews'/(task['topic_id']+'.json'),video_review)
 final='REVISE' if execution['decision']=='REVISE' or semantic['decision']=='REVISE' or (video_review and video_review['decision']=='REVISE') else 'REVIEW_INCOMPLETE'
 if coverage['decision']=='PASS' and result.get('freeze') and not conflicts and execution['decision']=='PASS' and semantic['decision']=='PASS' and video_review and video_review['decision']=='PASS':final='PASS'
 write(folder/'final_gate.json',{'topic_id':task['topic_id'],'decision':final,'contract_review':review['decision'],'frozen':bool(result.get('freeze')),'coverage':coverage['decision'],'deterministic':execution['decision'],'ir_semantic':semantic['decision'],'video':video_review['decision'] if video_review else 'NOT_MEASURED','contract_hash':digest(contract),'legacy_rules_used_for_build':False,'legacy_scene_used_only_after_contract':index<2,'new_topic_rendered':False if index==2 else None})
 archive()

if __name__=='__main__':
 assert json.loads((E/'tests/test_results.json').read_text())['all_passed']
 try:run(int(sys.argv[1]))
 except Exception as ex:
  with (E/'logs/errors.jsonl').open('a') as f:f.write(json.dumps({'topic_index':sys.argv[1],'error_type':type(ex).__name__,'error':str(ex)})+'\n')
  traceback.print_exc();raise
 finally:archive()
