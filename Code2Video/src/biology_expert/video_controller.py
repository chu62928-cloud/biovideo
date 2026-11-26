"""Goal-driven video tools. Only the registered renderer executes code."""
import hashlib,json,re,shutil,subprocess,sys,os
from pathlib import Path
from collections import Counter
from .contracts import write,digest
from .providers import parse_json
from .contract_builder import ScientificEvidenceRetriever
from .retrieval_quality import exact_support,source_quality
from .typed_science_builder import TypedScienceModelBuilder
from .model_reliability import ScientificCausalGraphValidator

TOOLS={
'research':'{url: exact public OpenStax textbook chapter HTTPS URL,keywords:[terms], objectives:[learning goals]}. Fetch and rank chapter paragraphs and figure captions.',
'facts':'{claims:[{id,statement,support:[{evidence_id,location,quote}]}],simplifications:[...]}. 2-4 atomic claims. Supply evidence_id and paragraph location only; the tool attaches its actual text. Independently review.',
'storyboard':'{scenes:[scene,...]}. Design 3 connected educational scenes, opening learning goal, mechanism, summary. Each scene has title,caption,claim_ids,verification:[CLAIM,ENTITY,RELATION,STATE,TEMPORAL,CONSERVATION,VISUAL as applicable],reference_use (what figure informed), objects. Each object {id,label,color:"#RRGGBB",closed:boolean,points:[[x,y],...],shift:[dx,dy],label_offset:[dx,dy]}. Coordinates in x -6..6, y -2..2. Use 3-12 distinct points per object to draw meaningful biological contours; positions and motion should explain the claim. Use short labels and captions in requested language. Reference geometry is original. Stable IDs across scenes.',
'repair_scene':'{index:zero-based scene index,scene:one complete replacement scene, same format as storyboard}. Only amend affected scene.',
'render_review':'{}. Render cached per-scene Manim clips, compose in order, independently inspect actual MP4 and each claim.',
'strict_model':'{}. Build staged scientific model and validate causal states on retrieved evidence.',
'finish':'{}. Return existing reviewed result or request human review if genuinely blocked.'}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def validate_scene(s,claims):
    if not s['claim_ids'] or not set(s['claim_ids'])<=claims:raise ValueError('missing or unknown claim')
    if not s['verification'] or not {'CLAIM','VISUAL'}<=set(s['verification']):raise ValueError('require CLAIM and VISUAL')
    if not (1<=len(s['objects'])<=24) or not all(isinstance(s[k],str) and 0<len(s[k])<=300 for k in ['title','caption']):raise ValueError('invalid scene content')
    ids=set()
    for o in s['objects']:
        if o['id'] in ids or not re.fullmatch('#[0-9A-Fa-f]{6}',o['color']):raise ValueError('duplicate object or invalid color')
        ids.add(o['id'])
        if not isinstance(o['label'],str) or not isinstance(o['closed'],bool) or not 2<=len(o['points'])<=60:raise ValueError('bad shape')
        for pt in o['points']+[o['shift'],o.get('label_offset',[0,.38])]:
            if len(pt)!=2 or any(type(x) not in (int,float) or not -12<=x<=12 for x in pt):raise ValueError('bad geometry')
    return s

