import sys,os,json,subprocess,ast,shutil
from pathlib import Path
E=Path(__file__).resolve().parent
R=E.parents[1]
sys.path[:0]=[str(R/'src'),str(R)]
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1);os.environ[k]=v
from agent import TeachingVideoAgent,RunConfig
from gpt_request import request_deepseek_token
i=int(sys.argv[1]);dest=E/'comparison_videos'/('T%02d'%(i+1));dest.mkdir(parents=True,exist_ok=True)
topic=json.loads((E/'assignments.json').read_text())[i]
os.environ.update(DEEPSEEK_THINKING='disabled',CODE2VIDEO_AUDIT_DIR=str(dest/'api'))
def api(prompt,**kw):
    if len(list((E/'comparison_videos').glob('*/api/*.prompt.txt')))>=10:raise RuntimeError('baseline budget exhausted')
    return request_deepseek_token(prompt+' Produce one concise section for grades 10–12 totaling 24 seconds, with clear English on-screen text.',max_tokens=min(7000,kw.get('max_tokens',7000)),max_retries=1)
try:
    (dest/'assets').mkdir(exist_ok=True);(dest/'json_files').mkdir(exist_ok=True)
    (dest/'json_files/long_video_ref_mapping.json').write_text('{}')
    a=TeachingVideoAgent(i,topic,folder=str(dest/'CASES'),cfg=RunConfig(api=api,use_feedback=False,use_assets=False,max_regenerate_tries=1))
    a.generate_outline();a.generate_storyboard()
    clips=[]
    for n,sec in enumerate(a.sections):
        code=a.generate_section_code(sec)
        tree=ast.parse(code);name=next(x.name for x in tree.body if isinstance(x,ast.ClassDef) and any(isinstance(f,ast.FunctionDef) and f.name=='construct' for f in x.body))
        folder=dest/('section_'+str(n));folder.mkdir(exist_ok=True);(folder/'lesson.py').write_text(code)
        cp=subprocess.run([sys.executable,'/autodl-tmp/code2biovideo/sandbox_exec.py',str(folder),'manim','-ql','--disable_caching','lesson.py',name],capture_output=True,timeout=180)
        (folder/'render.log').write_bytes(cp.stdout+cp.stderr)
        if cp.returncode:raise RuntimeError('sandbox render failed')
        clips.append(next((folder/'media').rglob(name+'.mp4')))
    (dest/'concat.txt').write_text(''.join("file '"+str(c.relative_to(dest))+"'\n" for c in clips))
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','1','-i',str(dest/'concat.txt'),'-c','copy',str(dest/'video.mp4')],check=True)
    subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(dest/'video.mp4'),'-f','null','-'],check=True)
    result=dict(status='RENDERED')
except Exception as ex:
    import traceback
    result=dict(status='FAILED',reason=str(ex),traceback=traceback.format_exc()[-2000:])
(dest/'result.json').write_text(json.dumps(result))
