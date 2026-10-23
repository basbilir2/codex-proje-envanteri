from pathlib import Path
import sys,subprocess
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
from lenticular.runner import find_blender
WORK=Path(__file__).resolve().parent
def run(mode):
    command=[str(find_blender()),'--background','--python-exit-code','1','--python',str(WORK/'render_fresh.py'),'--',mode]
    with (WORK/f'render-{mode}.log').open('a',encoding='utf-8') as log:
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        for line in process.stdout:
            log.write(line)
            if 'FRESH_' in line:
                log.flush();print(line.strip(),flush=True)
        if process.wait():raise RuntimeError('Render failed; inspect the saved log.')
if __name__=='__main__':run(sys.argv[1])
