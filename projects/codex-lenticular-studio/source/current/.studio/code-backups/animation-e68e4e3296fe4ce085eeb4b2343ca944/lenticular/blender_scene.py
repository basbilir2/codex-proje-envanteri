"""Executed only by Blender's bundled Python, via the host runner."""
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
import numpy as np


def main():
    job_path = Path(sys.argv[sys.argv.index("--") + 1])
    job = json.loads(job_path.read_text(encoding="utf-8"))
    config = job["config"]
    output = job_path.parent
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    # Camera jitter smooths reconstructed silhouettes; no denoising of photo detail.
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.cycles.transparent_max_bounces = 32
    scene.render.resolution_x, scene.render.resolution_y = job["size"]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.film_transparent = True
    if hasattr(scene.render, "use_motion_blur"):
        scene.render.use_motion_blur = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1

    layers = job.get("surfaces") or ([dict(mesh="mesh.npz", texture="source.png", name="Photo depth surface", extend=False)] + job.get("background_layers", []))
    for layer in layers:
        make_surface(output, layer, scene)

    camera_data = bpy.data.cameras.new("Parallel off-axis camera")
    camera = bpy.data.objects.new("Parallel off-axis camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "PERSP"
    camera_data.sensor_fit = "HORIZONTAL"
    camera_data.sensor_width = config["sensor_width_mm"]
    camera_data.lens = config["focal_mm"]
    camera_data.clip_start = min(config["near"], config["zero"]) / 100
    camera_data.clip_end = max(config["far"], config["zero"]) * 100
    camera_data.dof.use_dof = False
    camera.rotation_euler = (0, 0, 0)
    (output / "views").mkdir(exist_ok=True)
    records = []
    width, height = job["size"]
    fpx = width * config["focal_mm"] / config["sensor_width_mm"]
    axis = config.get("camera_axis","x")
    for i, position in enumerate(config["positions"]):
        camera.location = (position,0,0) if axis == "x" else (0,position,0)
        shift = -config["focal_mm"] * position / (config["sensor_width_mm"] * config["zero"])
        camera_data.shift_x = shift if axis == "x" else 0
        camera_data.shift_y = shift if axis == "y" else 0
        bpy.context.view_layer.update()
        checks = []
        for z in (config["near"], config["zero"], config["far"]):
            projected = world_to_camera_view(scene, camera, Vector((0, 0, -z)))
            actual = projected.x * width
            offset = fpx * position * (1/config["zero"]-1/z)
            expected = width/2 + (offset if axis == "x" else 0)
            expected_v = height/2 + (offset if axis == "y" else 0)
            if abs(actual - expected) > 0.01 or abs(projected.y * height - expected_v) > 0.01:
                raise RuntimeError(f"Blender camera projection mismatch: {actual} vs {expected}")
            checks.append(dict(z=z, u_px=actual, v_px=projected.y * height, expected_u_px=expected,expected_v_px=expected_v))
        filename = f"view_{i:04d}.png"
        scene.render.filepath = str(output / "views" / filename)
        bpy.ops.render.render(write_still=True)
        records.append(dict(index=i, camera_x=camera.location.x,camera_y=camera.location.y, shift_x=camera_data.shift_x,shift_y=camera_data.shift_y,
                            file=f"views/{filename}", projection_checks=checks))
        print(f"LENTICULAR_VIEW {i + 1}/{config['nr']}", flush=True)
    camera.location = (0, 0, 0)
    camera_data.shift_x = 0
    camera_data.shift_y = 0
    scene.render.filepath = str(output / "center.png")
    bpy.ops.render.render(write_still=True)
    for image in bpy.data.images:
        if image.source == 'FILE':
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "scene.blend"))
    (output / "render_result.json").write_text(json.dumps(records, indent=2), encoding="utf-8")


def make_surface(output, layer, scene):
    data = np.load(output / layer["mesh"], allow_pickle=False)
    mesh = bpy.data.meshes.new(layer["name"])
    mesh.from_pydata(data["vertices"].tolist(), [], data["triangles"].tolist())
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="Source photo UV")
    loop_vertices = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get("vertex_index", loop_vertices)
    uv_layer.data.foreach_set("uv", data["uv"][loop_vertices].reshape(-1))
    surface = bpy.data.objects.new(layer["name"], mesh)
    scene.collection.objects.link(surface)
    material = bpy.data.materials.new("Original photo unlit")
    material.use_nodes = True
    material.node_tree.nodes.clear()
    nodes, links = material.node_tree.nodes, material.node_tree.links
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(output / layer["texture"]), check_existing=False)
    texture.image.colorspace_settings.name = "sRGB"
    texture.interpolation = "Linear"
    texture.extension = "EXTEND" if layer["extend"] else "CLIP"
    emission = nodes.new("ShaderNodeEmission")
    links.new(texture.outputs["Color"], emission.inputs["Color"])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(texture.outputs["Alpha"], mix.inputs[0])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    material_output = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs[0], material_output.inputs["Surface"])
    surface.data.materials.append(material)



if __name__ == "__main__":
    main()
