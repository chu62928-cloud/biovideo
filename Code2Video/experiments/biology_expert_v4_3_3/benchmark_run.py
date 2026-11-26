from common import *
from copy import deepcopy
from biology_expert.model_repair import apply_model_patch
from biology_expert.typed_science_builder import validate_typed_model
import argparse
ops={'entities':'update_entity','relations':'update_relation','processes':'update_process'}
def fixtures():
    model,ev=material()
    rows=[]
    for n,(group,field,index) in enumerate([('entities','scientific_name',i) for i in range(4)]+[('relations','source_entity',i) for i in range(4)]+[('processes','input_roles',i) for i in range(2)]+[('entities','semantic_id',0),('entities','scientific_name',1)]):
        base=deepcopy(model)
        row=base[group][index]
        key=row.get('semantic_id',row.get('process_semantic_id'))
        original=row[field]
        if n<10:row[field]=[] if isinstance(original,list) else 'CORRUPTED'
        target=key if n!=11 else base['entities'][0]['semantic_id']
        issue=dict(issue_id='B'+str(n),target_ids=[target],evidence_ids=row['evidence_ids'])
        task=compile_task(base,issue,ev,'Preserve mechanism and IDs.')
        prompt=dict(id=n,instruction=('Infer and restore the corrupted '+field+' from evidence and context.' if n<10 else 'Rename this immutable identifier.' if n==10 else 'Rename the indicated unrelated entity without scope expansion.'),target=key,record=row,authorized=target,linked_entities=[(x['semantic_id'],x['scientific_name']) for x in base['entities']],support=row['support'][0],collection=group)
        rows.append((base,task,prompt,original,field,index))
    return rows
def evaluate(group,save=True):
    model,ev=material()
    rows=fixtures()
    data=[x[2] for x in rows]
    fmt='Each case: id, reject:true for impermissible; else operation (update_entity,update_relation,update_process), target_id, fields (only modified fields). The harness attaches the supplied citation to the operation.' if group=='G1' else 'Each case: id, reject:true for impermissible; else patch:{operations:[{op:"update",collection,target_id,fields}]}.'
    g=gateway()
    responses=[]
    for start in (0,6):
        out=parse_json(g.request('deepseek','harness_benchmark_'+group,'Return JSON {cases:[...]}. '+fmt+' No explanations. '+json.dumps(data[start:start+6])))
        responses+=out['cases']
    results=[]
    for base,task,prompt,expected,field,index in rows:
        n=prompt['id']; ans=next((x for x in responses if x.get('id')==n),{})
        reason=None;candidate=None
        try:
            if ans.get('reject'):raise ValueError('model declined')
            if group=='G1':
                result=preflight(base,task,[dict(ans,support=[prompt['support']])],ev)
                if result['errors']:raise ValueError(str(result['errors']))
                candidate=result['candidate']
            else:candidate,_=apply_model_patch(base,ans['patch'],[dict(issue_id=task['issue_id'],target_ids=task['primary_targets'],repair_goal='')],ev)
        except Exception as ex:reason=str(ex)
        value=candidate[prompt['collection']][index][field] if candidate else None
        ok=(value==expected) if n<10 else candidate is None
        results.append(dict(id=n,source='historical model with controlled corruption',expected=expected if n<10 else 'REJECT',observed=value,accepted=candidate is not None,exact_match=ok,response=ans,reason=reason))
    write(E/(group+'.json'),results)
if __name__=='__main__':evaluate(sys.argv[1])
