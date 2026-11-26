from pathlib import Path
import sys,os,json,hashlib
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;sys.path.insert(0,str(R/'src'))
from biology_expert.providers import ModelGateway,parse_json
from biology_expert.contracts import write,digest
from video_generation.providers import Wan3Provider,SeedanceProvider
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
 if '=' in line and not line.startswith('#'):
  k,v=line.split('=',1);os.environ[k]=v
G=ModelGateway(E/'visual_logs',{'deepseek':3,'qwen':0})
model=json.loads((E/'inputs/mitosis/original.json').read_text())['model'];evidence=json.loads((E/'inputs/mitosis/evidence.json').read_text())
# Actual retrieved figure metadata used as internal visual RAG references, no uploads.
refs=[]
for e in evidence:
 for f in e.get('figures',[]):refs.append({'reference_url':f['url'],'source_url':e['url'],'institution':e.get('author_or_institution'),'caption':f.get('caption'),'scientific_review':'CAPTION_ONLY_NOT_PIXEL_REVIEWED','license':'UNVERIFIED','actual_use':'internal caption-based visual design only','uploaded':False})
prompt='Keep output VERY COMPACT under1800 tokens total. Do not repeat original model or all source captions. Generate provider-neutral scientific_process_specification and visual_design_specification, plus scientific_prompt,visual_prompt,negative_constraints,combined_prompt. Return one JSON. Use approved typed model and actually retrieved visual-reference captions. NO Manim frames/geometry, no hardcoded prewritten theme prompt. Visual style professional high-school biological animation, clear scientific shapes rather than abstract circle diagram, fixed or limited camera, no rendered text; appropriate scientific simplifications explicit. Preserve original model events and identities; no invented molecular chemistry. References license unverified: do not upload or reproduce external images, form original visual design from descriptions only. Output references with exact original URLs, license status and actual use. scientific_prompt restricts mechanism; visual_prompt grants only stylistic degrees of freedom; negative constraints prohibit identities/count/causal violations. Combined prompt under3000chars. No validated=true. '
outfile=E/'visual_design.json'
if not outfile.exists():
 out=parse_json(G.request('deepseek','model_to_science_visual_spec',prompt+json.dumps({'typed_model':model,'retrieved_visual_references':refs},ensure_ascii=False)));out.update(typed_model_hash=digest(model),prompt_sha256=hashlib.sha256(out['combined_prompt'].encode()).hexdigest(),human_edits=[],reference_images_uploaded_to_provider=False,reference_license_status='UNVERIFIED');write(outfile,out)
out=json.loads(outfile.read_text());request={'input_mode':'text_to_video','prompt':out['combined_prompt'],'duration':5,'resolution':'480P'}
config={'model_id':'wan3.0-video','base_url':'https://ws-t97wmnhtb5p967oq.cn-beijing.maas.aliyuncs.com','region':'cn-beijing','price_cny_per_second':.3,'documentation':'https://help.aliyun.com/zh/model-studio/wan3-video-generation-api-reference'}
wan=Wan3Provider(E/'visual_dryrun/wan',config);seedance=SeedanceProvider(E/'visual_dryrun/seedance',{});write(E/'video_benchmark.json',{'runs':[{'provider':'wan','model_id':config['model_id'],'input_mode':'text_to_video','task_id':None,'status':'NOT_EXECUTED','scientific_model_hash':digest(model),'prompt_sha256':out['prompt_sha256'],'video_sha256':None,'actual_duration':None,'science_review':'NOT_MEASURED','visual_review':'NOT_MEASURED','actual_cost':None,'failure_reason':'New experiment paid generation not authorized','dry_run':wan.submit(request,dry_run=True)},{'provider':'seedance','model_id':None,'input_mode':'NOT_VERIFIED','task_id':None,'status':'NOT_EXECUTED','scientific_model_hash':digest(model),'prompt_sha256':out['prompt_sha256'],'video_sha256':None,'actual_duration':None,'science_review':'NOT_MEASURED','visual_review':'NOT_MEASURED','actual_cost':None,'failure_reason':'No configured exact model/API key and no paid authorization; not a working full adapter','dry_run':seedance.submit(request,dry_run=True)}]})
print('VISUAL_DRYRUN_COMPLETE',flush=True)
