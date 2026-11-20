# Sherlock - modèle en T-pose reconstruit d'après les relevés de la planche (reference-tpose.png).
# Unités : 1 u = 131 px de la planche ; pieds à z = 0, sommet du bouton à z = 3,40.
# Avant = -Y ; gauche du personnage = +X (droite de l'image en vue de face).
# Matériaux Principled simples (compatibles glTF) ; seul le tricot de l'écharpe est en texture (générée).
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector, Matrix

OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
TEXD = os.path.join(OUTD, "textures")
os.makedirs(TEXD, exist_ok=True)
M = bpy.data.materials
sc = bpy.context.scene
coll = sc.collection
KEEP = {"Camera", "Cible_camera", "Lumiere_cle", "Lumiere_debouchage", "Lumiere_contre", "Sol_ombre"}
for o in list(bpy.data.objects):
    if o.name not in KEEP:
        bpy.data.objects.remove(o, do_unlink=True)
for coll_ in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures):
    for d in list(coll_):
        if d.users == 0: coll_.remove(d)
for a in list(bpy.data.actions): bpy.data.actions.remove(a)


def hex2lin(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c)


def sgnpow(v, e): return math.copysign(abs(v) ** e, v)


def smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t): return a + (b - a) * t


# ------------------------------------------------------------------ couleurs : bleu et vert d'OPAC SAVOIE exacts, ivoire relevé sur la planche
COL_CORPS, COL_CASQUETTE, COL_ECHARPE, COL_OEIL = "#EBDFD8", "#226891", "#85C595", "#1A2836"


# ------------------------------------------------------------------ textures du tricot (générées, tuile 4 x 4 mailles)
def save_img(name, rgb, non_color):
    n = rgb.shape[0]
    old = bpy.data.images.get(name)
    if old: bpy.data.images.remove(old)
    img = bpy.data.images.new(name, n, n, alpha=False)
    if non_color: img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.concatenate([rgb, np.ones((n, n, 1))], axis=2).astype(np.float32).ravel())
    img.filepath_raw = os.path.join(TEXD, name + ".jpg"); img.file_format = 'JPEG'
    img.save()
    return img


def lin2srgb(a):
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(np.clip(a, 0, None), 1 / 2.4) - 0.055)


N = 256
yy, xx = np.mgrid[0:N, 0:N] / N * 4.0
fx = (xx + 0.5 * np.floor(yy)) % 1.0                         # mailles en quinconce, rangs horizontaux
fy = yy % 1.0
knit = (np.sin(np.pi * fx) ** 0.7) * (np.sin(np.pi * fy) ** 0.7)
g = np.array(hex2lin(COL_ECHARPE))
img_knit_c = save_img("tricot_couleur", lin2srgb(g * (0.84 + 0.22 * np.clip(knit, 0, 1)[..., None])), False)   # moyenne = vert exact
dx = (np.roll(knit, -1, 1) - np.roll(knit, 1, 1)) * 6.0
dy = (np.roll(knit, -1, 0) - np.roll(knit, 1, 0)) * 6.0
nrm = np.stack([-dx, -dy, np.ones_like(knit)], axis=2); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
img_knit_n = save_img("tricot_normale", nrm * 0.5 + 0.5, True)


def simple_mat(name, color, rough, color_img=None, normal_img=None, nstrength=1.0, emission=False):
    m = M.get(name) or M.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); P = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(P.outputs[0], out.inputs[0])
    P.inputs["Base Color"].default_value = tuple(color) + (1,)
    P.inputs["Roughness"].default_value = rough
    if color_img:
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = color_img
        nt.links.new(tx.outputs["Color"], P.inputs["Base Color"])
    if normal_img:
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = normal_img
        nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = nstrength
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], P.inputs["Normal"])
    if emission:
        P.inputs["Emission Color"].default_value = (1, 1, 1, 1); P.inputs["Emission Strength"].default_value = 1.0
    return m


simple_mat("Pate_blanche", hex2lin(COL_CORPS), 0.9)               # pâte à modeler mate
simple_mat("Casquette_bleu", hex2lin(COL_CASQUETTE), 0.92)
simple_mat("Casquette_couture", hex2lin("#1C587C"), 0.92)       # sillons de couture, plus sombres
simple_mat("Echarpe_vert", hex2lin(COL_ECHARPE), 0.95, img_knit_c, img_knit_n, 1.0)
simple_mat("Oeil_marine", hex2lin(COL_OEIL), 0.3)                 # yeux brillants
simple_mat("Blanc_oeil", hex2lin("#F4F1EC"), 0.5)
simple_mat("Reflet", (1, 1, 1), 0.3, emission=True)
simple_mat("Bouche", hex2lin(COL_OEIL), 0.45)
for n in ("Casquette_bleu_uni",):
    if n in M: M.remove(M[n])


