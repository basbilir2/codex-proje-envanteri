"""Render requested print trials from the cached corrected scene, without new inference."""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

manifest_path = Path(sys.argv[sys.argv.index('--') + 1])
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
source = Path(manifest['scene_source'])
source_job = json.loads((source / 'job.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(source / 'scene.blend'))
scene = bpy.context.scene
scene.render.use_persistent_data = True
camera = scene.camera
base = source_job['config']
reference = (1/base['zero'] - 1/base['far']) / (1/base['near'] - 1/base['far'])
original = {}
for surface in source_job['surfaces']:
    with np.load(source / surface['mesh'], allow_pickle=False) as data:
        original[surface['name']] = data['vertices'].copy()

for variant in manifest['variants']:
    folder = Path(variant['folder'])
    job = json.loads((folder / 'job.json').read_text(encoding='utf-8'))
    config = job['config']
    if (folder/'geometry-checks.json').is_file() and all(
        (folder/f'views/view_{i:04d}.png').is_file() for i in range(config['nr'])
    ):
        print('TRIAL_REUSED ' + variant['id'], flush=True)
        continue
    intervals = []
    for name, vertices in original.items():
        old_z = -vertices[:, 2].astype(np.float64)
        depth = (1/old_z - 1/base['far']) / (1/base['near'] - 1/base['far'])
        gain = np.where(depth >= reference, variant['front_gain'], variant['back_gain'])
        remapped = reference + (depth-reference)*gain
        new_z = 1 / ((1-remapped)/base['far'] + remapped/base['near'])
        updated = (vertices * (new_z/old_z)[:, None]).astype(np.float32)
        assert np.isfinite(updated).all()
        assert np.max(np.abs(updated[:, :2]/updated[:, 2:3] - vertices[:, :2]/vertices[:, 2:3])) < 1e-6
        intervals.append([float(remapped.min()), float(remapped.max())])
        obj = bpy.data.objects[name]
        obj.data.vertices.foreach_set('co', updated.reshape(-1))
        obj.data.update()
    assert all(a[1] < b[0] for a, b in zip(intervals, intervals[1:])), intervals
    records = []
    width, height = job['size']
    focal_px = width*config['focal_mm']/config['sensor_width_mm']
    for index, position in enumerate(config['positions']):
        camera.location = (position, 0, 0)
        camera.data.shift_x = -config['focal_mm']*position/(config['sensor_width_mm']*config['zero'])
        camera.data.shift_y = 0
        bpy.context.view_layer.update()
        checks = []
        for z in (config['near'], config['zero'], config['far']):
            projection = world_to_camera_view(scene, camera, Vector((0, 0, -z)))
            expected = width/2 + focal_px*position*(1/config['zero'] - 1/z)
            assert abs(projection.x*width - expected) < .01
            assert abs(projection.y*height - height/2) < .01
            checks.append(dict(z=z, u_px=projection.x*width, expected_u_px=expected))
        filename = f'views/view_{index:04d}.png'
        target = folder / filename
        reused = target.is_file()
        if not reused:
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
        records.append(dict(index=index, camera_x=position, camera_y=0,
                            shift_x=camera.data.shift_x, shift_y=0, file=filename,
                            projection_checks=checks, reused=reused))
        (folder/'render_result.json').write_text(json.dumps(records, indent=2))
        status = dict(stage='render', variant=variant['id'], completed_views=index+1,
                      total_views=len(config['positions']))
        (manifest_path.parent/'progress.json').write_text(json.dumps(status))
        print('TRIAL_PROGRESS ' + json.dumps(status), flush=True)
    (folder/'geometry-checks.json').write_text(json.dumps(dict(
        strict_layer_order=True, center_projection_preserved=True,
        depth_intervals=intervals, zero_reference=reference), indent=2))
print('ALL_TRIAL_VIEWS_READY', flush=True)
