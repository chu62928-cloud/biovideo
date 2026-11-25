from pathlib import Path
import ast,json,os,sys,time,shutil,difflib,traceback,hashlib

ROOT=Path('/autodl-tmp/code2biovideo').resolve();REPO=ROOT/'Code2Video'
E=REPO/'experiments/biology_v2_section4'
sys.path.insert(0,str(REPO/'src'))
from biology_v2_pipeline import TransactionRenderer,sha,validate_issues,replace_construct,trace_metrics
from gpt_request import request_deepseek_token,request_qwen_video_img
from utils import extract_json_from_markdown
from prompts import get_prompt4_layout_feedback
from agent import Section
for line in (ROOT/'.env').read_text().splitlines():
    if line and not line.startswith('#'):
        k,v=line.split('=',1);os.environ[k]=v
os.environ['CODE2VIDEO_AUDIT_DIR']=str(E/'logs/deepseek_raw')
os.environ['QWEN_CRITIC_AUDIT_DIR']=str(E/'logs/qwen_raw')
RUNTIME=REPO/'src/biology_runtime.py'
SPEC=json.loads((E/'specs/section4_mechanism.json').read_text())
STORY=json.loads((E/'specs/section4_storyboard_v2.json').read_text())
LEDGER=E/'logs/api_calls.jsonl'
LIMITS={'deepseek':8,'qwen':2,'wan':1}
STOP=False

def ledger():return [json.loads(x) for x in LEDGER.read_text().splitlines()] if LEDGER.exists() else []
def model_call(provider,stage,prompt,video=None):
    global STOP
    if STOP:raise RuntimeError('Earlier API failure; no further paid requests allowed')
    used=sum(x['provider']==provider for x in ledger())
    if used>=LIMITS[provider]:raise RuntimeError('Independent V2 API budget exhausted: '+provider)
    call_id=f'{provider}_{used+1:02d}'
    record={'call_id':call_id,'provider':provider,'stage':stage,'model':os.environ['DEEPSEEK_MODEL' if provider=='deepseek' else 'QWEN_MODEL'],'status':'pending','started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    with LEDGER.open('a') as f:f.write(json.dumps(record)+'\n')
    (E/'logs'/(call_id+'_prompt.txt')).write_text(prompt)
    os.environ['CODE2VIDEO_STAGE']=stage
    t=time.monotonic()
    try:
        if provider=='deepseek':
            response,usage=request_deepseek_token(prompt,max_tokens=10000,max_retries=1)
        else:
            response=request_qwen_video_img(prompt,str(video),str(REPO/'experiments/gemini3_critic_probe/GRID_upstream.png'),max_tokens=10000,max_retries=1)
            usage=response.usage.model_dump() if response.usage else {}
        (E/'logs'/(call_id+'_response.json')).write_text(response.model_dump_json(indent=2))
        record.update(status='ok',usage=usage,response_model=response.model)
        return response.choices[0].message.content
    except Exception as exc:
        STOP=True
        record.update(status='error',error_type=type(exc).__name__,http_status=getattr(exc,'status_code',None))
        raise
    finally:
        record['elapsed_seconds']=round(time.monotonic()-t,3)
        # Replace only this experiment's pending audit entry; historical ledgers are untouched.
        rows=ledger();rows[-1]=record
        LEDGER.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))

def clean_code(text):
    if '```python' in text:return text.split('```python',1)[1].split('```',1)[0].strip()+'\n'
    if '```' in text:return text.split('```',1)[1].split('```',1)[0].strip()+'\n'
    return text.strip()+'\n'

