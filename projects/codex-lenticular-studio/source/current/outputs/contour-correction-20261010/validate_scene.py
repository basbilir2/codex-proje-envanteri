from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.runner import render
OUT=Path(__file__).resolve().parent;SRC=ROOT/'outputs/surface-upgrade-20261009-220345/native-portrait-final'
job=json.loads((SRC/'job.json').read_text());config=job['config'];positions=config['positions']
config=config|dict(nr=2,positions=[positions[0],positions[-1]])
start=time.perf_counter()
result=render(SRC/'source.png',SRC/'depth_proximity.npy',OUT/'scene',config,
    repair=dict(enabled=True,layers=3,quality='advanced',checkpoint=lambda:print('Preparing layer',flush=True)))
print('Native endpoint scene ready',round(time.perf_counter()-start,1),'seconds',flush=True)
