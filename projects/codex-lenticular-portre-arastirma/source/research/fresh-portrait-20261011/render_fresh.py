from pathlib import Path
import importlib.util,json,sys
import numpy as np
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
WORK=Path(__file__).resolve().parent;OUT=WORK/'scene'
APP=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
job=json.loads((OUT/'job.json').read_text(encoding='utf-8'));cfg=job['config'];w,h=job['size']
mode=sys.argv[sys.argv.index('--')+1]

def camera_at(scene,position,config):
    camera=scene.camera;camera.location=(position,0,0)
    camera.data.shift_x=-config['focal_mm']*position/(config['sensor_width_mm']*config['zero'])
    camera.data.shift_y=0
    bpy.context.view_layer.update()
    checks=[]
    for z in (config['near'],config['zero'],config['far']):
        p=world_to_camera_view(scene,camera,Vector((0,0,-z)))
        expected=w/2+w*config['focal_mm']/config['sensor_width_mm']*position*(1/config['zero']-1/z)
        assert abs(p.x*w-expected)<.01 and abs(p.y*h-h/2)<.01
        checks.append(dict(z=z,u_px=p.x*w,expected_u_px=expected))
    return checks

if mode=='build':
    spec=importlib.util.spec_from_file_location('surface_builder',APP/'lenticular/blender_scene.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
    scene.cycles.use_denoising=False;scene.cycles.transparent_max_bounces=32
    scene.render.use_persistent_data=True
    scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    for layer in job['surfaces']:
        module.make_surface(OUT,layer,scene)
        print('FRESH_SURFACE_LOADED '+layer['name'],flush=True)
    data=bpy.data.cameras.new('Off axis');camera=bpy.data.objects.new('Off axis',data)
    scene.collection.objects.link(camera);scene.camera=camera
    data.type='PERSP';data.sensor_fit='HORIZONTAL';data.sensor_width=cfg['sensor_width_mm']
    data.lens=cfg['focal_mm'];data.clip_start=.01;data.clip_end=100;data.dof.use_dof=False
    camera.rotation_euler=(0,0,0)
    (OUT/'views').mkdir(exist_ok=True);records=[]
    for i,pos in enumerate(cfg['positions']+[0.]):
        checks=camera_at(scene,pos,cfg)
        filename=f'views/view_{i:04d}.png' if i<2 else 'center.png'
        scene.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True)
        records.append(dict(index=i,file=filename,camera_x=pos,projection_checks=checks))
        print('FRESH_REFERENCE_READY '+filename,flush=True)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'scene.blend'))
    (OUT/'render_result.json').write_text(json.dumps(records[:2],indent=2))
else:
    manifest=json.loads((WORK/'trials/manifest.json').read_text(encoding='utf-8'))
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'scene.blend'));scene=bpy.context.scene
    scene.render.use_persistent_data=True
    original={}
    for layer in job['surfaces']:
        with np.load(OUT/layer['mesh'],allow_pickle=False) as data:original[layer['name']]=data['vertices'].copy()
    reference=.5
    for variant in manifest['variants']:
        folder=Path(variant['folder']);current=json.loads((folder/'job.json').read_text(encoding='utf-8'))
        config=current['config']
        for name,vertices in original.items():
            z=-vertices[:,2].astype(np.float64)
            d=(1/z-1/cfg['far'])/(1/cfg['near']-1/cfg['far'])
            revised=reference+(d-reference)*np.where(d>=reference,variant['front_gain'],variant['back_gain'])
            new_z=1/((1-revised)/cfg['far']+revised/cfg['near'])
            updated=(vertices*(new_z/z)[:,None]).astype(np.float32)
            assert np.max(np.abs(updated[:,:2]/updated[:,2:3]-vertices[:,:2]/vertices[:,2:3]))<1e-6
            mesh=bpy.data.objects[name].data;mesh.vertices.foreach_set('co',updated.reshape(-1));mesh.update()
        records=[]
        for index,pos in enumerate(config['positions']):
            checks=camera_at(scene,pos,config);filename=f'views/view_{index:04d}.png'
            if not (folder/filename).is_file():
                scene.render.filepath=str(folder/filename);bpy.ops.render.render(write_still=True)
            records.append(dict(index=index,file=filename,camera_x=pos,projection_checks=checks))
            (folder/'render_result.json').write_text(json.dumps(records,indent=2))
            print(f"FRESH_VIEW {variant['id']} {index+1}/10",flush=True)
    print('FRESH_VIEWS_COMPLETE',flush=True)
