"""Scene diagnostics using the same geometry and print budgets as production."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .geometry import validate as geometry_settings
from .repair import editable_depth, plan_parallax
from .printing import validate as print_settings, frame_mapping
from .optics import sampling_budget, depth_sampling


def analyze_scene(photo, depth, render=None, printing=None):
    from .pipeline import render_settings
    r=render_settings(render or {})
    p=print_settings(printing or {},require_color_profile=False)
    image=photo.convert('RGB')
    d=np.asarray(depth,dtype=np.float32)
    if d.shape!=(image.height,image.width) or not np.isfinite(d).all() or d.min()<0 or d.max()>1:
        raise ValueError('Analiz derinliği fotoğrafla aynı boyutta, sonlu ve 0–1 aralığında olmalı.')
    if (r['camera_axis']=='x')!=(p['axis']=='vertical'):
        raise ValueError('Analiz için kamera yönü ile lens yönü eşleşmeli.')
    source_size=list(image.size)
    if r['render_long_edge'] and max(image.size)>r['render_long_edge']:
        image.thumbnail((r['render_long_edge'],r['render_long_edge']),Image.Resampling.LANCZOS)
        d=cv2.resize(d,image.size,interpolation=cv2.INTER_LINEAR)
    edited,edits=editable_depth(d,r,image)
    r=r|{'zero_reference':edits['zero_reference']}
    geometry,parallax,disparity=plan_parallax(edited,image.size,r)
    config=geometry_settings(dict(nr=r['nr'],camera_axis=r['camera_axis'],**geometry))
    indices=frame_mapping({'config':config},p)
    sampling,risk=depth_sampling(edited,config,image.size,p,indices)
    budget=sampling_budget(p)
    warnings=list(sampling['warnings'])
    if parallax['angle_limited']:
        warnings.append(f"Seçilen {r['angle_deg']:g}° açı korumalarla {parallax['effective_angle_deg']:.3f}° oluyor.")
    if edits['clipped_fraction']>0:
        warnings.append('Düzenleme derinlik uçlarını düzleştiriyor; yumuşak eğri veya daha düşük güç değerlendirin.')
    endpoint_fraction=float(np.mean((d<=0)|(d>=1)))
    if endpoint_fraction>.025:
        warnings.append('Derinlik haritasında uç değere yığılma var; kırpma veya düz yüzey olup olmadığını görselden kontrol edin.')
    if len(set(indices))<p['ne']:
        warnings.append('Baskı kanalları arasında tekrarlanan kamera kareleri var; yalnız kanal sayısını artırmak yeni görüş üretmez.')
    if budget['pixels_per_channel']<2:
        warnings.append('Kanal başına iki raster pikselden az var; kanal sayısı ve gerçek baskı ayrımı kontrol edilmeli.')
    for flag,label in (('pitch_verified','Pitch'),('lens_angle_verified','Lens açısı'),('raster_ppi_verified','Yazıcı/RIP kanal ayrımı')):
        if not p[flag]:warnings.append(label+' fiziksel ölçümle doğrulanmış değil.')
    # Compare at a fixed diagnostic resolution so counts do not grow with PPI.
    small=image.copy();small.thumbnail((768,768),Image.Resampling.LANCZOS)
    small_depth=cv2.resize(edited,small.size,interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(np.asarray(small),cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0)/8
    gy=cv2.Sobel(gray,cv2.CV_32F,0,1)/8
    texture_fraction=float(np.mean(np.hypot(gx,gy)>.08))
    axis=1 if r['camera_axis']=='x' else 0
    steps=np.abs(np.diff(small_depth,axis=axis))
    # These are depth-mask holes, not semantic detection of hands/hair/anatomy.
    foreground=(small_depth>edits['zero_reference']).astype(np.uint8)
    contours,hierarchy=cv2.findContours(foreground,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    holes=[]
    if hierarchy is not None:
        for contour,entry in zip(contours,hierarchy[0]):
            if entry[3]>=0 and cv2.contourArea(contour)>=4:
                x,y,w,h=cv2.boundingRect(contour)
                holes.append([x/small.width,y/small.height,w/small.width,h/small.height])
    recommendations={'render':{},'print':{}}
    if r['nr']<p['ne']:recommendations['render']['nr']=p['ne']
    if edits['clipped_fraction']>0:recommendations['render']['depth_curve']='soft'
    pitch_step=max(.0001,min(p['pitch_step'],budget['quarter_channel_pitch_error_lpi']))
    if pitch_step<p['pitch_step']:recommendations['print']['pitch_step']=float(pitch_step)
    if budget['quarter_channel_pitch_error_lpi']<.0001:
        warnings.append('Hesaplanan pitch hassasiyeti desteklenen en küçük test adımından dar; fiziksel ölçek/kanal sayısını gözden geçirin.')
    if holes:warnings.append('Derinlik maskesinde kapalı boşluk adayları var; bunlar otomatik hata veya anatomi tespiti değildir.')
    report=dict(schema_version=1,source_size=source_size,analysis_size=list(image.size),
        render_settings=r,print_settings=p,edits=edits,parallax=parallax,
        sampling_budget=budget,depth_sampling=sampling,source_indices=indices,
        details=dict(texture_edge_fraction=texture_fraction,endpoint_fraction=endpoint_fraction,
            depth_step_p99=float(np.quantile(steps,.99)) if steps.size else 0,
            hole_candidate_boxes=holes),recommendations=recommendations,warnings=warnings,
        physical_3d_verified=False,
        limitations=['Tek fotoğraf derinliği tahmindir; görünmeyen yüzeyler ölçülmez.',
            'Öneriler geometrik kontrollerdir; optik kapasite veya kusursuz baskı garantisi değildir.',
            'Sabit referans korunur; boşluklar ve anatomi otomatik değiştirilmez.'])
    risk_small=cv2.resize(risk,small.size,interpolation=cv2.INTER_AREA)
    color=np.asarray(small).copy()
    strength=np.clip(risk_small,0,1)*.65
    color=np.rint(color*(1-strength[...,None])+np.array([255,65,35])*strength[...,None]).astype(np.uint8)
    depth_image=Image.fromarray(np.rint(small_depth*255).astype(np.uint8)).convert('RGB')
    board=Image.new('RGB',(small.width*3,small.height),'white')
    board.paste(small,(0,0));board.paste(depth_image,(small.width,0));board.paste(Image.fromarray(color),(small.width*2,0))
    return report,board


def save_analysis(folder,report,diagnostic):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    (folder/'scene-analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    diagnostic.save(folder/'scene-analysis.png')
    lines=['SAHNE ANALİZİ','Görsel: solda fotoğraf, ortada kullanılan derinlik, sağda kanallar arası hareket riski.',
        f"İstenen / uygulanan açı: {report['parallax']['requested_angle_deg']:.3f}° / {report['parallax']['effective_angle_deg']:.3f}°",
        f"Kanal başına raster piksel: {report['sampling_budget']['pixels_per_channel']:.3f}",
        '','KONTROLLER',*report['warnings'],'','SINIRLAR',*report['limitations']]
    (folder/'scene-analysis.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
