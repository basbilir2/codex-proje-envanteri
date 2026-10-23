"""Versioned local projects and a serial, cancellable worker pipeline."""
from concurrent.futures import ThreadPoolExecutor, CancelledError
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import threading
import time
import uuid

import numpy as np
from PIL import Image, ImageCms, ImageOps

from .depth import estimate, MODEL_REVISION
from .geometry import validate as validate_render, read_depth
from .printing import DEFAULTS as PRINT_DEFAULTS, validate as validate_print, encode, pitch_test, registration, mixing_matrix,color_transform
from .repair import editable_depth, plan_parallax, save_parallax_map
from .runner import digest, render
from .animation import DEFAULTS as ANIMATION_DEFAULTS, VERSION as ANIMATION_VERSION, validate as validate_animation, generate as generate_animation, cache_key as animation_key, capabilities
from .frames import FrameSet


RENDER_DEFAULTS = dict(nr=12, angle_deg=.8, effect_strength=1.0, zero_reference=.5,
    depth_smoothing=.25, depth_strokes=[], grid_size=384, repair=True, layers=3,
    inpaint_radius=5.0, process_res=504, render_long_edge=512,
    depth_curve="soft",front_strength=1.0,back_strength=1.0,edge_refinement=.35,
    parallax_guard=True,max_parallax_percent=3.0,edge_guard=True)
RENDER_DEFAULTS["camera_axis"] = "x"
RENDER_DEFAULTS.update(depth_black=0.0, depth_white=1.0, depth_gamma=1.0)
RENDER_DEFAULTS.update(detail_enabled=False,detail_strength=1.0,surface_strength=0.0)
RENDER_ENGINE_VERSION = 15


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    # Windows readers/antivirus may briefly deny replacement of an open file.
    for attempt in range(20):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt==19:
                raise
            time.sleep(.1)


def render_settings(settings):
    if not isinstance(settings, dict) or set(settings)-set(RENDER_DEFAULTS):
        raise ValueError("Görünüş ayarları geçersiz.")
    result = RENDER_DEFAULTS | settings
    for key,limits in dict(depth_black=(0,.95),depth_white=(.05,1),depth_gamma=(.25,4),surface_strength=(-1,1)).items():
        v=result[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not limits[0]<=v<=limits[1]:
            raise ValueError(f"{key} ayarı geçersiz.")
    if type(result["detail_enabled"]) is not bool or isinstance(result["detail_strength"],bool) or not isinstance(result["detail_strength"],(int,float)) or not math.isfinite(result["detail_strength"]) or not 0<=result["detail_strength"]<=2:
        raise ValueError("Ayrıntılı derinlik ayarı geçersiz.")
    if result["depth_white"]-result["depth_black"]<.01-1e-9:
        raise ValueError("Beyaz derinlik sınırı siyah sınırdan en az 0.01 büyük olmalı.")
    for key, limits in dict(angle_deg=(0,30),effect_strength=(0,3),zero_reference=(0,1),depth_smoothing=(0,1),inpaint_radius=(1,20),front_strength=(0,2),back_strength=(0,2),edge_refinement=(0,1),max_parallax_percent=(.1,15)).items():
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value) or not limits[0] <= value <= limits[1]:
            raise ValueError(f"{key} ayarı geçersiz.")
    for key, limits in dict(nr=(2,256),grid_size=(32,2048),layers=(1,8),process_res=(140,1008),render_long_edge=(0,8192)).items():
        if type(result[key]) is not int or not limits[0] <= result[key] <= limits[1]:
            raise ValueError(f"{key} ayarı geçersiz.")
    if type(result["repair"]) is not bool or not isinstance(result["depth_strokes"],list):
        raise ValueError("Arka plan veya fırça ayarı geçersiz.")
    if len(result["depth_strokes"])>10000:
        raise ValueError("En fazla 10000 fırça noktası kullanılabilir.")
    for stroke in result["depth_strokes"]:
        for key,limits in dict(x=(0,1),y=(0,1),radius=(.00001,.5),value=(0,1),strength=(0,1)).items():
            value = stroke.get(key) if isinstance(stroke,dict) else None
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not limits[0]<=value<=limits[1]:
                raise ValueError("Derinlik fırça kaydı geçersiz.")
    if result["camera_axis"] not in ("x","y"):
        raise ValueError("Kamera yönü x veya y olmalı.")
    if result["depth_curve"] not in ("linear","soft") or type(result["parallax_guard"]) is not bool or type(result["edge_guard"]) is not bool:
        raise ValueError("Derinlik eğrisi veya paralaks sınırlaması geçersiz.")
    return result


