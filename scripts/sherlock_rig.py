# Sherlock - rig temps réel (glTF / three.js). Exécuté À LA SUITE de sherlock_build.py, dans le même espace de noms
# (il réutilise EYES, FLAPS, TAIL_PATHS, MOUTH_PTS, MOUTH_OPEN, PROPS, ARM_*, HAPPY_DEPTH...).
# 1. toutes les pièces fusionnées en un seul maillage « Sherlock », chaque pièce pondérée sur son os
# 2. occlusion ambiante cuite dans les couleurs de sommets (modelé doux quel que soit l'éclairage web)
# 3. armature « Rig » aux noms anglais (contrat d'export), pose de repos = T-pose
# Les actions sont créées ensuite par sherlock_anim.py.
from mathutils.bvhtree import BVHTree

O = bpy.data.objects
vl = bpy.context.view_layer
vl.update()
HEAD_C = Vector((0.0, 0.0, 1.95))  # centre de la tête = origine de l'os head
SHOULDER_X, ELBOW_X = 0.62, 0.90   # épaule et coude sur l'axe du bras en T

# ------------------------------------------------------------------ repères des os : nom -> (tête, queue, parent, axe Z local visé)
UP, FRONT = Vector((0, 0, 1)), Vector((0, -1, 0))
A = {"root": ((0, 0, 0), (0, 0, 0.3), None, None), "body": ((0, 0, 0.3), (0, 0, 1.44), "root", None),
     "head": (HEAD_C, HEAD_C + Vector((0, 0, 0.9)), "body", None)}
for s, sx in (("L", 1), ("R", -1)):
    p, n = EYES[s]
    piv = p - n * 0.85                                            # pivot du regard, près du centre de la tête
    A["eye_" + s] = (piv, piv + n * 0.3, "head", UP)
    A["eyelid_" + s] = (p, p + n * 0.12, "eye_" + s, UP)          # porte l'oeil ; Z local = hauteur, X = largeur, Y = vers l'extérieur
    A["eye_happy_" + s] = (p - n * HAPPY_DEPTH, p - n * (HAPPY_DEPTH - 0.12), "eye_" + s, UP)
    A["arm_" + s] = (Vector((SHOULDER_X * sx, ARM_Y, ARM_Z)), Vector((ELBOW_X * sx, ARM_Y, ARM_Z)), "body", UP)
    A["forearm_" + s] = (Vector((ELBOW_X * sx, ARM_Y, ARM_Z)), Vector((ARM_TIP * sx, ARM_Y, ARM_Z)), "arm_" + s, UP)
    A["hat_flap_" + s] = (FLAPS[s][0], FLAPS[s][1], "head", FRONT)
    A["leg_" + s] = (Vector((0.28 * sx, -0.01, 0.5)), Vector((0.28 * sx, -0.01, 0.0)), "root", FRONT)
A["mouth"] = (MOUTH_PTS[3], MOUTH_PTS[3] + Vector((0, -0.12, 0)), "head", UP)
mo_p_, mo_n_ = MOUTH_OPEN
A["mouth_open"] = (mo_p_ - mo_n_ * MO_DEPTH, mo_p_ - mo_n_ * (MO_DEPTH - 0.12), "head", UP)   # Y local = vers l'extérieur
ENDS = {"Echarpe.Bout.1": "scarf_end_1", "Echarpe.Bout.2": "scarf_end_2"}
for name, bn in ENDS.items():
    a_, m_, e_ = TAIL_PATHS[name.replace("Echarpe.", "")]
    A[bn] = (a_, m_, "body", FRONT); A[bn + "_tip"] = (m_, e_, bn, FRONT)
for bn, (c_, par_) in PROPS.items():
    A[bn] = (c_, c_ + Vector((0, 0, 0.15)), par_, None)
BONE_ORDER = (["root", "body", "head"] + [b + s for s in ("L", "R") for b in ("eye_", "eyelid_", "eye_happy_", "arm_", "forearm_", "hat_flap_", "leg_")]
              + ["mouth", "mouth_open", "scarf_end_1", "scarf_end_1_tip", "scarf_end_2", "scarf_end_2_tip"] + list(PROPS))

# ------------------------------------------------------------------ 1. fusion en un seul maillage skinné
RIGID = {"Casquette": "head", "Casquette.Bord": "head", "Visiere": "head", "Bouton": "head",
         "Echarpe": "body", "Noeud": "body", "Bouche": "mouth", "Bouche.bout.0": "mouth", "Bouche.bout.1": "mouth",
         "BoucheOuverte": "mouth_open", "Langue": "mouth_open",
         "Prop.loupe": "prop_loupe", "Prop.exclamation": "prop_exclamation", "Prop.ampoule": "prop_ampoule",
         "Prop.ampoule.culot": "prop_ampoule", "Prop.coche": "prop_coche",
         "Prop.prop_z": "prop_z", "Prop.prop_z_2": "prop_z_2", "Prop.prop_z_3": "prop_z_3"}
