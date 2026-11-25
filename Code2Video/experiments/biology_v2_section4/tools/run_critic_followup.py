from pathlib import Path
import sys,json,time,os,shutil,traceback
TOOLS=Path('/autodl-tmp/code2biovideo/Code2Video/experiments/biology_v2_section4/tools')
sys.path.insert(0,str(TOOLS))
import run_biology_v2 as base
from biology_v2_pipeline import TransactionRenderer,sha,replace_construct,validate_issues
from utils import extract_json_from_markdown
E=base.E
OUT=E/'groups/A3_critic_followup_two_rounds'
OUT.mkdir(exist_ok=False)
LOG=OUT/'logs';LOG.mkdir()
os.environ['CODE2VIDEO_AUDIT_DIR']=str(LOG/'deepseek_raw')
os.environ['QWEN_CRITIC_AUDIT_DIR']=str(LOG/'qwen_raw')
rows=[]
def save(): (OUT/'api_calls.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
def call(provider,rn,prompt,video=None):
    stage=f'{provider}_round_{rn}'
    (LOG/(stage+'_prompt.txt')).write_text(prompt)
    os.environ['CODE2VIDEO_STAGE']=stage
    rec={'provider':provider,'round':rn,'status':'pending','model':os.environ['DEEPSEEK_MODEL' if provider=='deepseek' else 'QWEN_MODEL'],'sdk_retries':0}
    rows.append(rec);save();t=time.monotonic()
    print('API_START',stage,flush=True)
    try:
        if provider=='deepseek':
            response,usage=base.request_deepseek_token(prompt,max_tokens=10000,max_retries=1)
        else:
            response=base.request_qwen_video_img(prompt,str(video),str(base.REPO/'experiments/gemini3_critic_probe/GRID_upstream.png'),max_tokens=10000,max_retries=1)
            usage=response.usage.model_dump() if response.usage else None
        (LOG/(stage+'_response.json')).write_text(response.model_dump_json(indent=2))
        rec.update(status='ok',usage=usage,response_model=response.model)
        return response.choices[0].message.content
    except Exception as ex:
        rec.update(status='error',error_type=type(ex).__name__,http_status=getattr(ex,'status_code',None))
        raise
    finally:
        rec['elapsed_seconds']=round(time.monotonic()-t,3);save()
        print('API_END',stage,rec['status'],rec['elapsed_seconds'],flush=True)

def validate(stage,trace,layout):
    base.validate(stage,trace,layout)
    assert not layout['out_of_frame'],'Objects outside frame'
    labels=[k for k,v in trace['object_metadata'].items() if v.get('role')=='label']
    assert len(labels)>=12,'Actual text labels must be registered'
    # Coverage changed from zero registered labels: no invalid comparison against old zero.
    first={}
    for frame in trace['frames']:
        for key,obj in frame['objects'].items():
            if key.startswith('fill_dna_') and obj.get('visible') and key not in first:
                first[key]={'time':frame['time'],'x':obj['center'][0]}
    ordered=sorted(first.items(),key=lambda x:x[1]['time'])
    assert len(ordered)>=3,'Missing visible progressive gap fill'
    assert all(a[1]['x']>b[1]['x'] for a,b in zip(ordered,ordered[1:])),'Lower-template gap filling must progress right-to-left'
    (stage/'followup_checks.json').write_text(json.dumps({'registered_labels':labels,'fill_first_visibility':ordered,'fill_direction_pass':True,'label_overlap_samples':len(layout['label_overlaps']),'note':'Bounding-box overlap is a heuristic; newly instrumented labels have no comparable old count.'},indent=2))

tx=TransactionRenderer(OUT,base.RUNTIME,E/'assets',duration_range=(25,35))
source=TransactionRenderer(E/'groups/A2_mechanism_assets',base.RUNTIME,E/'assets',(25,35)).state()
cached=E/'logs/qwen_retry_20261123_105828'
original=json.loads((E/'groups/A3_mechanism_assets_critic/round_1/input_pair.json').read_text())
assert source['code_sha256']==original['code_sha256'] and source['video_sha256']==original['video_sha256']
base.adopt(source,tx)
summary={'experiment':'Code2Video + DeepSeek + Qwen Critic model-substitution follow-up','scope':'V2 Section4 only','limits_this_followup':{'deepseek':2,'qwen_new':1},'prior_calls':{'deepseek':6,'qwen':2,'qwen_timeout_usage':'unknown'},'rounds':[],'manual_animation_code':False}
(OUT/'protocol.json').write_text(json.dumps(summary,indent=2))
t0=time.monotonic()
try:
    for rn in [1,2]:
        d=OUT/f'round_{rn}';d.mkdir()
        before=tx.state()
        (d/'input_pair.json').write_text(json.dumps(before,indent=2))
        code=Path(before['code']).read_text()
        trace=json.loads((Path(before['version'])/'geometry_trace.json').read_text())
        if rn==1:
            data=json.loads((cached/'structured_feedback.json').read_text())
            shutil.copy2(cached/'response.json',d/'critic_response.json')
            prompt=(E/'groups/A3_mechanism_assets_critic/round_1/critic_prompt.txt').read_text()
            (d/'feedback_provenance.json').write_text(json.dumps({'cached_feedback':str(cached),'same_code_sha256':before['code_sha256'],'same_video_sha256':before['video_sha256'],'new_qwen_request':False},indent=2))
        else:
            old=(E/'groups/A3_mechanism_assets_critic/round_1/critic_prompt.txt').read_text()
            prompt=old.split('ACTUAL OBJECT INVENTORY:')[0]+'ACTUAL OBJECT INVENTORY:\n'+json.dumps(trace['object_metadata'],ensure_ascii=False)
            # Same task and constraints, actual round-1 video and current IDs.
            content=call('qwen',rn,prompt,before['video'])
            (d/'feedback.txt').write_text(content)
            data=json.loads(extract_json_from_markdown(content))
        (d/'critic_prompt.txt').write_text(prompt)
        (d/'structured_feedback.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
        issues=data.get('issues',[])
        validate_issues(issues,set(trace['object_metadata']))
        query="""You are the Code2Video DeepSeek Coder. Repair the CURRENT VERIFIED MODULE using the Qwen Critic's validated object issues. This is a continuation, NOT a new scene or storyboard.
Return ONLY a single COMPLETE top-level def construct(self): function in a python code fence. It will replace just Section4Scene.construct via AST. DO NOT return imports or a class or ellipses. Keep the module helper functions unchanged; any new helpers must be nested inside construct.
Preserve all existing molecular IDs, SVG assets, five event markers, geometry identity, and current story/timing (total 25-35 seconds). Do not rewrite the scene from scratch.
Qwen may suggest place_at_grid, fake variables, or line numbers: IGNORE those executable snippets, implement their visual intent using ACTUAL local objects and object IDs.
Ensure all enzyme labels follow their actual moving enzymes with a one-argument updater lambda m: m.next_to(actual_enzyme, ...) or an equivalent parent group. Registered enzyme bindings continue to control enzyme motion. Label updaters must also work during waits; base runtime enables this.
Keep enzyme labels away from the center parental ladder y=0 and away from each other. Lagging polymerase/ligase labels can sit toward the bottom around y=-2.2, not on the center ladder. Leading label around y=0.4-0.7 must follow its enzyme. 3prime labels belonging to nascent strands must be next to their own green/orange strand row, not on blue template rows; preserve polarity values.
Register EVERY real on-screen Text object (title, caption, enzyme names, end glyphs, gap text, labels created via small_label) using self.register_object(unique_id, obj, role="label"). Do not register replacement Transform target Text as visible; register the original caption once. Every real label created via small_label can be registered in a nested local wrapper or manually. Keep molecular IDs intact.
There is an already documented mechanism constraint independent of Qwen: in EVENT5 the lower-template gap DNA currently appears incorrectly LEFT-TO-RIGHT. Reverse the nucleotide generation order so fill_dna_00, 01, 02 appear RIGHT-TO-LEFT within the SAME gap, because this nascent lagging strand grows 5prime->3prime toward the LEFT. Move the gap polymerase with this growth; do not use ligase for synthesis. Keep RNA removal then DNA fill then tiny nick sealing.
Do NOT add all gap DNA before FadeIn: it must visibly appear progressively. Preserve unique fill_dna_XX IDs and role=nucleotide metadata for automated actual-trace verification.
Keep simple safe working Manim calls and existing asset IDs. No manual file/network/process operations.
""" + '\nEXISTING GENERATION CONTRACT (function-only output overrides full-module wording):\n'+base.CONTRACT+'\nFIXED MECHANISM:\n'+json.dumps(base.SPEC,ensure_ascii=False)+'\nFIXED STORYBOARD:\n'+json.dumps(base.STORY,ensure_ascii=False)+'\nVALIDATED CRITIC ISSUES:\n'+json.dumps(issues,ensure_ascii=False)+'\nCURRENT VERIFIED MODULE:\n'+code
        reply=call('deepseek',rn,query)
        function=base.clean_code(reply);(d/'model_function.py').write_text(function)
        candidate=replace_construct(code,function)
        (d/'candidate_code.py').write_text(candidate)
        result=tx.attempt(candidate,f'critic_round_{rn}',extra_validator=validate)
        (d/'transaction.json').write_text(json.dumps(result,indent=2))
        summary['rounds'].append({'round':rn,'committed':result['committed'],'result':result,'issues':issues})
        (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        print('ROUND_DONE',rn,result['committed'],result.get('error'),flush=True)
        if not result['committed']:raise RuntimeError('Render gate failed: '+str(result.get('error')))
        shutil.copy2(result['after']['video'],d/'video.mp4')
        shutil.copy2(result['after']['code'],d/'rendered_code.py')
except Exception as ex:
    summary['error_type']=type(ex).__name__;summary['error']=str(ex)
    traceback.print_exc()
finally:
    summary['elapsed_seconds']=round(time.monotonic()-t0,3)
    summary['calls']=rows
    summary['completed_rounds']=sum(r['committed'] for r in summary['rounds'])
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print('FINISHED',summary['completed_rounds'],flush=True)
