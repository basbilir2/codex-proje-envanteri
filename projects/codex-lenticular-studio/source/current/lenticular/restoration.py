"""Local shared-layer completion and trimap matting. No per-view hallucination."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np

MODEL = Path(__file__).resolve().parents[1]/'.models/lama/big-lama.pt'


def linear_rgb(rgb):
    value=rgb.astype(np.float32)/255
    return np.where(value<=.04045,value/12.92,((value+.055)/1.055)**2.4)


def reconcile_matte(rgb, foreground, alpha, background, support):
    """Reconcile one matte with the background actually shown underneath it.

    The source photo must recompose at the source camera. Increase uncertain
    coverage only as much as needed to keep the recovered foreground in gamut,
    then solve I = a*F + (1-a)*B in the renderer's linear-light space. This avoids
    both erased source edges and an unmoved duplicate outline on the lower layer.
    """
    source=linear_rgb(rgb)
    difference=source-background
    minimum=np.max(np.where(difference>=0,difference/np.maximum(1-background,1e-7),
        -difference/np.maximum(background,1e-7)),axis=2)
    # The gamut bound alone is not an opacity estimate: it creates saturated,
    # weakly covered specks. Fit the color line using the matting foreground.
    direction=linear_rgb(foreground)-background
    energy=np.sum(direction**2,axis=2)
    fitted=np.sum(difference*direction,axis=2)/np.maximum(energy,1e-7)
    fitted=np.where(energy>1e-5,np.clip(fitted,0,1),alpha)
    result=alpha.copy()
    target=np.maximum(np.maximum(alpha,minimum),fitted)
    result[support]=np.ceil(np.clip(target[support],0,1)*255)/255
    changed=support&(result>alpha+1/255)
    selected=support&(result>0)
    a=result[selected,None]
    recovered=np.clip((source[selected]-(1-a)*background[selected])/a,0,1)
    srgb=np.where(recovered<=.0031308,recovered*12.92,1.055*np.maximum(recovered,0)**(1/2.4)-.055)
    color=foreground.copy();color[selected]=np.rint(np.clip(srgb,0,1)*255).astype(np.uint8)
    return result,color,dict(coverage_corrected_fraction=float(changed.mean()),
        source_consistency='linear-light foreground conditioned on completed lower surfaces')


@lru_cache(maxsize=1)
def lama_model():
    import torch
    if not MODEL.is_file():
        raise ValueError('Gelişmiş doldurma modeli eksik. setup-quality.ps1 ile kurun veya Klasik kaliteyi seçin.')
    metadata = json.loads(MODEL.with_name('provenance.json').read_text(encoding='utf-8-sig'))
    with MODEL.open('rb') as stream:
        checksum = hashlib.file_digest(stream,'sha256').hexdigest()
    if checksum != metadata['sha256']:
        raise ValueError('Doldurma modelinin dosya doğrulaması başarısız.')
    torch.set_num_threads(min(8, max(1, torch.get_num_threads())))
    return torch.jit.load(str(MODEL),map_location='cpu').eval()


def complete_color(rgb, mask, max_edge=1024):
    """Infer one shared texture; preserve every unmasked source pixel exactly."""
    import torch
    mask = np.asarray(mask,dtype=bool)
    if not np.any(mask): return rgb.copy(), dict(engine='unchanged',model_size=list(rgb.shape[1::-1]))
    if np.all(mask): raise ValueError('Arka planı tamamlamak için görünür örnek gerekli.')
    h,w = mask.shape
    scale = min(1., max_edge/max(w,h))
    size = (max(8,round(w*scale)),max(8,round(h*scale)))
    image = cv2.resize(rgb,size,interpolation=cv2.INTER_AREA) if scale < 1 else rgb
    # Any masked contribution in a reduced pixel must stay masked to avoid a silhouette leak.
    small = cv2.resize(mask.astype(np.float32),size,interpolation=cv2.INTER_AREA)>0 if scale < 1 else mask
    ph,pw = (-size[1])%8,(-size[0])%8
    image = np.pad(image,((0,ph),(0,pw),(0,0)),mode='symmetric')
    small = np.pad(small,((0,ph),(0,pw)),mode='symmetric')
    pixels = torch.from_numpy(np.ascontiguousarray(image.transpose(2,0,1))).float()[None]/255
    holes = torch.from_numpy(np.ascontiguousarray(small)).float()[None,None]
    with torch.inference_mode():
        prediction = lama_model()(pixels,holes)[0].permute(1,2,0).cpu().numpy()[:size[1],:size[0]]
    if not np.all(np.isfinite(prediction)): raise ValueError('Doldurma modeli geçersiz renk üretti.')
    prediction = cv2.resize(prediction,(w,h),interpolation=cv2.INTER_CUBIC) if scale < 1 else prediction
    output = rgb.copy()
    output[mask] = np.rint(np.clip(prediction[mask],0,1)*255).astype(np.uint8)
    return output, dict(engine='LaMa TorchScript v0.1.0 / CPU',model_size=list(size),
        estimated_fraction=float(mask.mean()),visible_pixels_unchanged=True,
        note='One shared layer for all views. Hidden content is inferred; not recovered ground truth.')


def matte(rgb, mask, tile_size=384):
    """Full-resolution closed-form alpha and foreground color in overlapping tiles."""
    from pymatting import estimate_alpha_cf, estimate_foreground_ml
    mask = mask.astype(bool)
    band = max(2,min(12,round(min(mask.shape)*.004)))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*band+1,2*band+1))
    core = cv2.erode(mask.astype(np.uint8),kernel)>0
    outer = cv2.dilate(mask.astype(np.uint8),kernel)>0
    unknown = outer & ~core
    alpha = mask.astype(np.float32)
    foreground = rgb.copy()
    if not np.any(core) or np.all(outer):
        return alpha,foreground,dict(engine='unchanged mask',unresolved_fraction=float(unknown.mean()),tiles=0)
    h,w = mask.shape
    accum = np.zeros_like(alpha); weight = np.zeros_like(alpha)
    colors = np.zeros(rgb.shape,np.float32)
    overlap = max(24,band*3)
    count = 0
    # Each tile includes a context collar, then only its center is retained.
    for y in range(0,h,tile_size):
        for x in range(0,w,tile_size):
            x1,y1=min(w,x+tile_size),min(h,y+tile_size)
            if not np.any(unknown[y:y1,x:x1]): continue
            left,top,right,bottom=max(0,x-overlap),max(0,y-overlap),min(w,x1+overlap),min(h,y1+overlap)
            sl=np.s_[top:bottom,left:right]
            inner=np.s_[y-top:y1-top,x-left:x1-left]
            if not np.any(core[sl]) or np.all(outer[sl]): continue
            trimap=np.where(core[sl],1.,np.where(outer[sl],.5,0.))
            image=rgb[sl].astype(np.float64)/255
            a=estimate_alpha_cf(image,trimap,laplacian_kwargs={'epsilon':1e-7},cg_kwargs={'maxiter':2000,'rtol':1e-6})
            if not np.all(np.isfinite(a)): raise ValueError('Kenar ayrımı geçersiz alfa üretti.')
            f=estimate_foreground_ml(image,a)
            # Preserve opaque source colors; unmix only the uncertain edge band.
            a=np.clip(a,0,1); f=np.clip(f,0,1)
            keep=unknown[y:y1,x:x1]
            accum[y:y1,x:x1][keep]=a[inner][keep]
            colors[y:y1,x:x1][keep]=f[inner][keep]
            weight[y:y1,x:x1][keep]=1
            count+=1
    solved=weight>0
    alpha[solved]=accum[solved]
    foreground[solved]=np.rint(colors[solved]*255).astype(np.uint8)
    return alpha,foreground,dict(engine='PyMatting closed-form alpha + multilevel foreground',tiles=count,
        uncertain_fraction=float(unknown.mean()),unresolved_fraction=float(np.mean(unknown&~solved)),
        fractional_alpha_fraction=float(np.mean((alpha>0)&(alpha<1))))


def complete_depth(depth, valid, low, high, surface_mask=None):
    """Bounded harmonic hidden depth, with exact visible depth retained."""
    from .layers import extend_depth
    result=extend_depth(depth,valid)
    collar = None
    if surface_mask is not None:
        # The visible silhouette belongs to this object. Do not let hidden
        # background interpolation pull its contour towards another surface.
        band=max(2,min(12,round(min(depth.shape)*.004)))
        support=cv2.dilate(surface_mask.astype(np.uint8),np.ones((2*band+1,2*band+1),np.uint8))>0
        collar=support&~valid
        smooth=cv2.bilateralFilter(result,9,.04,4)
        edge_values=smooth[collar].copy()
    h,w=depth.shape
    scale=min(1.,512/max(h,w));size=(max(2,round(w*scale)),max(2,round(h*scale)))
    small=cv2.resize(result,size,interpolation=cv2.INTER_AREA)
    known=cv2.resize(valid.astype(np.float32),size,interpolation=cv2.INTER_AREA)>.999
    if np.any(known):
        fixed=small.copy()
        for _ in range(160):
            blurred=cv2.blur(small,(3,3),borderType=cv2.BORDER_REPLICATE)
            blurred[known]=fixed[known]
            difference=float(np.max(np.abs(blurred-small)))
            small=blurred
            if difference<1e-5: break
        inferred=cv2.resize(small,(w,h),interpolation=cv2.INTER_LINEAR)
        result[~valid]=inferred[~valid]
    if collar is not None: result[collar]=edge_values
    return np.clip(result,low,high).astype(np.float32)
