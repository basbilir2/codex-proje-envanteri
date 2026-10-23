from pathlib import Path
import sys,json
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from lenticular.blender_scene import make_surface
p=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text());src=Path(p['source']);out=Path(p['out']);config=p['config'];w,h=p['size']
bpy.ops.wm.open_mainfile(filepath=str(src/'scene.blend'));scene=bpy.context.scene
bpy.data.objects.remove(bpy.data.objects['Depth layer 3'],do_unlink=True)
for i in (2,3):make_surface(out,dict(mesh=f'layer_{i:02d}.npz',texture=f'layer_{i:02d}.png',name=f'Corrected layer {i}',extend=False),scene)
scene.render.use_border=True;scene.render.use_crop_to_border=True
box=(370,1020,770,1540);x0,y0,x1,y1=box
scene.render.border_min_x=x0/w;scene.render.border_max_x=x1/w;scene.render.border_min_y=1-y1/h;scene.render.border_max_y=1-y0/h
for name,pos in [('left',config['positions'][0]),('center',0),('right',config['positions'][-1])]:
    scene.camera.location.x=pos;scene.camera.data.shift_x=-config['focal_mm']*pos/(config['sensor_width_mm']*config['zero'])
    scene.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
