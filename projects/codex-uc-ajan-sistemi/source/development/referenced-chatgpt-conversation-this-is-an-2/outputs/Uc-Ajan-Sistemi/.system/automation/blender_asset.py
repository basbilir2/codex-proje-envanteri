"""Run a project's Blender construction script, export and check its actual mesh."""
import bpy
from mathutils import Vector
import json
import math
from pathlib import Path
import runpy
import sys

config=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
output=Path(config['output']);output.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(config['script'],run_name='__main__')
scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
if not meshes:raise ValueError('The script created no visible mesh.')
errors=[];warnings=[];triangles=0;vertices=0;points=[];degenerate=0
deps=bpy.context.evaluated_depsgraph_get()
for obj in meshes:
    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles);vertices+=len(mesh.vertices)
        for v in mesh.vertices:
            p=obj.matrix_world@v.co
            if not all(math.isfinite(x) for x in p):errors.append(obj.name+': non-finite vertex')
            points.append(p)
        for face in mesh.polygons:
            if face.area<1e-12:degenerate+=1
    finally:evaluated.to_mesh_clear()
    if not obj.data.uv_layers:
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15192,island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
    if not obj.data.materials:warnings.append(obj.name+': no material assigned')
if triangles>config['max_triangles']:errors.append(f'Triangle budget exceeded: {triangles} > {config["max_triangles"]}')
if degenerate:errors.append(f'Degenerate faces: {degenerate}')
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file and not Path(bpy.path.abspath(image.filepath)).is_file():
        errors.append('Missing texture: '+image.name)
if errors:raise ValueError('; '.join(errors))
low=Vector(tuple(min(p[i] for p in points) for i in range(3)))
high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
center=(low+high)*.5;radius=max((p-center).length for p in points)
if radius<1e-6:raise ValueError('The mesh has no useful dimensions.')
# Preserve the asset's scale, transforms, rig and animations. Preview cameras are not exported.
for o in list(scene.objects):
    if o.type in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12
scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Studio World');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.12,.14,.18,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.6
for name,offset,power in [('Key',(2,-3,4),950),('Fill',(-3,-1,2),550),('Rim',(0,3,3),800)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power*radius*radius;light.shape='DISK';light.size=radius*3
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj)
    obj.location=center+Vector(offset)*radius;obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Preview Camera');camera=bpy.data.objects.new('Preview Camera',camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=radius*2.4
camera_data.clip_end=max(1000,radius*30)
for view,direction in [('preview',(1.8,-3,1.6)),('back',(-1.8,3,1.3))]:
    camera.location=center+Vector(direction).normalized()*radius*5
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(output/(view+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(output/'model.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.type in ('MESH','ARMATURE','EMPTY') and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(output/'model.glb'),export_format='GLB',use_selection=True,
                          export_cameras=False,export_lights=False,export_animations=True)
report={'passed':True,'triangles':triangles,'vertices':vertices,'meshes':len(meshes),
        'materials':len(bpy.data.materials),'rigs':sum(o.type=='ARMATURE' for o in scene.objects),
        'animations':len(bpy.data.actions),'dimensions_m':[round(x,5) for x in high-low],
        'uv_ready':all(bool(o.data.uv_layers) for o in meshes),'warnings':warnings,
        'method':'Vision-guided procedural Blender modeling; approximate reconstruction, not neural image-to-mesh.'}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(output/'model.glb'))
imported=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not imported or not any(len(o.data.polygons) for o in imported):raise ValueError('Exported GLB did not reimport as a mesh.')
report['glb_roundtrip']=True;report['imported_meshes']=len(imported)
(output/'model-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('UC_AI_ASSET_OK '+str(triangles),flush=True)
