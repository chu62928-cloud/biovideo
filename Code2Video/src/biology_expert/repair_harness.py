"""Scoped edit tools for the existing scientific repair transaction."""
from collections import defaultdict
from copy import deepcopy
from .contracts import digest
from .model_repair import ALLOWED_FIELDS, apply_model_patch
from .retrieval_quality import exact_support

KEYS = {'entities':'semantic_id','relations':'semantic_id','processes':'process_semantic_id','states':'state_id'}
OPS = {'update_entity':'entities','update_relation':'relations','update_process':'processes','bind_participant':'processes','update_observable':'processes','update_state':'states','update_scope':'scope'}


def compile_task(model, issue, evidence, requirement):
    items = {row[key]: (group,row) for group,key in KEYS.items() for row in model.get(group,[])}
    edges = defaultdict(set)
    def link(a,b):
        if a in items and b in items and a != b:
            edges[a].add(b)
            edges[b].add(a)
    for key,(group,row) in items.items():
        for field in ('source_entity','target_entity','subject_ref','producer_process_id'):
            link(key,row.get(field))
        for role in row.get('participants',[]):
            link(key,role['entity_ref'])
        for obs in row.get('observables',[]):
            link(key,obs.get('relation_ref'))
        for field in ('required_by_process_ids','precondition_state_refs','effect_state_refs','terminates_state_refs'):
            for ref in row.get(field,[]):
                link(key,ref)
    primary = sorted(set(issue['target_ids']) & (items.keys() | {'scope'}))
    dependencies = sorted(set().union(*(edges[i] for i in primary)) - set(primary))
    fields = {key: sorted(set(row) - {KEYS[group]}) for key,(group,row) in items.items()}
    for key,(group,row) in items.items():
        if group in ALLOWED_FIELDS:
            fields[key] = sorted(ALLOWED_FIELDS[group])
    fields['scope'] = ['included_processes','excluded_processes','simplifications']
    return dict(issue_id=issue['issue_id'],base_model_hash=digest(model),primary_targets=primary,
                dependency_targets=dependencies,allowed_operations=list(OPS)+["add_entity"],allowed_fields=fields,
                allowed_reference_ids=sorted(items),required_evidence_ids=issue.get('evidence_ids',[]),
                evidence_ids=[x['evidence_id'] for x in evidence],protected_requirements=[requirement],
                repair_goal=issue.get('reason',''),acceptance_conditions=['schema','references','causality','independent_review'])


def preflight(model, task, commands, evidence, extensions=()):
    errors = []
    targets = set(task['primary_targets'])
    for request in extensions:
        if request.get('reason') and request.get('target_id') in task['dependency_targets']:
            targets.add(request['target_id'])
        else:
            errors.append({'code':'INVALID_EXTENSION','request':request})
    if digest(model) != task['base_model_hash']:
        errors.append({'code':'STALE_MODEL'})
    patch = {'operations':[]}
    work = deepcopy(model)
    additions=[]
    for command in commands:
        target,op = command.get('target_id'),command.get('operation')
        group = OPS.get(op)
        def reject(code,**detail):
            errors.append(dict(code=code,target_id=target,**detail))
        if op=='add_entity':
            parent=command.get('for_target')
            item=command.get('fields',{})
            if parent not in targets or target in task['allowed_reference_ids'] or item.get('semantic_id')!=target or not exact_support(support,evidence):
                reject('INVALID_ADDITION')
            else:
                patch['operations'].append(dict(op='add',collection='entities',item=item,justifies_issue_id=task['issue_id']))
                additions.append(target)
            continue
        if target not in targets:
            reject('TARGET_OUTSIDE_TASK',allowed_targets=sorted(targets))
        support = command.get('support',[])
        if not exact_support(support,evidence):
            reject('MISSING_EVIDENCE')
        if group is None:
            reject('UNKNOWN_OPERATION')
            continue
        if group == 'scope' and target != 'scope':
            reject('UNAUTHORIZED_SCOPE')
            continue
        row = work['scope'] if group=='scope' else next((x for x in work.get(group,[]) if x[KEYS[group]]==target),None)
        if row is None:
            reject('UNKNOWN_TARGET')
            continue
        fields = deepcopy(command.get('fields',{}))
        if op=='bind_participant':
            role = next((r for r in row['participants'] if r['role']==command.get('role')),None)
            if role is None:
                reject('UNKNOWN_ROLE')
                continue
            role['entity_ref']=command.get('entity_ref')
            fields={'participants':deepcopy(row['participants'])}
        if op=='update_observable':
            obs=next((o for o in row['observables'] if o['constraint_id']==command.get('constraint_id')),None)
            if obs is None or not fields or not fields.keys()<=obs.keys()-{'constraint_id'}:
                reject('INVALID_OBSERVABLE')
                continue
            obs.update(fields)
            fields={'observables':deepcopy(row['observables'])}
        invalid = fields.keys()-set(task['allowed_fields'][target])
        if invalid:
            reject('FORBIDDEN_FIELDS',fields=sorted(invalid))
            continue
        row.update(fields)
        if group=='scope':
            patch['scope_patch']=dict(issue_id=task['issue_id'],fields=fields,support=support)
        elif group=='states':
            patch['state_upgrade']={'states':work['states']}
        else:
            patch['operations'].append(dict(op='update',collection=group,target_id=target,fields=fields))
    legacy=[dict(issue_id=task['issue_id'],target_ids=sorted(targets),repair_goal=task['repair_goal'])]
    try:
        candidate,changed=apply_model_patch(model,patch,legacy,evidence)
        for entity in additions:
            linked=any(r['semantic_id'] in targets and entity in (r['source_entity'],r['target_entity']) for r in candidate['relations'])
            linked |= any(p['process_semantic_id'] in targets and any(r['entity_ref']==entity for r in p['participants']) for p in candidate['processes'])
            if not linked:
                errors.append({'code':'UNRELATED_ADDITION','target_id':entity})
    except (KeyError,ValueError,TypeError,IndexError) as exc:
        errors.append({'code':'STRUCTURE_OR_SCOPE','message':str(exc)})
    except Exception as exc:
        from jsonschema import ValidationError
        if not isinstance(exc,ValidationError):
            raise
        errors.append({'code':'SCHEMA','path':list(exc.path),'message':exc.message})
    if errors:
        return dict(status='PREFLIGHT_REJECTED',errors=errors,rollback_hash=digest(model))
    return dict(status='PREFLIGHT_ACCEPTED',errors=[],patch=patch,tasks=legacy,candidate=candidate,changed=changed)