for s in ("L", "R"):
    RIGID.update({"Pied." + s: "leg_" + s, "Rabat." + s: "hat_flap_" + s,
                  "Globe." + s: "eyelid_" + s, "Pupille." + s: "eyelid_" + s, "Reflet." + s: "eyelid_" + s,
                  "Reflet2." + s: "eyelid_" + s, "Ferme." + s: "eye_happy_" + s})
ARMS = {"Bras.L": "L", "Bras.R": "R"}
if bpy.data.objects.get("Prop.loupe.verre"): RIGID["Prop.loupe.verre"] = "prop_loupe"      # verre de la loupe, s'il est construit
RIGID.update(globals().get("EXTRA_PARTS", {}))                 # tenues et objets d un thème (sherlock_themes.py)
SKIP = set(globals().get("SKIP_PARTS", ()))                   # pièces retirées par un thème (écharpe, casquette)
for n in SKIP:
    if O.get(n): bpy.data.objects.remove(O[n], do_unlink=True)
parts = [n for n in ["Corps"] + list(RIGID) + list(ENDS) + list(ARMS) if n not in SKIP]
# silhouettes lissées : une subdivision (Catmull-Clark) sur les pièces dont on voit le contour de près
SUBDIV = ("Casquette", "Visiere", "Bouton", "Rabat.L", "Rabat.R", "Bras.L", "Bras.R", "Pied.L", "Pied.R")
for n in [n for n in SUBDIV if n not in SKIP]:
    md_ = O[n].modifiers.new("Lissage", 'SUBSURF'); md_.levels = md_.render_levels = 1
vl.update()
dg = bpy.context.evaluated_depsgraph_get()
tmp = []
for n in parts:
    ob = O[n]
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(ob.matrix_world)
    if me.uv_layers: me.uv_layers[0].name = "UVMap"
    else:                                              # UV nulles : pas de sommets dupliqués à l'export
        uv = me.uv_layers.new(name="UVMap")
        for d in uv.data: d.uv = (0.0, 0.0)
    for pl in me.polygons: pl.use_smooth = True
    t = O.new("tmp_" + n, me); sc.collection.objects.link(t)
    if n == "Corps":
        gr, gb, gh = (t.vertex_groups.new(name=b) for b in ("root", "body", "head"))
        for v in me.vertices:
            z = v.co.z
            wr = 1 - smooth(0.22, 0.5, z); wh = smooth(1.32, 1.6, z); wb = max(0.0, 1 - wr - wh)
            for g_, w in ((gr, wr), (gb, wb), (gh, wh)):
                if w > 1e-4: g_.add([v.index], w, 'REPLACE')
    elif n in ENDS:
        bn = ENDS[n]
        a_, m_, e_ = TAIL_PATHS[n.replace("Echarpe.", "")]
        ax = (e_ - a_); L2 = ax.length_squared
        ga = t.vertex_groups.new(name=bn); gt = t.vertex_groups.new(name=bn + "_tip")
        for v in me.vertices:
            w = smooth(0.3, 0.7, max(0.0, min(1.0, (v.co - a_).dot(ax) / L2)))
            ga.add([v.index], 1 - w, 'REPLACE'); gt.add([v.index], w, 'REPLACE')
    elif n in ARMS:                                    # épaule -> coude : mélange progressif (coude souple, bras étirable)
        s = ARMS[n]
        ga = t.vertex_groups.new(name="arm_" + s); gf = t.vertex_groups.new(name="forearm_" + s)
        for v in me.vertices:
            w = smooth(SHOULDER_X + 0.04, ELBOW_X + 0.06, abs(v.co.x))
            if w < 0.999: ga.add([v.index], 1 - w, 'REPLACE')
            if w > 0.001: gf.add([v.index], w, 'REPLACE')
    else:
        t.vertex_groups.new(name=RIGID[n]).add([v.index for v in me.vertices], 1.0, 'REPLACE')
    tmp.append(t)
for n in parts:
    o = O.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
with bpy.context.temp_override(active_object=tmp[0], selected_editable_objects=tmp, selected_objects=tmp, object=tmp[0]):
    bpy.ops.object.join()
mesh = tmp[0]; mesh.name = "Sherlock"; mesh.data.name = "Sherlock"
me = mesh.data

