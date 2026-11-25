"""Evidence gaps and finite-state causal checks shared by all scientific topics."""
import copy,itertools,json
from .contracts import digest
from .providers import parse_json

class ScientificCausalGraphValidator:
    def validate(self,model,max_states=4096):
        processes=model.get('processes',[]);by={p['process_semantic_id']:p for p in processes};issues=[]
        def issue(kind,pid,detail):
            issues.append({'issue_id':'CAUSAL_'+str(len(issues)+1),'issue_type':kind,'affected_process_ids':[pid] if pid else [],'status':'DETECTED','explanation':detail})
        def dependencies(pid,trail=()):
            if pid in trail:return True
            return any(x in by and dependencies(x,trail+(pid,)) for x in by[pid].get('temporal_scope',{}).get('after',[]))
        for pid,p in by.items():
            if dependencies(pid):issue('CYCLIC_DEPENDENCY',pid,'Completion dependency cycle cannot be entered by a once-per-process execution.')
            if not p.get('temporal_scope',{}).get('end_condition'):issue('MISSING_END_CONDITION',pid,'No independent end condition.')
        initial=model.get('initial_states')
        if initial is None:
            # Legacy model preconditions are not initial states. Never silently seed them.
            issue('INITIAL_STATE_UNSPECIFIED',None,'Historical model has no explicit initial_states; reachability is conditional, not automatically FAIL/PASS.')
            initial={}
        if not isinstance(initial,dict):raise ValueError('initial_states must be a state dictionary')
        queue=[(copy.deepcopy(initial),frozenset())];seen=set();reachable=set();witness={}
        while queue and len(seen)<max_states:
            state,done=queue.pop(0);sig=(json.dumps(state,sort_keys=True),tuple(sorted(done)))
            if sig in seen:continue
            seen.add(sig)
            for pid,p in by.items():
                if pid in done or not set(p.get('temporal_scope',{}).get('after',[]))<=done:continue
                if not all(k in state and state[k]==v for k,v in p.get('preconditions',{}).items()):continue
                nxt=copy.deepcopy(state);nxt.update(p.get('effects',{}));reachable.add(pid);witness.setdefault(pid,{'state_before':state,'state_after':nxt,'completed_before':sorted(done)})
                queue.append((nxt,done|{pid}))
        for pid,p in by.items():
            for key,value in p.get('preconditions',{}).items():
                producers=[q['process_semantic_id'] for q in processes if q['process_semantic_id']!=pid and q.get('effects',{}).get(key,object())==value]
                if key not in initial and not producers:issue('UNREACHABLE_PRECONDITION' if model.get('initial_states') is not None else 'UNRESOLVED_INITIAL_OR_PRODUCER',pid,{'key':key,'value':value,'producers':[],'initial_state_declared':model.get('initial_states') is not None})
            if model.get('initial_states') is not None and pid not in reachable:issue('UNREACHABLE_PROCESS',pid,'No executable state path satisfies both dependencies and state predicates.')
            for concurrent in p.get('temporal_scope',{}).get('concurrent_with',[]):
                if concurrent not in by:continue
                q=by[concurrent];conflict={k:[v,q.get('effects',{}).get(k)] for k,v in p.get('effects',{}).items() if k in q.get('effects',{}) and q['effects'][k]!=v}
                invalidates={k:[v,p['effects'][k]] for k,v in q.get('preconditions',{}).items() if k in p.get('effects',{}) and p['effects'][k]!=v}
                if conflict or invalidates:issue('CONCURRENT_STATE_CONFLICT',pid,{'other_process':concurrent,'conflicting_writes':conflict,'invalidated_preconditions':invalidates})
        return {'model_sha256':digest(model),'status':('REVIEW_INCOMPLETE' if model.get('initial_states') is None else 'REVISE') if issues else 'PASS','issues':issues,'reachable_process_ids':sorted(reachable),'witnesses':witness,'states_explored':len(seen),'exhaustive':not queue,'limit':max_states,'semantics':'Finite paths with exact state values, completion dependencies, once-per-process invocation; dynamic loops and unmodeled continuous chemistry not proven.'}

