"""Controlled print test: filter separate views, never the interlaced raster.

This is a test candidate, not a physically verified sharpness correction.
No camera, geometry, depth, channel order, pitch or machine settings change.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import cv2
import numpy as np
from PIL import Image, ImageCms
import tifffile

ROOT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(ROOT))
from lenticular.frames import FrameSet
from lenticular.printing import fitted_tile, channel_pattern, color_transform, to_linear, from_linear

JOB=ROOT/'outputs/studio/20261009-113404-b9f6d34d'
OLD=Path(r'C:\Users\USER\Downloads\Lenticular-50LPI-Bolgesel-20261009-113340')
SOURCE=Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')
OUT=Path(r'C:\Users\USER\Downloads')/('Lenticular-50LPI-Tasarim-Netlik-Testi-'+datetime.now().strftime('%Y%m%d-%H%M%S'))

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def prefilter(image,sigma):
    # Linear-light, one-axis, symmetric filtering cannot mix camera channels.
    return from_linear(cv2.GaussianBlur(to_linear(image),(0,1),sigma,borderType=cv2.BORDER_REFLECT_101))

def self_checks():
    flat=np.full((16,128,3),127,np.uint8)
    assert np.array_equal(prefilter(flat,2),flat)
    ystep=np.zeros_like(flat);ystep[8:]=255
    assert np.array_equal(prefilter(ystep,2),ystep),'Vertical edge was softened.'
    stripe=flat.copy();stripe[:,64]=255
    filtered=prefilter(stripe,2)
    np.testing.assert_array_equal(filtered[:,55:64],filtered[:,65:74][:,::-1])
    checker=np.tile((np.arange(128)%2*255)[None,:,None],(16,1,3)).astype(np.uint8)
    assert np.std(prefilter(checker,2)[:,8:-8])<np.std(checker[:,8:-8])*.1

def main():
    cv2.setNumThreads(2);self_checks()
    paths=[SOURCE,JOB/'prepared/depth.npy',JOB/'project.json',OLD/'Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif',OLD/'ONCE-YUZ-TESTI-6Kanal.tif']
    before={str(p):sha(p) for p in paths}
    settings=json.loads((JOB/'project.json').read_text(encoding='utf-8'))['print']|{'ne':6}
    frames=FrameSet(JOB/'render');plan=frames.plan(settings);indices=plan['source_indices']
    assert indices==[11,9,7,4,2,0]
    raster=tifffile.memmap(OLD/'Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif')
    old=tifffile.memmap(OLD/'ONCE-YUZ-TESTI-6Kanal.tif')
    width,height=raster.shape[1],raster.shape[0]
    start=round(100*1200*130/25.4/1872);stop=round(750*1200*130/25.4/1872)
    assert np.array_equal(old,raster[start:stop])
    source_pitch=frames.size[0]/(settings['width_mm']/25.4*settings['effective_lpi'])
    sigma=source_pitch/4 # Gentle trial; not a measured optical transfer function.
    pattern=channel_pattern(width,0,1,settings)[0]
    np.testing.assert_array_equal(pattern[:24],np.repeat(np.arange(6),4))
    assert np.array_equal(pattern[24:],pattern[:-24])
    transform,icc=color_transform(settings)
    corrected=np.empty_like(old);baseline=np.empty_like(old)
    comparisons={}
    OUT.mkdir(exist_ok=False)
    for channel,index in enumerate(indices):
        with frames.image(index) as im:rgba=np.asarray(im)
        alpha=rgba[:,:,3:4].astype(np.float32)/255
        pixels=np.rint(rgba[:,:,:3]*alpha+255*(1-alpha)).astype(np.uint8)
        candidate=prefilter(pixels,sigma)
        columns=np.flatnonzero(pattern==channel)
        for y in range(start,stop,128):
            rows=min(128,stop-y);relative=y-start
            baseline[relative:relative+rows,columns]=fitted_tile(pixels,width,height,y,rows,settings,columns)
            corrected[relative:relative+rows,columns]=fitted_tile(candidate,width,height,y,rows,settings,columns)
        patch=pixels[145:750,755:1165]
        changed=candidate[145:750,755:1165]
        smooth=lambda p:cv2.GaussianBlur(p.astype(np.float32),(0,1),source_pitch/3)
        comparisons[str(index)]=dict(face_mae=float(np.mean(np.abs(patch.astype(float)-changed))),
            fine_x_rms_before=float(np.sqrt(np.mean((patch-smooth(patch))**2))),
            fine_x_rms_after=float(np.sqrt(np.mean((changed-smooth(changed))**2))))
        if index==4:
            Image.fromarray(np.concatenate([patch,changed],axis=1)).save(OUT/'Kamera-Karesi-Eski-Yeni.png')
        print(f'Kanal {channel+1}/6 tamamlandi.',flush=True)
    baseline=np.asarray(ImageCms.applyTransform(Image.fromarray(baseline),transform))
    corrected=np.asarray(ImageCms.applyTransform(Image.fromarray(corrected),transform))
    assert np.array_equal(baseline,old),'Independent reconstruction did not match the delivered TIFF.'
    assert not np.array_equal(corrected,old)
    kwargs=dict(photometric='rgb',resolution=(1200,1200),resolutionunit='INCH',metadata=None,
        extratags=[(34675,'B',len(icc),icc,False)])
    candidate_path=OUT/'B-YUZ-50LPI-1200PPI-6Kanal-TASARIM-DENEMESI.tif'
    paired_path=OUT/'AB-KARSILASTIRMA-UST-ESKI-ALT-YENI-50LPI-6Kanal.tif'
    tifffile.imwrite(candidate_path,corrected,**kwargs)
    paired=np.concatenate([old,corrected],axis=0)
    tifffile.imwrite(paired_path,paired,**kwargs)
    for p,expected in ((candidate_path,corrected),(paired_path,paired)):
        actual=tifffile.memmap(p)
        assert np.array_equal(actual,expected)
        with tifffile.TiffFile(p) as f:
            assert f.pages[0].tags['XResolution'].value==(1200,1)
            assert f.pages[0].tags['YResolution'].value==(1200,1)
            assert f.pages[0].tags[34675].value==icc
    after={str(p):sha(p) for p in paths};assert before==after
    report=dict(status='controlled_design_trial_physical_pending',originals_unchanged=True,
        filter=dict(stage='separate RGB camera views before stripe selection',axis='x',linear_light=True,
            gaussian_sigma_source_px=sigma,source_pixels_per_lenticule=source_pitch,post_interlace_filter=False),
        unchanged=['depth.npy','camera positions','3.8 degree angle','nose reference','6 channel source order',
            '50 LPI pitch','1200 PPI','phase=0','stripe width=4 pixels','print orientation','all machine/RIP settings'],
        source_indices=indices,baseline_reconstruction_exact=True,saved_pixels_exact=True,
        paired_size_mm=[width/1200*25.4,len(paired)/1200*25.4],single_size_mm=[width/1200*25.4,len(old)/1200*25.4],
        comparisons=comparisons,protected_hashes=before,
        files={p.name:sha(p) for p in (candidate_path,paired_path)},physical_sharpness_verified=False,
        limitations=['Gaussian is a trial anti-alias filter, not measured lens compensation.',
            'Less grain may trade some lateral fine detail; compare physical samples before adoption.',
            'No optical sharpness or physical depth guarantee; known-good printer/RIP settings unchanged.'])
    (OUT/'Denetim.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(output=str(OUT),report=report['status'],size_mm=report['paired_size_mm']),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