def mk(name, bm, mat, recalc=True):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    if recalc: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    for m_ in ([mat] if isinstance(mat, str) else mat): me.materials.append(M[m_])
    return ob


def loft(rings, cap_start=None, cap_end=None, uv=None, mat_fn=None):
    """Surface fermée en travers passant par des anneaux de même nombre de points. cap_* : sommet de fermeture."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap") if uv else None
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(vs) - 1):
        for j in range(n):
            f = bm.faces.new((vs[i][j], vs[i][(j + 1) % n], vs[i + 1][(j + 1) % n], vs[i + 1][j]))
            if mat_fn: f.material_index = mat_fn(i, j)
            if uv:
                for lp, (ci, cj) in zip(f.loops, [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]):
                    lp[uvl].uv = uv(ci, cj)
    for cap, ring in ((cap_start, vs[0]), (cap_end, vs[-1])):
        if cap is None: continue
        c = bm.verts.new(cap)
        for j in range(n):
            bm.faces.new((c, ring[j], ring[(j + 1) % n]))
    return bm


def superellipsoid(u, v, rx, ry, rz, p=2.0):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    for vt in bm.verts:
        x, y, z = vt.co
        phi = math.atan2(math.hypot(x, y), z); th = math.atan2(y, x)
        s = abs(math.sin(phi)) ** (2 / p)
        vt.co = Vector((rx * s * math.cos(th), ry * s * math.sin(th), rz * sgnpow(math.cos(phi), 2 / p)))
    return bm


# ------------------------------------------------------------------ corps : ventre rond, cou resserré, tête large (relevé face + profil)
BODY = [(0.215, 0.17), (0.235, 0.28), (0.27, 0.39), (0.3125, 0.505), (0.381, 0.625), (0.45, 0.697), (0.518, 0.75),
        (0.587, 0.793), (0.655, 0.823), (0.724, 0.842), (0.793, 0.857), (0.861, 0.865), (0.93, 0.865), (0.998, 0.857),
        (1.08, 0.84), (1.17, 0.81), (1.254, 0.78), (1.34, 0.755), (1.44, 0.74), (1.53, 0.765), (1.616, 0.812),
        (1.684, 0.857), (1.753, 0.884), (1.82, 0.903), (1.89, 0.911), (1.96, 0.908), (2.1, 0.897), (2.25, 0.861),
        (2.4, 0.80), (2.55, 0.705), (2.68, 0.585), (2.78, 0.45), (2.85, 0.31), (2.895, 0.16)]
BODY_BOTTOM, BODY_TOP = 0.205, 2.91
NS = 56


def densify(tab, max_dz=0.075):
    """Ajoute un anneau au milieu des intervalles trop hauts (interpolation cubique) : silhouette sans facettes."""
    sl = [(tab[min(i + 1, len(tab) - 1)][1] - tab[max(i - 1, 0)][1]) / (tab[min(i + 1, len(tab) - 1)][0] - tab[max(i - 1, 0)][0]) for i in range(len(tab))]
    out = [tab[0]]
    for i in range(len(tab) - 1):
        (z0, r0), (z1, r1) = tab[i], tab[i + 1]
        if z1 - z0 > max_dz: out.append(((z0 + z1) / 2, (r0 + r1) / 2 + (z1 - z0) / 8 * (sl[i] - sl[i + 1])))
        out.append(tab[i + 1])
    return out


BODY = densify(BODY)


def depth_factors(z):
    t = smooth(1.3, 1.6, z)                       # ventre un peu aplati, tête presque ronde
    return lerp(0.885, 0.925, t), lerp(0.935, 0.955, t)


def body_ring(z, rx):
    ff, fb = depth_factors(z)
    ring = []
    for i in range(NS):
        th = 2 * math.pi * i / NS
        c = math.cos(th)
        ring.append(Vector((rx * math.sin(th), -rx * c * (ff if c > 0 else fb), z)))
    return ring


body = mk("Corps", loft([body_ring(z, r) for z, r in BODY], cap_start=(0, 0, BODY_BOTTOM), cap_end=(0, 0, BODY_TOP)), "Pate_blanche")
bpy.context.view_layer.update()
be = body.evaluated_get(bpy.context.evaluated_depsgraph_get())


def surf(x, z):
    """Point et normale de la surface avant du corps à l'aplomb (x, z) de la vue de face."""
    ok, loc, nor, idx = be.ray_cast(Vector((x, -5, z)), Vector((0, 1, 0)))
    return loc, nor.normalized()


