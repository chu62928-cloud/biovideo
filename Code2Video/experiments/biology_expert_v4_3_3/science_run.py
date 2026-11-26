from common import *
from biology_expert.model_repair import ScientificModelRepairTransaction
from biology_expert.model_reliability import ScientificCausalGraphValidator
from biology_expert.typed_science_builder import TypedScienceModelBuilder,TypedScienceModelReviewer
from biology_expert.contract_builder import ScientificContractBuilder,ScientificEvidenceRetriever
def repair(g,task,model,ev,issue,folder):
    issue=dict(issue,issue_id='R001',target_ids=[issue['target_id']])
    auth=compile_task(model,issue,ev,task['user_request'])
    write(folder/'task.json',auth)
    relevant=[r for k in ['entities','relations','processes','states'] for r in model.get(k,[]) if (r.get('semantic_id') or r.get('process_semantic_id') or r.get('state_id')) in auth['primary_targets']+auth['dependency_targets']]
    quotes=[p for e in ev if e['evidence_id'] in issue['evidence_ids'] for p in e['passages'][:12]]
    payload=dict(task=task,issue=issue,authorization=auth,records=relevant,passages=quotes)
    feedback=None
    for n in range(2):
        prompt='Return JSON {commands:[{operation,target_id,fields,support:[{quote,location,evidence_id}]}],extensions:[{target_id,reason}]}. For add_entity use new stable target_id, for_target authorized ID, fields complete entity including semantic_id,scientific_name,entity_type,evidence_ids,support. For bind_participant use role,entity_ref. Update dependencies when endpoint changes. Exact body evidence per command. No self approval. '+json.dumps(dict(payload,feedback=feedback))
        out=parse_json(g.request('deepseek','harness_scientific_repair',prompt))
        result=preflight(model,auth,out['commands'],ev,out.get('extensions',[]))
        write(folder/('preflight_'+str(n)+'.json'),dict(proposal=out,result=result))
        if result['errors']:
            feedback=result['errors']
            continue
        tx=ScientificModelRepairTransaction(g,folder)
        return tx.run(task,model,[issue],ev,n,prepared=(result['tasks'],result['patch']))
    return dict(status='NEEDS_HUMAN_REVIEW',errors=feedback)
def main(group):
    out=E/group;out.mkdir(exist_ok=True);g=gateway()
    if group=='R2':
        model,ev=material();task=read(U/'task.json')
        issue=next(x for x in read(U/'recovered_review.json')['issues'] if x['target_id']=='REL_CA_TO_TROPONIN_TROPOMYOSIN')
        write(out/'evidence_gap.json',dict(issue=issue,source='original independent review and prior targeted retrieval',evidence_ids=issue['evidence_ids']))
        return repair(g,task,model,ev,issue,out)
    task=read(out/'assignment.json')
    retriever=ScientificEvidenceRetriever(out/'research',limit=15,visual_limit=0)
    plan=ScientificContractBuilder(g,out,retriever).plan(task)
    write(out/'discovery.json',plan)
    retrieval=retriever.retrieve(task,plan);write(out/'retrieval.json',retrieval)
    if not retrieval['evidence']:raise ValueError('NO_READABLE_EVIDENCE')
    model=TypedScienceModelBuilder(g).build_staged(task,retrieval,out/'stages')
    write(out/'model.json',model)
    causal=ScientificCausalGraphValidator().validate(model);write(out/'causal.json',causal)
    rev=TypedScienceModelReviewer(g).review(model,retrieval['evidence'],task);write(out/'review.json',rev)
    if rev['decision']=='PASS' and causal['status']=='PASS':return dict(status='INITIAL_APPROVED')
    if rev.get('issues') and rev['issues'][0].get('target_id'):
        return repair(g,task,model,retrieval['evidence'],rev['issues'][0],out)
    return dict(status='NEEDS_HUMAN_REVIEW')
if __name__=='__main__':
    g=sys.argv[1]
    try:out=main(g)
    except Exception as exc:
        import traceback
        out=dict(status='ERROR',error=str(exc)[:1600],traceback=traceback.format_exc()[-4000:])
    write(E/g/'result.json',out)
