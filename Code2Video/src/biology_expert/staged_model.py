"""Build and validate four bounded outputs, caching only valid stages."""
import json
from copy import deepcopy
from pathlib import Path
from jsonschema import Draft202012Validator
from .contracts import digest, write
from .typed_science_builder import validate_typed_model
from .retrieval_quality import exact_support


def assemble(gateway, task, retrieval, cache):
    schema = json.loads((Path(__file__).parent/'schemas/typed_science_model.schema.json').read_text())
    props = schema['properties']
    proc = props['processes']['items']
    def subset(fields):
        return {'type':'object','required':list(fields),'properties':fields,'additionalProperties':False}
    def rows(fields):
        return {'type':'array','minItems':1,'items':subset(fields)}
    stages = [
        subset({k:props[k] for k in ('model_id','scope','entities')}),
        subset({'relations':props['relations'],'bindings':rows({k:proc['properties'][k] for k in ('process_semantic_id','participants','input_roles','output_roles')})}),
        subset({'states':props['states'],'clip_start':props['clip_start'],'details':rows({k:v for k,v in proc['properties'].items() if k not in ('participants','input_roles','output_roles','observables') and k in set(proc['required'])|{'precondition_state_refs','effect_state_refs','terminates_state_refs'}})}),
        subset({'constraints':rows({k:proc['properties'][k] for k in ('process_semantic_id','observables')}),'unresolved_questions':props['unresolved_questions']})]
    ev = retrieval['evidence']
    sources = [{'id':e['evidence_id'],'passages':e['passages'][:10]} for e in ev]
    state = {'schema_version':'1.1'}
    def validate(index, data):
        Draft202012Validator(stages[index]).validate(data)
        result = deepcopy(state)
        if index==0:
            result.update(data)
        elif index==1:
            result.update(relations=data['relations'],processes=data['bindings'])
        elif index==2:
            result.update(states=data['states'],clip_start=data['clip_start'])
        if index>=2:
            key='details' if index==2 else 'constraints'
            ids=[x['process_semantic_id'] for x in data[key]]
            if len(set(ids))!=len(ids) or set(ids)!={p['process_semantic_id'] for p in result['processes']}:
                raise ValueError('stage must cover each frozen process exactly once')
            updates={x['process_semantic_id']:x for x in data[key]}
            for p in result['processes']:
                p.update(updates[p['process_semantic_id']])
        if index==3:
            result['unresolved_questions']=data['unresolved_questions']
            validate_typed_model(result,ev)
        entities={x['semantic_id'] for x in result['entities']}
        if len(entities)!=len(result['entities']):
            raise ValueError('duplicate entity')
        for r in result.get('relations',[]):
            if {r['source_entity'],r['target_entity']}-entities:
                raise ValueError('unknown relation endpoint '+r['semantic_id'])
        for p in result.get('processes',[]):
            bindings=p['participants']
            roles={r['role'] for r in bindings}
            if len(roles)!=len(bindings) or set(p['input_roles']+p['output_roles'])-roles or {r['entity_ref'] for r in bindings}-entities:
                raise ValueError('undefined or duplicate role in '+p['process_semantic_id'])
        for row in result['entities']+result.get('relations',[])+result.get('states',[])+[p for p in result.get('processes',[]) if 'support' in p]:
            if not exact_support(row['support'],ev):
                raise ValueError('unsupported quote for '+str(row.get('semantic_id',row.get('state_id',row.get('process_semantic_id')))))
        return result
    for i,contract in enumerate(stages):
        prompt={'instruction':'Build only this stage of a compact scientific teaching model, 1-3 processes. Return one JSON object matching stage_schema. Use exact quotes and paragraph locations. Use existing IDs and participant roles. Preserve the full educational goal. No code or approval claims.','task':task,'stage':i+1,'stage_schema':contract,'frozen':state,'evidence':sources}
        path=Path(cache)/(digest(prompt)+'.json')
        if path.exists():
            state=validate(i,json.loads(path.read_text()))
            continue
        for attempt in range(2):
            try:
                raw=gateway.request('deepseek','staged_model_'+str(i+1),json.dumps(prompt,ensure_ascii=False))
                data=json.loads(raw)
                result=validate(i,data)
            except (ValueError, __import__('jsonschema').ValidationError) as exc:
                if attempt: raise
                prompt['field_diagnostic']=str(exc)[:1400]
                continue
            write(path,data)
            state=result
            break
    return state
