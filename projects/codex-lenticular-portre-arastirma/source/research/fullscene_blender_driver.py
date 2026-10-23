"""Task-local high-sampling Blender driver; no application defaults change."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(r'C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1')
sys.path.insert(0,str(ROOT))
from lenticular.blender_scene import make_surface

def main():
    path=Path(sys.argv[sys.argv.index('--')+1]);job=json.loads(path.read_text(encoding='utf-8'))
    output=path.parent;cfg=job['config']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=32;scene.cycles.use_adaptive_sampling=False
    scene.cycles.use_denoising=False;scene.cycles.seed=0;scene.cycles.transparent_max_bounces=32
    scene.render.resolution_x,scene.render.resolution_y=job['size'];scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.render.film_transparent=True
    if hasattr(scene.render,'use_motion_blur'):scene.render.use_motion_blur=False
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.image_settings.color_depth='8';scene.render.use_file_extension=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    for layer in job['surfaces']:make_surface(output,layer,scene)
    data=bpy.data.cameras.new('Parallel off-axis camera');cam=bpy.data.objects.new('Camera',data)
    scene.collection.objects.link(cam);scene.camera=cam
    data.type='PERSP';data.sensor_fit='HORIZONTAL';data.sensor_width=cfg['sensor_width_mm']
    data.lens=cfg['focal_mm'];data.clip_start=min(cfg['near'],cfg['zero'])/100
    data.clip_end=max(cfg['far'],cfg['zero'])*100;data.dof.use_dof=False;cam.rotation_euler=(0,0,0)
    (output/'views').mkdir(exist_ok=False)
    w,h=job['size'];fpx=w*cfg['focal_mm']/cfg['sensor_width_mm'];records=[]
    for i,pos in enumerate(cfg['positions']):
        cam.location=(pos,0,0);data.shift_x=-cfg['focal_mm']*pos/(cfg['sensor_width_mm']*cfg['zero'])
        data.shift_y=0;bpy.context.view_layer.update()
        checks=[]
        for z in (cfg['near'],cfg['zero'],cfg['far']):
            uv=world_to_camera_view(scene,cam,Vector((0,0,-z)))
            expected=w/2+fpx*pos*(1/cfg['zero']-1/z)
            assert abs(uv.x*w-expected)<.01 and abs(uv.y*h-h/2)<.01
            checks.append(dict(z=z,u_px=uv.x*w,expected_u_px=expected))
        scene.render.filepath=str(output/f'views/view_{i:04d}.png')
        bpy.ops.render.render(write_still=True)
        records.append(dict(index=i,camera_x=pos,file=f'views/view_{i:04d}.png',projection_checks=checks))
        print(f'LENTICULAR_VIEW {i+1}/{len(cfg["positions"])}',flush=True)
    cam.location=(0,0,0);data.shift_x=0;bpy.context.view_layer.update()
    scene.render.filepath=str(output/'center.png');bpy.ops.render.render(write_still=True)
    (output/'render_result.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('LENTICULAR_DONE',flush=True)

if __name__=='__main__':main()
