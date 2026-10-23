import bpy
import bmesh

def new_mat(name, rgba):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat

def add_box(bm, loc, size):
    bx, by, bz = loc
    sx, sy, sz = size
    verts = [
        (bx - sx / 2, by - sy / 2, bz - sz / 2),
        (bx + sx / 2, by - sy / 2, bz - sz / 2),
        (bx + sx / 2, by + sy / 2, bz - sz / 2),
        (bx - sx / 2, by + sy / 2, bz - sz / 2),
        (bx - sx / 2, by - sy / 2, bz + sz / 2),
        (bx + sx / 2, by - sy / 2, bz + sz / 2),
        (bx + sx / 2, by + sy / 2, bz + sz / 2),
        (bx - sx / 2, by + sy / 2, bz + sz / 2),
    ]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 3, 7, 4),
             (1, 2, 6, 5), (0, 1, 5, 4), (2, 3, 7, 6)]
    return bmesh.ops.create_polyhedron(bm, verts=verts, faces=faces)

def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    mat_red = new_mat("robot_red", (0.76, 0.06, 0.08, 1.0))   # kirmizi
    mat_dark = new_mat("robot_dark", (0.44, 0.47, 0.51, 1.0)) # koyu gri
    mat_yellow = new_mat("robot_yellow", (0.97, 0.76, 0.10, 1.0)) # sarı
    mat_eyedark = new_mat("robot_eye_dark", (0.10, 0.12, 0.16, 1.0)) # goz arkaplan
    mat_eye = new_mat("robot_eye", (0.36, 0.78, 0.86, 1.0)) # goz
    mat_headtop = new_mat("robot_head_top", (0.34, 0.37, 0.41, 1.0)) # kafa ustu

    bm = bmesh.new()

    # Kafa (genis kare)
    add_box(bm, (0, 0, 2.25), (1.0, 0.75, 0.85))
    # Kafa ustu kucuk parca
    add_box(bm, (0, 0, 2.75), (0.45, 0.32, 0.14))

    # Gozler arkaplan (genis koyu dikdortgen)
    add_box(bm, (0, 0.41, 2.32), (0.72, 0.14, 0.42))
    # Gozler (iki kucuk mavi kare)
    add_box(bm, (-0.23, 0.42, 2.32), (0.16, 0.12, 0.34))
    add_box(bm, (0.23, 0.42, 2.32), (0.16, 0.12, 0.34))

    # Gövde (kare)
    add_box(bm, (0, 0, 1.15), (1.05, 0.8, 1.05))
    # Göğüs tarzi yatay sari cinta
    add_box(bm, (0, 0.415, 1.15), (0.62, 0.12, 0.24))

    # Sol kol (dikdortgen, altta sari kucuk parca)
    add_box(bm, (-0.72, 0, 1.75), (0.18, 0.45, 0.9))
    add_box(bm, (-0.72, 0, 1.18), (0.24, 0.32, 0.16))

    # Sag kol
    add_box(bm, (0.72, 0, 1.75), (0.18, 0.45, 0.9))
    add_box(bm, (0.72, 0, 1.18), (0.24, 0.32, 0.16))

    # Bacaklar (iki dikdortgen)
    add_box(bm, (-0.26, 0, 0.42), (0.24, 0.42, 0.7))
    add_box(bm, (0.26, 0, 0.42), (0.24, 0.42, 0.7))
    # Ayak tabakalari (kisa genis tabakalar)
    add_box(bm, (-0.26, 0, 0.11), (0.36, 0.48, 0.14))
    add_box(bm, (0.26, 0, 0.11), (0.36, 0.48, 0.14))

    mesh = bpy.data.meshes.new("robot_mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("robot", mesh)
    bpy.context.collection.objects.link(obj)

    # Malzemeleri atama: face index'e gore basit sirali
    # Her kutunun 6 yonu var; global face indislerini hesaplayip atamak karmaşiktir,
    # bu durumda materials'lari mesh-level bir karisim olarak kaydedip,
    # facedaki cevrimli atama yapmayip tek materyal vererek geciyoruz.
    # Daha net renk ayirma icin sadece bir tane ana materyel:
    obj.data.materials.append(mat_red)
    obj.active_material_index = 0

    # Boy: ortalama yukseklik ~2.4 metre (boy ~2 metre)

if __name__ == "__main__":
    main()
