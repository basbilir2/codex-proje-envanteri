"""Local effect generation; no depth inference or Blender dependency."""
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .interpolation import MotionInterpolator, MeshMorph, linear, encoded
from .runner import digest


VERSION = 1
DEFAULTS = dict(mode='motion', engine='rife', nt=24, long_edge=1024,
    pingpong=False, easing='linear', points=[], weights=[], preview_fps=12,
    zoom_start=1., zoom_end=1.3, anchor_x=.5, anchor_y=.5, device='0')


def validate(values):
    if not isinstance(values,dict) or set(values)-set(DEFAULTS):
        raise ValueError('Animasyon ayarlarında bilinmeyen alan var.')
    result = DEFAULTS | values
    for key, limits in dict(nt=(2,256),long_edge=(64,4096),preview_fps=(1,60)).items():
        if type(result[key]) is not int or not limits[0]<=result[key]<=limits[1]:
            raise ValueError(f'{key} ayarı {limits[0]}–{limits[1]} arasında tam sayı olmalı.')
    for key, bounds in dict(zoom_start=(1,8),zoom_end=(1,8),anchor_x=(0,1),anchor_y=(0,1)).items():
        v = result[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not bounds[0]<=v<=bounds[1]:
            raise ValueError(f'{key} ayarı geçersiz.')
    if result['mode'] not in ('motion','morph','flip','sequence','zoom','dissolve') or result['engine'] not in ('rife','flow'):
        raise ValueError('Animasyon türü/motoru geçersiz.')
    if result['easing'] not in ('linear','smoothstep') or type(result['pingpong']) is not bool or result['device'] not in ('0','-1'):
        raise ValueError('Animasyon yönü, zaman eğrisi veya cihaz geçersiz.')
    if not isinstance(result['points'],list) or len(result['points'])>100:
        raise ValueError('Morph için en fazla 100 nokta kullanılabilir.')
    for row in result['points']:
        if not isinstance(row,list) or len(row)!=4 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1 for x in row):
            raise ValueError('Morph noktaları [Ax,Ay,Bx,By] biçiminde 0–1 arasında olmalı.')
    if not isinstance(result['weights'],list) or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0 for x in result['weights']):
        raise ValueError('Flip payları pozitif sayılardan oluşmalı.')
    if result['mode']=='flip' and result['pingpong']:
        raise ValueError('Flip bekleme paylarıyla ileri/geri birlikte kullanılamaz.')
    return result


def rife_paths():
    folder = Path(__file__).resolve().parents[1]/'.deps/rife-ncnn-vulkan-20221029/rife-ncnn-vulkan-20221029-windows'
    return folder/'rife-ncnn-vulkan.exe', folder/'rife-v4.6'


def capabilities():
    executable, model = rife_paths()
    return dict(rife=executable.is_file() and (model/'flownet.bin').is_file(),
        flow=True, morph=True, modes=['motion','morph','flip','sequence','zoom','dissolve'])


