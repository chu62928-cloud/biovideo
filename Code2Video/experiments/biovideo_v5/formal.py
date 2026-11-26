from pathlib import Path
import json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
E=Path(__file__).resolve().parent
tasks=json.loads((E/'assignments.json').read_text())
def execute(i):
    folder=E/'tasks'/('T%02d'%(i+1))
    with (E/('formal_%s.log'%i)).open('w') as f:
        subprocess.run([sys.executable,str(E/'launch.py'),'--request',tasks[i],'--duration','24','--output',str(folder)],stdout=f,stderr=subprocess.STDOUT)
    return (folder/'video.json').exists()
with ThreadPoolExecutor(2) as pool:
    first=list(pool.map(execute,range(2)))
    if any(first):list(pool.map(execute,range(2,5)))
