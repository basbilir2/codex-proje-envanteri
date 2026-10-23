"""One 100-LPI portrait with coherent semantic surfaces and bounded hand motion."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0, str(APP))
from lenticular.geometry import build_mesh, validate
from lenticular.layers import extend_depth
from lenticular.repair import plan_parallax
from lenticular.restoration import matte, complete_color
from lenticular.runner import digest, find_blender, preview
from lenticular.printing import validate as validate_print, encode

OUT = ROOT / 'vd_100lpi_codex_20261012'
INPUT = OUT / 'prepared'
PHOTO = Path(r'C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg')
MASK = Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f\fullscene-20261009-135756\person-mask.png')
RAW = ROOT / 'prepared_depth/depth.npy'
NR = 6
ZERO = .5
ANGLE = 4.0


def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t*t*(3-2*t)


def prepare():
    cv2.setNumThreads(2)
    INPUT.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(Image.open(PHOTO).convert('RGB'))
    base = np.load(RAW, allow_pickle=False)
    h, w = base.shape
    assert rgb.shape[:2] == (h,w) == (3098,1872)
    assert digest(PHOTO) == 'd7d3c1c669483c99540c1f82ad71e34d3aa9b027facf6ce1c5785e400f694ec5'
    yy, xx = np.ogrid[:h,:w]
    person = np.asarray(Image.open(MASK).convert('L')) > 127
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    cyan = ((hsv[:,:,0] >= 80)&(hsv[:,:,0] <= 115)&(hsv[:,:,1] > 45)&(hsv[:,:,2] > 40)).astype(np.uint8)
    cyan[:2300] = 0
    cyan = cv2.morphologyEx(cyan,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    shoe = np.zeros((h,w),np.uint8)
    for contour in cv2.findContours(cyan,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        if cv2.contourArea(contour)>3000: cv2.drawContours(shoe,[contour],-1,1,-1)
    skin = (hsv[:,:,0]<35)&(hsv[:,:,1]>15)&(rgb[:,:,0].astype(float)>rgb[:,:,2]*1.06)
    legs = np.zeros((h,w),np.uint8)
    for poly in ([[120,2220],[555,2270],[532,2340],[550,2410],[582,2490],[565,2570],[510,2605],[390,2580],[315,2490],[225,2390]], [[1240,2270],[1740,2140],[1660,2300],[1550,2380],[1420,2450],[1360,2510],[1260,2520],[1170,2450],[1160,2400],[1190,2340]]):
        cv2.fillPoly(legs,[np.array(poly,np.int32)],1)
    lower = cv2.morphologyEx((skin&(legs>0)).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    for contour in cv2.findContours(lower,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        if cv2.contourArea(contour)>2000: cv2.drawContours(lower,[contour],-1,1,-1)
    person[2350:] = ((lower>0)|(shoe>0))[2350:]
    # Segment the actual forearm/fist, never rectangular depth-only finger patches.
    initial = skin & person & (xx>250)&(xx<700)&(yy>1080)&(yy<1680)
    roi = np.s_[1050:1730,230:740]
    local = initial[roi].astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15))
    core = cv2.erode(local,kernel)>0
    outer = cv2.dilate(local,kernel)>0
    trimap = np.where(local,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    trimap[core] = cv2.GC_FGD
    trimap[~outer] = cv2.GC_BGD
    cv2.setRNGSeed(0)
    cv2.grabCut(rgb[roi].copy(),trimap,None,np.zeros((1,65)),np.zeros((1,65)),2,cv2.GC_INIT_WITH_MASK)
    hand = np.zeros((h,w),bool)
    local = (trimap==cv2.GC_FGD)|(trimap==cv2.GC_PR_FGD)
    _, labels = cv2.connectedComponents(local.astype(np.uint8))
    label = labels[1240-1050,525-230]
    assert label>0
    hand[roi] = labels==label
    hand &= person
    # A closed fist/forearm has no interior holes. Skin highlights must not
    # become holes exposing an inpainted shirt behind the palm.
    filled_hand = np.zeros((h,w),np.uint8)
    for contour in cv2.findContours(hand.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]:
        cv2.drawContours(filled_hand,[contour],-1,1,-1)
    hand = (filled_hand>0)&person
    # Body wall/floor and anatomical relief are encoded directly in endpoint pixels.
    def gauss(cx,cy,rx,ry):
        return np.exp(-.5*(((xx-cx)/rx)**2+((yy-cy)/ry)**2)).astype(np.float32)
    def shape(cx,cy,rx,ry):
        q=((xx-cx)/rx)**2+((yy-cy)/ry)**2
        return smoothstep((1-q)/.35).astype(np.float32),np.sqrt(np.clip(1-q,0,1)).astype(np.float32)
    low = cv2.GaussianBlur(base,(0,0),12)
    # Existing depth-predicted relief, not brightness-to-geometry conversion.
    residual = cv2.GaussianBlur(base-low,(0,0),2.5)
    wall = 38 - 4*xx/(w-1) - 4*gauss(470,400,260,270) - 5*gauss(1600,440,190,230)
    floor = 26-24*np.clip((yy-1850)/(h-1-1850),0,1)
    floor_mix = 1/(1+np.exp(-(yy-2040)/140))
    background = ((1-floor_mix)*wall+floor_mix*floor).astype(np.float32)
    background += np.clip(-residual*80,-3,3)
    field = background.copy()
    field[person] = np.broadcast_to(np.where(yy<1900,14.,7.),(h,w))[person]
    def blend(mask,target):
        nonlocal field
        a = mask*person
        field = field*(1-a)+np.asarray(target,dtype=np.float32)*a
    body, curve = shape(980,1370,620,750)
    blend(body,18-22*curve-np.clip(residual*190,-3.5,3.5))
    shoulders,curve = shape(975,805,585,235)
    blend(shoulders,13-10*curve)
    # Rounded limbs remain continuous with the shirt and floor perspective.
    for cx,cy,rx,ry,edge,relief in [(1480,1620,205,390,5,9),(1350,1945,250,220,0,7),(360,2240,270,330,9,11),(1530,2180,280,330,9,11),(450,2480,175,255,6,9),(1370,2380,225,200,6,9)]:
        a,curve = shape(cx,cy,rx,ry)
        blend(a,edge-relief*curve-np.clip(residual*90,-1.5,1.5))
    shoe_distance = cv2.distanceTransform(shoe,cv2.DIST_L2,5)
    field[shoe>0] = (3-8*np.clip(shoe_distance/100,0,1))[shoe>0]
    # Face: curved forehead, cheeks, sockets, jaw and a small nose projection.
    a,curve = shape(958,390,215,340)
    face = 14-12*curve+5*gauss(860,345,46,30)+5*gauss(1044,345,46,30)
    face += 3*gauss(809,453,43,77)+3*gauss(1093,453,43,77)
    face -= 1.5*gauss(958,540,60,24)+2*gauss(958,626,70,45)
    face -= np.clip(residual*100,-2,2)
    blend(a,face)
    a,curve = shape(963,690,155,160)
    blend(a,11-6*curve)
    # Move the zero plane behind the nose; do not add a single-pixel pin/dent.
    nasal_weight = gauss(958,432,37,50)*person
    field -= (float(field[432,958])+4.0)*nasal_weight
    for cx in [750,1160]:
        a,curve=shape(cx,365,40,108);blend(a,13-3*curve)
    # One intact hand mesh with shallow, smooth true-silhouette curvature.
    progress = np.clip((xx-280)/300,0,1)
    hand_target = 2-8*progress-np.clip(residual*50,-1,1)
    for kind,y0,y1,x0,x1,strength in [('thumb',1080,1355,465,625,4),('palm',1320,1680,440,700,5)]:
        region = hand&(yy>=y0)&(yy<=y1)&(xx>=x0)&(xx<=x1)
        arch = np.zeros((h,w),np.float32)
        for y in range(y0,min(h,y1+1)):
            indices=np.flatnonzero(region[y])
            if len(indices)<5:continue
            left,right=float(indices[0]),float(indices[-1]);half=(right-left+2)/2;center=(right+left)/2
            arch[y,indices]=np.sqrt(np.clip(1-((indices-center)/half)**2,0,1))
        arch=cv2.GaussianBlur(arch,(0,0),3)
        hand_target -= strength*arch
    # Smooth small fold/knuckle relief without hard rectangular boundaries.
    for cy in [1410,1490,1560,1610]:
        hand_target -= .7*gauss(555,cy,92,13)*hand
    hand_target=cv2.GaussianBlur(hand_target.astype(np.float32),(0,0),3)
    assert hand_target[hand].min()>-18 and hand_target[hand].max()<6
    field[hand]=hand_target[hand]
    config = validate(dict(nr=NR,ne=NR,near=1.5,far=3.,zero=2.,camera_span=4*math.tan(math.radians(ANGLE)/2),grid_size=1024,camera_axis='x',edge_mode='split'))
    coefficient=w*50/36*config['camera_span']*(1/1.5-1/3)
    depth=(ZERO-field/coefficient).astype(np.float32)
    background_depth=(ZERO-background/coefficient).astype(np.float32)
    assert np.isfinite(depth).all() and 0<depth.min()<depth.max()<1
    np.save(INPUT/'depth.npy',depth,allow_pickle=False)
    np.save(INPUT/'background_depth.npy',background_depth,allow_pickle=False)
    np.save(INPUT/'endpoint_motion.npy',field,allow_pickle=False)
    Image.fromarray(rgb).save(INPUT/'photo.png')
    for name,mask in [('person',person),('hand',hand)]: Image.fromarray(mask.astype(np.uint8)*255).save(INPUT/f'{name}_mask.png')
    Image.fromarray(np.rint(depth*255).astype(np.uint8)).save(INPUT/'depth.png')
    overlay=rgb.copy();overlay[person]=(overlay[person]*.6+np.array([0,160,80])*.4).astype(np.uint8);overlay[hand]=(rgb[hand]*.5+np.array([255,70,30])*.5).astype(np.uint8)
    Image.fromarray(overlay).resize((604,1000)).save(OUT/'semantic-mask-review.png')
    values={name:float(field[y,x]) for name,(x,y) in {'nose':(958,432),'left_cheek':(848,444),'right_cheek':(1046,444),'forehead':(958,241),'chin':(958,625),'thumb':(525,1240),'shirt_center':(1010,1350),'shirt_side':(650,1370),'rear_hand':(1390,1950),'wall_left':(250,450),'wall_right':(1570,620)}.items()}
    settings=dict(config=config,source_sha256=digest(PHOTO),input_depth_sha256=digest(RAW),depth_sha256=digest(INPUT/'depth.npy'),angle_deg=ANGLE,zero_reference=ZERO,reference_point=None,nose_endpoint_motion_px=values['nose'],endpoint_values=values,range_px=[float(field.min()),float(field.max())],hand_range_px=[float(field[hand].min()),float(field[hand].max())],inference_note='Anatomical relief is inferred/artistic, not measured 3D. Source RGB is unchanged; separate semantic surfaces replace depth-quantile cuts.',physical_3d_verified=False)
    write(INPUT/'scene-plan.json',settings)
    print(json.dumps(settings,ensure_ascii=True),flush=True)


def textures():
    identity={name:digest(INPUT/name) for name in ['photo.png','person_mask.png','hand_mask.png']}
    old_report=json.loads((INPUT/'texture-report.json').read_text(encoding='utf-8')) if (INPUT/'texture-report.json').is_file() else {}
    if old_report.get('input_identity')==identity:return
    cv2.setNumThreads(2)
    rgb=np.asarray(Image.open(INPUT/'photo.png').convert('RGB'))
    person=np.asarray(Image.open(INPUT/'person_mask.png'))>0
    hand=np.asarray(Image.open(INPUT/'hand_mask.png'))>0
    padding=48
    removal=cv2.dilate(person.astype(np.uint8),np.ones((13,13),np.uint8))>0
    padded=np.pad(rgb,((padding,padding),(padding,padding),(0,0)),mode='edge')
    holes=np.pad(removal,((padding,padding),(padding,padding)),constant_values=True)
    print('Completing only hidden background once.',flush=True)
    wall,wall_report=complete_color(padded,holes)
    Image.fromarray(wall).save(INPUT/'wall_texture.png')
    print('Matting coherent body silhouette and intact forearm/fist.',flush=True)
    alpha,color,person_report=matte(rgb,person)
    hand_alpha,hand_color,hand_report=matte(rgb,hand)
    hand_removal=cv2.dilate(hand.astype(np.uint8),np.ones((9,9),np.uint8))>0
    body,body_report=complete_color(color,hand_removal)
    # Strict source colors away from hand occlusion and true matte edge collars.
    for name,pixels,a in [('body',body,alpha),('hand',hand_color,hand_alpha)]:
        rgba=np.dstack([pixels,np.rint(a*255).astype(np.uint8)])
        Image.fromarray(rgba).save(INPUT/f'{name}_texture.png')
    write(INPUT/'texture-report.json',dict(input_identity=identity,wall=wall_report,person=person_report,hand=hand_report,hand_hidden_completion=body_report,padding=padding,visible_source_changed=False))


def render_scene(stage):
    textures()
    scene= json.loads((INPUT/'scene-plan.json').read_text(encoding='utf-8'))
    config=scene['config'].copy()
    identity=dict(geometry_revision=3,depth_sha256=digest(INPUT/'depth.npy'),person_mask_sha256=digest(INPUT/'person_mask.png'),hand_mask_sha256=digest(INPUT/'hand_mask.png'),stage=stage,config=config)
    suffix=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:8]
    folder=OUT/('preview' if stage=='preview' else 'render')
    if folder.exists():
        if (folder/'input-identity.json').is_file() and json.loads((folder/'input-identity.json').read_text(encoding='utf-8'))==identity and (folder/'coverage.json').is_file():
            print('Completed identical scene exists; reuse.',flush=True);return
        folder=OUT/(('preview' if stage=='preview' else 'render')+'-'+suffix)
    if (folder/'coverage.json').is_file():return
    folder.mkdir(exist_ok=False)
    write(folder/'input-identity.json',identity)
    write(OUT/('preview-current.json' if stage=='preview' else 'render-current.json'),dict(folder=str(folder),identity=identity))
    full=np.load(INPUT/'depth.npy',allow_pickle=False)
    background=np.load(INPUT/'background_depth.npy',allow_pickle=False)
    person=np.asarray(Image.open(INPUT/'person_mask.png'))>0
    hand=np.asarray(Image.open(INPUT/'hand_mask.png'))>0
    original=Image.open(INPUT/'photo.png').convert('RGB')
    size=original.size
    if stage=='preview':
        original.thumbnail((1024,1024),Image.Resampling.LANCZOS);size=original.size;config['grid_size']=512
        full=cv2.resize(full,size,interpolation=cv2.INTER_LINEAR)
        background=cv2.resize(background,size,interpolation=cv2.INTER_LINEAR)
        person=cv2.resize(person.astype(np.uint8),size,interpolation=cv2.INTER_NEAREST)>0
        hand=cv2.resize(hand.astype(np.uint8),size,interpolation=cv2.INTER_NEAREST)>0
    padding=round(48*size[0]/1872)
    original.save(folder/'source.png');np.save(folder/'depth_proximity.npy',full,allow_pickle=False)
    surfaces=[];stats={}
    for name,depth,valid,pad in [('wall',background,np.ones(full.shape,bool),padding),('body',full,person&~hand,0),('hand',full,hand,0)]:
        d=extend_depth(depth,valid) if name!='wall' else depth
        # A reconstructed shirt behind the forearm must never penetrate it.
        # Nearest-body extrapolation alone can put it in FRONT of the arm,
        # despite correct alpha and zero transparent pixels.
        if name=='body':
            support=cv2.dilate(hand.astype(np.uint8),np.ones((7,7),np.uint8))>0
            hand_surface=extend_depth(full,hand)
            d[support]=np.minimum(d[support],hand_surface[support]-.03)
        if name=='wall':
            support=cv2.dilate(person.astype(np.uint8),np.ones((7,7),np.uint8))>0
            person_surface=extend_depth(full,person)
            d[support]=np.minimum(d[support],person_surface[support]-.03)
        mesh,s=build_mesh(d,config|{'edge_threshold':1.},padding=pad,sample_mode='linear')
        if name=='wall':
            # Padded texture coordinates must retain exact registration at the
            # zero camera; padding must not rescale/shift the visible wall.
            mesh['uv']=(mesh['uv']*np.array(size)+padding)/np.array([size[0]+2*padding,size[1]+2*padding])
            mesh['uv']=mesh['uv'].astype(np.float32)
        np.savez_compressed(folder/f'{name}.npz',**mesh)
        im=Image.open(INPUT/f'{name}_texture.png')
        target=(size[0]+2*padding,size[1]+2*padding) if name=='wall' else size
        if im.size!=target:im=im.resize(target,Image.Resampling.LANCZOS)
        im.save(folder/f'{name}.png')
        surfaces.append(dict(name=name,mesh=f'{name}.npz',texture=f'{name}.png',extend=False));stats[name]=s
    job=dict(schema_version=1,config=config,size=list(size),surfaces=surfaces,mesh=stats,source_inputs=dict(photo=str(INPUT/'photo.png'),depth=str(INPUT/'depth.npy'),photo_sha256=digest(INPUT/'photo.png'),depth_sha256=digest(INPUT/'depth.npy')),limitations=['Single photograph; inferred anatomical geometry and hidden surfaces.','No physical lens/RIP calibration.'])
    write(folder/'job.json',job)
    cmd=[str(find_blender()),'--background','--factory-startup','--python-exit-code','1','--python',str(APP/'lenticular/blender_scene.py'),'--',str(folder/'job.json')]
    with (folder/'blender.log').open('w',encoding='utf-8') as log:
        process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        for line in process.stdout:
            log.write(line)
            if line.startswith('LENTICULAR_VIEW'):print(line.strip(),flush=True)
        if process.wait():raise RuntimeError('Blender failed; inspect saved log.')
    preview(folder,job)
    board=Image.new('RGB',(3*size[0],size[1]+40),'#202329');draw=ImageDraw.Draw(board)
    for j,index in enumerate([0,NR//2,NR-1]):
        with Image.open(folder/f'views/view_{index:04d}.png') as im:board.paste(im.convert('RGB'),(j*size[0],40))
        draw.text((j*size[0]+8,10),f'View {index+1}/{NR}',fill='white')
    board.thumbnail((2400,1600));board.save(folder/'endpoint-review.jpg',quality=93)
    print('Scene rendered; endpoint-review and look-around saved.',flush=True)


def printing():
    finish_render()
    settings=validate_print(dict(width_mm=6141*25.4/1200,height_mm=10163*25.4/1200,ppi=1200,printer_dpi=1200,nominal_lpi=100,effective_lpi=100,ne=NR,axis='vertical',phase=0,fit='contain',stripe_sampling='center',color_mode='RGB',mirror=False,white_underbase=False,pitch_verified=False,lens_angle_verified=False,raster_ppi_verified=False,allow_unfilled=False))
    folder=OUT/'print';folder.mkdir(exist_ok=True)
    if (folder/'print-report.json').is_file():return
    render_folder=Path(json.loads((OUT/'render-current.json').read_text(encoding='utf-8'))['folder'])
    report=encode(render_folder,folder,settings)
    write(folder/'print-report.json',report)
    print('100-LPI TIFF encoded.',flush=True)


def finish_render():
    """Finish only verified isolated partial-alpha floor raster seams."""
    folder=Path(json.loads((OUT/'render-current.json').read_text(encoding='utf-8'))['folder'])
    job=json.loads((folder/'job.json').read_text(encoding='utf-8'))
    # Printing diagnostics require the common camera focal length, alongside
    # the individual semantic-surface mesh statistics.
    if 'focal_px' not in job['mesh']:
        focal={s['focal_px'] for s in job['mesh'].values()}
        assert len(focal)==1
        job['mesh']['focal_px']=focal.pop()
        write(folder/'job.json',job)
    report_path=folder/'alpha-finalization.json'
    if report_path.is_file():return
    person=np.asarray(Image.open(INPUT/'person_mask.png'))>0
    records=[]
    paths=sorted((folder/'views').glob('view_*.png'))+[folder/'center.png']
    assert len(paths)==NR+1
    for path in paths:
        a=np.array(Image.open(path).convert('RGBA'))
        missing=a[:,:,3]<255
        ys,xs=np.where(missing)
        assert a.shape[:2]==person.shape
        assert len(xs)<=20 and (not len(xs) or (ys.min()>a.shape[0]-64 and not person[ys,xs].any() and np.all(a[ys,xs,3]==223)))
        _,_,stats,_=cv2.connectedComponentsWithStats(missing.astype(np.uint8),8)
        assert len(stats)==1 or stats[1:,cv2.CC_STAT_AREA].max()==1
        before=digest(path)
        # Straight-alpha RGB is complete and consistent with adjacent floor;
        # retain every RGB value. Never paint or conceal a geometry opening.
        if len(xs):
            a[ys,xs,3]=255
            Image.fromarray(a).save(path)
        records.append(dict(file=path.name,partial_alpha_pixels=int(len(xs)),coordinates=list(zip(xs.tolist(),ys.tolist())),rgb_unchanged=True,before_sha256=before,after_sha256=digest(path)))
    (folder/'coverage-before-alpha-finalization.json').write_bytes((folder/'coverage.json').read_bytes())
    preview(folder,job)
    write(report_path,dict(method='Set alpha to 255 only for isolated 223-alpha floor pixels in final 64 rows; all RGB values retained. Any other nonopacity fails.',files=records,geometry_rerendered=False))
    print('Final RGB unchanged; isolated floor alpha seams finalized.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','preview','final','finish','print']);args=parser.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage in ('preview','final'):render_scene(args.stage)
    elif args.stage=='finish':finish_render()
    else:printing()