class Studio:
    def __init__(self, root):
        self.root = Path(root).resolve()
        if "sources" in (p.lower() for p in self.root.parts):
            raise ValueError("Uygulama sources altında çalışamaz.")
        self.local = self.root/".studio"
        self.local.mkdir(exist_ok=True)
        self.state_path = self.local/"state.json"
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="lenticular")
        self.cancellations = {}
        self.state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else dict(schema_version=1, assets={}, jobs={}, profiles={})
        for job in self.state["jobs"].values():
            if job["status"] in ("queued","running","cancel_requested"):
                job.update(status="interrupted",message="Önceki çalışma kapatılırken durdu; yeni iş başlatabilirsiniz.")
        self.seed()
        self.save()

    def save(self):
        with self.lock:
            write_json(self.state_path, self.state)

    def seed(self):
        folder = self.root/"outputs/wedding/depth"
        if not self.state["assets"] and (folder/"photo.png").is_file():
            photo = folder/"photo.png"
            self.state["assets"]["wedding"] = dict(id="wedding",name="Düğün fotoğrafı", photo=str(photo),
                original=str(folder/"original.png"),sha256=digest(photo),size=list(Image.open(photo).size),
                depth_folder=str(folder),created=now())
            result = self.root/"outputs/wedding/render"
            if (result/"job.json").is_file():
                self.state["jobs"]["initial"] = dict(id="initial",asset_id="wedding",stage="render",
                    status="complete",message="İlk 12 görünüş; arka plan düzeltmesi henüz uygulanmadı.",
                    progress=100,created=now(),output=str(result.parent),render_folder=str(result),
                    render=RENDER_DEFAULTS|{"nr":12},print=PRINT_DEFAULTS.copy(),warnings=[])

    def snapshot(self):
        with self.lock:
            data = json.loads(json.dumps(self.state))
        data["defaults"] = {"render":RENDER_DEFAULTS,"print":PRINT_DEFAULTS,"animation":ANIMATION_DEFAULTS}
        data['animation_capabilities'] = capabilities()
        data["engines"] = {"depth":"DA3MONO-LARGE · yerel CPU", "scene":"Blender · 2.5D",
            "repair":"Ayrık derinlik katmanları · kenar maskesi · Telea", "print":"Lenticular raster + ICC TIFF"}
        data['engines']['animation'] = 'Yerel RIFE · optik akış · noktalı morph · flip/sekans/zoom'
        for asset in data["assets"].values():
            asset["photo_url"] = self.file_url(asset["photo"])
            folder = Path(asset.get("depth_folder", ""))
            if (folder/"depth_preview.png").is_file():
                asset["depth_url"] = self.file_url(folder/"depth_preview.png")
            detail=Path(asset.get("detail_folder",""))
            if asset.get("detail_source_folder")==asset.get("depth_folder") and (detail/"detail_delta.png").is_file():
                asset["detail_delta_url"]=self.file_url(detail/"detail_delta.png")
                asset["detail_delta_limit"]=.06
                if (detail/"surface_delta.png").is_file():
                    asset["surface_delta_url"]=self.file_url(detail/"surface_delta.png")
        for job in data["jobs"].values():
            job["files"] = {}
            output = Path(job["output"])
            for key, relative in dict(scene="render/scene.blend",preview="render/look-around.png",center="render/center.png",
                depth="prepared/depth.png",detail_depth="prepared/depth_detail.png",base_depth="prepared/depth_base.png",parallax="prepared/parallax.png",quality="quality.json",handoff="print/baski-notlari.txt",interlaced="print/interlaced.tif",pitch="print/pitch-test.tif",
                report="print/print-report.json",white="print/white-underbase.tif",registration="print/registration.svg",
                proof="print/lens-proof.png",comparison="print/ghosting-comparison.png",project="project.json",response="print/lens-response-test.tif",matrix_template="print/lens-response-template.json").items():
                candidate = output/relative
                if candidate.is_file():
                    job["files"][key] = self.file_url(candidate)
            if job.get('frames_folder'):
                folder = Path(job['frames_folder'])
                if job.get('status')=='complete' and (folder/'frameset.json').is_file():
                    manifest = json.loads((folder/'frameset.json').read_text(encoding='utf-8'))
                    job['view_count'] = len(manifest['frames'])
                    job['view_base'] = self.file_url(folder/'views')
                    job['nt'] = len(manifest['frames'])
                    for key,relative in dict(preview='look-around.png',frameset='frameset.json',center='center.png').items():
                        job['files'][key] = self.file_url(folder/relative)
                for key,relative in dict(channel_plan='print/channel-plan.json').items():
                    candidate=output/relative
                    if candidate.is_file() and job.get('status')=='complete':
                        job['files'][key]=self.file_url(candidate)
            if job.get("render_folder"):
                for key, relative in dict(scene="scene.blend",preview="look-around.png",center="center.png").items():
                    candidate = Path(job["render_folder"])/relative
                    if candidate.is_file():
                        job["files"][key] = self.file_url(candidate)
                try:
                    job["view_count"] = json.loads((Path(job["render_folder"])/"job.json").read_text(encoding="utf-8"))["config"]["nr"]
                    job["view_base"] = self.file_url(Path(job["render_folder"])/"views")
                except (OSError,ValueError):
                    job["status"],job["message"] = "missing","Bu çalışmanın render dosyaları bulunamıyor."
                for key,relative in dict(parallax="prepared/parallax.png",quality="quality.json").items():
                    candidate = Path(job["render_folder"]).parent/relative
                    if candidate.is_file():
                        job["files"][key] = self.file_url(candidate)
        return data

    def file_url(self, path):
        from urllib.parse import quote
        path = Path(path).resolve()
        for name, parent in (("local",self.local),("outputs",self.root/"outputs")):
            if path.is_relative_to(parent.resolve()):
                return "/files/"+name+"/"+quote(path.relative_to(parent).as_posix())
        raise ValueError("Uygulama dışındaki dosya sunulamaz.")

    def add_photo(self, data, name):
        checksum = hashlib.sha256(data).hexdigest()
        with self.lock:
            for asset in self.state["assets"].values():
                original = Path(asset.get("original",""))
                existing = asset.get("original_sha256")
                if existing is None and original.is_file():
                    existing = digest(original)
                    asset["original_sha256"] = existing
                if existing == checksum:
                    self.save()
                    return asset
        identifier = uuid.uuid4().hex[:16]
        folder = self.local/"assets"/identifier
        folder.mkdir(parents=True)
        suffix = Path(name).suffix.lower()
        if suffix not in (".png",".jpg",".jpeg",".tif",".tiff",".webp",".bmp"):
            raise ValueError("PNG, JPEG, TIFF, WebP veya BMP fotoğraf seçin.")
        original = folder/("original"+suffix)
        original.write_bytes(data)
        with Image.open(original) as source:
            if source.width*source.height > 100_000_000:
                raise ValueError("Fotoğraf 100 megapikseli aşamaz.")
            source = ImageOps.exif_transpose(source)
            alpha = source.convert("RGBA").getchannel("A")
            if source.info.get("icc_profile"):
                import io
                profile = ImageCms.ImageCmsProfile(io.BytesIO(source.info["icc_profile"]))
                source = ImageCms.profileToProfile(source, profile, ImageCms.createProfile("sRGB"), outputMode="RGB")
            elif source.mode == "CMYK":
                raise ValueError("CMYK fotoğraf ICC profili içermiyor; sRGB olarak dışa aktarın.")
            source = source.convert("RGBA")
            source.putalpha(alpha)
            photo = folder/"photo.png"
            source.save(photo)
        asset = dict(id=identifier,name=Path(name).name,photo=str(photo),original=str(original),
            sha256=digest(photo),original_sha256=digest(original),size=list(source.size),created=now())
        with self.lock:
            self.state["assets"][identifier] = asset
            self.save()
        return asset

    def add_depth(self, identifier, data, name, convention="white-near"):
        with self.lock:
            asset = self.state["assets"][identifier]
        if convention not in ("white-near","black-near"):
            raise ValueError("Depth yönü geçersiz.")
        suffix = Path(name).suffix.lower()
        if suffix not in (".png",".tif",".tiff",".npy"):
            raise ValueError("Depth PNG, TIFF veya NPY olmalı.")
        folder = self.local/"depth"/(identifier+"_"+uuid.uuid4().hex[:8])
        folder.mkdir(parents=True)
        source = folder/("supplied"+suffix)
        source.write_bytes(data)
        depth = read_depth(source, tuple(asset["size"]), convention)
        np.save(folder/"depth_proximity.npy",depth,allow_pickle=False)
        Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(folder/"depth_preview.png")
        with self.lock:
            asset["depth_folder"] = str(folder)
            asset["supplied_depth"] = True
            self.save()

    def add_sequence(self, identifiers, name='Animasyon'):
        if not isinstance(identifiers,list) or not 1<=len(identifiers)<=256:
            raise ValueError('Animasyon için 1–256 kaynak fotoğraf seçin.')
        with self.lock:
            if any(not isinstance(i,str) or i not in self.state['assets'] or self.state['assets'][i].get('kind')=='sequence' for i in identifiers):
                raise ValueError('Animasyon kaynakları mevcut tek fotoğraflar olmalı.')
            sources=[self.state['assets'][i] for i in identifiers]
            checksum=hashlib.sha256(json.dumps([s['sha256'] for s in sources]).encode()).hexdigest()
            existing=next((a for a in self.state['assets'].values() if a.get('kind')=='sequence' and a.get('sha256')==checksum),None)
            if existing:
                return existing
            asset=dict(id=uuid.uuid4().hex[:16],kind='sequence',name=str(name)[:100] or 'Animasyon',
                photo=sources[0]['photo'],size=sources[0]['size'],sha256=checksum,source_ids=identifiers[:],created=now())
            self.state['assets'][asset['id']]=asset
            self.save()
            return asset

    def upload_resource(self, data, name, kind):
        folder = self.local/"resources"
        folder.mkdir(exist_ok=True)
        if kind == "icc":
            import io
            ImageCms.ImageCmsProfile(io.BytesIO(data))
            path = folder/(uuid.uuid4().hex+".icc")
            path.write_bytes(data)
            return {"path":str(path),"name":Path(name).name}
        if kind == "matrix":
            matrix = json.loads(data.decode("utf-8-sig"))
            if isinstance(matrix,dict):
                if matrix.get("template_only"):
                    raise ValueError("Bu ölçüm şablonu. Gerçek kanal yanıtlarını girip template_only alanını false yapın.")
                matrix = matrix.get("matrix",matrix.get("mixing_matrix"))
            values = np.asarray(matrix,dtype=float)
            if values.ndim != 2 or values.shape[0] != values.shape[1] or not 2 <= len(values) <= 64 or not np.isfinite(values).all() or np.any(values<0) or np.any(values.sum(1)<=0):
                raise ValueError("Lens matrisi 2–64 kanallı kare JSON dizi olmalı.")
            return {"matrix":values.tolist(),"name":Path(name).name}
        raise ValueError("Kaynak türü geçersiz.")

    def profile(self, name, data):
        if not isinstance(name,str) or not name.strip() or len(name)>100:
            raise ValueError("Profil adı geçersiz.")
        values = {"render":render_settings(data.get("render",{})),"print":validate_print(data.get("print",{}),require_color_profile=False)}
        if 'animation' in data:
            values['animation']=validate_animation(data['animation'])
        with self.lock:
            self.state["profiles"][name.strip()] = values
            self.save()
        return values

    def start(self, request):
        asset_id, stage = request.get("asset_id"), request.get("stage","full")
        if asset_id not in self.state["assets"] or stage not in ("render","print","full","pitch","depth","animation","animation_full","animation_print"):
            raise ValueError("Fotoğraf veya işlem türü geçersiz.")
        animation_stage=stage.startswith('animation')
        asset=self.state['assets'][asset_id]
        if animation_stage and asset.get('kind')!='sequence':
            raise ValueError('Önce animasyon fotoğraflarını seçip bir kare dizisi oluşturun.')
        if not animation_stage and stage!='pitch' and asset.get('kind')=='sequence':
            raise ValueError('Bu kaynak animasyon dizisi. Animasyon oluştur/baskı düğmelerini kullanın.')
        effect=validate_animation(request.get('animation',{})) if animation_stage else None
        if animation_stage:
            count=len(asset['source_ids'])
            if (effect['mode'] in ('motion','morph','dissolve') and count!=2) or (effect['mode']=='zoom' and count!=1) or (effect['mode'] in ('flip','sequence') and count<2):
                raise ValueError('Hareket/morph için iki, zoom için bir, flip/sekans için en az iki fotoğraf seçin.')
        rendering = render_settings(request.get("render",{}))
        printing = validate_print(request.get("print",{}),require_color_profile=stage not in ("render","depth","animation"))
        if printing["icc_path"]:
            path = Path(printing["icc_path"]).resolve()
            if not path.is_relative_to((self.local/"resources").resolve()) or not path.is_file():
                raise ValueError("ICC profili uygulamaya yüklenmiş bir dosya olmalı.")
        if stage not in ("render","depth","animation"):
            mixing_matrix(printing)
            color_transform(printing)
        render_job = request.get("render_job")
        if stage=='animation_print':
            previous=self.state['jobs'].get(render_job,{})
            if previous.get('status')!='complete' or previous.get('asset_id')!=asset_id or not previous.get('frames_folder'):
                raise ValueError('Bu dizinin tamamlanmış animasyon işini seçin.')
            effect=previous['animation'].copy()
        if stage in ('print','animation_print'):
            previous=self.state['jobs'].get(render_job,{})
            calibration_fields=('ppi','printer_dpi','nominal_lpi','effective_lpi','axis','tilt_deg','mirror','phase','width_mm','height_mm','bleed_mm','viewing_distance_mm','icc_path','white_underbase')
            old=previous.get('print',{})
            if printing['pitch_verified'] and old.get('pitch_verified') and any(old.get(k)!=printing[k] for k in calibration_fields):
                printing['pitch_verified']=False
        if stage == "print":
            previous = self.state["jobs"].get(render_job,{})
            # A print/calibration failure must not discard completed Blender work.
            folder=Path(previous.get("render_folder",""))
            recoverable=previous.get("status")=="failed" and "render_warnings" in previous and previous.get("quality") is not None
            if recoverable:
                recoverable=(folder/"scene.blend").is_file() and (folder/"coverage.json").is_file() and all(
                    (folder/f"views/view_{index:04d}.png").is_file() for index in range(previous["render"]["nr"]))
            if not (previous.get("status") == "complete" or recoverable) or previous.get("asset_id") != asset_id or not previous.get("render_folder"):
                raise ValueError("Bu fotoğrafın tamamlanmış bir render işini seçin.")
            rendering = previous["render"].copy()
        if stage in ("full","print"):
            expected_axis = "x" if printing["axis"] == "vertical" else "y"
            if rendering.get("camera_axis","x") != expected_axis:
                raise ValueError("Lens ve kamera yönü uyuşmuyor. Dikey lens sağ/sol, yatay lens yukarı/aşağı görünüş gerektirir.")
        identifier = datetime.now().strftime("%Y%m%d-%H%M%S-")+uuid.uuid4().hex[:8]
        output = self.root/"outputs/studio"/identifier
        job = dict(id=identifier,asset_id=asset_id,stage=stage,status="queued",message="Sırada",progress=0,
            created=now(),output=str(output),render=rendering,print=printing,render_job=render_job,warnings=[],render_engine_version=RENDER_ENGINE_VERSION)
        if effect is not None:
            job.update(animation=effect,animation_engine_version=ANIMATION_VERSION)
        with self.lock:
            self.state["jobs"][identifier] = job
            self.cancellations[identifier] = threading.Event()
            self.save()
        self.executor.submit(self.work,identifier)
        return identifier

    def cancel(self, identifier):
        with self.lock:
            if identifier in self.cancellations:
                if self.state["jobs"][identifier]["status"] in ("queued","running","cancel_requested"):
                    self.cancellations[identifier].set()
                    self.update(identifier,status="cancel_requested",message="Durduruluyor")

    def update(self, identifier, **values):
        with self.lock:
            self.state["jobs"][identifier].update(values)
            self.save()

    def checkpoint(self, identifier, message=None, percent=None):
        if self.cancellations[identifier].is_set():
            raise CancelledError()
        if message:
            self.update(identifier,message=message,**({"progress":percent} if percent is not None else {}))

    def get_depth(self, identifier, asset, settings):
        folder = Path(asset.get("depth_folder",""))
        if (folder/"depth_proximity.npy").is_file():
            if asset.get("supplied_depth") or asset.get("depth_process_res",504) == settings["process_res"]:
                self.checkpoint(identifier,"Hazır derinlik kullanılıyor",10)
                return np.load(folder/"depth_proximity.npy",allow_pickle=False)
        key = hashlib.sha256((asset["sha256"]+MODEL_REVISION+str(settings["process_res"])).encode()).hexdigest()
        folder = self.local/"depth"/key
        if not (folder/"metadata.json").is_file():
            # A failed partial depth run is retained; a fresh folder is used for retry.
            if folder.exists() and any(folder.iterdir()):
                folder = folder.with_name(key+"_"+uuid.uuid4().hex[:8])
            self.checkpoint(identifier,"Fotoğrafın derinliği hesaplanıyor",5)
            estimate(asset["photo"],folder,process_res=settings["process_res"])
        with self.lock:
            asset["depth_folder"],asset["depth_process_res"] = str(folder),settings["process_res"]
            self.save()
        return np.load(folder/"depth_proximity.npy",allow_pickle=False)

    def detailed_depth(self,identifier,asset,base,settings):
        from .detail_depth import VERSION,estimate_detail,surface_relief
        source=Path(asset["depth_folder"])/"depth_proximity.npy"
        key=hashlib.sha256((asset["sha256"]+digest(source)+str(VERSION)).encode()).hexdigest()
        folder=self.local/"depth_detail"/key
        if (folder/"metadata.json").is_file():
            delta=np.load(folder/"detail_delta.npy",allow_pickle=False)
        else:
            delta=estimate_detail(asset["photo"],base,folder,
                progress=lambda done,total:self.checkpoint(identifier,f"Yerel AI derinliği {done}/{total}",10+round(done/total*8)))
        surface=surface_relief(asset["photo"],base,folder)
        with self.lock:
            asset["detail_folder"]=str(folder)
            asset["detail_source_folder"]=asset["depth_folder"]
            self.save()
        combined = base+settings["detail_strength"]*delta+settings["surface_strength"]*surface
        # Reserve range for added relief instead of flattening near/far details.
        low, high = min(0.0,float(combined.min())), max(1.0,float(combined.max()))
        return ((combined-low)/(high-low)).astype(np.float32)

    def work(self, identifier):
        job = self.state["jobs"][identifier]
        asset = self.state["assets"][job["asset_id"]]
        output = Path(job["output"])
        try:
            self.checkpoint(identifier)
            self.update(identifier,status="running",message="Başlatılıyor")
            output.mkdir(parents=True)
            write_json(output/"project.json",dict(schema_version=1,asset_name=asset["name"],source_sha256=asset["sha256"],
                render=job["render"],print=job["print"],created=job["created"],
                **({'animation':job['animation']} if 'animation' in job else {})))
            if job['stage'].startswith('animation'):
                self.work_animation(identifier,job,asset,output)
                return
            if job["stage"] == "pitch":
                folder = output/"print"
                folder.mkdir()
                pitch_test(folder,job["print"])
                registration(folder,job["print"])
            else:
                result = None
                if job["stage"] == "full":
                    folder = Path(asset.get("depth_folder",""))
                    current_depth = digest(folder/"depth_proximity.npy") if (folder/"depth_proximity.npy").is_file() else None
                    with self.lock:
                        previous = next((candidate for candidate in reversed(list(self.state["jobs"].values()))
                            if candidate["id"] != identifier and candidate.get("status") == "complete"
                            and candidate.get("asset_id") == job["asset_id"]
                            and candidate.get("render_engine_version") == RENDER_ENGINE_VERSION
                            and candidate.get("render") == job["render"]
                            and current_depth and candidate.get("depth_source_hash") == current_depth
                            and candidate.get("render_folder") and (Path(candidate["render_folder"])/"scene.blend").is_file()), None)
                    if previous:
                        result = Path(previous["render_folder"])
                        self.update(identifier,render_folder=str(result),render_reused_from=previous["id"],depth_source_hash=current_depth,quality=previous.get("quality"),render_warnings=previous.get("render_warnings",[]))
                        job["warnings"].extend(previous.get("render_warnings",[]))
                        self.checkpoint(identifier,"Aynı ayarlı Blender görünüşleri yeniden kullanılıyor",70)
                if job["stage"] in ("render","full","depth"):
                    if result is not None:
                        self.finish_print(identifier,job,result,output)
                        return
                    depth = self.get_depth(identifier,asset,job["render"])
                    self.update(identifier,depth_source_hash=digest(Path(asset["depth_folder"])/"depth_proximity.npy"))
                    prepared = output/"prepared"
                    prepared.mkdir()
                    if job["render"]["detail_enabled"]:
                        Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(prepared/"depth_base.png")
                        depth=self.detailed_depth(identifier,asset,depth,job["render"])
                        self.checkpoint(identifier)
                    with Image.open(asset["photo"]) as original:
                        photo = original.convert("RGBA")
                    long_edge = 0 if job["stage"]=="depth" else job["render"]["render_long_edge"]
                    if long_edge and max(photo.size)>long_edge:
                        photo.thumbnail((long_edge,long_edge),Image.Resampling.LANCZOS)
                        import cv2
                        depth = cv2.resize(depth,photo.size,interpolation=cv2.INTER_LINEAR)
                    depth, edits = editable_depth(depth,job["render"],photo)
                    photo.save(prepared/"photo.png")
                    np.save(prepared/"depth.npy",depth,allow_pickle=False)
                    Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(prepared/"depth.png")
                    if job["render"]["detail_enabled"]:
                        Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(prepared/"depth_detail.png")
                    if job["stage"]=="depth":
                        self.update(identifier,status="complete",progress=100,message="Derinlik haritası hazır",completed=now())
                        return
                    geometry,parallax,disparity = plan_parallax(depth,photo.size,job["render"])
                    config = validate_render(dict(nr=job["render"]["nr"],ne=job["print"]["ne"],camera_axis=job["render"]["camera_axis"],
                        grid_size=job["render"]["grid_size"],edge_mode="split",**geometry))
                    quality = dict(edits=edits,parallax=parallax,
                        repair_engine="Alpha-separated depth layers / Telea" if job["render"]["repair"] else "none")
                    save_parallax_map(disparity,prepared/"parallax.png")
                    if parallax["angle_limited"]:
                        reason = "Kenar/paralaks koruması" if parallax["edge_limited"] else "Paralaks sınırı"
                        job["warnings"].append(f"{reason} nedeniyle açı {parallax['requested_angle_deg']:.2f}° yerine {parallax['effective_angle_deg']:.2f}° uygulandı.")
                    elif parallax["max_parallax_percent"]>job["render"]["max_parallax_percent"]:
                        job["warnings"].append("Paralaks seçilen sınırı aşıyor; sınırlamayı açın veya açı/etkiyi azaltın.")
                    if edits["clipped_fraction"]>.01:
                        job["warnings"].append("Derinlik uçlarında düzleşme var; yumuşak derinlik eğrisini kullanın.")
                    self.checkpoint(identifier,"Blender sahnesi ve arka plan katmanları hazırlanıyor",20)
                    def rendered(message):
                        frame,total = map(int,message.split()[-1].split('/'))
                        self.checkpoint(identifier,f"Blender görünüşü {frame}/{total}",20+round(50*frame/total))
                    result = render(prepared/"photo.png",prepared/"depth.npy",output/"render",config,
                        repair={"enabled":job["render"]["repair"],"layers":job["render"]["layers"],"radius":job["render"]["inpaint_radius"]},progress=rendered)
                    self.update(identifier,render_folder=str(result))
                    coverage = json.loads((result/"coverage.json").read_text(encoding="utf-8"))
                    mesh = json.loads((result/"job.json").read_text(encoding="utf-8"))["mesh"]
                    quality.update(max_nonopaque_fraction=coverage["max_nonopaque_fraction"],mesh=mesh)
                    if coverage["max_nonopaque_fraction"]>.0005:
                        job["warnings"].append("Görünüşlerde boş alan var; baskıdan önce arka plan veya açı ayarını düzeltin.")
                    write_json(output/"quality.json",quality)
                    self.update(identifier,quality=quality,render_warnings=list(job["warnings"]))
                else:
                    result = Path(self.state["jobs"][job["render_job"]]["render_folder"])
                    previous = self.state["jobs"][job["render_job"]]
                    self.update(identifier,render_folder=str(result),quality=previous.get("quality"),render_warnings=previous.get("render_warnings",[]))
                    job["warnings"].extend(previous.get("render_warnings",[]))
                if job["stage"] in ("full","print"):
                    self.finish_print(identifier,job,result,output)
                    return
            self.checkpoint(identifier)
            self.update(identifier,status="complete",progress=100,message="Tamamlandı",completed=now())
        except CancelledError:
            self.update(identifier,status="cancelled",message="Durduruldu; tamamlanmamış çıktı baskı için kullanılmaz.")
        except Exception as error:
            import traceback
            output.mkdir(parents=True,exist_ok=True)
            (output/"error.log").write_text(traceback.format_exc(),encoding="utf-8")
            self.update(identifier,status="failed",message=str(error))

    def close(self):
        for event in self.cancellations.values():
            event.set()
        self.executor.shutdown(wait=False,cancel_futures=True)

    def work_animation(self,identifier,job,asset,output):
        sources=[self.state['assets'][i] for i in asset['source_ids']]
        key=animation_key(sources,job['animation'])
        folder=None
        if job['stage']=='animation_print':
            folder=Path(self.state['jobs'][job['render_job']]['frames_folder'])
        else:
            for previous in reversed(list(self.state['jobs'].values())):
                if previous['id']!=identifier and previous.get('status')=='complete' and previous.get('animation_key')==key and previous.get('frames_folder'):
                    candidate=Path(previous['frames_folder'])
                    if (candidate/'frameset.json').is_file():
                        FrameSet(candidate)
                        folder=candidate
                        self.update(identifier,animation_reused_from=previous['id'])
                        break
        if folder is None:
            folder=output/'animation'
            generate_animation(sources,folder,job['animation'],
                checkpoint=lambda message=None,percent=None:self.checkpoint(identifier,message,percent))
        frameset=FrameSet(folder)
        self.update(identifier,frames_folder=str(folder),animation_key=key,nt=len(frameset.records),
            animation_quality=frameset.data.get('quality',{}))
        job['warnings'].extend(frameset.data.get('warnings',[]))
        if job['stage'] in ('animation_full','animation_print'):
            self.finish_print(identifier,job,folder,output)
        else:
            self.checkpoint(identifier)
            self.update(identifier,status='complete',progress=100,message='Animasyon kareleri hazır',completed=now())

    def finish_print(self,identifier,job,result,output):
        self.checkpoint(identifier,"Lenticular baskı kanalları hazırlanıyor",75)
        def printed(message):
            self.checkpoint(identifier,message,75+round(int(message.split('%')[-1])*.2))
        report = encode(result,output/"print",job["print"],progress=printed)
        job["warnings"].extend(message for message in report["warnings"] if message not in job["warnings"])
        self.update(identifier,print_quality={key:report[key] for key in ("pixels_per_lens","source_native_ppi","compensation_clipped_fraction","compensation_limited_fraction","raster_channel_coverage_fraction","simulation_error")})
        self.checkpoint(identifier)
        self.update(identifier,status="complete",progress=100,message="Tamamlandı",completed=now())