class EvidenceSufficiencyAuditor:
    TYPES=['MISSING_REQUIRED_ROLE','UNSUPPORTED_CAUSAL_CLAIM','INSUFFICIENT_EVIDENCE','SOURCE_CONTRADICTION','SCOPE_MISMATCH','UNRESOLVED_SCIENTIFIC_IDENTITY']
    def __init__(self,gateway=None):self.gateway=gateway
    def audit(self,task,model,evidence,prior_review=None):
        ids={e['evidence_id'] for e in evidence};issues=[]
        for item in model.get('entities',[])+model.get('relations',[])+model.get('processes',[]):
            if not item.get('support') or not set(item.get('evidence_ids',[]))<=ids:
                issues.append({'issue_type':'INSUFFICIENT_EVIDENCE','affected_entity_id':item.get('semantic_id'),'affected_process_id':item.get('process_semantic_id'),'required_evidence':'Verifiable supporting source passage for this item.'})
        if self.gateway:
            prompt='Audit evidence sufficiency against original task and retrieved passages. Do not trust past PASS or REVISE blindly. No theme-specific answer list provided. Return JSON {issues:[{issue_id,affected_process_id,affected_entity_id,requirement_id,evidence_ids,issue_type,required_evidence,allowed_repair_actions,severity,status,explanation}],requirements:[{requirement_id,requirement,covered_by_process_ids}],coverage_status:PASS|REVIEW_INCOMPLETE}. issue_type only '+str(self.TYPES)+'. Missing required actors and unsupported causality require supporting source/task evidence, not name presence. Preserve original user scope. Source disagreement must cite actual snippets. Existing schematic limits are allowed; do not require excluded molecular detail without task basis. Prior independent review is a clue not ground truth. Produce targeted evidence questions, no invented facts. Compact output.'
            sources=[{k:e[k] for k in ['evidence_id','url','title','passages']} for e in evidence]
            out=parse_json(self.gateway.request('deepseek','evidence_sufficiency_audit',prompt+json.dumps({'task':task,'model':model,'sources':sources,'prior_review':prior_review},ensure_ascii=False)))
            for i in out.get('issues',[]):
                if i.get('issue_type') not in self.TYPES:raise ValueError('Unknown evidence gap type')
                if not set(i.get('evidence_ids',[]))<=ids:raise ValueError('Unknown audit evidence reference')
            issues+=out.get('issues',[])
        else:out={'coverage_status':'REVIEW_INCOMPLETE','requirements':[],'note':'Offline structural evidence checks only; no scientific entailment claim.'}
        for n,i in enumerate(issues):
            i.setdefault('issue_id','GAP_'+str(n+1));i.setdefault('affected_process_id',None);i.setdefault('affected_entity_id',None);i.setdefault('requirement_id',None);i.setdefault('evidence_ids',[]);i.setdefault('allowed_repair_actions',['retrieve_evidence','revise_supported_model']);i.setdefault('severity','blocking');i.setdefault('status','DETECTED')
        return {**out,'issues':issues,'model_sha256':digest(model)}

class EvidenceGapResearch:
    def __init__(self,gateway,retriever,max_attempts=2):self.gateway=gateway;self.retriever=retriever;self.max_attempts=max_attempts
    def plan(self,task,issues):
        prompt='Create targeted NEW evidence requests for these scientific gaps, not a whole-topic restart. Return JSON {candidate_urls:[2-4 likely authoritative direct content URLs],scientific_queries:[one precise query],gap_mapping:[{issue_id,question,strategy}]}. Strategy depends on missing role, causal mechanism, conflicting source, state production or organism scope. No fabricated claims; URLs will be fetched. Prefer independent specialist sources. '
        return parse_json(self.gateway.request('deepseek','gap_driven_research_plan',prompt+json.dumps({'task':task,'issues':issues},ensure_ascii=False)))
    def retrieve(self,task,issues,cache):
        from pathlib import Path
        from .contracts import write
        path=Path(cache);key=digest({'task':task,'issues':issues});path.mkdir(parents=True,exist_ok=True);dest=path/(key+'.json')
        if dest.exists():return json.loads(dest.read_text())
        result={'gap_hash':key,'attempts':[],'evidence':[]};known=set()
        for n in range(self.max_attempts):
            plan=self.plan(task,issues);retrieval=self.retriever.retrieve(task,plan);new=[e for e in retrieval['evidence'] if e['content_sha256'] not in known]
            result['attempts'].append({'plan':plan,'retrieval':retrieval,'new_sources':len(new)});result['evidence']+=new;known.update(e['content_sha256'] for e in new)
            if new:break
            result['stop_reason']='NO_PROGRESS'
        write(dest,result);return result

def validate_repair(before,after,new_evidence,issues):
    if digest(before)==digest(after):return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Target model unchanged'}
    if any(i.get('evidence_required',True) for i in issues) and not new_evidence:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'No new evidence for evidence-dependent repair'}
    before_ids={p['process_semantic_id'] for p in before['processes']};after_ids={p['process_semantic_id'] for p in after['processes']}
    if not before_ids<=after_ids:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Removing existing required processes is forbidden'}
    before_checks={o['constraint_id'] for p in before['processes'] for o in p['observables']};after_checks={o['constraint_id'] for p in after['processes'] for o in p['observables']}
    if not before_checks<=after_checks:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Removing existing constraints is forbidden'}
    return {'accepted':True,'status':'CANDIDATE_CREATED','before_sha256':digest(before),'after_sha256':digest(after),'science_approval':False}