CONTRACT='''Use Manim Community 0.19.0, 854x480, 15 fps. Output a COMPLETE Python module defining Section4Scene(BiologyScene).
Allowed imports only: manim, numpy, math, biology_runtime. No filesystem/network/process calls; no eval/exec/getattr/setattr.
biology_runtime provides BiologyScene, load_bio_asset(asset_id,width=...), and np is available from manim.
BiologyScene is a generic instrumentation base, NOT a full lesson. You must write the entire animation, including all five events. Do not override setup, tear_down, update_mobjects, or runtime helpers.
Methods: register_object(object_id, mobject, role="molecule", **metadata) returns the same Mobject and records a UNIQUE persistent ID; duplicate IDs forbidden. role="label" for text, role="anchor" for an invisible small Dot that tracks an active site. You must add/show the mobjects yourself.
bind_near(enzyme_id,target_anchor_id,offset=(0,0,0),max_distance=0.8) attaches an updater; move the anchor, not the enzyme, during active synthesis. Enzyme and label should follow the SAME moving group/active site, never independent drifting.
mark_event("event_1_fork") etc records start of each event; use all FIVE exact event IDs at the requested starts. Total 25-35 seconds, aim exactly 30. Sum play/wait run_times explicitly. Avoid Text glyph drawing overhead: simple FadeIn/FadeOut captions.
Keep all content in x=[-6.5,6.5], y=[-3.5,3.5]. Use nearly the full frame for mechanism; no fixed left lecture panel. Title font 22, caption font 20, molecular labels 16-18. At most 1-2 main labels at any moment, changing English captions along bottom; the 5prime/3prime endpoint markers can be small separate short labels. Do not use LaTeX or nonstandard fonts.
Register these actual molecular Mobjects using EXACT IDs: replication_fork, template_leading, template_lagging, new_leading_strand, new_lagging_strand, primase, rna_primer, dna_polymerase_leading, dna_polymerase_lagging, okazaki_fragment, dna_ligase, incoming_nucleotide. Additional objects use unique meaningful IDs, e.g. rna_primer_lagging_1, rna_primer_lagging_2, okazaki_fragment_2, nucleotide_leading_01. Groups should contain the actual drawn children, not disconnected empty stand-ins.
Register nucleotide children individually (unique IDs, role="nucleotide", strand="leading" or "lagging", fragment="...", material="DNA"), so growth order can be checked from geometry. RNA primer children use material="RNA". Stable groups can be registered before adding growing children.
Use at least two bind_near relations for leading/lagging DNA polymerase active sites. Show primase at the site it primes. Different geometry, shape and short names distinguish enzymes; color alone is insufficient.
The fork is open to the LEFT and parental duplex lies to its RIGHT. Leading upper TEMPLATE runs 3prime-left to 5prime-right; the separate new strand just BELOW it grows RIGHT (5prime-left to growing3prime-right). Lower TEMPLATE runs 5prime-left to 3prime-right; new lagging fragments just ABOVE it each grow LEFT from their own primer3prime end. The fork may stay fixed to camera with schematic exposure progression; do not change strand identity.
At event5, visibly remove RNA primer first, leave space, add DNA nucleotides with polymerase into that space, then ligase seals only a small nick. Do not use ligase to draw a long green segment; it does not synthesize DNA or turn orange RNA into green DNA.
Never recolor a template to represent a new strand. Distinct Mobjects must remain spatially distinguishable. Polymerase must visibly accompany incremental nucleotide additions, not jump before/after a fully formed line.
Keep code clear and robust; standard Create/FadeIn/FadeOut/Transform/animate only. Labels should be positioned relative to their own object. Avoid unsupported kwargs such as stroke_dash. Return ONLY Python code in one fenced python block.'''

def initial_prompt(assets):
    common='You are the Code2Video DeepSeek Coder for a single controlled biology experiment.\n'+CONTRACT
    common+='\nFIXED MECHANISM SPEC:\n'+json.dumps(SPEC,ensure_ascii=False,indent=2)
    common+='\nFIXED STORYBOARD (identical across A1/A2):\n'+json.dumps(STORY,ensure_ascii=False,indent=2)
    if assets:
        common+='\nASSET CONDITION A2: Use load_bio_asset for the enzyme bodies, primer/nucleotide components as useful. All SVG components are independently movable; do NOT paste a whole static pathway diagram. Register the resulting SVG Mobjects using the same mechanism IDs. DNA backbone/fork and progressive synthesis still require explicit geometry and incremental motion.\nREGISTRY:\n'+(E/'assets/asset_registry.json').read_text()
    else:
        common+='\nASSET CONDITION A1: Use ONLY basic Manim geometric primitives; no SVGs, no load_bio_asset calls. Otherwise follow exactly the same mechanism and storyboard.'
    return common

def validate(stage,trace,layout):
    observed=trace.get('object_metadata',{})
    missing=set(x['id'] for x in SPEC['objects'])-set(observed)
    assert not missing,'Missing actual registered mechanism objects: '+str(sorted(missing))
    ids=[x['id'] for x in trace.get('events',[])]
    assert all(i in ids for i in STORY['required_runtime_events']),'Missing event markers'
    assert len(trace.get('bindings',[]))>=2,'Missing active-site bindings'
    assert not layout['binding_violations'],'Enzyme/active-site geometry violated'