class RifeInterpolator:
    def __init__(self,a,b,folder,device,checkpoint):
        self.a,self.b,self.folder,self.device,self.checkpoint = a,b,folder,device,checkpoint
        self.executable,self.model = rife_paths()
        if not capabilities()['rife']:
            raise ValueError('RIFE motoru kurulu değil. Hareket motorunda Optik akış seçin veya yerel RIFE kurulumunu tamamlayın.')
        self.inputs = folder/'rife-input'
        self.inputs.mkdir()
        Image.fromarray(a).save(self.inputs/'a.png')
        Image.fromarray(b).save(self.inputs/'b.png')
        self.counter = 0
        self.quality = dict(method='RIFE-4.6-ncnn', uncertain_fraction=None,
            model_sha256=digest(self.model/'flownet.bin'),runtime_sha256=digest(self.executable),
            release='20221029', device=device, license='MIT',
            source='https://github.com/nihui/rife-ncnn-vulkan',
            archive_sha256='D8E4D772D26CD8006EF0AD0BC82EB191B53C68677D1AE2F42506D74CBBBEA606',
            warnings=['RIFE ara pikselleri tahmin eder; yüz, yazı ve örtüşen kenarları önizlemede kontrol edin.'])

    def frame(self,t):
        if t==0 or np.array_equal(self.a,self.b):
            return self.a.copy()
        if t==1:
            return self.b.copy()
        self.counter += 1
        target = self.inputs/f'intermediate_{self.counter:04d}.png'
        # The Windows runtime calls setlocale(LC_ALL, "") before _wtof.
        # Its decimal separator follows the user's Windows locale, not Python's C locale.
        timestep = str(t)
        import os
        if os.name == 'nt':
            import ctypes
            separator = ctypes.create_unicode_buffer(8)
            if not ctypes.windll.kernel32.GetLocaleInfoEx(None,0x0000000E,separator,len(separator)):
                raise ValueError('Windows sayı biçimi okunamadı.')
            timestep = timestep.replace('.',separator.value)
        args = [str(self.executable),'-0',str(self.inputs/'a.png'),'-1',str(self.inputs/'b.png'),
            '-o',str(target),'-m',self.model.name,'-s',timestep,'-g',self.device,'-j','1:1:1']
        with (self.inputs/f'run_{self.counter:04d}.log').open('wb') as log:
            process = subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,cwd=self.executable.parent,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            started = time.monotonic()
            try:
                while process.poll() is None:
                    self.checkpoint()
                    if time.monotonic()-started > 600:
                        raise ValueError('RIFE ara kare işlemi zaman sınırını aştı; daha düşük çözünürlük veya Optik akış seçin.')
                    time.sleep(.2)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait()
        if process.returncode or not target.is_file():
            detail=(self.inputs/f'run_{self.counter:04d}.log').read_text(encoding='utf-8',errors='replace')[-1500:]
            raise ValueError(f'RIFE çalışamadı (kod {process.returncode}). Cihazı CPU olarak seçin veya Optik akış kullanın. {detail}')
        with Image.open(target) as image:
            if image.size != (self.a.shape[1],self.a.shape[0]):
                raise ValueError('RIFE çıktı boyutu kaynakla uyuşmuyor.')
            return np.asarray(image.convert('RGB'))


def cache_key(assets,spec):
    content = dict(version=VERSION,sources=[a['sha256'] for a in assets],
        effect={k:v for k,v in spec.items() if k!='preview_fps'})
    if spec['mode']=='motion' and spec['engine']=='rife':
        executable, model = rife_paths()
        content['rife'] = [digest(executable),digest(model/'flownet.bin')] if executable.is_file() and (model/'flownet.bin').is_file() else None
    return hashlib.sha256(json.dumps(content,sort_keys=True,allow_nan=False).encode()).hexdigest()


