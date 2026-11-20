# Sherlock - rendu de contrôle « repos » (PNG 512, vue 3/4) + export sherlock.glb + vérification du fichier.
import bpy, os, json, struct, math
from mathutils import Vector

SCR = r"C:\Users\breuilla\AppData\Local\Temp\claude\851202e51721bef7\4117ccba-52cf-45a4-bebf-96650bfc65c0\scratchpad"
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
GLB = os.path.join(OUTD, "sherlock.glb")
sc = bpy.context.scene


def render_repos(setup_light, frame=1, path=None):
    """Vue 3/4 face (caméra à 17° sur la droite du personnage), même cadrage que docs/personnage/repos.png."""
    setup_light()
    cam = bpy.data.objects["Camera"]; cam.data.type = 'PERSP'; cam.data.lens = 90
    d, th = 12.0, math.radians(20)
    cam.location = (-d * math.sin(th), -d * math.cos(th), 3.6)
    bpy.data.objects["Cible_camera"].location = (0, 0, 2.16)
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.frame_set(frame)
    sc.render.filepath = path or os.path.join(OUTD, "repos.png")
    bpy.ops.render.render(write_still=True)
    sc.frame_set(1)


def export_glb(ao_links):
    arm, mesh = bpy.data.objects["Rig"], bpy.data.objects["Sherlock"]
    ao_links(False)                                   # matériaux simples : l'occlusion part dans COLOR_0
    for o in sc.objects: o.select_set(False)
    arm.select_set(True); mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm
    want = dict(filepath=GLB, export_format='GLB', use_selection=True, export_yup=True, export_apply=True,
                export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                export_skins=True, export_all_influences=False, export_morph=False, export_cameras=False,
                export_lights=False, export_draco_mesh_compression_enable=False, export_image_format='AUTO',
                export_texcoords=True, export_normals=True, export_tangents=False, export_materials='EXPORT',
                export_def_bones=False, export_anim_single_armature=True, export_reset_pose_bones=True,
                export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False,
                export_extras=False, export_anim_slide_to_zero=True,
                export_vertex_color='ACTIVE', export_all_vertex_colors=False, export_active_vertex_color_when_no_material=True)
    props = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    kw = {k: v for k, v in want.items() if k in props}
    try:
        bpy.ops.export_scene.gltf(**kw)
    finally:
        ao_links(True)
    return sorted(set(want) - set(kw))


def inspect_glb():
    data = open(GLB, "rb").read()
    jlen = struct.unpack_from("<I", data, 12)[0]
    j = json.loads(data[20:20 + jlen])
    acc = j["accessors"]
    tris = 0; attrs = set(); verts = 0
    for m in j["meshes"]:
        for p in m["primitives"]:
            tris += acc[p["indices"]]["count"] // 3
            verts += acc[p["attributes"]["POSITION"]]["count"]
            attrs |= set(p["attributes"])
    skin = j["skins"][0]
    bones = [j["nodes"][i]["name"] for i in skin["joints"]]
    anims = {}
    for a in j.get("animations", []):
        lo = min(acc[s["input"]]["min"][0] for s in a["samplers"])
        hi = max(acc[s["input"]]["max"][0] for s in a["samplers"])
        targets = sorted({j["nodes"][c["target"]["node"]]["name"] for c in a["channels"]})
        anims[a["name"]] = {"duree": [round(lo, 3), round(hi, 3)], "canaux": len(a["channels"]), "os": targets}
    mats = {}
    for m in j.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        mats[m["name"]] = {"couleur": [round(v, 3) for v in pbr.get("baseColorFactor", [1, 1, 1, 1])[:3]], "texture": "baseColorTexture" in pbr,
                           "normale": "normalTexture" in m, "rugosite": round(pbr.get("roughnessFactor", 1), 2)}
    return {"size_ko": round(len(data) / 1024, 1), "tris": tris, "sommets": verts, "attributs": sorted(attrs), "bones": bones,
            "animations": anims, "materiaux": mats, "images": [i.get("mimeType") for i in j.get("images", [])],
            "extensions": j.get("extensionsUsed", []), "noeuds": len(j["nodes"]), "cameras": len(j.get("cameras", []))}


def job(ao_links, setup_light):
    render_repos(setup_light)
    missing = export_glb(ao_links)
    info = inspect_glb()
    info["options_absentes"] = missing
    open(os.path.join(SCR, "EXPORT_DONE.txt"), "w", encoding="utf-8").write(json.dumps(info, ensure_ascii=False, indent=1))
    return None
