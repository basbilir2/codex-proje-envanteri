from pathlib import Path
import sys,json
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
p=Path(sys.argv[sys.argv.index('--')+1]);out=p.parent;job=json.loads(p.read_text());config=job['config']
records=json.loads((out/'endpoint-records.json').read_text());records[-1]['index']=11;records[-1]['file']='views/view_0011.png'
bpy.ops.wm.open_mainfile(filepath=str(out/'scene.blend'));scene=bpy.context.scene;camera=scene.camera
w,h=job['size'];fpx=w*config['focal_mm']/config['sensor_width_mm'];axis=config.get('camera_axis','x')
for i in range(1,11):
    pos=config['positions'][i];camera.location=(pos,0,0) if axis=='x' else (0,pos,0)
    shift=-config['focal_mm']*pos/(config['sensor_width_mm']*config['zero'])
    camera.data.shift_x=shift if axis=='x' else 0;camera.data.shift_y=shift if axis=='y' else 0
    bpy.context.view_layer.update();checks=[]
    for z in (config['near'],config['zero'],config['far']):
        projected=world_to_camera_view(scene,camera,Vector((0,0,-z)));offset=fpx*pos*(1/config['zero']-1/z)
        u=w/2+(offset if axis=='x' else 0);v=h/2+(offset if axis=='y' else 0)
        assert abs(projected.x*w-u)<.01 and abs(projected.y*h-v)<.01
        checks.append(dict(z=z,u_px=projected.x*w,v_px=projected.y*h,expected_u_px=u,expected_v_px=v))
    filename=f'views/view_{i:04d}.png';scene.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
    records.append(dict(index=i,camera_x=camera.location.x,camera_y=camera.location.y,shift_x=camera.data.shift_x,
        shift_y=camera.data.shift_y,file=filename,projection_checks=checks))
    print(f'LENTICULAR_VIEW {i+1}/12',flush=True)
(out/'render_result.json').write_text(json.dumps(sorted(records,key=lambda r:r['index']),indent=2))
