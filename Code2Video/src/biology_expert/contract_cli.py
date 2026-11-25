"""Canonical offline contract audit entrypoint. Paid requests are not available here."""
from pathlib import Path
import argparse,json,sys,subprocess,hashlib
from .contracts import schema_validate,write,digest
from .agent import BiologyExpertAgent
from .contract_compiler import ScientificContractCompiler
from .temporal_validator import TemporalMechanismValidator,MechanismMutationTester
from .role_binder import ScientificRoleBinder
from .observation_adapter import RuntimeObservationAdapter,SemanticObservationAdapter,ObservationMutationTester,merged_coverage

class OfflineGateway:
 def request(self,*args,**kwargs):raise RuntimeError('PAID_REQUESTS_DISABLED: offline CLI')
def audit(contract,scene,trace,output,review=None,video=None,model=None,contract_review=None):
 schema_validate(contract)
 ids=[o['object_id'] for o in scene.get('objects',[])]
 if len(ids)!=len(set(ids)):raise ValueError('INVALID_SCENE: duplicate object_id')
 agent=BiologyExpertAgent(Path(output)/'workflow',OfflineGateway())
 agent.registry.register('scientific_role_binder',ScientificRoleBinder().bind)
 agent.registry.register('runtime_observation_adapter',RuntimeObservationAdapter().execute)
 agent.registry.register('semantic_observation_adapter',SemanticObservationAdapter().adapt)
 agent.registry.register('observation_mutation_tester',ObservationMutationTester().run)
 call=lambda tool,args,reason:agent._call(tool,args,'Offline contract-to-observation audit',reason)
 bindings=call('scientific_role_binder',{'contract':contract,'scene':scene,'trace':trace},'Match explicit identity/metadata before observing; preserve ambiguous roles.')
 execution=call('runtime_observation_adapter',{'contract':contract,'scene':scene,'trace':trace,'bindings':bindings},'Measure actual participant lifecycle and supported registered relations; never replace full science semantics with prerequisites.')
 semantic=[]
 if review:
  vh=hashlib.sha256(Path(video).read_bytes()).hexdigest() if video else None
  semantic=call('semantic_observation_adapter',{'contract':contract,'review':review,'video_sha256':vh,'model':model},'Replay only constraint-specific observations with intervals and matching hashes; overall PASS is insufficient.')
 goal=(contract_review or {}).get('semantic_review',{}).get('goal_coverage')
 coverage=merged_coverage(contract,execution,semantic,goal)
 mutation=call('observation_mutation_tester',{'contract':contract,'scene':scene,'trace':trace,'bindings':bindings,'baseline':execution},'Mutate copies of actual PASS participant-identity evidence, preserving baseline and unrelated appearance controls.')
 plan=ScientificContractCompiler().compile(contract,contract_review or {},scene,bindings,trace)
 mechanism=TemporalMechanismValidator().execute(plan,contract,scene,trace)
 mechanism_mutations=MechanismMutationTester().run(plan,contract,scene,trace,mechanism)
 write(Path(output)/'execution_plan.json',plan)
 write(Path(output)/'mechanism_checks.json',mechanism)
 write(Path(output)/'mechanism_mutations.json',mechanism_mutations)
 result={'roles_bound':sum(r['status']=='BOUND' and r['kind']=='entity' for r in bindings['bindings']),'processes_bound':sum(r['status']=='BOUND' and r['kind']=='process' for r in bindings['bindings']),'runtime_checks_measured':sum(s['status'] in ['PASS','FAIL'] for c in execution['checks'] for s in c['subchecks']),'runtime_full_constraints_verified':sum(c['full_constraint_verified'] for c in execution['checks']),'runtime_parent_constraints_partially_verified':sum(c['status']=='PARTIALLY_VERIFIED' for c in execution['checks']),'vlm_checks_supported':sum(s['status'] in ['PASS','FAIL'] for s in semantic),'scientific_mutations_valid':mutation['valid_scientific_mutations'],'scientific_mutations_detected':mutation['detected'],'mutation_scope':'required scientific participant identity continuity, not full chemical mechanism','coverage_status':coverage['decision'],'contract_review':(contract_review or {}).get('decision','NOT_PROVIDED'),'final_gate':'REVIEW_INCOMPLETE','model_calls':0}
 result.update(constraints_compiled=sum(r['compile_status']=='COMPILED' for r in plan['compiled_constraints']),full_mechanism_checks_pass=sum(c['full_constraint_verified'] and c['status']=='PASS' for c in mechanism['checks']),full_mechanism_checks_fail=sum(c['full_constraint_verified'] and c['status']=='FAIL' for c in mechanism['checks']),distinct_valid_mutation_types=mechanism_mutations['distinct_valid_mutation_types'],valid_mechanism_mutations=mechanism_mutations['valid_mutations'])
 for name,data in [('bindings',bindings),('checks',execution),('semantic_observations',semantic),('coverage',coverage),('mutations',mutation),('results',result)]:write(Path(output)/(name+'.json'),data)
 return result

def main(argv=None):
 p=argparse.ArgumentParser(description='V4.2.2 canonical offline scientific contract audit; no legacy fallback or paid calls')
 sub=p.add_subparsers(dest='command',required=True);a=sub.add_parser('audit')
 for name in ['contract','scene','output']:a.add_argument('--'+name,required=True)
 for name in ['trace','review','video','model','contract-review']:a.add_argument('--'+name)
 args=p.parse_args(argv)
 try:
  load=lambda x:json.loads(Path(x).read_text(encoding='utf-8')) if x else {}
  version=subprocess.run(['git','rev-parse','HEAD'],cwd=Path(__file__).parent,capture_output=True,text=True)
  provenance={'module_path':str(Path(__file__).resolve()),'git_commit':version.stdout.strip() if version.returncode==0 else None,'python':sys.executable,'offline':True,'paid_model_calls':0,'legacy_topic_checker_loaded':False}
  print(json.dumps(provenance,ensure_ascii=False),flush=True)
  result=audit(load(args.contract),load(args.scene),load(args.trace),args.output,load(args.review),args.video,args.model,load(args.contract_review))
  write(Path(args.output)/'loaded_version.json',provenance);print(json.dumps(result,ensure_ascii=False));return 0
 except FileNotFoundError as ex:print(json.dumps({'error_code':'INPUT_NOT_FOUND','message':str(ex)}),file=sys.stderr);return 2
 except Exception as ex:print(json.dumps({'error_code':'VERSION_CONFLICT' if 'VERSION_CONFLICT' in str(ex) else 'INVALID_INPUT_OR_EXECUTION','type':type(ex).__name__,'message':str(ex)}),file=sys.stderr);return 3
if __name__=='__main__':sys.exit(main())
