"""Evidence gaps and finite-state causal checks shared by all scientific topics."""
import copy,itertools,json
from .contracts import digest
from .providers import parse_json

class ScientificCausalGraphValidator:
    def validate(self,model,max_states=4096):
        if model.get('schema_version')=='1.1':return self._validate_typed_states(model,max_states)
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
        if queue:issue('STATE_SPACE_INCOMPLETE',None,'Finite state exploration limit reached; unvisited paths remain.')
        return {'model_sha256':digest(model),'status':('REVIEW_INCOMPLETE' if model.get('initial_states') is None else 'REVISE') if issues else 'PASS','issues':issues,'reachable_process_ids':sorted(reachable),'witnesses':witness,'states_explored':len(seen),'exhaustive':not queue,'limit':max_states,'semantics':'Finite paths with exact state values, completion dependencies, once-per-process invocation; dynamic loops and unmodeled continuous chemistry not proven.'}

    def _validate_typed_states(self,model,max_states):
        states={s['state_id']:s for s in model.get('states',[])};processes={p['process_semantic_id']:p for p in model['processes']};entities={e['semantic_id'] for e in model['entities']};issues=[];unknown=False
        def issue(kind,pid,detail):issues.append({'issue_id':'STATE_'+str(len(issues)+1),'issue_type':kind,'affected_process_ids':[pid] if pid else [],'status':'DETECTED','explanation':detail})
        if len(states)!=len(model.get('states',[])):issue('CONFLICTING_STATE',None,'Duplicate state IDs')
        def slot(s):return (s['subject_ref'],s['property'])
        initial={};initial_refs=set()
        for sid,s in states.items():
            if s['subject_ref'] not in entities:issue('INVALID_INITIAL_CONDITION',None,{'state_id':sid,'unknown_subject':s['subject_ref']})
            if s['state_kind']=='UNKNOWN':unknown=True
            if s['state_kind']=='INITIAL_CONDITION':
                if s.get('producer_process_id'):issue('INVALID_INITIAL_CONDITION',None,{'state_id':sid,'reason':'Initial state also claims in-clip producer'})
                key=slot(s)
                if key in initial and initial[key]!=s['value']:issue('CONFLICTING_STATE',None,{'state_id':sid,'slot':key})
                initial[key]=s['value'];initial_refs.add(sid)
            if s.get('producer_process_id') and s['producer_process_id'] not in processes:issue('MISSING_STATE_PRODUCER',None,{'state_id':sid})
        for omitted in model.get('clip_start',{}).get('omitted_processes',[]):
            if omitted.get('required_by_task'):issue('SCOPE_MISMATCH',None,'Required teaching mechanism cannot be omitted')
        def refs(p,key):
            out=p.get(key,[])
            for sid in out:
                if sid not in states:issue('MISSING_STATE_PRODUCER',p['process_semantic_id'],{'unknown_state_ref':sid})
            return [sid for sid in out if sid in states]
        requirements={pid:refs(p,'precondition_state_refs') for pid,p in processes.items()};effects={pid:refs(p,'effect_state_refs') for pid,p in processes.items()}
        for pid,p in processes.items():
            if not p.get('temporal_scope',{}).get('start_condition') or not p.get('temporal_scope',{}).get('end_condition'):issue('NOT_MEASURED',pid,'Explicit start/end conditions missing')
            for sid in effects[pid]:
                if states[sid].get('producer_process_id')!=pid:issue('MISSING_STATE_PRODUCER',pid,{'state_id':sid,'declared_producer':states[sid].get('producer_process_id')})
            for sid in requirements[pid]:
                s=states[sid];producers=[qid for qid in processes if any(slot(states[x])==slot(s) and states[x]['value']==s['value'] for x in effects[qid])]
                if sid not in initial_refs and not any(slot(states[x])==slot(s) and states[x]['value']==s['value'] for x in initial_refs) and not producers:issue('MISSING_STATE_PRODUCER',pid,{'state_id':sid})
            for qid in p.get('temporal_scope',{}).get('concurrent_with',[]):
                if qid not in processes:continue
                conflicts=[(x,y) for x in effects[pid] for y in effects[qid] if slot(states[x])==slot(states[y]) and states[x]['value']!=states[y]['value']]
                invalidations=[(x,y) for x in effects[pid] for y in requirements[qid] if slot(states[x])==slot(states[y]) and states[x]['value']!=states[y]['value']]
                if conflicts or invalidations:issue('CONFLICTING_STATE',pid,{'concurrent_process':qid,'conflicting_writes':conflicts,'invalidated_preconditions':invalidations})
        queue=[(initial,frozenset())];seen=set();reachable=set();witness={}
        while queue and len(seen)<max_states:
            state,done=queue.pop(0);signature=(json.dumps(sorted([(list(k),v) for k,v in state.items()]),sort_keys=True),tuple(sorted(done)))
            if signature in seen:continue
            seen.add(signature)
            for pid,p in processes.items():
                if pid in done or not set(p.get('temporal_scope',{}).get('after',[]))<=done:continue
                if any(states[sid]['state_kind'] in ['UNKNOWN','OUT_OF_SCOPE'] or slot(states[sid]) not in state or state[slot(states[sid])]!=states[sid]['value'] for sid in requirements[pid]):continue
                nxt=copy.deepcopy(state)
                for sid in p.get('terminates_state_refs',[]):
                    if sid in states:nxt.pop(slot(states[sid]),None)
                writes={}
                for sid in effects[pid]:
                    key=slot(states[sid]);value=states[sid]['value']
                    if key in writes and writes[key]!=value:issue('CONFLICTING_STATE',pid,'Single process produces incompatible state values')
                    writes[key]=value
                nxt.update(writes);reachable.add(pid);witness.setdefault(pid,{'completed_before':sorted(done),'required_state_refs':requirements[pid],'produced_state_refs':effects[pid]});queue.append((nxt,done|{pid}))
        incomplete=bool(queue) or bool(model.get('requires_continuous_or_unbounded_reasoning'))
        if incomplete:issue('STATE_SPACE_INCOMPLETE',None,'Unvisited state space or declared continuous/unbounded semantics')
        if not incomplete:
            for pid in processes:
                if pid not in reachable:issue('UNREACHABLE_PRECONDITION',pid,{'required_state_refs':requirements[pid]})
        if unknown:issue('NOT_MEASURED',None,'Explicit UNKNOWN states; no closed-world default')
        return {'model_sha256':digest(model),'status':'STATE_SPACE_INCOMPLETE' if incomplete else 'REVIEW_INCOMPLETE' if unknown else 'REVISE' if issues else 'PASS','issues':issues,'reachable_process_ids':sorted(reachable),'witnesses':witness,'states_explored':len(seen),'exhaustive':not incomplete,'limit':max_states,'semantics':'Bounded single-execution state paths on explicit subject/property/value; no claim about chemistry, loops or all continuous trajectories.'}

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
        prompt='Create a targeted evidence plan, not a whole-topic restart. Return JSON {requests:[{issue_id,research_question,required_claim,biological_scope,source_preferences,search_queries:[complete contextual query],expected_evidence_type:MECHANISM_DESCRIPTION}],candidate_urls:[2 likely authoritative content URLs],scientific_queries:[one complete query]}. Include every issue_id. search_queries and scientific_queries MUST be arrays, never strings. Queries retain original scientific mechanism/organism context. Source candidates are suggestions, not evidence. No theme-specific solution list is supplied.'
        from .retrieval_quality import validate_queries
        plan=parse_json(self.gateway.request('deepseek','gap_driven_research_plan',prompt+json.dumps({'task':task,'issues':issues},ensure_ascii=False)))
        validate_queries(plan,task)
        required={i['issue_id'] for i in issues};requests=plan.get('requests',[])
        if {q.get('issue_id') for q in requests}!=required:raise ValueError('Evidence requests must cover original gaps')
        for q in requests:
            for key in ['research_question','required_claim','biological_scope','source_preferences','expected_evidence_type']:
                if key not in q:raise ValueError('Missing research request '+key)
            validate_queries(q,dict(task,**{k:q[k] for k in ['research_question','required_claim']}))
        return plan
    def retrieve(self,task,issues,cache):
        from pathlib import Path
        from .contracts import write
        from .retrieval_quality import EvidenceEntailmentCheck,RetrievalQueryInvalid
        path=Path(cache);key=digest({'task':task,'issues':issues});path.mkdir(parents=True,exist_ok=True);dest=path/(key+'.json')
        if dest.exists():return json.loads(dest.read_text())
        result={'gap_hash':key,'attempts':[],'evidence':[],'claim_evidence_matches':[]};known=set();no_gain=0
        for n in range(self.max_attempts):
            try:plan=self.plan(task,issues)
            except (RetrievalQueryInvalid,ValueError) as ex:
                result['attempts'].append({'status':'RETRIEVAL_QUERY_INVALID','error':str(ex)});continue
            retrieval=self.retriever.retrieve(task,plan);new=[e for e in retrieval['evidence'] if e['content_sha256'] not in known];result['evidence']+=new;known.update(e['content_sha256'] for e in new)
            entailment=EvidenceEntailmentCheck(self.gateway).check(plan['requests'],result['evidence']);resolved={c['claim_id'] for c in entailment['claims'] if c['entailment_status'] in ['SUPPORTED','CONTRADICTED']};previous={c['claim_id'] for c in result['claim_evidence_matches'] if c['entailment_status'] in ['SUPPORTED','CONTRADICTED']}
            result['attempts'].append({'plan':plan,'retrieval':retrieval,'new_sources':len(new),'entailment':entailment,'resolved_gap_ids':sorted(resolved)});result['claim_evidence_matches']=entailment['claims']
            if resolved=={i['issue_id'] for i in issues}:result['stop_reason']='GAPS_SUPPORTED_OR_CONTRADICTED';break
            no_gain=no_gain+1 if resolved<=previous else 0
            if no_gain>=2:result['stop_reason']='NO_EFFECTIVE_INFORMATION_GAIN';break
        result.setdefault('stop_reason','RESEARCH_ATTEMPT_LIMIT');write(dest,result);return result

def validate_repair(before,after,new_evidence,issues):
    if digest(before)==digest(after):return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Target model unchanged'}
    if any(i.get('evidence_required',True) for i in issues) and not new_evidence:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'No new evidence for evidence-dependent repair'}
    before_ids={p['process_semantic_id'] for p in before['processes']};after_ids={p['process_semantic_id'] for p in after['processes']}
    if not before_ids<=after_ids:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Removing existing required processes is forbidden'}
    before_checks={o['constraint_id'] for p in before['processes'] for o in p['observables']};after_checks={o['constraint_id'] for p in after['processes'] for o in p['observables']}
    if not before_checks<=after_checks:return {'accepted':False,'status':'REPAIR_NOT_EFFECTIVE','reason':'Removing existing constraints is forbidden'}
    return {'accepted':True,'status':'CANDIDATE_CREATED','before_sha256':digest(before),'after_sha256':digest(after),'science_approval':False}
