"""Overlapping local AI depth estimates; bounded relief, no luminance displacement."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .depth import load_mono_model, predict_depth, proximity_from_depth, MODEL_REVISION

VERSION = 2
DELTA_LIMIT = .06


def surface_relief(photo, base, output):
    """Optional artistic shading relief. This is not AI-estimated geometry."""
    output=Path(output)
    if (output/'surface_delta.npy').is_file():
        return np.load(output/'surface_delta.npy',allow_pickle=False)
    image=Image.open(photo).convert('L')
    image.thumbnail((1536,1536),Image.Resampling.LANCZOS)
    gray=np.asarray(image,dtype=np.float32)/255
    coarse=cv2.resize(base,image.size,interpolation=cv2.INTER_LINEAR)
    # Remove broad lighting and sensor texture; preserve medium-sized relief.
    smooth=cv2.GaussianBlur(gray,(0,0),1.2)
    residual=smooth-cv2.GaussianBlur(smooth,(0,0),max(3,min(image.size)*.012))
    jump=cv2.dilate(coarse,np.ones((7,7),np.uint8))-cv2.erode(coarse,np.ones((7,7),np.uint8))
    delta=np.clip(residual*.25,-DELTA_LIMIT,DELTA_LIMIT)*np.clip(1-jump/.12,0,1)
    delta=cv2.resize(delta,(base.shape[1],base.shape[0]),interpolation=cv2.INTER_LINEAR).astype(np.float32)
    output.mkdir(parents=True,exist_ok=True)
    np.save(output/'surface_delta.npy',delta,allow_pickle=False)
    code=np.rint((delta/DELTA_LIMIT+1)*32767.5).astype(np.uint16)
    Image.fromarray(np.stack([(code>>8).astype(np.uint8),(code&255).astype(np.uint8),np.zeros_like(code,dtype=np.uint8)],axis=-1)).save(output/'surface_delta.png')
    return delta


def estimate_detail(photo, base, output, progress=lambda *_: None):
    output=Path(output)
    image=Image.open(photo).convert('RGB')
    image.thumbnail((1536,1536),Image.Resampling.LANCZOS)
    width,height=image.size
    coarse=cv2.resize(base,(width,height),interpolation=cv2.INTER_LINEAR)
    accum=np.zeros_like(coarse);weights=np.zeros_like(coarse)
    model=load_mono_model()
    tw,th=max(32,round(width*.5)),max(32,round(height*.5))
    xs=np.linspace(0,max(0,width-tw),3).round().astype(int)
    ys=np.linspace(0,max(0,height-th),3).round().astype(int)
    tiles=[(int(x),int(y),tw,th,False) for y in ys for x in xs]
    # Image edges only select where to ask the AI again; never become depth.
    gray=np.asarray(image.convert('L'),dtype=np.float32)/255
    texture=cv2.magnitude(cv2.Sobel(gray,cv2.CV_32F,1,0),cv2.Sobel(gray,cv2.CV_32F,0,1))
    depth_edges=cv2.magnitude(cv2.Sobel(coarse,cv2.CV_32F,1,0),cv2.Sobel(coarse,cv2.CV_32F,0,1))
    fw,fh=max(24,round(width*.28)),max(24,round(height*.28))
    candidates=[]
    for y in np.linspace(0,max(0,height-fh),5).round().astype(int):
        for x in np.linspace(0,max(0,width-fw),5).round().astype(int):
            score=float(np.mean(texture[y:y+fh,x:x+fw]))/(.015+float(np.mean(depth_edges[y:y+fh,x:x+fw])))
            candidates.append((score,int(x),int(y)))
    for _,x,y in sorted(candidates,reverse=True)[:8]:
        tiles.append((x,y,fw,fh,True))
    records=[]
    for i,(x,y,cw,ch,focused) in enumerate(tiles):
        progress(i,len(tiles))
        crop=image.crop((x,y,min(x+cw,width),min(y+ch,height)))
        _,raw=predict_depth(crop,model,504)
        try:
            local,_=proximity_from_depth(raw)
        except ValueError:
            records.append(dict(tile=i,accepted=False,reason='flat local prediction'))
            continue
        target=coarse[y:y+local.shape[0],x:x+local.shape[1]]
        # Fit relative local scale to the coarse scene, not to image brightness.
        a=cv2.resize(local,(64,64),interpolation=cv2.INTER_AREA).ravel().astype(float)
        b=cv2.resize(target,(64,64),interpolation=cv2.INTER_AREA).ravel().astype(float)
        da,db=a-a.mean(),b-b.mean()
        covariance=float(np.mean(da*db))
        correlation=covariance/max(float(np.std(a)*np.std(b)),1e-8)
        if correlation<=.05:
            records.append(dict(tile=i,accepted=False,correlation=correlation))
            continue
        scale=float(np.clip(covariance/max(float(np.mean(da*da)),1e-8),.15 if focused else .05,1.5))
        fine=(local-cv2.GaussianBlur(local,(0,0),max(2,min(local.shape)*.045)))*scale
        fine=np.clip(fine,-DELTA_LIMIT,DELTA_LIMIT)
        weight=np.maximum(.02,np.outer(np.hanning(local.shape[0]),np.hanning(local.shape[1]))).astype(np.float32)
        weight*=min(1,correlation/.5)
        if focused:
            weight*=3
        accum[y:y+local.shape[0],x:x+local.shape[1]]+=fine*weight
        weights[y:y+local.shape[0],x:x+local.shape[1]]+=weight
        records.append(dict(tile=i,accepted=True,correlation=correlation,scale=scale,focused=focused,
            box=[x/width,y/height,crop.width/width,crop.height/height]))
    del model
    if not any(r['accepted'] for r in records):
        raise ValueError('Yerel derinlik tahminleri genel haritayla uyuşmadı. Ayrıntı seçeneğini kapatıp temel haritayı kullanın.')
    delta=np.divide(accum,weights,out=np.zeros_like(accum),where=weights>0)
    delta-=cv2.GaussianBlur(delta,(0,0),max(3,min(width,height)*.025))
    # Suppress relief on coarse occlusion edges to avoid new silhouette halos.
    jump=cv2.dilate(coarse,np.ones((5,5),np.uint8))-cv2.erode(coarse,np.ones((5,5),np.uint8))
    delta*=np.clip(1-jump/.12,0,1)
    delta=np.clip(cv2.resize(delta,(base.shape[1],base.shape[0]),interpolation=cv2.INTER_LINEAR),-DELTA_LIMIT,DELTA_LIMIT)
    output.mkdir(parents=True,exist_ok=True)
    np.save(output/'detail_delta.npy',delta.astype(np.float32),allow_pickle=False)
    code=np.rint((delta/DELTA_LIMIT+1)*32767.5).astype(np.uint16)
    encoded=np.stack([(code>>8).astype(np.uint8),(code&255).astype(np.uint8),np.zeros_like(code,dtype=np.uint8)],axis=-1)
    Image.fromarray(encoded).save(output/'detail_delta.png')
    Image.fromarray(np.rint(np.clip(base+delta,0,1)*255).astype(np.uint8)).save(output/'detail_preview.png')
    report=dict(version=VERSION,model_revision=MODEL_REVISION,tiles=records,delta_limit=DELTA_LIMIT,
        delta_range=[float(delta.min()),float(delta.max())],delta_rms=float(np.sqrt(np.mean(delta**2))),
        method='9 overlapping AI regions plus 8 finer crops selected by texture/depth detail mismatch; positive affine scale; bounded residual; edge suppression',
        limitation='Estimated local relief, not recovered ground-truth geometry. No luminance-to-depth conversion.')
    (output/'metadata.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    progress(len(tiles),len(tiles))
    return delta