# ------------------------------------------------------------------ jambes et bras (T-pose)
def capsule(length, r0, r1, round_len, p=2.4, seg=16, n_straight=2):
    """Boudin de section ronde le long de +X, de x = 0 (rayon r0, enfoui) à x = length (bout arrondi sur round_len)."""
    u0 = 1 - round_len / length
    rings = []
    for u in [u0 * i / n_straight for i in range(n_straight + 1)] + [u0 + (1 - u0) * t for t in (0.35, 0.6, 0.78, 0.9, 0.97)]:
        r = lerp(r0, r1, u)
        if u > u0: r *= (1 - ((u - u0) / (1 - u0)) ** p) ** (1 / p)
        rings.append([Vector((length * u, r * math.cos(a), r * math.sin(a))) for a in (2 * math.pi * j / seg for j in range(seg))])
    return loft(rings, cap_start=(0, 0, 0), cap_end=(length, 0, 0))


ARM_Y, ARM_Z, ARM_X0, ARM_TIP = 0.16, 1.242, 0.45, 1.223
for s, sx in (("L", 1), ("R", -1)):
    # jambe : cylindre court ovale (0,42 de large, 0,50 de profond), dessous arrondi
    bm = capsule(0.52, 0.215, 0.21, 0.13)
    bm.transform(Matrix.Rotation(math.radians(90), 4, 'Y'))       # +X -> -Z : le bout rond en bas
    bmesh.ops.scale(bm, vec=(1, 1.19, 1), verts=bm.verts)
    mk("Pied." + s, bm, "Pate_blanche").location = (0.28 * sx, -0.01, 0.52)
    # bras : boudin rond horizontal, bout arrondi
    ob = mk("Bras." + s, capsule(ARM_TIP - ARM_X0, 0.215, 0.2, 0.22, n_straight=7), "Pate_blanche")   # anneaux serrés : coude souple
    ob.location = (ARM_X0 * sx, ARM_Y, ARM_Z)
    if sx < 0: ob.rotation_euler = (0, 0, math.pi)

# ------------------------------------------------------------------ yeux : pastilles plaquées sur la tête (ovales exacts en vue de face)
EYE_X, EYE_Z, EYE_W, EYE_H = 0.405, 2.045, 0.212, 0.247          # blanc
PUP_W, PUP_H, PUP_IN = 0.173, 0.226, 0.036                       # pupille, décalée vers le nez
HL_DX, HL_DZ, HL_R = 0.068, 0.115, 0.052                          # reflet, en haut à droite de la pupille
HAPPY_DEPTH = 0.14


def decal(cx, cz, w, h, off, rings=4, seg=24, bulge=0.0):
    """Ellipse (cx, cz, demi-axes w, h en vue de face) plaquée sur la tête, décollée de off ; faces vers l'extérieur."""
    bm = bmesh.new()
    p, n0 = surf(cx, cz)
    c = bm.verts.new(p + n0 * (off + bulge))
    prev = None
    for r in range(1, rings + 1):
        t = r / rings
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            p, n = surf(cx + w * t * math.cos(a), cz + h * t * math.sin(a))
            ring.append(bm.verts.new(p + n * (off + bulge * (1 - t * t) - (0.004 if r == rings else 0.0))))
        for j in range(seg):
            if prev is None: bm.faces.new((c, ring[j], ring[(j + 1) % seg]))
            else: bm.faces.new((prev[j], ring[j], ring[(j + 1) % seg], prev[(j + 1) % seg]))
        prev = ring
    bm.normal_update()
    if sum((f.normal.dot(n0) for f in bm.faces)) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


