from pathlib import Path
import sys,json
import bpy,numpy as np
p=Path(sys.argv[sys.argv.index('--')+1]);out=p.parent;src=out.parent/'rejected-coincident-surfaces'
job=json.loads(p.read_text());config=job['config'];bpy.ops.wm.open_mainfile(filepath=str(src/'scene.blend'));scene=bpy.context.scene
for layer in job['surfaces']:
    obj=bpy.data.objects[layer['name']]
    with np.load(out/layer['mesh']) as data:vertices=data['vertices']
    obj.data.vertices.foreach_set('co',vertices.reshape(-1));obj.data.update()
for i,pos in enumerate(config['positions']+[0]):
    scene.camera.location.x=pos;scene.camera.data.shift_x=-config['focal_mm']*pos/(config['sensor_width_mm']*config['zero'])
    filename=f'views/view_{i:04d}.png' if i<2 else 'center.png';(out/'views').mkdir(exist_ok=True)
    scene.render.filepath=str(out/filename);bpy.ops.render.render(write_still=True)
(out/'render_result.json').write_text((src/'render_result.json').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