def run_generation(label,assets):
    group=E/'groups'/label
    tx=TransactionRenderer(group,RUNTIME,E/'assets' if assets else None,duration_range=(25,35))
    prompt=initial_prompt(assets);(group/'coder_prompt.txt').write_text(prompt)
    start=time.monotonic();code=None;attempts=[]
    for n in range(1,4):
        if STOP:break
        if n==1:query=prompt
        else:
            last=attempts[-1];failure=group/'attempts'/last['tag']/'stderr.log'
            query=prompt+'\nYour previous full module failed validation/rendering. Return a corrected COMPLETE module, preserving the same five events and condition.\nERROR:\n'+last.get('error','')+'\n'+(failure.read_text()[-9000:] if failure.exists() else '')+'\nPREVIOUS MODEL CODE:\n'+code
        text=model_call('deepseek',label+':initial' if n==1 else label+':automatic_repair',query)
        code=clean_code(text)
        if n==1:(group/'generated_code.py').write_text(code)
        (group/f'candidate_{n}.py').write_text(code)
        result=tx.attempt(code,f'coder_attempt_{n}',extra_validator=validate)
        attempts.append(result);print('GROUP_ATTEMPT',label,n,result['committed'],result.get('error'),flush=True)
        if result['committed']:break
    (group/'generation_summary.json').write_text(json.dumps({'group':label,'attempts':attempts,'elapsed_seconds':round(time.monotonic()-start,3),'success':bool(tx.state()),'human_animation_code_intervention':False},indent=2))
    return tx

def adopt(source,target):
    group=target.group;dest=group/'versions/initial_A2_copy';dest.parent.mkdir(exist_ok=True)
    shutil.copytree(source['version'],dest)
    (group/'current').symlink_to(dest.relative_to(group),target_is_directory=True)
    for name in ['rendered_code.py','video.mp4','status.json']:(group/name).symlink_to('current/'+name)
    shutil.copy2(source['code'],group/'generated_code.py')
    (group/'initial_copy.json').write_text(json.dumps({'source':source,'no_new_coder_sample':True},indent=2))