EYES = {}
for s, sx in (("L", 1), ("R", -1)):
    ex = EYE_X * sx
    mk("Globe." + s, decal(ex, EYE_Z, EYE_W, EYE_H, 0.010, seg=40, bulge=0.004), "Blanc_oeil", recalc=False)
    px_ = ex - PUP_IN * sx
    mk("Pupille." + s, decal(px_, EYE_Z, PUP_W, PUP_H, 0.024, seg=40, bulge=0.006), "Oeil_marine", recalc=False)
    mk("Reflet." + s, decal(px_ + HL_DX, EYE_Z + HL_DZ, HL_R, HL_R, 0.040, rings=2, seg=20), "Reflet", recalc=False)
    mk("Reflet2." + s, decal(px_ - 0.06, EYE_Z - 0.105, 0.022, 0.022, 0.040, rings=1, seg=12), "Reflet", recalc=False)   # petit reflet en bas à gauche
    p, n = surf(ex, EYE_Z)
    EYES[s] = (p.copy(), n.copy())
    # yeux fermés « contents » : arc ∩ bleu marine, rentré sous la peau, sorti par l'os eye_happy_*
    cu = bpy.data.curves.new("Ferme." + s, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = 0.022; cu.bevel_resolution = 2; cu.resolution_u = 6; cu.use_fill_caps = True
    pts = [(-0.19, -0.07), (-0.11, 0.04), (0.0, 0.085), (0.11, 0.04), (0.19, -0.07)]
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bpt, (dx_, dz_) in zip(sp.bezier_points, pts):
        q, qn = surf(ex + dx_, EYE_Z + dz_)
        bpt.co = q + qn * 0.012 - n * HAPPY_DEPTH
        bpt.handle_left_type = bpt.handle_right_type = 'AUTO'
    ar = bpy.data.objects.new("Ferme." + s, cu); coll.objects.link(ar); cu.materials.append(M["Bouche"])

# ------------------------------------------------------------------ bouche : petit « U » doux, bouts arrondis
MOUTH_Z, MOUTH_W = 1.825, 0.14
cu = bpy.data.curves.new("Bouche", 'CURVE'); cu.dimensions = '3D'
cu.bevel_depth = 0.021; cu.bevel_resolution = 2; cu.resolution_u = 6; cu.use_fill_caps = True
U = [(-1.0, 0.05), (-0.8, 0.0), (-0.42, -0.035), (0.0, -0.045), (0.42, -0.035), (0.8, 0.0), (1.0, 0.05)]
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(U) - 1)
MOUTH_PTS = []
for bpt, (ux, uz) in zip(sp.bezier_points, U):
    q, qn = surf(ux * MOUTH_W, MOUTH_Z + uz)
    bpt.co = q + qn * 0.004; bpt.handle_left_type = bpt.handle_right_type = 'AUTO'
    MOUTH_PTS.append(bpt.co.copy())
mo = bpy.data.objects.new("Bouche", cu); coll.objects.link(mo); cu.materials.append(M["Bouche"])
for i, q in enumerate((MOUTH_PTS[0], MOUTH_PTS[-1])):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.021)
    mk("Bouche.bout.%d" % i, bm, "Bouche").location = q

# bouche ouverte (fond sombre + langue), rentrée sous la peau au repos ; sortie et mise en forme par l'os mouth_open
MO_Z, MO_W, MO_H, MO_DEPTH = 1.79, 0.15, 0.125, 0.14
simple_mat("Langue", hex2lin("#4C82B4"), 0.6)
mo_p, mo_n = surf(0.0, MO_Z)
MOUTH_OPEN = (mo_p.copy(), mo_n.copy())
for nm_, bm_, mat_ in (("BoucheOuverte", decal(0.0, MO_Z, MO_W, MO_H, 0.012, rings=3, seg=32, bulge=0.003), "Bouche"),
                       ("Langue", decal(0.0, MO_Z - 0.04, MO_W * 0.6, MO_H * 0.42, 0.02, rings=2, seg=14), "Langue")):
    o_ = mk(nm_, bm_, mat_, recalc=False)
    o_.location = -mo_n * MO_DEPTH

# ------------------------------------------------------------------ casquette (repère local : centre de la calotte, puis bascule de 9° vers l'arrière)
HAT_C = Vector((0.0, 0.14, 2.40))
HAT_TILT = math.radians(9)
HAT = Matrix.Translation(HAT_C) @ Matrix.Rotation(-HAT_TILT, 4, 'X')
HR = 0.82                                                        # + 3 % de bombé des panneaux = 0,845
SEAMS = [math.radians(a) for a in (45, 135, 225, 315)]          # 4 panneaux, coutures en X vers le bouton
SEAM_W = 0.022                                                   # demi-largeur angulaire du sillon
az = sorted(set([round(math.radians(k * 360 / 32), 5) for k in range(32)]
                + [round(s + d, 5) for s in SEAMS for d in (-SEAM_W, SEAM_W)]))


def seam_dist(th):
    return min(abs(math.atan2(math.sin(th - s), math.cos(th - s))) for s in SEAMS)


def seam_factor(th):
    d = seam_dist(th)
    groove = 0.02 if d < 1e-3 else 0.0                            # sillon de couture
    puff = 0.03 * min(1.0, d / 0.5) ** 0.45                        # panneau bombé
    return 1 + puff - groove


rings = []
for k in range(1, 12):
    phi = math.radians(8 + (82 - 8) * (k - 1) / 10)                # de l'apex (caché par le bouton) à la base
    ring = []
    for th in az:
        f = 1 + (seam_factor(th) - 1) * min(1.0, math.sin(phi) * 1.4)
        ring.append(Vector((HR * math.sin(phi) * math.sin(th) * f, -HR * math.sin(phi) * math.cos(th) * f, HR * math.cos(phi))))
    rings.append(ring)
