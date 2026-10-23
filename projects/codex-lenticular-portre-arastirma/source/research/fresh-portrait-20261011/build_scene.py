"""Fresh photo-based semantic surfaces. No previous portrait depth or layers are inputs."""
from pathlib import Path
import sys,json,math
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(APP))
from lenticular.geometry import build_mesh,validate
from lenticular.layers import reliable_depth_core
from lenticular.restoration import matte,complete_color,complete_depth,linear_rgb,reconcile_matte
from lenticular.runner import digest
WORK=Path(__file__).resolve().parent
OUT=WORK/'scene'

PERSON=[(.425,.016),(.495,.009),(.56,.013),(.61,.035),(.65,.075),(.66,.13),(.645,.193),
 (.66,.211),(.745,.233),(.79,.28),(.82,.355),(.846,.416),(.855,.47),(.84,.515),
 (.82,.565),(.85,.58),(.9,.614),(.936,.66),(.94,.713),(.906,.736),(.885,.785),
 (.816,.827),(.826,.857),(.832,.895),(.80,.923),(.75,.935),(.695,.93),(.655,.901),
 (.607,.88),(.601,.85),(.632,.822),(.66,.774),(.683,.727),(.659,.687),(.59,.662),
 (.523,.656),(.465,.683),(.43,.738),(.402,.79),(.369,.823),(.377,.86),(.373,.916),
 (.334,.962),(.281,.99),(.211,.995),(.153,.967),(.13,.936),(.148,.904),(.183,.851),
 (.153,.806),(.097,.768),(.059,.724),(.035,.701),(.036,.655),(.059,.61),(.095,.575),
 (.125,.551),(.123,.529),(.142,.509),(.19,.508),(.191,.491),(.166,.469),(.147,.44),
 (.147,.403),(.159,.372),(.169,.327),(.207,.286),(.266,.254),(.328,.227),(.401,.208),
 (.407,.169),(.403,.12),(.408,.067)]
LEFT=[(.267,.352),(.285,.352),(.298,.371),(.307,.4),(.32,.432),(.349,.437),(.361,.451),
 (.363,.479),(.349,.51),(.326,.531),(.299,.536),(.272,.529),(.254,.511),(.222,.502),
 (.193,.487),(.172,.467),(.154,.444),(.146,.422),(.15,.404),(.176,.401),(.199,.407),
 (.223,.423),(.245,.441),(.258,.415),(.263,.384)]
RIGHT=[(.754,.479),(.787,.47),(.819,.469),(.847,.479),(.845,.509),(.833,.542),
 (.812,.574),(.797,.605),(.798,.633),(.789,.66),(.78,.669),(.767,.664),(.754,.669),
 (.738,.665),(.727,.656),(.718,.659),(.704,.661),(.693,.651),(.68,.653),(.661,.65),
 (.649,.658),(.634,.659),(.622,.653),(.605,.654),(.603,.641),(.618,.62),(.64,.607),
 (.671,.596),(.685,.581),(.7,.548),(.713,.515),(.731,.491)]