def generate(assets,folder,spec,checkpoint=lambda *a:None):
    spec=validate(spec); folder=Path(folder)
    mode=spec['mode']
    if len(assets)>256 or not assets or (mode!='zoom' and len(assets)<2):
        raise ValueError('Animasyon için 2–256 fotoğraf, zoom için en az bir fotoğraf seçin.')
    if mode in ('motion','morph','dissolve') and len(assets)!=2:
        raise ValueError('Hareket ve morph için tam iki fotoğraf seçin.')
    if mode=='zoom' and len(assets)!=1:
        raise ValueError('Zoom için tek fotoğraf seçin.')
    if folder.exists():
        raise ValueError('Animasyon yeni çalışma klasöründe üretilmeli.')
    folder.mkdir(parents=True); views=folder/'views'; views.mkdir()
    first=assets[0]['size']; scale=min(1,spec['long_edge']/max(first))
    size=(max(16,round(first[0]*scale)),max(16,round(first[1]*scale)))
    images=[]; framing=[]
    def load_image(asset):
        with Image.open(asset['photo']) as source:
            rgba=ImageOps.pad(source.convert('RGBA'),size,method=Image.Resampling.LANCZOS,color=(255,255,255,255))
            background=Image.new('RGBA',size,'white'); background.alpha_composite(rgba)
            return np.asarray(background.convert('RGB'))
    for asset in assets:
        checkpoint()
        path=Path(asset['photo'])
        if digest(path)!=asset['sha256']:
            raise ValueError('Kaynak fotoğrafın hash değeri değişmiş.')
        if mode not in ('flip','sequence'):
            images.append(load_image(asset))
        framing.append(dict(asset_id=asset['id'],source_size=asset['size'],fit='contain',canvas=list(size)))
    warnings=[]
    if any(a['size']!=assets[0]['size'] for a in assets):
        warnings.append('Kaynaklar farklı boyutta; ortak tuvalde tamamı korunarak beyaz kenar eklenmiştir.')
    quality=dict(method=mode,warnings=[])
    interpolator=None
    if mode=='motion':
        interpolator = RifeInterpolator(images[0],images[1],folder,spec['device'],checkpoint) if spec['engine']=='rife' else MotionInterpolator(*images)
    elif mode=='morph':
        interpolator=MeshMorph(images[0],images[1],spec['points'])
    if interpolator:
        quality=interpolator.quality; warnings.extend(quality['warnings'])
    times=np.linspace(0,1,spec['nt']) if mode not in ('flip','sequence') else np.linspace(0,1,len(assets))
    if spec['easing']=='smoothstep':
        times=times*times*(3-2*times)
    records=[]
    for index,t in enumerate(times):
        checkpoint(f'Ara kare hazırlanıyor: {index+1}/{len(times)}',round(10+55*index/len(times)))
        if interpolator:
            rgb=interpolator.frame(float(t))
        elif mode in ('flip','sequence'):
            rgb=load_image(assets[index])
        elif mode=='dissolve':
            rgb=images[0] if t==0 else images[1] if t==1 else encoded((1-t)*linear(images[0])+t*linear(images[1]))
        else:
            zoom=(1-t)*spec['zoom_start']+t*spec['zoom_end']
            w,h=size; x=(w-1)*spec['anchor_x']; y=(h-1)*spec['anchor_y']
            rgb=cv2.warpAffine(images[0],np.float32([[zoom,0,x*(1-zoom)],[0,zoom,y*(1-zoom)]]),size,flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
        target=views/f'view_{index:04d}.png'; Image.fromarray(rgb).save(target)
        records.append(dict(path=f'views/{target.name}',sha256=digest(target),source_t=float(t),
            time_s=float(index),generated=bool(mode not in ('flip','sequence') and 0<t<1)))
    if spec['pingpong']:
        for src in list(records)[-2:0:-1]:
            index=len(records); target=views/f'view_{index:04d}.png'
            # Reuse exact pixels; no new inference on the return path.
            import shutil
            shutil.copyfile(folder/src['path'],target)
            records.append(src|dict(path=f'views/{target.name}',time_s=float(index)))
    Image.open(folder/records[len(records)//2]['path']).save(folder/'center.png')
    data=dict(schema_version=1,kind='time_sequence',size=list(size),ns=len(assets),nt=len(records),
        nr=None,mode=mode,engine=quality.get('method',mode),engine_version=VERSION,
        effect=spec,sources=[dict(id=a['id'],sha256=a['sha256']) for a in assets],framing=framing,
        frames=records,quality=quality,warnings=warnings,color_space='sRGB',alpha='opaque')
    if mode=='flip':
        weights=spec['weights'] or [1]*len(records)
        if len(weights)!=len(records):
            raise ValueError('Flip payı sayısı fotoğraf sayısına eşit olmalı.')
        data['weights']=weights
    preview(folder,data,spec['preview_fps'])
    checkpoint()
    temporary=folder/'frameset.json.tmp'; temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(folder/'frameset.json')
    return data


def preview(folder,data,fps):
    frames=[]
    edge=min(640,max(64,int(math.sqrt(24*1024*1024/(3*len(data['frames']))))))
    for record in data['frames']:
        with Image.open(Path(folder)/record['path']) as image:
            image=image.convert('RGB'); image.thumbnail((edge,edge)); frames.append(image)
    frames[0].save(Path(folder)/'look-around.png',save_all=True,append_images=frames[1:],
        duration=round(1000/fps),loop=0,disposal=0,blend=0)
