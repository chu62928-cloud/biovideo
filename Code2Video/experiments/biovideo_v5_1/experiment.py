import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
E=Path(__file__).resolve().parent
def execute(pair):
    group,i=pair
    name,topic=json.loads((E/'protocol.json').read_text())['dev'][i]
    cache=E.parent/'biovideo_v5'/'tasks'/f'T0{i+1}'/'evidence.json'
    with (E/f'{group}_{name}.log').open('w') as output:
        subprocess.run([sys.executable,str(E/'launch.py'),'--request',topic,'--output',str(E/'tasks'/group/name),'--workflow','fixed' if group=='G1' else 'agent','--budget','8','--evidence-cache',str(cache)],stdout=output,stderr=subprocess.STDOUT)
if __name__=='__main__':
    pairs=[(g,i) for g in ('G1','G2') for i in range(2)]
    with ThreadPoolExecutor(2) as pool:list(pool.map(execute,pairs))