rings.append([Vector((0.76 * math.sin(th), -0.76 * math.cos(th), -0.05)) for th in az])   # retour sous le bandeau
seam_j = {j for j, th in enumerate(az) if seam_dist(th) < SEAM_W + 1e-3 and seam_dist(az[(j + 1) % len(az)]) < SEAM_W + 1e-3}
dome = mk("Casquette", loft(rings, cap_start=(0, 0, HR), cap_end=(0, 0, -0.05), mat_fn=lambda i, j: 1 if (j in seam_j and i < 10) else 0),
          ["Casquette_bleu", "Casquette_couture"])
dome.matrix_world = HAT

# bandeau : gros bourrelet à l'arrière seulement (de rabat à rabat), fondu dans la calotte à ses extrémités
BAND_R, BAND_RR, BAND_RZ, BAND_Z = 0.79, 0.065, 0.155, -0.06
rings = []
NB = 40
for i in range(NB + 1):
    u = -1 + 2 * i / NB
    th = math.pi + math.radians(108) * u                          # centré sur l'arrière
    k = min(1.0, (1 - abs(u)) / 0.2)                              # extrémités effilées, cachées sous les rabats
    rr_, rz_ = BAND_RR * (0.2 + 0.8 * k), BAND_RZ * (0.6 + 0.4 * k)
    rings.append([Vector(((BAND_R + rr_ * math.cos(a)) * math.sin(th), -(BAND_R + rr_ * math.cos(a)) * math.cos(th),
                          BAND_Z + rz_ * sgnpow(math.sin(a), 0.8))) for a in (2 * math.pi * j / 12 for j in range(12))])
c0 = sum(rings[0], Vector()) / 12; c1 = sum(rings[-1], Vector()) / 12
mk("Casquette.Bord", loft(rings, cap_start=c0, cap_end=c1), "Casquette_bleu").matrix_world = HAT

# visière : croissant épais ; le dessus prolonge la calotte puis retombe vers un bord rond, les extrémités s'effilent
VIS_A, VIS_OUT, VIS_H = math.radians(64), 0.21, 0.145
rings = []
NA = 20
for i in range(NA + 1):
    u = -1 + 2 * i / NA
    a = VIS_A * u
    w = max(0.0, math.cos(math.pi / 2 * u)) ** 0.55
    r_in, r_out = 0.70, 0.855 + VIS_OUT * w
    rc, hl, hz = (r_in + r_out) / 2, (r_out - r_in) / 2, VIS_H * (0.18 + 0.82 * w ** 1.3)   # croissant : épais au centre
    ring = []
    for j in range(10):
        b = 2 * math.pi * j / 10
        rr = rc + hl * sgnpow(math.cos(b), 0.6)
        t = max(0.0, rr - 0.84) / max(1e-4, r_out - 0.84)         # 0 à la calotte, 1 au bord
        zz = 0.035 + hz * (1 - 0.35 * t) * sgnpow(math.sin(b), 0.6) - 0.5 * w * max(0.0, rr - 0.84)
        ring.append(Vector((rr * math.sin(a), -rr * math.cos(a), zz)))
    rings.append(ring)
c0 = sum(rings[0], Vector()) / 10; c1 = sum(rings[-1], Vector()) / 10
mk("Visiere", loft(rings, cap_start=c0, cap_end=c1), "Casquette_bleu").matrix_world = HAT

# bouton
bt = mk("Bouton", superellipsoid(16, 8, 0.215, 0.215, 0.085, p=2.5), "Casquette_bleu")   # pastille aplatie, enfoncée dans la calotte
bt.matrix_world = HAT @ Matrix.Translation((0, 0, 0.845))

# rabats : gros coussins en goutte (bas rond, haut resserré), évasés vers l'extérieur
FLAPS = {}
for s, sx in (("L", 1), ("R", -1)):
    bm = superellipsoid(18, 12, 0.21, 0.40, 1.0, p=2.1)
    for v in bm.verts:
        up = max(0.0, v.co.z)                                     # 0 à l'équateur, 1 en haut
        v.co.y *= 1 - 0.1 * up ** 2
        v.co.x *= 1 - 0.15 * up ** 1.5
        v.co.z *= 0.43 if v.co.z > 0 else 0.37
    fl = mk("Rabat." + s, bm, "Casquette_bleu")
    ctr = Vector((0.915 * sx, 0.22, 2.24))
    rot = Matrix.Rotation(math.radians(-24) * sx, 3, 'Y')         # le bas part vers l'extérieur
    fl.matrix_world = Matrix.Translation(ctr) @ rot.to_4x4()
    FLAPS[s] = (ctr + rot @ Vector((0, 0, 0.34)), ctr + rot @ Vector((0, 0, -0.34)))

