"""Launch one configured experiment without putting credentials on the command line."""
import os,sys,subprocess
from pathlib import Path
for line in Path('/autodl-tmp/code2biovideo/.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        k,v=line.split('=',1)
        os.environ[k]=v
os.environ.update(DEEPSEEK_THINKING='disabled',QWEN_MODEL='qwen3.8-27b')
E=Path(__file__).resolve().parent
R=E.parents[1]
os.environ['PATH']=str(Path(sys.executable).parent)+':'+os.environ['PATH']
subprocess.run([sys.executable,str(R/'generate_biology_video.py'),*sys.argv[1:]],check=True)
