"""Local, evidence-grounded typed model repair transaction using existing reviewer."""
from pathlib import Path
import copy,json
from .contracts import digest,write
from .providers import parse_json
from .typed_science_builder import validate_typed_model,TypedScienceModelReviewer
from .model_reliability import ScientificCausalGraphValidator
from .tools.repair_planner import plan_model_repairs

ALLOWED_FIELDS={'entities':{'scientific_name','entity_type','support','evidence_ids','states','cardinality'},'relations':{'relation_type','definition','source_entity','target_entity','support','evidence_ids'},'processes':{'action_category','scientific_name','participants','input_roles','output_roles','preconditions','effects','temporal_scope','observables','support','evidence_ids','exceptions','precondition_state_refs','effect_state_refs','terminates_state_refs'}}

def apply_model_patch(before,patch,tasks,evidence):
    after=copy.deepcopy(before);changed=[];target_ids={x for task in tasks for x in task['target_ids']};allowed_global={'schema_version','states','clip_start'}
    for operation in patch.get('operations',[]):
        collection=operation['collection'];target=operation.get('target_id');fields=operation.get('fields',{})
        if collection not in ALLOWED_FIELDS:raise ValueError('Unrelated patch collection')
        idkey='process_semantic_id' if collection=='processes' else 'semantic_id';items=after[collection]
        if operation['op']=='update':
            if target not in target_ids:raise ValueError('Patch target outside repair task')
            if not set(fields)<=ALLOWED_FIELDS[collection]:raise ValueError('Patch touches forbidden field')
            item=next((x for x in items if x[idkey]==target),None)
            if item is None:raise ValueError('Unknown patch target')
            if collection=='processes' and 'observables' in fields:
                oldids={o['constraint_id'] for o in item['observables']};newids={o['constraint_id'] for o in fields['observables']}
                if not oldids<=newids:raise ValueError('Deleting failed constraints forbidden')
            for k,v in fields.items():
                if item.get(k)!=v:changed.append(collection+'/'+target+'/'+k)
                item[k]=v
        elif operation['op']=='add':
            item=operation['item']
            if any(x[idkey]==item[idkey] for x in items):raise ValueError('Duplicate added ID')
            if operation.get('justifies_issue_id') not in {t['issue_id'] for t in tasks}:raise ValueError('Added item lacks issue justification')
            items.append(item);changed.append(collection+'/'+item[idkey])
        else:raise ValueError('Only local update/add operations allowed')
    scope_patch=patch.get('scope_patch')
    if scope_patch:
        from .retrieval_quality import exact_support
        scoped_tasks=[t for t in tasks if 'scope' in t['target_ids']]
        if not scoped_tasks:raise ValueError('Scope patch lacks explicitly targeted repair task')
        if scope_patch.get('issue_id') not in {t['issue_id'] for t in scoped_tasks}:raise ValueError('Scope patch issue not authorized')
        fields=scope_patch.get('fields',{})
        if not fields or not set(fields)<={'included_processes','excluded_processes','simplifications'}:raise ValueError('Scope patch may not change topic, audience or organism')
        if not exact_support(scope_patch.get('support',[]),evidence):raise ValueError('Scope patch requires exact original body evidence')
        original_scope=before['scope']
        if 'included_processes' in fields and not set(original_scope['included_processes'])<=set(fields['included_processes']):raise ValueError('Cannot remove original included teaching processes')
        if 'excluded_processes' in fields and not set(fields['excluded_processes'])<=set(original_scope['excluded_processes']):raise ValueError('Cannot add new exclusions to evade original task')
        for field,value in fields.items():
            if not isinstance(value,list) or any(not isinstance(x,str) for x in value):raise ValueError('Scope lists require strings')
            if after['scope'].get(field)!=value:changed.append('scope/'+field)
            after['scope'][field]=value
    for k,v in patch.get('state_upgrade',{}).items():
        if k not in allowed_global:raise ValueError('Scope change not allowed in state upgrade')
        if after.get(k)!=v:changed.append(k)
        after[k]=v
    if not changed:raise ValueError('REPAIR_NOT_EFFECTIVE')
    if all(path.endswith(('/support','/evidence_ids','/scientific_name','/definition')) for path in changed) and any('precondition' in str(t['repair_goal']).lower() or 'state' in str(t['repair_goal']).lower() or 'role' in str(t['repair_goal']).lower() for t in tasks):raise ValueError('Text-only change cannot resolve structural issue')
    validate_typed_model(after,evidence)
    return after,changed

