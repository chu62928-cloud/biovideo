"""Evidence-backed short lessons using the upstream Code2Video generator."""
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from .code2video_adapter import Code2VideoAdapter, probe, render
from .contract_builder import ScientificEvidenceRetriever
from .contracts import digest, write
from .providers import parse_json
from .retrieval_quality import source_quality

RUBRIC = """Inspect the actual video under the given high-school teaching goal.
Evaluate these eight dimensions separately: facts, identity, mechanism, coverage,
labels, clarity, continuity, technical. Return JSON with science and visual objects
(each with decision PASS or REVISE), checks mapping the eight exact keys to
PASS, FAIL, INCOMPLETE or NOT_APPLICABLE, and issues (each {issue_id,
scene_id:"section_1", time_range:[start,end], claim_ids:[], severity,
observed_problem, expected_behavior}). Require observable changes over time
for a dynamic mechanism. A static arrow or a caption alone is insufficient.
Use only actual visible evidence and give concrete timestamps for failures.
An essential unsupported claim, mechanism or learning objective blocks approval."""

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def critic(gateway, task, path):
    data = parse_json(gateway.request('qwen','v51_video_critic',
        RUBRIC+'\nTeaching goal: '+json.dumps(task,ensure_ascii=False),video=path))
    keys = set('facts identity mechanism coverage labels clarity continuity technical'.split())
    checks = data.get('checks', {})
    passed = (isinstance(checks,dict) and keys==checks.keys()
              and all(checks[k]=='PASS' for k in keys-{'technical'})
              and checks['technical'] in ('PASS','NOT_APPLICABLE')
              and not data.get('issues')
              and data['science']['decision']==data['visual']['decision']=='PASS')
    return data | {'video_sha256':sha(path),'domain_status':'PASS' if passed else 'REVISE'}

def bind_decision(model_action, observation, video_hash, issues):
    tool=model_action.get('tool')
    if tool=='repair_scene':
        if model_action.get('scene_id')!='section_1' or model_action.get('issue_id') not in issues:
            raise ValueError('Unknown scene or issue')
        if observation.get('video_sha256')!=video_hash:
            raise ValueError('Stale video observation')
    if tool not in ('repair_scene','request_human_review'):
        raise ValueError('Unknown decision tool')
    return {'tool':tool,'observation_hash':digest(observation),'video_sha256':video_hash}