def critic_experiment(a2):
    group=E/'groups/A3_mechanism_assets_critic';tx=TransactionRenderer(group,RUNTIME,E/'assets',duration_range=(25,35))
    adopt(a2,tx);rounds=[]
    original_section=Section('section_4',STORY['title'],[],[x['action'] for x in STORY['events']])
    native=get_prompt4_layout_feedback(original_section,'V2 whole-frame scene; use object IDs and actual geometry below, not the historical right-half grid coordinates.')
    for rn in [1,2]:
        before=tx.state();rounddir=group/f'round_{rn}';rounddir.mkdir(exist_ok=False)
        code=Path(before['code']).read_text();trace=json.loads((Path(before['version'])/'geometry_trace.json').read_text())
        known=trace['object_metadata']
        snapshot={'code_sha256':before['code_sha256'],'video_sha256':before['video_sha256'],'video':before['video'],'code':before['code']}
        (rounddir/'input_pair.json').write_text(json.dumps(snapshot,indent=2));shutil.copy2(before['code'],rounddir/'before_code.py')
        extension='''\nV2 EXTENSION (replaces line-number solution output only; original visual-overlap/bounds requirements still apply): inspect molecular-label association, identity/continuity across time, enzyme-active-site contact, and distinguishability of template vs nascent DNA. The scene uses the full frame rather than the old left lecture panel. Original GRID image is only a spatial reference, not a command to force right-half layout. Do NOT invent line numbers or variable names. Use only actual object_id values from the inventory. Return JSON containing both "layout":{"has_issues":bool,"improvements":[]} and "issues":[{"object_id":"known ID","issue_type":"overlap|bounds|label_relation|continuity|enzyme_contact|strand_confusion","current_state":{},"target_constraint":{},"suggested_change":"..."}]. At most 3 important issues. Do not assert scientific correctness from this layout inspection alone. Preserve strand polarities and RNA-removal→DNA-fill→nick-sealing order.\nACTUAL OBJECT INVENTORY:\n'''+json.dumps(known,ensure_ascii=False)
        prompt=native+extension
        (rounddir/'critic_prompt.txt').write_text(prompt)
        (rounddir/'prompt.diff').write_text(''.join(difflib.unified_diff(native.splitlines(True),prompt.splitlines(True),fromfile='original_layout_prompt',tofile='v2_object_constraint_prompt')))
        text=model_call('qwen',f'A3:critic_round_{rn}',prompt,video=before['video'])
        (rounddir/'raw_feedback.txt').write_text(text)
        data=json.loads(extract_json_from_markdown(text));issues=data.get('issues',[])
        try:validate_issues(issues,set(known))
        except AssertionError as exc:
            rounds.append({'round':rn,'status':'rejected_unknown_or_incomplete_object','error':str(exc),'input_pair':snapshot});break
        (rounddir/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2))
        if not issues:
            rounds.append({'round':rn,'status':'no_actionable_issues','input_pair':snapshot,'committed':False});break
        query='You are the same project DeepSeek Coder. Safely repair ONLY Section4Scene.construct based on validated OBJECT issues. Do not alter imports, helper definitions or other class methods. Return a single complete def construct(self): function in a Python code fence. Keep the fixed mechanism, all IDs, all five mark_event calls, 25-35s duration, SVG condition and anchored molecular relations. Do not use visual-model line numbers.\n'+CONTRACT+'\nFIXED MECHANISM:\n'+json.dumps(SPEC,ensure_ascii=False)+'\nFIXED STORYBOARD:\n'+json.dumps(STORY,ensure_ascii=False)+'\nISSUES:\n'+json.dumps(issues,ensure_ascii=False)+'\nCURRENT VERIFIED MODULE:\n'+code
        reply=model_call('deepseek',f'A3:repair_round_{rn}',query)
        function=clean_code(reply);(rounddir/'model_function.py').write_text(function)
        try:candidate=replace_construct(code,function)
        except Exception as exc:
            rounds.append({'round':rn,'status':'rejected_AST_patch','error':str(exc),'input_pair':snapshot,'committed':False});break
        (rounddir/'candidate_code.py').write_text(candidate)
        old_metrics=json.loads((Path(before['version'])/'layout_metrics.json').read_text())
        def guarded(stage,new_trace,new_layout):
            validate(stage,new_trace,new_layout)
            assert len(new_layout['out_of_frame'])<=len(old_metrics['out_of_frame'])+2,'New bounds regression detected'
            assert len(new_layout['label_overlaps'])<=len(old_metrics['label_overlaps'])+3,'New label overlap regression detected'
        result=tx.attempt(candidate,f'critic_round_{rn}',extra_validator=guarded)
        (rounddir/'transaction.json').write_text(json.dumps(result,indent=2))
        rounds.append({'round':rn,'status':'committed' if result['committed'] else 'rolled_back','committed':result['committed'],'input_pair':snapshot,'result':result})
        print('CRITIC_ROUND',rn,rounds[-1]['status'],flush=True)
        if not result['committed']:break
    (group/'critic_rounds.json').write_text(json.dumps(rounds,indent=2))
    return tx

if __name__=='__main__':
    assert json.loads((E/'pipeline_tests.json').read_text())['all_passed'],'Offline tests must pass before APIs'
    assert json.loads((E/'assets/svg_loading_test.json').read_text())['success'],'SVG test required'
    if LEDGER.exists():raise SystemExit('Existing experiment API ledger: do not overwrite')
    start=time.monotonic()
    try:
        a1=run_generation('A1_mechanism',False)
        a2=run_generation('A2_mechanism_assets',True)
        if a2.state():critic_experiment(a2.state())
        else:(E/'groups/A3_mechanism_assets_critic/status.json').write_text(json.dumps({'success':False,'skipped':'A2 never passed full render gate'},indent=2))
    except Exception as exc:
        (E/'logs/run_error.json').write_text(json.dumps({'error_type':type(exc).__name__,'error':str(exc)},indent=2));traceback.print_exc()
    finally:
        (E/'run_summary.json').write_text(json.dumps({'elapsed_seconds':round(time.monotonic()-start,3),'api_calls':ledger(),'limits':LIMITS,'wan_enabled':False},indent=2))
        print('RUN_FINISHED',len(ledger()),flush=True)
