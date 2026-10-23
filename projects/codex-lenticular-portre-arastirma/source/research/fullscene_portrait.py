"""Full-scene inferred volumes; controlled 6/10/12-channel comparison."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

ROOT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from lenticular.layers import align_mask,layered_surfaces
from lenticular.repair import plan_parallax,save_parallax_map
from lenticular.geometry import validate
from lenticular.runner import digest,find_blender,preview
from lenticular.printing import encode,channel_pattern,color_transform,to_linear,from_linear

ACCEPTED=ROOT/'outputs/studio/20261009-113404-b9f6d34d'
INITIAL=ROOT/'outputs/studio/20261008-223746-051b86f3'
OLD=Path(r'C:\Users\USER\Downloads\Lenticular-50LPI-Bolgesel-20261009-113340')
ORIGINAL=Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')
RECORD=HERE/'fullscene-current.json'
POINTS={'burun':(958,432),'sol_yanak':(848,444),'sag_yanak':(1046,444),'alin':(952,241),
 'cene':(954,625),'basparmak':(525,1240),'diger_el':(1390,1950),'govde':(1040,1330),
 'sol_diz':(390,2230),'sag_diz':(1550,2170),'sol_baldir':(460,2450),
 'sag_baldir':(1360,2380),'sol_ayakkabi':(385,2830),'sag_ayakkabi':(1360,2680),
 'duvar_sol':(250,450),'duvar_sag':(1570,620)}

def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def protected():
    return {str(p):digest(p) for p in (ORIGINAL,ACCEPTED/'prepared/photo.png',
      ACCEPTED/'prepared/depth.npy',ACCEPTED/'project.json',OLD/'Portre-50LPI-1200PPI-6Kanal-BOLGESEL.tif')}
def record():return json.loads(RECORD.read_text(encoding='utf-8'))

def uniform_views():
    rec=record();cfg=rec['configs']['A']
    angles=np.unique(np.round(np.concatenate([np.linspace(-1.9,1.9,n) for n in (6,10,12)]),12))
    cfg=validate(cfg|{'nr':len(angles),'positions':(cfg['zero']*np.tan(np.deg2rad(angles))).tolist()})
    rec['configs']['A']=cfg;rec['render']['nr']=len(angles)
    rec['plan'].update(nr=len(angles),camera_step_deg_approx={'6':3.8/5,'10':3.8/9,'12':3.8/11},
        unique_source_angles_deg=angles.tolist(),
        source_generation='Union of exact equal-angle 6/10/12 camera grids; shared endpoint renders; no view interpolation')
    write(Path(rec['delivery'])/'Sahne-Plani.json',rec['plan']);write(RECORD,rec)
    print(json.dumps(dict(unique_views=len(angles),delivery=rec['delivery']),ensure_ascii=False),flush=True)

def prepare():
    cv2.setNumThreads(2);before=protected()
    assert before[str(ORIGINAL)]=='d7d3c1c669483c99540c1f82ad71e34d3aa9b027facf6ce1c5785e400f694ec5'
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
    work=HERE/('fullscene-'+stamp);delivery=Path(r'C:\Users\USER\Downloads')/('Lenticular-50LPI-TamSahne-6-10-12-'+stamp)
    work.mkdir(exist_ok=False);delivery.mkdir(exist_ok=False);shared=work/'shared';shared.mkdir()
    prior=json.loads((ACCEPTED/'project.json').read_text(encoding='utf-8'))
    rendering=prior['render']|dict(nr=12,grid_size=640,depth_smoothing=0,edge_refinement=0)
    printing=prior['print']|{'ne':6}
    with Image.open(ACCEPTED/'prepared/photo.png') as im:photo=im.convert('RGBA');rgb=np.array(im.convert('RGB'))
    raw=np.load(INITIAL/'prepared/depth.npy',allow_pickle=False)
    accepted=np.load(ACCEPTED/'prepared/depth.npy',allow_pickle=False)
    h,w=raw.shape;assert (w,h)==(1872,3098)
    yy,xx=np.ogrid[:h,:w];nose=rendering['zero_reference']
    _,old_stats,old_disp=plan_parallax(accepted,(w,h),prior['render'])
    coefficient=abs(old_disp[0,0]/(nose-accepted[0,0]))
    def ellipse(cx,cy,rx,ry,feather=.3):
        q=((xx-cx)/rx)**2+((yy-cy)/ry)**2;t=np.clip((1-q)/feather,0,1)
        return (t*t*(3-2*t)).astype(np.float32),np.sqrt(np.clip(1-q,0,1)).astype(np.float32)
    def gaussian(cx,cy,rx,ry):return np.exp(-.5*(((xx-cx)/rx)**2+((yy-cy)/ry)**2)).astype(np.float32)
    cached_mask=HERE/'fullscene-20261009-135756/person-mask.png'
    if cached_mask.is_file():
        with Image.open(cached_mask) as cached:person=np.array(cached)>0
        assert person.shape==raw.shape
    else:person=align_mask(rgb,raw>.15)
    # Keep the nose-containing connected silhouette, not unrelated background islands.
    _,components=cv2.connectedComponents(person.astype(np.uint8));label=int(components[432,958])
    assert label>0;person=components==label
    # The inherited AI silhouette includes floor below the shoes. Segment the
    # visible cyan footwear and skin so volume cannot spill into those tiles.
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    blue=cv2.inRange(hsv,np.array([80,55,35]),np.array([115,255,255]))
    blue[:2300]=0
    blue=cv2.morphologyEx(blue,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    shoe_masks=[np.zeros((h,w),np.uint8),np.zeros((h,w),np.uint8)]
    for contour in cv2.findContours(blue,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        if cv2.contourArea(contour)<2000:continue
        moments=cv2.moments(contour);side=0 if moments['m10']/moments['m00']<w/2 else 1
        cv2.drawContours(shoe_masks[side],[contour],-1,1,-1)
    assert all(np.count_nonzero(mask)>30000 for mask in shoe_masks)
    shoe_left,shoe_right=[mask.astype(bool) for mask in shoe_masks]
    skin=(hsv[:,:,0]<35)&(hsv[:,:,1]>20)&(rgb[:,:,0].astype(float)>rgb[:,:,2]*1.06)
    leg_rois=np.zeros((h,w),np.uint8)
    cv2.fillPoly(leg_rois,[np.array([[120,2300],[550,2300],[650,2630],[355,2660]],np.int32),
      np.array([[1160,2300],[1700,2300],[1420,2520],[1180,2510]],np.int32)],1)
    skin=skin&(leg_rois>0)
    skin=cv2.morphologyEx(skin.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    filled_skin=np.zeros_like(skin)
    for contour in cv2.findContours(skin,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        if cv2.contourArea(contour)>2000:cv2.drawContours(filled_skin,[contour],-1,1,-1)
    person[2350:]=(filled_skin>0)[2350:]|shoe_left[2350:]|shoe_right[2350:]
    low=cv2.GaussianBlur(raw,(0,0),8)
    detail=np.clip(raw-low,-.010,.010)*coefficient
    # Smooth wall-to-floor transition. No hard horizontal background plane.
    wall=46-3*xx/(w-1)-6*gaussian(425,450,240,260)-8*gaussian(1475,490,230,270)
    floor=32-38*np.clip((yy-1900)/(h-1-1900),0,1)
    floor_mix=1/(1+np.exp(-(yy-2020)/160))
    disp=((1-floor_mix)*wall+floor_mix*floor).astype(np.float32)
    # Restrained inherited surface variation, never luminance/textile-to-depth.
    disp+=np.where(person,0,np.clip((raw-low)*coefficient,-2.5,2.5))
    # Every visible human pixel starts on a coherent human surface, not on the
    # distant wall. Region masks must never leave elbows/limb rims behind.
    human_baseline=np.broadcast_to(np.where(yy<1900,28.,5.),(h,w))
    disp[person]=human_baseline[person]
    def blend(mask,target):
        nonlocal disp
        m=mask*person;disp=disp*(1-m)+np.asarray(target,dtype=np.float32)*m
    body,roundness=ellipse(980,1400,620,770);blend(body,33-18*roundness-detail*.25)
    shoulder,r=ellipse(980,820,590,240);blend(shoulder,29-7*r)
    # Separate near-side knees, shins and shoes with rounded cross-sections.
    for spec in ((360,2230,265,310,-7,18),(1550,2150,275,320,-4,17)):
        cx,cy,rx,ry,edge,relief=spec;m,r=ellipse(cx,cy,rx,ry);blend(m,edge-relief*r-detail*.3)
    for spec in ((460,2450,170,230,-3,9),(1360,2370,245,185,-2,9)):
        cx,cy,rx,ry,edge,relief=spec;m,r=ellipse(cx,cy,rx,ry)
        t=np.clip((yy-(cy-150))/170,0,1);m=m*(t*t*(3-2*t))
        blend(m,edge-relief*r-detail*.25)
    for mask,cx,cy,rx,ry in ((shoe_left,400,2800,260,280),(shoe_right,1330,2610,270,310)):
        _,r=ellipse(cx,cy,rx,ry);blend(mask.astype(np.float32),-4-11*r-detail*.25)
    m,r=ellipse(1450,1660,200,410);blend(m,-8-18*r-detail*.3)
    m,r=ellipse(1330,1920,265,220);blend(m,-15-18*r-detail*.35)
    m,r=ellipse(485,1470,250,315);blend(m,-19-20*r-detail*.3)
    # Hair, forehead, cheeks, eye sockets, nose bridge, lips and chin are one surface.
    m,r=ellipse(965,355,230,340);blend(m,27-10*r)
    m,r=ellipse(965,680,150,180);blend(m,25-5*r)
    face,r=ellipse(958,435,205,310,.35)
    face_target=24-13*r+5*gaussian(860,346,46,30)+5*gaussian(1045,346,46,30)
    face_target+=2*gaussian(826,456,55,75)+2*gaussian(1090,452,55,75)
    face_target-=2*gaussian(958,547,60,23)+2*gaussian(958,625,73,42)
    face_target-=detail*.45;blend(face,face_target)
    for cx in (750,1160):m,r=ellipse(cx,375,38,105);blend(m,25-3*r)
    # A smooth nose-tip pin, not a single-pixel dent.
    disp-=float(disp[432,958])*gaussian(958,432,37,52)*person
    # Cover the entire real forearm silhouette; a geometric ellipse missed its
    # outer elbow and produced a displaced skin fragment in the first QA render.
    forearm_skin=(hsv[:,:,0]<35)&(hsv[:,:,1]>20)&(rgb[:,:,0].astype(float)>rgb[:,:,2]*1.06)&person
    forearm_skin&=(xx>=245)&(xx<740)&(yy>=1180)&(yy<1730)
    along=np.clip(((xx-310)*250+(yy-1340)*120)/(250**2+120**2),0,1)
    arm_target=-12-40*along-detail*.2
    disp[forearm_skin]=np.broadcast_to(arm_target,(h,w))[forearm_skin]
    # Preserve the accepted thumb's depth and all of its reliable raised-hand core.
    hand,_=ellipse(525,1400,310,470)
    core=(hand>0)&(accepted>.70)
    weight=cv2.GaussianBlur(core.astype(np.float32),(0,0),8);weight[core]=1
    disp=disp*(1-weight)+old_disp*weight;disp[432,958]=0
    depth=(nose-disp/coefficient).astype(np.float32)
    # Only absorb float32 round-trip epsilon; reject real clipped geometry.
    assert np.isfinite(depth).all() and depth.min()>=-1e-6 and depth.max()<=1+1e-6,(float(depth.min()),float(depth.max()))
    depth=np.clip(depth,0,1)
    depth[core]=accepted[core];depth[432,958]=nose
    assert np.array_equal(depth[core],accepted[core])
    photo.save(shared/'photo.png');np.save(shared/'depth.npy',depth,allow_pickle=False)
    Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(delivery/'Hacim-Derinlik-Plani.png')
    Image.fromarray(person.astype(np.uint8)*255).save(work/'person-mask.png')
    Image.fromarray(rgb[2300:]).save(work/'lowerbody-source.png')
    stats={};measurements={};configs={}
    for label,angle in (('A',3.8),):
        render=rendering|dict(angle_deg=angle)
        geometry,s,disparity=plan_parallax(depth,(w,h),render)
        assert not s['angle_limited'],s
        assert abs(float(disparity[432,958]))<.001
        values={name:float(disparity[y,x]) if name=='burun' else float(np.median(disparity[y-10:y+11,x-10:x+11]))
             for name,(x,y) in POINTS.items()}
        assert min(values['sol_yanak'],values['sag_yanak'])>5
        assert values['diger_el']<-15 and max(values['sol_diz'],values['sag_diz'])<-10,values
        assert values['govde']>7 and min(values['duvar_sol'],values['duvar_sag'])>30
        assert abs(values['burun'])<.001
        stats[label]=s;measurements[label]=values
        configs[label]=validate(dict(nr=12,ne=12,grid_size=640,edge_mode='split',camera_axis='x',**geometry))
        save_parallax_map(disparity,delivery/f'{label}-On-Arka-Derinlik.png')
    plan=dict(status='planned_physical_unverified',source='one original photograph; inferred/artistic geometry',
      source_size=[w,h],zero_reference=nose,nose_point=[958,432],nr=12,ne_variants=[6,10,12],ppi=1200,lpi=50,
      native_print_size_mm=[130,215.139],channel_width_raster_px={'6':4,'10':2.4,'12':2},
      camera_angles_deg=[-1.9,1.9],camera_step_deg_approx=3.8/11,
      camera_note='Parallel off-axis synthetic views, not actual measured photographs or lens viewing angle',
      sole_comparison_difference='print channel count and corresponding source selection; same full camera span, depth, RGB preparation, dimensions, pitch, renderer',
      parallax=stats,endpoint_source_px=measurements,
      endpoint_print_mm={k:{n:v*130/w for n,v in vals.items()} for k,vals in measurements.items()},
      endpoint_note='Full first-to-last camera image shift, NOT perceived depth in millimetres',
      volume_method='Smooth rounded full-person volumes; continuous face relief and separate limbs; preserved accepted thumb core',
      texture_preparation='After rendering, symmetric horizontal filter sigma=source lens pitch/8; no post-interlace filtering',
      render_samples=32,renderer_denoising=False,thumb_core_pixels=int(core.sum()),
      protected_hashes=before,limitations=['Unseen surfaces are Telea estimates, not genuine photographs.',
        'Lens angle, effective pitch and effective printer resolution remain unmeasured.',
        '10-channel stripes occupy alternating two/three raster pixels; 12-channel stripes are two pixels wide.',
        'Stronger 4.8-degree depth alternative postponed until channel count comparison.'])
    write(delivery/'Sahne-Plani.json',plan)
    rec=dict(work=str(work),delivery=str(delivery),shared=str(shared),configs=configs,printing=printing,
      render=rendering,protected_hashes=before,plan=plan)
    write(RECORD,rec);assert protected()==before
    print(json.dumps(dict(work=str(work),delivery=str(delivery),endpoint_px=measurements,depth_range=[float(depth.min()),float(depth.max())]),ensure_ascii=False),flush=True)

def render():
    cv2.setNumThreads(2);rec=record();shared=Path(rec['shared']);work=Path(rec['work'])
    with Image.open(shared/'photo.png') as im:photo=im.copy()
    depth=np.load(shared/'depth.npy',allow_pickle=False)
    surfaces,mesh=layered_surfaces(photo,depth,shared,rec['configs']['A'],count=4,radius=5)
    for s in surfaces:s['mesh']=str(shared/s['mesh']);s['texture']=str(shared/s['texture'])
    blender=find_blender();driver=HERE/'fullscene_blender_driver.py'
    full_cfg=rec['configs']['A'];n=full_cfg['nr'];split=n//2
    batches=[full_cfg['positions'][:split],full_cfg['positions'][split:]]
    def one(label):
        folder=work/f'batch-{label}'/'render';folder.mkdir(parents=True,exist_ok=False)
        cfg=validate(full_cfg|{'nr':len(batches[label]),'positions':batches[label]})
        job=dict(schema_version=1,config=cfg,size=list(photo.size),surfaces=surfaces,
            mesh=mesh,quality=dict(samples=32,denoising=False),source_inputs=dict(photo_sha256=digest(shared/'photo.png'),depth_sha256=digest(shared/'depth.npy')))
        write(folder/'job.json',job)
        cmd=[str(blender),'--background','--factory-startup','--threads','8','--python-exit-code','1',
             '--python',str(driver),'--',str(folder/'job.json')]
        with (folder/'blender.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            try:
                for line in process.stdout:
                    log.write(line);log.flush()
                    if line.startswith('LENTICULAR_'):print(str(label)+' '+line.strip(),flush=True)
                code=process.wait()
            except BaseException:
                process.terminate();raise
        if code:raise RuntimeError(f'{label} Blender failed; see {folder}/blender.log')
        preview(folder,job)
        return label
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,(0,1)))
    folder=work/'A'/'render';(folder/'views').mkdir(parents=True,exist_ok=False)
    job=dict(schema_version=1,config=full_cfg,size=list(photo.size),surfaces=surfaces,mesh=mesh,
      quality=dict(samples=32,denoising=False),source_inputs=dict(photo_sha256=digest(shared/'photo.png'),depth_sha256=digest(shared/'depth.npy')))
    write(folder/'job.json',job)
    for batch,positions in enumerate(batches):
        base=0 if batch==0 else split
        for i in range(len(positions)):shutil.copy2(work/f'batch-{batch}'/f'render/views/view_{i:04d}.png',folder/f'views/view_{base+i:04d}.png')
    shutil.copy2(work/'batch-0/render/center.png',folder/'center.png');preview(folder,job)
    assert protected()==rec['protected_hashes']
    print('EXACT_6_10_12_CAMERA_GRIDS_RENDER_COMPLETE',flush=True)

def inspect_motion(folder,source):
    nr=json.loads((folder/'job.json').read_text(encoding='utf-8'))['config']['nr']
    frames=[cv2.imread(str(folder/f'views/view_{i:04d}.png')) for i in (0,nr-1)]
    source=cv2.cvtColor(source,cv2.COLOR_RGB2BGR);results={}
    for name,(x,y) in POINTS.items():
        observations=[]
        for radius in (9,15,25):
            template=source[y-radius:y+radius+1,x-radius:x+radius+1]
            positions=[];scores=[]
            for frame in frames:
                match=cv2.matchTemplate(frame[y-40:y+41,x-115:x+116],template,cv2.TM_CCOEFF_NORMED)
                _,score,_,loc=cv2.minMaxLoc(match);positions.append(loc[0]-(115-radius));scores.append(float(score))
            observations.append(dict(radius=radius,endpoint_px=positions[1]-positions[0],scores=scores))
        reliable=[v for v in observations if min(v['scores'])>=.8]
        if len(reliable)<2:raise ValueError(f'{name}: unreliable matching {observations}')
        if np.ptp([v['endpoint_px'] for v in reliable])>5:raise ValueError(f'{name}: inconsistent motion {observations}')
        value=float(np.median([v['endpoint_px'] for v in reliable]))
        if name=='burun':assert abs(value)<=2,observations
        results[name]=dict(endpoint_px=value,observations=observations)
    return results

def deliver():
    cv2.setNumThreads(2);rec=record();work=Path(rec['work']);delivery=Path(rec['delivery'])
    with Image.open(Path(rec['shared'])/'photo.png') as im:source=np.array(im.convert('RGB'))
    sigma=source.shape[1]/(130/25.4*50)/8
    reports={};tiffs={};counts=(6,10,12)
    render=work/'A'/'render';coverage=json.loads((render/'coverage.json').read_text(encoding='utf-8'))
    assert coverage['max_nonopaque_fraction']<.0005
    motions=inspect_motion(render,source)
    for name in POINTS:
        expected=rec['plan']['endpoint_source_px']['A'][name];actual=motions[name]['endpoint_px']
        assert abs(expected-actual)<8,(name,expected,actual)
    print('Whole-scene motion checks passed.',flush=True)
    conditioned=work/'conditioned';(conditioned/'views').mkdir(parents=True,exist_ok=False)
    job=json.loads((render/'job.json').read_text(encoding='utf-8'));write(conditioned/'job.json',job)
    nr=job['config']['nr']
    for i in range(nr):
        with Image.open(render/f'views/view_{i:04d}.png') as im:rgba=np.array(im.convert('RGBA'))
        linear=to_linear(rgba[:,:,:3]);filtered=from_linear(cv2.GaussianBlur(linear,(0,1),sigma,borderType=cv2.BORDER_REFLECT_101))
        rgba[:,:,:3]=filtered;Image.fromarray(rgba).save(conditioned/f'views/view_{i:04d}.png')
    shutil.copy2(render/'center.png',conditioned/'center.png')
    for ne in counts:
        folder=work/f'print-{ne}';settings=rec['printing']|{'ne':ne}
        report=encode(conditioned,folder,settings,progress=lambda m,n=ne:print(str(n)+' '+m,flush=True))
        assert report['distinct_source_images']==ne and report['raster_integrity']['sampled_pixels_verified']
        assert report['source_indices'][0]==nr-1 and report['source_indices'][-1]==0
        assert len(set(report['source_indices']))==ne
        coords=np.arctan(np.array(job['config']['positions'])/job['config']['zero'])
        np.testing.assert_allclose(coords[report['source_indices'][::-1]],np.linspace(coords[0],coords[-1],ne),atol=1e-11)
        target=delivery/f'{ne}-GORSEL-TAM-PORTRE-50LPI-1200PPI.tif'
        assert not target.exists();shutil.copy2(folder/'interlaced.tif',target)
        assert digest(target)==digest(folder/'interlaced.tif')
        tiffs[ne]=target;reports[ne]=report;write(delivery/f'{ne}-Gorsel-Baski-Raporu.json',report)
        shutil.copy2(folder/'lens-proof.png',delivery/f'{ne}-Gorsel-Onizleme-FIZIKSEL-KANIT-DEGIL.png')
    # All three local strip origins fall on the same 24-pixel lens phase.
    rasters=[tifffile.memmap(tiffs[ne]) for ne in counts]
    assert len(set(a.shape for a in rasters))==1
    h,w=rasters[0].shape[:2];gap=240+(-w)%24;origins=[i*(w+gap) for i in range(3)]
    sheet_w=origins[-1]+w;footer_h=1320
    assert all(origin%24==0 for origin in origins)
    footer=make_footer(w,sheet_w,origins,counts,rec['printing'],source,reports)
    with tifffile.TiffFile(tiffs[6]) as f:icc=f.pages[0].tags[34675].value
    pair=delivery/'TEK-BASKI-SOL-6-ORTA-10-SAG-12-GORSEL.tif'
    def strips():
        for y in range(0,h+footer_h,128):
            rows=min(128,h+footer_h-y);tile=np.full((rows,sheet_w,3),255,np.uint8)
            image_rows=max(0,min(rows,h-y))
            if image_rows:
                for origin,raster in zip(origins,rasters):tile[:image_rows,origin:origin+w]=raster[y:y+image_rows]
            if image_rows<rows:
                fy=max(0,y-h);tile[image_rows:]=footer[fy:fy+rows-image_rows]
            yield tile
    with tifffile.TiffWriter(pair) as f:f.write(data=strips(),shape=(h+footer_h,sheet_w,3),dtype=np.uint8,
        photometric='rgb',rowsperstrip=128,resolution=(1200,1200),resolutionunit='INCH',metadata=None,
        extratags=[(34675,'B',len(icc),icc,False)])
    actual=tifffile.memmap(pair)
    for y in range(0,h,128):
        for origin,raster in zip(origins,rasters):
            assert np.array_equal(actual[y:min(h,y+128),origin:origin+w],raster[y:y+128])
    assert np.array_equal(actual[h:],footer)
    # Optional same-sized white mask; only use if the established workflow uses white.
    white=delivery/'UC-GORSEL-YAN-YANA-BEYAZ-MASKESI.tif'
    with tifffile.TiffWriter(white) as f:f.write(data=(np.full((min(128,h+footer_h-y),sheet_w),255,np.uint8)
        for y in range(0,h+footer_h,128)),shape=(h+footer_h,sheet_w),dtype=np.uint8,photometric='minisblack',
        rowsperstrip=128,resolution=(1200,1200),resolutionunit='INCH',metadata=None)
    with tifffile.TiffFile(pair) as f:
        assert f.pages[0].tags['XResolution'].value==(1200,1) and f.pages[0].tags['YResolution'].value==(1200,1)
    assert protected()==rec['protected_hashes']
    validation=dict(status='digital_checks_passed_physical_comparison_pending',rendered_motion=motions,
      source_unchanged=True,comparison_panels_exact=True,panel_origins_px=origins,channel_counts=list(counts),
      paired_size_mm=[sheet_w/1200*25.4,(h+footer_h)/1200*25.4],individual_size_mm=[w/1200*25.4,h/1200*25.4],
      common_pre_interlace_filter_sigma_source_px=sigma,physical_depth_verified=False,physical_sharpness_verified=False,
      common_view_indices=reports[12]['source_indices'],source_selections={str(ne):reports[ne]['source_indices'] for ne in counts},
      files={p.name:digest(p) for p in (*tiffs.values(),pair,white)},
      difference='Only print channel count and source selection change; full camera span is 3.8 degrees for every panel.',
      limitations=rec['plan']['limitations'])
    write(delivery/'Son-Denetim.json',validation)
    # Layout preview uses camera images, not a claim of physical lens behavior.
    with Image.open(render/'center.png') as im:im=im.convert('RGB');im.thumbnail((450,750));panel=im.copy()
    visual=Image.new('RGB',(1410,875),'white');draw=ImageDraw.Draw(visual)
    for i,ne in enumerate(counts):visual.paste(panel,(10+i*470,65))
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',26)
    for i,ne in enumerate(counts):draw.text((10+i*470,15),f'{ne} GORSEL / AYNI 3.8 DERECE',font=font,fill='black')
    draw.text((10,825),'Yerlesim onizlemesi; lens altindaki netlik ve akiciligi gostermez.',font=font,fill='black')
    visual.save(delivery/'Yan-Yana-Yerlesim-Onizleme.jpg',quality=95)
    rec['validation']=validation;rec['status']='complete';write(RECORD,rec)
    print(json.dumps(dict(status='complete',delivery=str(delivery),paired_size_mm=validation['paired_size_mm']),ensure_ascii=False),flush=True)

def make_footer(w,sw,origins,counts,settings,source,reports):
    img=Image.new('RGB',(sw,1320),'white');d=ImageDraw.Draw(img)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',90);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',58)
    for origin,ne in zip(origins,counts):d.text((origin+100,28),f'{ne} GORSEL / AYNI 3.8 DERECE / EN 13 cm',font=font,fill='black')
    array=np.array(img)
    for origin,ne in zip(origins,counts):
        pattern=channel_pattern(w,0,1,settings|{'ne':ne})[0]
        assert np.all(np.bincount(pattern[:24],minlength=ne)>=2)
        mixed=np.zeros((430,w,3),np.uint8)
        for channel,index in enumerate(reports[ne]['source_indices']):
            hue=int(160*(ne-channel-1)/max(ne-1,1));color=cv2.cvtColor(np.array([[[hue,180,200]]],np.uint8),cv2.COLOR_HSV2RGB)[0,0]
            card=Image.new('RGB',(w,430),tuple(int(v) for v in color));draw=ImageDraw.Draw(card)
            number_font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',300)
            for x in (120,w//2-250,w-800):draw.text((x,12),f'{ne-channel:02d}',font=number_font,fill='white')
            mixed[:,pattern==channel]=np.array(card)[:,pattern==channel]
        array[185:615,origin:origin+w]=mixed
    # Static, un-interlaced fine-detail source strip. Inspect this without a lens.
    for origin in origins:
        region=Image.fromarray(source[335:495]);region=region.resize((w,525),Image.Resampling.LANCZOS)
        array[750:1275,origin:origin+w]=np.array(region)
    img=Image.fromarray(array);d=ImageDraw.Draw(img)
    for origin in origins:d.text((origin+100,645),'DUZ KAYNAK DETAYI - LENS OLMADAN KONTROL',font=small,fill='black')
    return np.array(img)

if __name__=='__main__':
    args=argparse.ArgumentParser();args.add_argument('stage',choices=('prepare','uniform','render','deliver'))
    {'prepare':prepare,'uniform':uniform_views,'render':render,'deliver':deliver}[args.parse_args().stage]()