def run(agent, task):
    root=agent.root
    gateway=agent.gateway
    get=lambda name:read(root/(name+'.json'))
    save=lambda name,data:write(root/(name+'.json'),data)
    has=lambda name:(root/(name+'.json')).exists()
    if has('result'):
        return get('result')
    trace=root/'trajectory.jsonl'
    def event(tool, domain, data, source='DETERMINISTIC_WORKFLOW', execution='SUCCESS'):
        row=dict(tool_name=tool,domain_status=domain,execution_status=execution,
                 decision_source=source,observation_hash=digest(data),observation=data)
        with trace.open('a') as output:
            output.write(json.dumps(row,ensure_ascii=False)+'\n')
        save('checkpoint',dict(user_goal=task,latest=row,remaining={
            provider:limit-sum(r['provider']==provider for r in gateway.rows)
            for provider,limit in gateway.limits.items()},
            artifacts=sorted(p.name for p in root.glob('*.json'))))
    def request(stage,prompt):
        return parse_json(gateway.request('deepseek','harness_v51_'+stage,prompt))
    stage='evidence'
    video=None
    review=None
    failure=None
    try:
        evidence=get('evidence') if has('evidence') else []
        if evidence:
            evidence=[e for e in evidence if source_quality(e)['status']=='READABLE_BODY']
        if not evidence:
            net=ScientificEvidenceRetriever(root/'research',limit=8,visual_limit=0)
            if task['workflow']=='agent':
                decision=request('research','Choose a focused research question and keywords for this teaching task. Return JSON {tool:"research",query:string,keywords:[string],reason:string}. '+json.dumps(task))
                if decision.get('tool')!='research':
                    raise ValueError('Unsupported research action')
                event('research_decision','SELECTED',decision,'LLM_DECISION')
                query=decision['query']
            else:
                query=task['request']
            result=net.retrieve(dict(topic_id='lesson',user_request=task['request'],research_question=query),
                                dict(search_queries=[query],candidate_urls=[]))
            by_id={e['evidence_id']:e for e in evidence+result['evidence']
                   if source_quality(e)['status']=='READABLE_BODY'}
            words=set(re.findall('[a-z]{4,}',task['request'].lower()))
            def rank(text):
                return len(words & set(re.findall('[a-z]{4,}',text.lower())))
            evidence=[e | {'passages':sorted(e['passages'],key=lambda p:-rank(p['text']))[:3]}
                      for e in by_id.values()]
            save('evidence',evidence)
            event('retrieve_scientific_evidence','RETRIEVED' if evidence else 'INSUFFICIENT_EVIDENCE',
                  {'sources':len(evidence),'failures':result['failures']})
        if not evidence:
            raise ValueError('No readable scientific source')
        stage='fact_sheet'
        if has('fact_sheet'):
            context=get('fact_sheet')
        else:
            context=request('fact_sheet','Create compact evidence-backed claims for this prompt. Return JSON '
                '{claims:[{id,statement,evidence_id,location}],learning_objectives:[string],'
                'required_entities:[string],required_dynamic_mechanisms:[string],forbidden_outcomes:[string],'
                'allowed_simplifications:[string]}. Use only supplied passages. '+json.dumps(dict(task=task,evidence=evidence),ensure_ascii=False))
            passages={(e['evidence_id'],p['location']):(e['url'],p['text'])
                      for e in evidence for p in source_quality(e)['usable_passages']}
            claims=context['claims']
            if not claims or len({c['id'] for c in claims})!=len(claims):
                raise ValueError('Claim IDs must be unique')
            for claim in claims:
                url, body=passages[(claim['evidence_id'],claim['location'])]
                claim['source_url']=url
                claim['support']=body
            result=request('fact_review','Independently check entailment and original educational coverage. '
                'Return JSON {decision:PASS|REVISE, passed_ids:[string], blocking_reason:string}. '
                +json.dumps(dict(task=task,facts=context),ensure_ascii=False))
            context.update(review=result,verified=result['decision']=='PASS'
                           and set(result['passed_ids'])=={c['id'] for c in claims})
            save('fact_sheet',context)
            event('verify_scientific_claims',result['decision'],result)
        if not context['verified']:
            raise ValueError(context['review'].get('blocking_reason') or 'Independent facts review incomplete')
        stage='planning'
        compact=dict(context)
        compact['claims']=[{k:v for k,v in c.items() if k!='support'} for c in context['claims']]
        compact['references']=[{'source':e['url'],'caption':f['caption'],'alt':f.get('alt',''),
                                'use':'caption and visual description for original schematic'}
                               for e in evidence for f in e.get('figures',[])][:4]
        compact['task']=task
        save('visual_design',compact['references'])
        adapter=Code2VideoAdapter(root,task['request'],compact,gateway)
        section=adapter.plan()
        save('storyboard',dict(scene_id=section.id,section=asdict(section),
                              claim_ids=[c['id'] for c in context['claims']]))
        event('upstream_planner','PLANNED',{'scene_id':section.id,'context':digest(compact)})
        stage='generation'
        attempt=root/'generated_code'/'initial'
        if has('video'):
            video=root/get('video')['path']
            if sha(video)!=get('video')['sha256']:
                raise ValueError('Persisted video changed')
        else:
            code=adapter.code(section)
            video=render(root,code,'initial')
            save('video',dict(path=video.name,sha256=sha(video),**probe(video)))
            event('upstream_coder_and_render','RENDERED',get('video'))
        stage='review'
        review=get('validation') if has('validation') else critic(gateway,task,video)
        if review['video_sha256']!=sha(video):
            raise ValueError('Stale video review')
        save('validation',review)
        event('review_video',review['domain_status'],review)
        if review['domain_status']=='REVISE' and review.get('issues'):
            stage='repair'
            issues={i['issue_id']:i for i in review['issues'] if isinstance(i,dict)
                    and i.get('issue_id') and i.get('scene_id')=='section_1'}
            if not issues:
                raise ValueError('No located repair issue')
            if task['workflow']=='agent' and sum(r['provider']=='deepseek' for r in gateway.rows)+2<=gateway.limits['deepseek']:
                decision=request('repair_decision','Choose tool repair_scene or request_human_review. '
                    'Return JSON {tool,scene_id,issue_id,reason,repair_instruction}. '
                    'Use actual issue IDs. Given this evidence and remaining one Coder call, choose '
                    'the best local fix or stop if no reliable edit. '+json.dumps(review))
            elif task['workflow']=='fixed':
                decision=dict(tool='repair_scene',scene_id='section_1',issue_id=next(iter(issues)),
                              reason='Fixed workflow repairs first located issue',
                              repair_instruction='Address the observed issue without changing correct facts.')
            else:
                decision={'tool':'request_human_review','reason':'Remaining budget reserved for completed candidate'}
            binding=bind_decision(decision,review,sha(video),issues)
            event(decision['tool'],'SELECTED',binding|decision,
                  'LLM_DECISION' if task['workflow']=='agent' else 'HARNESS_POLICY')
            if decision['tool']=='repair_scene':
                record={'before':sha(video),'issue':issues[decision['issue_id']],'status':'PENDING'}
                save('repair_records',record)
                try:
                    from agent import Section
                    local=Section(**asdict(section))
                    adapter.agent.section_codes[local.id]=(attempt/'lesson.py').read_text()
                    code=adapter.code(local,json.dumps(record['issue'])+' '+decision['repair_instruction'])
                    candidate=render(root,code,'repair_1')
                    verdict=critic(gateway,task,candidate)
                    save('repair_review',verdict)
                    record.update(after=sha(candidate),status='COMMITTED' if verdict['domain_status']=='PASS' else 'ROLLED_BACK')
                    if record['status']=='COMMITTED':
                        video,review=candidate,verdict
                except Exception as exc:
                    record.update(status='ROLLED_BACK',error=str(exc)[:600])
                save('repair_records',record)
                event('repair_scene',record['status'],record)
    except Exception as exc:
        failure={'stage':stage,'reason':str(exc)[:1000]}
        event(stage,'FAILED',failure,execution='FAILED')
    outcome=dict(generation_status='RENDERED' if video else 'NOT_RENDERED',
                 release_status='VIDEO_APPROVED' if review and review['domain_status']=='PASS'
                 else 'VIDEO_CANDIDATE' if video else 'RENDER_FAILED',
                 video_path=video.name if video else None,video_sha256=sha(video) if video else None,
                 media=probe(video) if video else None,review=review,failure=failure)
    save('result',outcome)
    return outcome
