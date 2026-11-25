from pathlib import Path
import sys,json,time,shutil
E=Path('/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4')
sys.path.insert(0,str(E/'tools'))
import run_biology_v2 as run
assert json.loads((E/'pipeline_tests.json').read_text())['all_passed']
started=time.monotonic()
try:
    a1=run.TransactionRenderer(E/'groups/A1_mechanism',run.RUNTIME,duration_range=(25,35))
    result=a1.attempt((a1.group/'candidate_2.py').read_text(),'checker_fixed_replay_candidate_2',extra_validator=run.validate)
    (a1.group/'checker_recovery.json').write_text(json.dumps({'reason':'Binding monitor and helper corrected; original model candidate unchanged','new_api_calls':0,'result':result},indent=2))
    print('A1_REPLAY',result['committed'],result.get('error'),flush=True)
    a2=run.TransactionRenderer(E/'groups/A2_mechanism_assets',run.RUNTIME,E/'assets',duration_range=(25,35))
    code=(a2.group/'candidate_2.py').read_text()
    result=a2.attempt(code,'checker_fixed_replay_candidate_2',extra_validator=run.validate)
    print('A2_REPLAY',result['committed'],result.get('error'),flush=True)
    if not result['committed']:
        log=a2.group/'attempts/checker_fixed_replay_candidate_2/stderr.log'
        prompt=run.initial_prompt(True)+'\nReturn a corrected COMPLETE module. Do not change the five events. The binding checker is now fixed; latest actual error:\n'+result.get('error','')+'\n'+(log.read_text()[-8000:] if log.exists() else '')+'\nMODEL CODE:\n'+code
        code=run.clean_code(run.model_call('deepseek','A2:automatic_repair_after_checker_fix',prompt))
        (a2.group/'candidate_3.py').write_text(code)
        result=a2.attempt(code,'coder_attempt_3_after_checker_fix',extra_validator=run.validate)
        print('A2_REPAIR',result['committed'],result.get('error'),flush=True)
    (a2.group/'checker_recovery.json').write_text(json.dumps({'reason':'Replay interrupted saved candidate after monitor correction, no manual animation edits','result':result},indent=2))
    if a2.state():run.critic_experiment(a2.state())
    else:(E/'groups/A3_mechanism_assets_critic/status.json').write_text(json.dumps({'success':False,'skipped':'A2 failed validation'},indent=2))
except Exception as exc:
    (E/'logs/continuation_error.json').write_text(json.dumps({'type':type(exc).__name__,'error':str(exc)},indent=2))
    import traceback;traceback.print_exc()
finally:
    (E/'continuation_summary.json').write_text(json.dumps({'elapsed_seconds':round(time.monotonic()-started,3),'api_calls':run.ledger(),'limits':run.LIMITS},indent=2))
    print('CONTINUATION_FINISHED',len(run.ledger()),flush=True)
