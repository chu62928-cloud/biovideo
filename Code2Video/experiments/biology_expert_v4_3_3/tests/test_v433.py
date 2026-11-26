from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmark_run import *
import pytest

@pytest.mark.parametrize('n',range(10))
def test_valid_edit(n):
    base,t,p,expected,f,i=fixtures()[n]
    result=preflight(base,t,[dict(operation=ops[p['collection']],target_id=p['target'],fields={f:expected},support=[p['support']])],material()[1])
    assert result['errors']==[]
@pytest.mark.parametrize('error',['TARGET_OUTSIDE_TASK','STALE_MODEL','FORBIDDEN_FIELDS','MISSING_EVIDENCE','INVALID_EXTENSION'])
def test_reject(error):
    m,ev=material()
    _,t,p,*_=fixtures()[0]
    t['base_model_hash']=digest(m)
    cmd=dict(operation='update_entity',target_id=p['target'],fields={'scientific_name':'Test'},support=[p['support']])
    if error=='STALE_MODEL':t['base_model_hash']='stale'
    if error=='TARGET_OUTSIDE_TASK':t['primary_targets']=[]
    if error=='FORBIDDEN_FIELDS':cmd['fields']={'semantic_id':'new'}
    if error=='MISSING_EVIDENCE':cmd['support']=[]
    prev=digest(m)
    out=preflight(m,t,[cmd],ev,[{'target_id':'absent','reason':'scope'}] if error=='INVALID_EXTENSION' else [])
    assert error in {x['code'] for x in out['errors']}
    assert digest(m)==prev
@pytest.mark.parametrize('n',range(3))
def test_historical_replay(n):
    folder=U/'recovered_automatic/repairs'/('attempt_'+str(n))
    m=read(folder/'before.json');t=read(folder/'tasks.json');p=read(folder/'patch.json')
    targets=list({x for task in t for x in task['target_ids']})
    issue=dict(issue_id='replay',target_ids=targets)
    ev=material()[1];auth=compile_task(m,issue,ev,'original')
    commands=[dict(operation=ops[x['collection']],target_id=x.get('target_id'),fields=x.get('fields',{}),support=m['entities'][0]['support']) for x in p['operations']]
    out=preflight(m,auth,commands,ev)
    write(E/('replay_'+str(n)+'.json'),out)
    assert out['status']=='PREFLIGHT_REJECTED'