# ------------------------------------------------------------------ écharpe : boudin tricoté autour du cou, nœud sur le côté, deux pans
SC_Z, SC_R, SC_RR, SC_RZ = 1.445, 0.75, 0.124, 0.154
SC_DEPTH_F, SC_DEPTH_B = 0.87, 0.905
KNOT_AZ = math.radians(28)
COLS, ROWS = 116, 20                                             # mailles le long du tour / autour du boudin
nt, ns = 72, 12
rings = []
for i in range(nt + 1):
    th = 2 * math.pi * (i % nt) / nt
    c = math.cos(th)
    front = max(0.0, c)
    cz = SC_Z - 0.045 * front ** 2                                # un peu plus bas devant
    rz = SC_RZ * (1 + 0.18 * front ** 2)                          # et plus épais
    dep = SC_DEPTH_F if c > 0 else SC_DEPTH_B
    ring = []
    for j in range(ns):
        ph = 2 * math.pi * j / ns
        rr = SC_R + SC_RR * sgnpow(math.cos(ph), 0.6)             # section en rectangle très arrondi
        ring.append(Vector((rr * math.sin(th), -rr * c * dep, cz + rz * sgnpow(math.sin(ph), 0.6))))
    rings.append(ring)
mk("Echarpe", loft(rings, uv=lambda i, j: (i / nt * COLS / 4, j / ns * ROWS / 4)), "Echarpe_vert")

kout = SC_R + SC_RR - 0.02
KN = Vector((kout * math.sin(KNOT_AZ), -kout * math.cos(KNOT_AZ) * SC_DEPTH_F, 1.40))
kn_n = Vector((math.sin(KNOT_AZ), -math.cos(KNOT_AZ), 0)).normalized()
kn_t = Vector((math.cos(KNOT_AZ), math.sin(KNOT_AZ), 0))
bm = superellipsoid(22, 14, 0.21, 0.14, 0.2, p=2.2)
uvl = bm.loops.layers.uv.new("UVMap")
for f in bm.faces:
    for lp in f.loops:
        co = lp.vert.co
        lp[uvl].uv = (math.atan2(co.y, co.x) / (2 * math.pi) * 6, co.z / 0.35 * 2.2)
knot = mk("Noeud", bm, "Echarpe_vert")
knot.matrix_world = Matrix.Translation(KN) @ Matrix((kn_t, -kn_n, Vector((0, 0, 1)))).transposed().to_4x4()

# pans : langues épaisses plaquées sur le ventre, bouts ronds, de longueurs différentes
TAILS = (("Bout.1", (0.37, 1.31), (0.27, 0.905), 0.165, 0.0), ("Bout.2", (0.45, 1.31), (0.585, 0.99), 0.16, 0.015))
TAIL_TH = 0.058
TAIL_PATHS = {}
for name, (x0, z0), (x1, z1), wmax, extra in TAILS:
    NSEG, NR = 16, 14
    rings = []; path = []
    flat = Vector((x1 - x0, 0, z1 - z0)).normalized()

    def frame(x, z):
        p, n = surf(x, z)
        b = n.cross(flat).normalized()
        return p, n, b, b.cross(n).normalized()

    def section(ctr, n, b, w, th_):
        return [ctr + b * (w * sgnpow(math.cos(a), 0.8)) + n * (th_ * sgnpow(math.sin(a), 0.8))
                for a in (2 * math.pi * j / NR for j in range(NR))]

    for i in range(NSEG + 1):
        s_ = i / NSEG
        p, n, b, tdir = frame(lerp(x0, x1, s_), lerp(z0, z1, s_))
        k_ = min(1.0, s_ * 2.0)
        w, th_ = wmax * lerp(0.62, 1.0, k_), TAIL_TH * lerp(0.8, 1.0, k_)
        ctr = p + n * (th_ + 0.008 + extra + 0.03 * (1 - s_) ** 2)   # décollé près du nœud
        path.append(ctr.copy()); rings.append(section(ctr, n, b, w, th_))
    for k in (1, 2, 3):                                          # bout arrondi en demi-cercle
        a_ = math.radians(30 * k)
        xe, ze = x1 + flat.x * wmax * math.sin(a_), z1 + flat.z * wmax * math.sin(a_)
        p, n, b, tdir = frame(xe, ze)
        w, th_ = (wmax * math.cos(a_), TAIL_TH * math.cos(a_ * 0.8)) if k < 3 else (0.02, 0.02)
        ctr = p + n * (th_ + 0.008 + extra)
        path.append(ctr.copy()); rings.append(section(ctr, n, b, w, th_))
    L = (Vector((x1, 0, z1)) - Vector((x0, 0, z0))).length + wmax
    mk("Echarpe." + name, loft(rings, cap_start=path[0], cap_end=path[-1] + tdir * 0.01,
                               uv=lambda i, j, L=L, w=wmax: (j / NR * (4 * w + 0.25) / 0.043 / 4, i / (NSEG + 3) * L / 0.043 / 4)), "Echarpe_vert")
    TAIL_PATHS[name] = (path[0].copy(), path[NSEG // 2].copy(), path[-1].copy())

bpy.context.view_layer.update()
result = {"objets": len(bpy.data.objects)}

# ------------------------------------------------------------------ accessoires des états (un os prop_* chacun, échelle 0 = caché)
simple_mat("Prop_marine", hex2lin("#22405F"), 0.5)
simple_mat("Prop_orange", hex2lin("#E5A13A"), 0.5)
simple_mat("Prop_vert", hex2lin("#7FC08F"), 0.55)
simple_mat("Prop_gris", hex2lin("#B9B2AB"), 0.5)
mj = simple_mat("Prop_jaune", hex2lin("#F7D24B"), 0.4)
Pj = [n_ for n_ in mj.node_tree.nodes if n_.bl_idname == "ShaderNodeBsdfPrincipled"][0]
Pj.inputs["Emission Color"].default_value = tuple(hex2lin("#F7D24B")) + (1,); Pj.inputs["Emission Strength"].default_value = 0.6


def rod(bm, p0, p1, r, seg=8):
    """Bâtonnet à bouts ronds entre deux points, ajouté dans bm."""
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0).normalized()
    u_ = ax.orthogonal().normalized(); v_ = ax.cross(u_)
    rings = []
    for t, k_ in ((-0.75, 0.66), (0.0, 1.0), (1.0, 1.0), (1.75, 0.66)):
        c_ = (p0 + ax * (r * t)) if t <= 0 else (p1 + ax * (r * (t - 1)))
        rings.append([bm.verts.new(c_ + (u_ * math.cos(a) + v_ * math.sin(a)) * r * k_) for a in (2 * math.pi * j / seg for j in range(seg))])
    for i in range(3):
        for j in range(seg):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j]))
    for ring, c_ in ((rings[0], p0 - ax * r), (rings[-1], p1 + ax * r)):
        cv = bm.verts.new(c_)
        for j in range(seg): bm.faces.new((cv, ring[j], ring[(j + 1) % seg]))