# ------------------------------------------------------------------ 2. occlusion ambiante par sommet -> couleur de sommet « Col »
THIN = ("Blanc_oeil", "Oeil_marine", "Reflet", "Bouche", "Langue", "Verre_loupe", "Prop_marine", "Prop_orange", "Prop_vert", "Prop_gris", "Prop_jaune")
_thin = {i for i, m_ in enumerate(me.materials) if m_.name in THIN or m_.name.startswith("S_")}        # pastilles, traits, accessoires : pas d'ombre cuite
bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); bm.verts.ensure_lookup_table()
bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons if p.material_index not in _thin])
NDIR = 40
dirs = []
for k in range(NDIR):                                             # hémisphère, répartition de Fibonacci pondérée en cosinus
    z_ = math.sqrt((k + 0.5) / NDIR); r_ = math.sqrt(1 - z_ * z_); ph_ = k * 2.399963
    dirs.append(Vector((r_ * math.cos(ph_), r_ * math.sin(ph_), z_)))
ao = [1.0] * len(bm.verts)
for v in bm.verts:
    nrm_ = v.normal
    if nrm_.length < 1e-6: continue
    q = Vector((0, 0, 1)).rotation_difference(nrm_)
    org = v.co + nrm_ * 0.012
    hits = 0.0
    for d in dirs:
        loc, _n, _i, dist = bvh.ray_cast(org, q @ d, 0.55)
        if loc is not None: hits += 1 - 0.5 * (dist / 0.55)       # un obstacle proche assombrit davantage
    ao[v.index] = 1 - hits / NDIR
for _ in range(2):                                                # lissage
    ao = [0.5 * ao[v.index] + 0.5 * (sum(ao[e.other_vert(v).index] for e in v.link_edges) / max(1, len(v.link_edges))) for v in bm.verts]
bm.free()
NO_AO = _thin | {i for i, m_ in enumerate(me.materials) if m_.name == "Casquette_couture"}
ARM_VG = {mesh.vertex_groups[g].index for g in ("arm_L", "arm_R", "forearm_L", "forearm_R")}
AO_MIN = 0.55
col = me.color_attributes.new("Col", 'BYTE_COLOR', 'CORNER')
for pl in me.polygons:
    for li in pl.loop_indices:
        vtx = me.vertices[me.loops[li].vertex_index]
        a_ = AO_MIN + (1 - AO_MIN) * min(1.0, ao[vtx.index] * 1.15) ** 1.3
        if pl.material_index in NO_AO: a_ = 1.0
        elif any(g.group in ARM_VG for g in vtx.groups): a_ = max(a_, 0.9)     # les bras bougent : presque pas d'ombre cuite
        col.data[li].color = (a_, a_, a_, 1.0)
me.color_attributes.active_color = col
try: me.color_attributes.render_color_index = 0
except Exception: pass


def ao_links(enable):
    """Branche (rendu Blender) ou débranche (export glTF, où COLOR_0 est multiplié par le moteur) l'occlusion dans les matériaux."""
    for m_ in me.materials:
        nt = m_.node_tree
        P = [n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"][0]
        mix = nt.nodes.get("AO_mix")
        if enable and mix is None:
            mix = nt.nodes.new("ShaderNodeMix"); mix.name = "AO_mix"; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1.0
            att = nt.nodes.new("ShaderNodeVertexColor"); att.name = "AO_att"; att.layer_name = "Col"
            src = P.inputs["Base Color"].links[0].from_socket if P.inputs["Base Color"].links else None
            if src: nt.links.new(src, mix.inputs[6])
            else: mix.inputs[6].default_value = P.inputs["Base Color"].default_value
            nt.links.new(att.outputs["Color"], mix.inputs[7])
            nt.links.new(mix.outputs[2], P.inputs["Base Color"])
        elif not enable and mix is not None:
            src = mix.inputs[6].links[0].from_socket if mix.inputs[6].links else None
            for l in list(P.inputs["Base Color"].links): nt.links.remove(l)
            if src: nt.links.new(src, P.inputs["Base Color"])
            nt.nodes.remove(mix); nt.nodes.remove(nt.nodes["AO_att"])


ao_links(True)

# ------------------------------------------------------------------ 3. armature
arm_d = bpy.data.armatures.new("Rig"); arm = O.new("Rig", arm_d); sc.collection.objects.link(arm)
arm.show_in_front = True
for o in sc.objects: o.select_set(False)
vl.objects.active = arm; arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
E = arm_d.edit_bones
for name in BONE_ORDER:
    head_, tail_, par_, roll_to = A[name]
    b = E.new(name); b.head = Vector(head_); b.tail = Vector(tail_); b.roll = 0
    if roll_to is not None: b.align_roll(roll_to)                 # axe Z local de l'os orienté vers roll_to
    if par_: b.parent = E[par_]; b.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
for b in arm_d.bones: b.use_deform = True
mw_ = mesh.matrix_world.copy(); mesh.parent = arm; vl.update(); mesh.matrix_world = mw_
md = mesh.modifiers.new("Armature", 'ARMATURE'); md.object = arm
sc.render.fps = 24
tris = sum(len(p.vertices) - 2 for p in me.polygons)
result = {"bones": len(arm_d.bones), "tris": tris, "verts": len(me.vertices), "materials": [m.name for m in me.materials]}