def run(agent,task):
    root=agent.root
    get=lambda name:read(root/(name+'.json'))
    put=lambda name,data:write(root/(name+'.json'),data)
    has=lambda name:(root/(name+'.json')).is_file()
    log=root/'trajectory.jsonl'
    history=[json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    if has('result'):return get('result')
    net=ScientificEvidenceRetriever(root/'research',limit=9,visual_limit=3)
    def research(url,keywords,objectives):
        from urllib.parse import urlsplit
        parsed=urlsplit(url)
        if parsed.hostname!='openstax.org' or not parsed.path.startswith('/books/'):raise ValueError('use approved textbook chapter')
        ev=net.fetch(url,'chapter')
        if source_quality(ev)['status']!='READABLE_BODY':raise ValueError('INSUFFICIENT_EVIDENCE')
        score=lambda text:sum(w.lower() in text.lower() for w in keywords)
        passages=sorted(ev['passages'],key=lambda x:-score(x['text']))[:9]
        figs=sorted(ev['figures'],key=lambda f:-score(f['caption']+' '+f['alt']))[:2]
        evidence={**ev,'passages':passages,'figures':figs}
        put('evidence',[evidence])
        put('visual_design',dict(objectives=objectives,figures=figs,license='external pixels not imported; captions used for original schematic',upload=False))
        return dict(evidence_id=ev['evidence_id'],passages=passages,figures=figs,objectives=objectives)
    def facts(claims,simplifications):
        evidence=get('evidence')
        if not claims or len({c['id'] for c in claims})!=len(claims):raise ValueError('Invalid claims')
        for c in claims:
            for ref in c['support']:
                if 'quote' not in ref:
                    for ev in evidence:
                        if ev['evidence_id']==ref.get('evidence_id'):
                            for passage in ev['passages']:
                                if passage['location']==ref.get('location'):
                                    ref['quote']=passage['text']
            if not exact_support(c['support'],evidence):raise ValueError('Exact source text/location missing for '+c['id'])
        review=parse_json(agent.gateway.request('deepseek','harness_fact_review','Return JSON {decision:PASS|REVISE,claim_reviews:[{id,decision,reason}]}. Check each statement against its exact quoted evidence, original goal coverage, omitted steps and simplifications. '+json.dumps(dict(task=task,claims=claims,simplifications=simplifications))))
        passed=review.get('decision')=='PASS' and {r['id'] for r in review['claim_reviews'] if r['decision']=='PASS'}=={c['id'] for c in claims}
        put('fact_sheet',dict(evidence_hash=digest(evidence),claims=claims,simplifications=simplifications,review=review,verified=passed))
        return dict(verified=passed,issues=review,claims=claims)
    def storyboard(scenes):
        claims={c['id'] for c in get('fact_sheet')['claims']}
        if not 2<=len(scenes)<=5:raise ValueError('2-5 scenes required')
        for s in scenes:validate_scene(s,claims)
        if set.union(*(set(s['claim_ids']) for s in scenes))!=claims:raise ValueError('omitted critical claim')
        put('storyboard',scenes)
        put('story_source',digest(get('fact_sheet')))
        return dict(scene_count=len(scenes),captions=[s['caption'] for s in scenes],verification=[s['verification'] for s in scenes])
    def repair_scene(index,scene):
        scenes=get('storyboard')
        if type(index)!=int or not 0<=index<len(scenes):raise ValueError('invalid scene index')
        put('storyboard_'+digest(scenes)[:12],scenes)
        scenes[index]=scene
        return storyboard(scenes)
    def strict_model():
        model=TypedScienceModelBuilder(agent.gateway).build_staged(dict(user_request=task['request'],topic=task['request']),{'evidence':get('evidence')},root/'typed_cache')
        out=ScientificCausalGraphValidator().validate(model)
        put('typed',dict(model=model,causal=out))
        return {'status':out['status']}
    def render_review():
        scenes=get('storyboard')
        clips=[]
        for i,scene in enumerate(scenes):
            data=dict(scene,duration=task['duration']/len(scenes))
            folder=root/'clips'/digest(data)
            folder.mkdir(parents=True,exist_ok=True)
            clip=folder/'clip.mp4'
            if not clip.exists():
                write(folder/'scene.json',data)
                shutil.copyfile(Path(__file__).with_name('lesson_scene.py'),folder/'lesson.py')
                base=Path('/autodl-tmp/code2biovideo')
                cp=subprocess.run([str(base/'env/bin/python'),str(base/'sandbox_exec.py'),str(folder),'manim','-ql','--disable_caching','lesson.py','Lesson'],capture_output=True,timeout=160)
                (folder/'render.log').write_bytes(cp.stderr+cp.stdout)
                if cp.returncode:raise ValueError('RENDER_ERROR scene '+str(i)+' '+cp.stderr.decode(errors='replace')[-500:])
                src=next((folder/'media').rglob('Lesson.mp4'))
                shutil.copy(src,clip)
            clips.append(clip)
        listing=root/'concat.txt'
        listing.write_text(''.join("file '"+str(c.relative_to(root))+"'\n" for c in clips))
        video=root/('candidate_'+digest(scenes)[:12]+'.mp4')
        subprocess.run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','1','-i',str(listing),'-c','copy',str(video)],check=True)
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
        put('video',dict(path=video.name,sha256=sha(video),storyboard=digest(scenes),clips=[str(c.relative_to(root)) for c in clips]))
        prompt='Independently inspect actual video. Check every claim, state change, relation, continuity, on-screen terminology, learning goal and legibility. Locate issues by scene and timestamp. Return JSON {science:{decision:PASS|REVISE},visual:{decision:PASS|REVISE},coverage:PASS|REVISE,mechanism_observable:FULLY_VISIBLE|PARTIAL,mechanism_evidence:[timestamped observed state/relationship changes],checks:[{claim_id,status:PASS|FAIL|INCOMPLETE,seconds,observation}],issues:[]}. '+json.dumps({'task':task,'facts':get('fact_sheet')['claims'],'scenes':[(s['caption'],s['verification']) for s in scenes]})
        review=parse_json(agent.gateway.request('qwen','v5_video_review',prompt,video=video))
        review.update(video_sha256=sha(video),evidence_level='VLM_INFERRED')
        put('validation',review);put('review_'+sha(video)[:12],review)
        return review
    callbacks=dict(research=research,facts=facts,storyboard=storyboard,strict_model=strict_model,render_review=render_review,repair_scene=repair_scene,finish=lambda:{'terminal':True})
    for name,fn in callbacks.items():agent.registry.register(name,fn)
    reason='step limit'
    for step in range(len(history)+1,13):
        names=['research','finish']
        if has('evidence'):names+=['facts','strict_model']
        if has('fact_sheet') and get('fact_sheet')['verified'] and get('fact_sheet').get('evidence_hash')==digest(get('evidence')):names+=['storyboard']
        if has('storyboard') and 'storyboard' in names and get('story_source')==digest(get('fact_sheet')):names+=['repair_scene','render_review']
        available={n:TOOLS[n] for n in names}
        last=history[-1] if history else None
        obs=last['observation_summary'] if last else {'new_user_request':task}
        prompt='You control an educational biology video agent. Choose an executable action with actual arguments from the available tools. Use evidence before claims. Seek targeted recovery after failure. Finish only after a reviewed video or genuine blocker. Exact JSON keys: tool_name,arguments,decision_summary,based_on_observation_ids. Include last observation ID, or [] initially. For facts omit quote; supply only evidence_id and location. Do not supply approval or costs. '+json.dumps(dict(task=task,tools=available,observation=obs,REQUIRED_based_on_observation_ids=[last['observation_id']] if last else [],history=[(r['tool_name'],r['execution_status']) for r in history],facts=get('fact_sheet')['claims'] if has('fact_sheet') else None,evidence={'id':get('evidence')[0]['evidence_id'],'passages':get('evidence')[0]['passages']} if has('evidence') and (not has('fact_sheet') or not get('fact_sheet')['verified']) else None,figures=get('visual_design')['figures'] if has('visual_design') else [],storyboard=get('storyboard') if has('storyboard') else None),ensure_ascii=False)
        try:d=parse_json(agent.gateway.request('deepseek','harness_video_decision',prompt))
        except Exception as ex:reason=str(ex)[:350];break
        tool=d.get('tool_name');args=d.get('arguments',{});status='OK'
        try:
            refs=d.get('based_on_observation_ids',[])
            if tool not in names or not isinstance(refs,list) or not set(refs)<={'new_user_request',*(r['observation_id'] for r in history)} or (last and last['observation_id'] not in refs):raise ValueError('Invalid tool or observation reference. Include latest actual observation ID. Available: '+str([r['observation_id'] for r in history]))
            if tool=='repair_scene' and sum(h['tool_name']==tool and h.get('index')==args.get('index') for h in history)>=2:raise ValueError('Scene repair limit')
            result=agent.registry.invoke(tool,args,task['request'],d['decision_summary'])
        except Exception as exc:status='FAILED';result={'error':str(exc)[:1300],'type':type(exc).__name__}
        record=dict(step_id=step,task_id=root.name,state_hash=digest(history),decision_source='LLM',tool_name=tool,decision_summary=d.get('decision_summary'),based_on_observation_ids=d.get('based_on_observation_ids'),arguments_hash=digest(args),execution_status=status,observation_id='O'+str(step),observation_summary=result,index=args.get('index'))
        with log.open('a') as f:f.write(json.dumps(record)+'\n')
        history.append(record)
        if tool=='finish' and status=='OK':reason=d['decision_summary'];break
        if sum(h['tool_name']==tool and h['observation_summary']==result and h['execution_status']=='FAILED' for h in history)>=2:reason='Repeated identical failure: '+str(result);break
    video=get('video') if has('video') else {}
    review=get('validation') if has('validation') and get('validation').get('video_sha256')==video.get('sha256') else {}
    checked={r.get('claim_id') for r in review.get('checks',[]) if r.get('status')=='PASS'}
    approved=bool(review and has('storyboard') and video.get('storyboard')==digest(get('storyboard')) and get('story_source')==digest(get('fact_sheet')) and get('fact_sheet')['evidence_hash']==digest(get('evidence')) and get('fact_sheet')['verified'] and review['science']['decision']==review['visual']['decision']==review.get('coverage')=='PASS' and checked=={c['id'] for c in get('fact_sheet')['claims']} and all(r.get('status')=='PASS' for r in review['checks']))
    strict_requirements=has('storyboard') and any(set(s['verification']) & {'CONSERVATION','RELATION','STATE','TEMPORAL'} for s in get('storyboard'))
    if strict_requirements:
        approved=approved and review.get('mechanism_observable')=='FULLY_VISIBLE' and bool(review.get('mechanism_evidence')) and not any('CONSERVATION' in s['verification'] for s in get('storyboard'))
    result=dict(unmeasured_strict_requirements=bool(strict_requirements),generation_status='RENDERED' if video else 'NOT_RENDERED',release_status='VIDEO_APPROVED' if approved else 'REVISE' if review else 'REVIEW_INCOMPLETE',video_path=video.get('path'),video_sha256=video.get('sha256'),science_status=review.get('science',{}).get('decision'),visual_status=review.get('visual',{}).get('decision'),agent_steps=len(history),stop_reason=reason)
    put('result',result)
    return result