def ball(bm, c, r, seg=10):
    tmp_ = bmesh.new(); bmesh.ops.create_uvsphere(tmp_, u_segments=seg, v_segments=max(4, seg // 2 + 1), radius=r)
    me_ = bpy.data.meshes.new("tmp_ball"); tmp_.to_mesh(me_); tmp_.free()
    me_.transform(Matrix.Translation(Vector(c))); bm.from_mesh(me_); bpy.data.meshes.remove(me_)


PROPS = {}      # nom de l'os -> (origine de l'os, os parent)

# loupe : anneau + manche, tenue devant l'oeil droit du personnage (repère = centre de l'anneau)
LOUPE_C = Vector((-0.42, -1.13, 2.03))
bm = bmesh.new()
rings = []
for i in range(21):
    a = 2 * math.pi * (i % 20) / 20
    c_ = Vector((math.cos(a), 0, math.sin(a))) * 0.26
    rings.append([c_ + (Vector((math.cos(a), 0, math.sin(a))) * math.cos(b) + Vector((0, 1, 0)) * math.sin(b)) * 0.05 for b in (2 * math.pi * j / 6 for j in range(6))])
for i in range(20):
    for j in range(6):
        bm.faces.new([bm.verts.new(q) for q in (rings[i][j], rings[i][(j + 1) % 6], rings[i + 1][(j + 1) % 6], rings[i + 1][j])])
rod(bm, (-0.17, 0, -0.26), (-0.34, 0, -0.56), 0.052)
ob = mk("Prop.loupe", bm, "Prop_marine"); ob.location = LOUPE_C
PROPS["prop_loupe"] = (LOUPE_C.copy(), "body")


def verre_loupe():
    """Verre de la loupe : matière transparente qui dévie la lumière. Dans Blender (Eevee) comme dans three.js
    (KHR_materials_transmission, _ior, _volume), l'image vue à travers est décalée selon la pente de la lentille :
    une lentille bombée grossit donc ce qui est derrière."""
    m = M.get("Verre_loupe") or M.new("Verre_loupe")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); P = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(P.outputs[0], out.inputs[0])
    P.inputs["Base Color"].default_value = (1, 1, 1, 1); P.inputs["Roughness"].default_value = 0.03
    P.inputs["Transmission Weight"].default_value = 1.0; P.inputs["IOR"].default_value = LOUPE_IOR
    if "Thickness" in out.inputs: out.inputs["Thickness"].default_value = LOUPE_EP          # Eevee
    for attr, val in (("use_raytrace_refraction", True), ("thickness_mode", 'SLAB'), ("use_transparency_overlap", False)):
        try: setattr(m, attr, val)
        except Exception: pass
    try:                                                                                     # épaisseur pour l'export glTF
        from io_scene_gltf2.blender.com.material_helpers import create_settings_group, get_gltf_node_name
        grp = bpy.data.node_groups.get(get_gltf_node_name()) or create_settings_group(get_gltf_node_name())
        g = nt.nodes.new("ShaderNodeGroup"); g.node_tree = grp; g.name = "glTF_sortie"
        g.inputs["Thickness"].default_value = LOUPE_EP
    except Exception as ex:
        print("Verre de la loupe : épaisseur glTF non posée :", ex)
    return m


# lentille biconvexe : calottes de rayon LOUPE_RC, bord à LOUPE_R (rentre dans l'anneau)
LOUPE_R, LOUPE_RC, LOUPE_IOR, LOUPE_EP = 0.225, 0.39, 1.45, 0.42
LOUPE_VERRE = False      # EN CHANTIER : dans Eevee le verre sort blanc (la réfraction ne trouve pas le visage). Voir saisons/REPRISE.md
if LOUPE_VERRE:
    verre_loupe()
    bm = bmesh.new()
    _sag = lambda r_: math.sqrt(LOUPE_RC ** 2 - r_ ** 2) - math.sqrt(LOUPE_RC ** 2 - LOUPE_R ** 2)
    for sg in (-1, 1):
        c_ = bm.verts.new((0, sg * _sag(0), 0)); prev = None
        for i in range(1, 9):
            r_ = LOUPE_R * i / 8
            ring = [bm.verts.new((r_ * math.cos(a), sg * _sag(r_), r_ * math.sin(a))) for a in (2 * math.pi * j / 28 for j in range(28))]
            for j in range(28):
                if prev is None: bm.faces.new((c_, ring[j], ring[(j + 1) % 28]))
                else: bm.faces.new((prev[j], ring[j], ring[(j + 1) % 28], prev[(j + 1) % 28]))
            prev = ring
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    for f in bm.faces: f.smooth = True
    mk("Prop.loupe.verre", bm, "Verre_loupe").location = LOUPE_C

# point d'exclamation orange, au-dessus de la tête
EXC_C = Vector((0.0, -0.05, 3.62))
bm = bmesh.new(); rod(bm, (0, 0, 0.06), (0, 0, 0.3), 0.055); ball(bm, (0, 0, -0.1), 0.065)
mk("Prop.exclamation", bm, "Prop_orange").location = EXC_C
PROPS["prop_exclamation"] = (EXC_C + Vector((0, 0, -0.17)), "head")

# ampoule jaune (émissive) et son culot, au-dessus de la tête
AMP_C = Vector((0.0, -0.05, 3.66))
bm = bmesh.new(); ball(bm, (0, 0, 0.1), 0.19, 12); mk("Prop.ampoule", bm, "Prop_jaune").location = AMP_C
bm = bmesh.new(); rod(bm, (0, 0, -0.11), (0, 0, -0.17), 0.085); mk("Prop.ampoule.culot", bm, "Prop_gris").location = AMP_C
PROPS["prop_ampoule"] = (AMP_C + Vector((0, 0, -0.2)), "head")

# coche verte, en haut à gauche du personnage (à droite de l'image)
COCHE_C = Vector((1.05, -0.3, 3.0))
bm = bmesh.new(); rod(bm, (-0.16, 0, 0.0), (-0.05, 0, -0.12), 0.045); rod(bm, (-0.05, 0, -0.12), (0.18, 0, 0.16), 0.045)
mk("Prop.coche", bm, "Prop_vert").location = COCHE_C
PROPS["prop_coche"] = (COCHE_C.copy(), "head")

# trois « z » du sommeil, de plus en plus grands, au-dessus de l'épaule droite
for i_, (c_, s_) in enumerate((((-0.72, -0.35, 2.95), 0.1), ((-0.9, -0.35, 3.2), 0.13), ((-1.1, -0.35, 3.5), 0.17))):
    bm = bmesh.new()
    rod(bm, (-s_, 0, s_), (s_, 0, s_), s_ * 0.27, 6); rod(bm, (s_, 0, s_), (-s_, 0, -s_), s_ * 0.27, 6); rod(bm, (-s_, 0, -s_), (s_, 0, -s_), s_ * 0.27, 6)
    nm_ = "prop_z" if i_ == 0 else "prop_z_%d" % (i_ + 1)
    mk("Prop." + nm_, bm, "Prop_marine").location = c_
    PROPS[nm_] = (Vector(c_), "root")

bpy.context.view_layer.update()
result = {"objets": len(bpy.data.objects)}
