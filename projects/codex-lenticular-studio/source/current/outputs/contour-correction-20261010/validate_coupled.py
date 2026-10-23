from pathlib import Path
import sys,json
from unittest.mock import patch
import numpy as np,cv2
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.runner import render
OUT=Path(__file__).resolve().parent;CACHE=OUT/'rejected-global-slices';T=OUT/'coupled'
job=json.loads((CACHE/'job.json').read_text());report=json.loads((CACHE/'repair.json').read_text())
config=job['config']|dict(nr=2,positions=[job['config']['positions'][0],job['config']['positions'][-1]])
calls=[]
def cached_prediction(rgb,mask,max_edge=1024):
    i=len(calls);pad=report['layers'][i]['texture_padding_px']
    with Image.open(CACHE/f'layer_{i+1:02d}_mask.png') as im:hidden=np.asarray(im)>0
    expected=cv2.dilate(hidden.astype(np.uint8),np.ones((15,15),np.uint8))>0
    if pad:expected=np.pad(expected,((pad,pad),(pad,pad)),constant_values=True)
    np.testing.assert_array_equal(mask,expected)
    with Image.open(CACHE/f'layer_{i:02d}.png') as im:prediction=np.asarray(im.convert('RGB')).copy()
    assert prediction.shape==rgb.shape
    calls.append(i)
    print('Verified shared completion reused',i,flush=True)
    return prediction,report['layers'][i]['completion']|dict(reused_identical_model_input=True)
with patch('lenticular.restoration.complete_color',side_effect=cached_prediction):
    render(CACHE/'source.png',CACHE/'depth_proximity.npy',T,config,repair=dict(enabled=True,layers=3,quality='advanced'))
print('Coupled endpoint validation ready',flush=True)