class ScientificModelRepairTransaction:
    def __init__(self,gateway,root):self.gateway=gateway;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def propose(self,task,model,issues,evidence,feedback=None):
        tasks=plan_model_repairs(issues,model)
        # State schema migration is explicit model data, not inferred in validator.
        if not tasks:raise ValueError('No actionable issue')
        prompt='Optional scope_patch:{issue_id,fields:{included_processes,excluded_processes,simplifications},support:[{evidence_id,location,quote}]} is allowed ONLY when a repair task explicitly targets scope. It may remove an obsolete exclusion, add included processes, or correct simplification text, but cannot remove original included processes, add exclusions, or change original user task/audience/organism. Exact source body support and independent review still required. Generate LOCAL scientific model JSON patch, not a complete model. Return {operations:[{op:update,collection:entities|relations|processes,target_id,fields:{...}} or {op:add,collection,item:{complete item},justifies_issue_id}],state_upgrade:{schema_version:1.1,clip_start:{stage,existing_entity_refs,omitted_processes:[]},states:[...]},issue_resolution:[{issue_id,changed_target_ids,reason,evidence_ids}]}. Preserve every existing process_semantic_id and constraint_id. Do not delete constraints, change original task scope, rename identifiers or omit required mechanisms. Only modify specified target IDs; add necessary evidence-supported entities/processes/relations with issue justification. Scientific identity, actors, intermediate states and causal dependence require actual support. Copy short EXACT original quote and paragraph location incl Greek letters. State records have state_id,subject_ref,property,value,state_kind(INITIAL_CONDITION|PRODUCED_STATE|REQUIRED_PRECONDITION|MAINTAINED_STATE|TERMINATED_STATE|OUT_OF_SCOPE|UNKNOWN),scope,producer_process_id,required_by_process_ids,evidence_ids,support. Use stable subject/property/value state slots, precondition_state_refs/effect_state_refs on every process. Required preconditions must be initial or produced, never silently seeded. Preconditions/effects legacy text may remain for compatibility but must not contradict typed references. state_kind INITIAL_CONDITION only for biologically supported pre-clip conditions. Describe intentional omissions only if not required by user. Each original requirement/observable remains subject to independent review. Only local fields of affected processes, state migration may affect all processes refs; explain migration in issue_resolution. Each attempt is against the supplied ORIGINAL model, not against the last failed candidate. Feedback patches were rolled back: an object added in failed patch does NOT exist and must be re-added, never update it. The provided allowed fields are exact; do not include semantic_id in update fields. Compact output below5500tokens. No scientific approval self-assertion.'
        schema=json.loads((Path(__file__).parent/'schemas/typed_science_model.schema.json').read_text())
        import re
        tokens=set(re.findall(r'[a-z]+',(task['user_request']+json.dumps(issues)).lower()));sources=[]
        for e in evidence:
            passages=sorted(e['passages'],key=lambda p:-len(tokens&set(re.findall(r'[a-z]+',p['text'].lower()))))[:10]
            sources.append({k:e.get(k) for k in ['evidence_id','url','title','evidence_level']}|{'passages':passages})
        patch=parse_json(self.gateway.request('deepseek','local_scientific_model_patch',prompt+json.dumps({'task':task,'model':model,'repair_tasks':tasks,'sources':sources,'feedback':feedback,'schema':schema,'allowed_fields':{k:sorted(v) for k,v in ALLOWED_FIELDS.items()}},ensure_ascii=False)))
        return tasks,patch
    def run(self,task,model,issues,evidence,attempt=0,feedback=None,prepared=None):
        folder=self.root/('attempt_'+str(attempt));folder.mkdir(exist_ok=True);write(folder/'before.json',model);before_hash=digest(model)
        if prepared is not None:
            tasks,patch=prepared;write(folder/'tasks.json',tasks);write(folder/'patch.json',patch)
        elif (folder/'patch.json').exists():tasks=json.loads((folder/'tasks.json').read_text());patch=json.loads((folder/'patch.json').read_text())
        else:tasks,patch=self.propose(task,model,issues,evidence,feedback);write(folder/'tasks.json',tasks);write(folder/'patch.json',patch)
        record={'before_hash':before_hash,'repair_tasks':tasks,'patch':patch,'accepted':False,'status':'CANDIDATE_CREATED','independent_review':'NOT_EXECUTED'}
        try:
            candidate,fields=apply_model_patch(model,patch,tasks,evidence);write(folder/'candidate.json',candidate);record.update(after_hash=digest(candidate),changed_fields=fields)
            causal=ScientificCausalGraphValidator().validate(candidate);write(folder/'causal.json',causal);record['causal_status']=causal['status']
            reviewfile=folder/'review.json'
            if reviewfile.exists() and prepared is None:review=json.loads(reviewfile.read_text())
            else:
                review_task=task if prepared is None else dict(task,original_issues=issues,original_model=model,actual_changes=patch)
                review=TypedScienceModelReviewer(self.gateway).review(candidate,evidence,review_task);write(reviewfile,review)
            record.update(independent_review=review['decision'],review=review)
            # Every targeted gap must be explicitly independently resolved; global PASS required.
            if review['decision']=='PASS' and causal['status']=='PASS':write(self.root/'committed.json',{'model':candidate,'review':review,'model_hash':digest(candidate)});record.update(accepted=True,status='COMMITTED')
            else:record.update(status='ROLLED_BACK',rollback_hash=before_hash)
        except Exception as ex:record.update(status='ROLLED_BACK',error_type=type(ex).__name__,error=str(ex)[:2500],rollback_hash=before_hash)
        write(folder/'result.json',record);return record