def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def refine(rgb,points,band,seed):
    h,w=rgb.shape[:2]
    initial=np.zeros((h,w),np.uint8)
    polygon=np.rint(np.asarray(points)*[w,h]).astype(np.int32)
    cv2.fillPoly(initial,[polygon],1)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*band+1,2*band+1))
    inside=cv2.erode(initial,kernel)>0;outside=cv2.dilate(initial,kernel)==0
    trimap=np.where(initial,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype(np.uint8)
    trimap[inside]=cv2.GC_FGD;trimap[outside]=cv2.GC_BGD
    cv2.setRNGSeed(0)
    cv2.grabCut(rgb,trimap,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK)
    mask=((trimap==cv2.GC_FGD)|(trimap==cv2.GC_PR_FGD)).astype(np.uint8)
    _,components=cv2.connectedComponents(mask)
    label=components[round(seed[1]*h),round(seed[0]*w)]
    assert label>0,'Foreground seed must belong to the selected surface.'
    return components==label

def prepare():
    OUT.mkdir(exist_ok=False)
    with Image.open(WORK/'inference/photo.png') as im:rgb=np.asarray(im.convert('RGB')).copy()
    h,w=rgb.shape[:2]
    raw=np.load(WORK/'inference/relative_depth.npy',allow_pickle=False)
    inverse=1/raw
    nose=float(inverse[432,958])
    # Preserve all model values, including nearby hand relief; no percentile clipping.
    z0=2.;span=2*z0*math.tan(math.radians(4)/2)
    coefficient=w*50/36*span*(1/1.5-1/3)
    target=(.024*w)/coefficient
    delta=inverse-nose
    depth=(.5+delta*np.where(delta>=0,target/float(delta.max()),target/-float(delta.min()))).astype(np.float32)
    assert depth.min()>0 and depth.max()<1 and depth[432,958]==.5
    np.save(OUT/'depth_proximity.npy',depth,allow_pickle=False)
    Image.fromarray(np.rint(depth*65535).astype(np.uint16)).save(OUT/'depth-16bit.png')
    Image.fromarray(rgb).save(OUT/'source.png')
    masks={}
    masks['person']=refine(rgb,PERSON,65,(.5,.4))
    masks['left_arm']=refine(rgb,LEFT,26,(.29,.46))
    masks['right_arm']=refine(rgb,RIGHT,24,(.76,.55))
    masks['person'] |= masks['left_arm']|masks['right_arm']
    assert not np.any(masks['left_arm']&masks['right_arm'])
    for key,mask in masks.items():
        Image.fromarray(mask.astype(np.uint8)*255).save(OUT/f'{key}-mask.png')
    cfg=validate(dict(nr=2,ne=10,near=1.5,far=3.,zero=z0,focal_mm=50.,sensor_width_mm=36.,
        camera_span=span,positions=[-span/2,span/2],grid_size=512,edge_threshold=1.,
        depth_convention='white-near',sweep_seconds=2.,camera_axis='x',edge_mode='cut'))
    plan=dict(config=cfg,size=[w,h],source_inputs=dict(photo=str(WORK/'inference/photo.png'),
        photo_sha256=digest(WORK/'inference/photo.png'),depth=str(WORK/'inference/relative_depth.npy'),
        depth_sha256=digest(WORK/'inference/relative_depth.npy')),
        method='Fresh DA3 at 1008; source-image semantic occlusion masks; continuous torso/shorts geometry; no depth quantile partitions.',
        model_source='https://github.com/ByteDance-Seed/Depth-Anything-3',
        nose_pixel=[958,432],zero_reference=.5,max_endpoint_parallax_percent=2.4,
        no_old_depth_or_layers=True,no_detail_crops=True,no_luminance_relief=True)
    write(OUT/'plan.json',plan)
    overlay=rgb.copy().astype(np.float32)
    overlay[masks['person']]=.7*overlay[masks['person']]+.3*np.array([70,210,255])
    for key,color in [('left_arm',[255,110,60]),('right_arm',[230,90,240])]:
        overlay[masks[key]]=.55*rgb[masks[key]]+.45*np.array(color)
    image=Image.fromarray(overlay.astype(np.uint8));image.thumbnail((730,1210))
    image.save(WORK/'semantic-boundaries.jpg',quality=96)
    print('FRESH_SEMANTIC_MASKS_READY',flush=True)

def surfaces():
    plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    rgb=np.asarray(Image.open(OUT/'source.png').convert('RGB')).copy()
    depth=np.load(OUT/'depth_proximity.npy',allow_pickle=False)
    cfg=plan['config'];h,w=depth.shape
    masks={k:np.asarray(Image.open(OUT/f'{k}-mask.png'))>0 for k in ('person','left_arm','right_arm')}
    def dilate(mask,r):
        return cv2.dilate(mask.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1)))>0
    removal={k:dilate(m,8) for k,m in masks.items()}
    hidden_arms=removal['left_arm']|removal['right_arm']
    # Complete each concealed material once; all camera views share these textures.
    pad=64
    padded=np.pad(rgb,((pad,pad),(pad,pad),(0,0)),mode='edge')
    bg_holes=np.pad(removal['person'],((pad,pad),(pad,pad)),constant_values=True)
    bg_color,bg_info=complete_color(padded,bg_holes)
    body_color,body_info=complete_color(rgb,hidden_arms)
    core_bg=~dilate(masks['person'],12)
    bg_depth=complete_depth(depth,core_bg,0.,1.)
    bg_depth[removal['person']]=np.minimum(bg_depth[removal['person']],depth[removal['person']]-.002)
    body_valid=masks['person']&~dilate(hidden_arms,8)
    body_core=reliable_depth_core(body_valid,depth,0.,1.,fine=True)
    body_depth=complete_depth(depth,body_core,0.,1.,surface_mask=body_valid)
    body_depth[hidden_arms]=np.minimum(body_depth[hidden_arms],depth[hidden_arms]-.002)
    body_alpha,body_foreground,body_matte=matte(rgb,masks['person'])
    # Keep the inferred hidden sleeve/torso pixels, with original visible color.
    body_foreground[hidden_arms]=body_color[hidden_arms]
    background=linear_rgb(bg_color[pad:-pad,pad:-pad])
    body_alpha,body_foreground,info=reconcile_matte(rgb,body_foreground,body_alpha,background,
                                                  removal['person']&~hidden_arms)
    background=linear_rgb(body_foreground)*body_alpha[...,None]+background*(1-body_alpha[...,None])
    body_matte.update(info)
    layers=[dict(name='Background',depth=bg_depth,color=bg_color,alpha=np.ones((h+2*pad,w+2*pad)),pad=pad,info=bg_info),
            dict(name='Continuous torso and shorts',depth=body_depth,color=body_foreground,alpha=body_alpha,pad=0,info=body_info|body_matte)]
    for key in ('left_arm','right_arm'):
        a,f,info=matte(rgb,masks[key])
        a,f,consistency=reconcile_matte(rgb,f,a,background,removal[key])
        core=reliable_depth_core(masks[key],depth,0.,1.,fine=True)
        geometry=complete_depth(depth,core,0.,1.,surface_mask=masks[key])
        # Occlusion order is enforced only where these surfaces overlap.
        # There are no global depth intervals cutting through cloth or anatomy.
        support=dilate(masks[key],12)
        body_depth[support]=np.minimum(body_depth[support],geometry[support]-.003)
        layers.append(dict(name=key,depth=geometry,color=f,alpha=a,pad=0,info=info|consistency))
        background=linear_rgb(f)*a[...,None]+background*(1-a[...,None])
    # Recompose at the source camera before any view synthesis.
    srgb=np.where(background<=.0031308,background*12.92,1.055*np.maximum(background,0)**(1/2.4)-.055)
    recomposed=np.rint(np.clip(srgb,0,1)*255).astype(np.uint8)
    difference=np.abs(recomposed.astype(np.int16)-rgb.astype(np.int16))
    visible_error=dict(mean_rgb=float(difference.mean()),large_error_fraction=float(np.mean(np.max(difference,axis=2)>32)))
    assert visible_error['large_error_fraction']<.002,visible_error
    Image.fromarray(recomposed).save(OUT/'source-recomposition.png')
    entries=[];vertices=triangles=0
    for index,layer in enumerate(layers):
        geometry=np.clip(layer['depth'],0,1).astype(np.float32)
        mesh,stats=build_mesh(geometry,cfg,padding=layer['pad'],sample_mode='linear')
        if layer['pad']:
            mesh['uv']=(mesh['uv']*[w,h]+layer['pad'])/[w+2*layer['pad'],h+2*layer['pad']]
            mesh['uv']=mesh['uv'].astype(np.float32)
        name=f'layer_{index:02d}'
        np.savez_compressed(OUT/f'{name}.npz',**mesh)
        alpha=np.rint(np.clip(layer['alpha'],0,1)*255).astype(np.uint8)
        Image.fromarray(np.dstack([layer['color'],alpha])).save(OUT/f'{name}.png')
        np.save(OUT/f'{name}-depth.npy',geometry,allow_pickle=False)
        entries.append(dict(name=layer['name'],mesh=f'{name}.npz',texture=f'{name}.png',extend=False))
        vertices+=stats['vertices'];triangles+=stats['triangles']
        print('SURFACE_READY '+layer['name'],flush=True)
    job=dict(schema_version=1,stage='fresh_semantic_portrait',config=cfg,size=[w,h],
        mesh=dict(vertices=vertices,triangles=triangles,focal_px=w*50/36,layer_count=len(entries)),
        surfaces=entries,source_inputs=plan['source_inputs'],fresh_plan=plan,
        coordinate_convention='X right, Y up; positive endpoint disparity is behind',
        limitations=['Single-photo geometry and hidden surfaces are estimated; physical print verification required.'])
    write(OUT/'job.json',job)
    write(OUT/'surface-report.json',dict(source_recomposition=visible_error,
        surface_names=[l['name'] for l in layers],depth_partitioning=False,old_assets_used=False,
        completion=[l['info'] for l in layers]))
    print(json.dumps(dict(stage='fresh_scene_ready',source_recomposition=visible_error)),flush=True)

if __name__=='__main__':
    cv2.setNumThreads(2)
    (prepare if sys.argv[-1]=='prepare' else surfaces)()
