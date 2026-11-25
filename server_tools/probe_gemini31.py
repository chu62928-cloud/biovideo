from pathlib import Path
import sys,os,json,base64,time
R=Path('/autodl-tmp/code2biovideo').resolve();REPO=R/'Code2Video'
sys.path.insert(0,str(REPO/'src'))
from openai import OpenAI
from agent import Section
from prompts import get_prompt4_layout_feedback
from scope_refine import GridPositionExtractor
env=dict(l.split('=',1) for l in (R/'.critic.env').read_text().splitlines())
OUT=REPO/'experiments/gemini31_critic_probe';OUT.mkdir(parents=True,exist_ok=True)
CASE=REPO/'src/CASES/B2_dna_deepseek_nonthinking/0-DNA_replication_in_eukaryotic_cells'
sec=json.loads((CASE/'storyboard.json').read_text())['sections'][0]
section=Section(id=sec['id'],title=sec['title'],lecture_lines=sec['lecture_lines'],animations=sec['animations'])
ex=GridPositionExtractor()
prompt=get_prompt4_layout_feedback(section,ex.generate_position_table(ex.extract_grid_positions((CASE/'section_1.py').read_text())))
(OUT/'critic_original_prompt.txt').write_text(prompt)
client=OpenAI(api_key=env['CRITIC_API_KEY'],base_url=env['CRITIC_BASE_URL'],max_retries=0,timeout=120)
grid=REPO/'experiments/gemini3_critic_probe/GRID_upstream.png'
video=CASE/'media/videos/section_1/480p15/Section1Scene.mp4'
def dataurl(p,mime):return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
def request(mode):
    target=OUT/(mode+'_metrics.json')
    if target.exists():raise RuntimeError('Probe already recorded; do not overwrite')
    content=[{'type':'text','text':prompt}]
    if mode=='original_video':
        content.append({'type':'image_url','image_url':{'url':dataurl(video,'video/mp4'),'detail':'high'},'media_type':'video/mp4'})
    else:
        for percent in [25,65,90]:
            frame=REPO/f'experiments/biology_baseline/previews/B2_dna_deepseek_nonthinking/section_1_{percent}.png'
            content.append({'type':'image_url','image_url':{'url':dataurl(frame,'image/png'),'detail':'high'}})
    content.append({'type':'image_url','image_url':{'url':dataurl(grid,'image/png'),'detail':'high'},'media_type':'image/png'})
    record={'mode':mode,'requested_model':env['CRITIC_MODEL'],'max_tokens':2500,'retries':0,
            'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    start=time.monotonic()
    try:
        response=client.chat.completions.create(model=env['CRITIC_MODEL'],messages=[{'role':'user','content':content}],max_tokens=2500)
        (OUT/(mode+'_response.json')).write_text(response.model_dump_json(indent=2))
        text=response.choices[0].message.content or ''
        from utils import extract_json_from_markdown
        record.update(status='ok',model=response.model,usage=response.usage.model_dump() if response.usage else None,finish_reason=response.choices[0].finish_reason)
        try:
            parsed=json.loads(extract_json_from_markdown(text))
            assert isinstance(parsed['layout']['has_issues'],bool)
            assert isinstance(parsed['layout']['improvements'],list)
            record.update(valid_critic_json=True,has_issues=parsed['layout']['has_issues'],improvements=len(parsed['layout']['improvements']))
            (OUT/(mode+'_feedback.json')).write_text(json.dumps(parsed,ensure_ascii=False,indent=2))
        except Exception as exc:record.update(valid_critic_json=False,parse_error=type(exc).__name__)
        print('CRITIC_RESPONSE',text,flush=True)
    except Exception as exc:
        record.update(status='error',error_type=type(exc).__name__,http_status=getattr(exc,'status_code',None))
        body=getattr(exc,'body',None)
        if body:
            clean=json.dumps(body,ensure_ascii=False).replace(env['CRITIC_API_KEY'],'[REDACTED]')
            (OUT/(mode+'_error.json')).write_text(clean)
            print('ERROR_BODY',clean[:2000],flush=True)
    finally:
        record['elapsed_seconds']=round(time.monotonic()-start,3)
        target.write_text(json.dumps(record,ensure_ascii=False,indent=2))
        print('METRICS',json.dumps(record,ensure_ascii=False),flush=True)
    return record
first=request('original_video')
if first.get('http_status') in (400,415,422):
    request('sampled_frames')
