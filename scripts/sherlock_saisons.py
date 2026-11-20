# Sherlock - saisons et fêtes : tenues, objets et animations spéciales. Planches de validation (images fixes).
# Exécuté À LA SUITE de sherlock_build.py, sherlock_rig.py et sherlock_anim.py, dans le même espace de noms.
#
# Principe :
#   - la SAISON donne la base (écharpe en hiver, bottes au printemps, lunettes en été, gilet en automne) ;
#   - la FÊTE ajoute une tenue portée en permanence pendant sa période (étoile, cocarde, chapeau de sorcière...) ;
#   - de temps en temps dans la journée, Sherlock sort un OBJET et joue une ANIMATION SPÉCIALE.
# Chaque thème produit trois images : la tenue, l'objet sorti, la pose clé de l'animation spéciale.
# Rien ici ne modifie sherlock.glb : les accessoires sont des objets à part, posés sur les os pour le rendu.
#
# Les formes sont modelées « pâte à modeler lisse » : pièces bombées (pillow), tournées (lathe), tubes souples (tube),
# feuilles épaisses (sheet), boîtes aux arêtes rondes (rbox). Les objets tenus ont leur origine AU POINT DE PRISE :
# c'est ce point qui vient au centre du poing.
import json, random
from mathutils import Euler

OUT = os.path.abspath(SAISONS_OUT); os.makedirs(OUT, exist_ok=True)
FILTRE = [k for k in SAISONS_FILTRE.split(",") if k]
rnd = random.Random(11)
TAU = 2 * math.pi

# ------------------------------------------------------------------ matières et atelier de formes
_mats = {}


def smat(col, emit=0.0, rough=0.7):
    key = (col, round(emit, 2), rough)
    if key in _mats: return _mats[key]
    m = bpy.data.materials.new("S_%s_%d_%d" % (col.lstrip("#"), int(emit * 100), int(rough * 100))); m.use_nodes = True
    P_ = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"][0]
    P_.inputs["Base Color"].default_value = tuple(hex2lin(col)) + (1,); P_.inputs["Roughness"].default_value = rough
    if emit: P_.inputs["Emission Color"].default_value = tuple(hex2lin(col)) + (1,); P_.inputs["Emission Strength"].default_value = emit
    _mats[key] = m
    return m


def TRS(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    if not isinstance(scale, (tuple, list)): scale = (scale, scale, scale)
    return Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Diagonal(tuple(scale) + (1,))


def chaikin(pts, it=2, closed=True):
    """Arrondit un contour (coins coupés) ; ouvert : les deux bouts restent en place."""
    for _ in range(it):
        out = []; n = len(pts)
        for i in range(n if closed else n - 1):
            a, b_ = pts[i], pts[(i + 1) % n]
            out.append(tuple(0.75 * u + 0.25 * v for u, v in zip(a, b_))); out.append(tuple(0.25 * u + 0.75 * v for u, v in zip(a, b_)))
        pts = out if closed else [pts[0]] + out + [pts[-1]]
    return pts


def _frames(pts, up=None):
    """Repères (tangente, normale, binormale) le long d'une ligne, sans vrille."""
    pts = [Vector(p) for p in pts]; n = len(pts)
    tg = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    u = Vector(up) if up else Vector((0, -1, 0))
    if abs(u.dot(tg[0])) > 0.95: u = Vector((1, 0, 0))
    nr = [(u - tg[0] * u.dot(tg[0])).normalized()]
    for i in range(1, n):
        v = nr[-1] - tg[i] * nr[-1].dot(tg[i])
        nr.append(v.normalized() if v.length > 1e-6 else nr[-1])
    return pts, tg, nr, [t_.cross(n_) for t_, n_ in zip(tg, nr)]


class B:
    """Accumule des formes dans un seul objet. Axes : X droite, Y profondeur (-Y = vers la caméra), Z haut."""
    def __init__(s, name, base=None):
        s.name, s.bm, s.mats, s.base = name, bmesh.new(), [], base or Matrix.Identity(4)

    def sub(s, M_):
        """Même objet, vu dans un repère local (pour poser une pièce sur une autre)."""
        v = B.__new__(B); v.name, v.bm, v.mats, v.base = s.name, s.bm, s.mats, s.base @ M_
        return v

    def _mi(s, col, emit=0.0, rough=0.7):
        m = smat(col, emit, rough)
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)

    def _merge(s, tmp, M_):
        bmesh.ops.transform(tmp, matrix=s.base @ M_, verts=tmp.verts)
        me_ = bpy.data.meshes.new("t"); tmp.to_mesh(me_); tmp.free(); s.bm.from_mesh(me_); bpy.data.meshes.remove(me_)
        return s

    def _add(s, tmp, M_, col, emit=0.0, rough=0.7):
        i = s._mi(col, emit, rough)
        for f in tmp.faces: f.material_index = i; f.smooth = True
        return s._merge(tmp, M_)

    def sphere(s, col, loc=(0, 0, 0), r=1.0, scale=(1, 1, 1), rot=(0, 0, 0), emit=0.0, seg=18, fn=None, rough=0.7):
        tmp = bmesh.new(); bmesh.ops.create_uvsphere(tmp, u_segments=seg, v_segments=max(6, seg // 2 + 1), radius=r)
        if fn:
            for v in tmp.verts: fn(v)
        return s._add(tmp, TRS(loc, rot, scale), col, emit, rough)

    def cone(s, col, loc=(0, 0, 0), r1=1.0, r2=0.0, h=1.0, rot=(0, 0, 0), scale=(1, 1, 1), emit=0.0, seg=20, rough=0.7):
        """Tronc de cône d'axe Z, base (rayon r1) à z = 0, sommet (rayon r2) à z = h."""
        tmp = bmesh.new(); bmesh.ops.create_cone(tmp, cap_ends=True, cap_tris=False, segments=seg, radius1=max(r1, 1e-3), radius2=max(r2, 1e-3), depth=h)
        bmesh.ops.translate(tmp, vec=(0, 0, h / 2), verts=tmp.verts)
        return s._add(tmp, TRS(loc, rot, scale), col, emit, rough)

    def rbox(s, col, loc=(0, 0, 0), size=(1, 1, 1), rot=(0, 0, 0), r=0.3, seg=3, emit=0.0, rough=0.7):
        """Boîte aux arêtes rondes (r : part du plus petit côté)."""
        tmp = bmesh.new(); bmesh.ops.create_cube(tmp, size=1.0)
        bmesh.ops.scale(tmp, vec=size, verts=tmp.verts)
        bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=r * min(size), segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)
        return s._add(tmp, TRS(loc, rot, 1), col, emit, rough)

    def tube(s, col, pts, r, seg=8, up=None, emit=0.0, rough=0.7):
        """Tube le long d'une ligne. r : rayon, ou (épaisseur le long de « up », demi-largeur), ou fonction de t (0 à 1)."""
        pts, tg, nr, bn = _frames(pts, up); n = len(pts); tmp = bmesh.new(); rings = []
        for i in range(n):
            rr = r(i / (n - 1)) if callable(r) else r
            ra, rb = rr if isinstance(rr, tuple) else (rr, rr)
            rings.append([tmp.verts.new(pts[i] + nr[i] * (ra * math.cos(a)) + bn[i] * (rb * math.sin(a))) for a in (TAU * j / seg for j in range(seg))])
        for i in range(n - 1):
            for j in range(seg): tmp.faces.new((rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j]))
        for ring, p in ((rings[0], pts[0]), (rings[-1], pts[-1])):
            c = tmp.verts.new(p)
            for j in range(seg): tmp.faces.new((c, ring[j], ring[(j + 1) % seg]))
        return s._add(tmp, Matrix.Identity(4), col, emit, rough)

    def lathe(s, col, prof, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), seg=28, emit=0.0, rough=0.7, wob=None, colfn=None):
        """Pièce tournée autour de Z. prof : (rayon, z) de bas en haut, rayon 0 aux deux bouts. wob(a, i, r, z) -> (r, z)."""
        tmp = bmesh.new(); rings = []
        for i, (r, z) in enumerate(prof):
            if r < 1e-5: rings.append([tmp.verts.new((0, 0, z))]); continue
            ring = []
            for j in range(seg):
                a = TAU * j / seg; rr, zz = wob(a, i, r, z) if wob else (r, z)
                ring.append(tmp.verts.new((rr * math.cos(a), rr * math.sin(a), zz)))
            rings.append(ring)
        idx = s._mi(col, emit, rough)
        for i in range(len(rings) - 1):
            r0_, r1_ = rings[i], rings[i + 1]
            if len(r0_) == 1 and len(r1_) == 1: continue
            for j in range(seg):
                k = (j + 1) % seg
                if len(r0_) == 1: f = tmp.faces.new((r0_[0], r1_[k], r1_[j]))
                elif len(r1_) == 1: f = tmp.faces.new((r0_[j], r0_[k], r1_[0]))
                else: f = tmp.faces.new((r0_[j], r0_[k], r1_[k], r1_[j]))
                f.smooth = True; f.material_index = s._mi(colfn(i, j), emit, rough) if colfn else idx
        return s._merge(tmp, TRS(loc, rot, scale))

    def pillow(s, col, pts, thick, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), edge=1.0, n=4, emit=0.0, rough=0.7):
        """Forme plate (contour x, z, étoilé autour de son centre) bombée comme un biscuit, épaisseur le long de Y.
        edge : part de la largeur prise par l'arrondi (1 = lentille, 0,2 = plat à bord rond)."""
        cx = sum(p[0] for p in pts) / len(pts); cz = sum(p[1] for p in pts) / len(pts)
        tmp = bmesh.new(); m = len(pts)

        def ring(k, sgn):
            th = (math.pi / 2) * k / n; f = 1 - edge * (1 - math.cos(th))
            return [tmp.verts.new((cx + (x - cx) * f, sgn * thick / 2 * math.sin(th), cz + (z - cz) * f)) for x, z in pts]
        eq = ring(0, 0)
        for sgn in (-1, 1):
            prev = eq
            for k in range(1, (n if edge < 0.999 else n - 1) + 1):
                cur = ring(k, sgn)
                for j in range(m): tmp.faces.new((prev[j], prev[(j + 1) % m], cur[(j + 1) % m], cur[j]))
                prev = cur
            c = tmp.verts.new((cx, sgn * thick / 2, cz))
            for j in range(m): tmp.faces.new((prev[j], prev[(j + 1) % m], c))
        return s._add(tmp, TRS(loc, rot, scale), col, emit, rough)

    def sheet(s, col, fn, nu, nv, thick, wrap=False, emit=0.0, rough=0.7, colfn=None):
        """Feuille épaisse : fn(u, v) -> (point, normale), u et v de 0 à 1 ; wrap : refermée en u."""
        tmp = bmesh.new(); cu = nu if wrap else nu + 1; fr, bk = [], []
        for i in range(cu):
            a_, b_ = [], []
            for j in range(nv + 1):
                p, n_ = fn(i / nu, j / nv)
                a_.append(tmp.verts.new(Vector(p) + Vector(n_) * (thick / 2))); b_.append(tmp.verts.new(Vector(p) - Vector(n_) * (thick / 2)))
            fr.append(a_); bk.append(b_)
        idx = s._mi(col, emit, rough)

        def quad(vs, i, j):
            f = tmp.faces.new(vs); f.smooth = True; f.material_index = s._mi(colfn(i, j), emit, rough) if colfn else idx
        for i in range(nu):
            i2 = (i + 1) % cu
            for j in range(nv):
                quad((fr[i][j], fr[i2][j], fr[i2][j + 1], fr[i][j + 1]), i, j)
                quad((bk[i][j], bk[i][j + 1], bk[i2][j + 1], bk[i2][j]), i, j)
            quad((fr[i][0], bk[i][0], bk[i2][0], fr[i2][0]), i, 0)
            quad((fr[i][nv], fr[i2][nv], bk[i2][nv], bk[i][nv]), i, nv - 1)
        if not wrap:
            for i, ii in ((0, 0), (nu, nu - 1)):
                for j in range(nv): quad((fr[i][j], fr[i][j + 1], bk[i][j + 1], bk[i][j]), ii, j)
        return s._merge(tmp, Matrix.Identity(4))

    def torus(s, col, loc=(0, 0, 0), R=1.0, r=0.2, rot=(0, 0, 0), scale=(1, 1, 1), seg=36, rs=10, emit=0.0, rough=0.7):
        """Tore d'axe Z (dans le plan XY)."""
        tmp = bmesh.new(); rings = []
        for i in range(seg):
            a = TAU * i / seg; rad = Vector((math.cos(a), math.sin(a), 0))
            rings.append([tmp.verts.new(rad * R + (rad * math.cos(b_) + Vector((0, 0, 1)) * math.sin(b_)) * r) for b_ in (TAU * j / rs for j in range(rs))])
        for i in range(seg):
            for j in range(rs): tmp.faces.new((rings[i][j], rings[i][(j + 1) % rs], rings[(i + 1) % seg][(j + 1) % rs], rings[(i + 1) % seg][j]))
        return s._add(tmp, TRS(loc, rot, scale), col, emit, rough)

    def done(s):
        bmesh.ops.recalc_face_normals(s.bm, faces=s.bm.faces)
        me_ = bpy.data.meshes.new("S_" + s.name); s.bm.to_mesh(me_); s.bm.free()
        for m in s.mats: me_.materials.append(m)
        ob = bpy.data.objects.new("S." + s.name, me_); coll.objects.link(ob)
        return ob


def star(R, n=5, inner=0.45):
    return [(R * (1 if k % 2 == 0 else inner) * math.cos(math.radians(90 + 180 * k / n)), R * (1 if k % 2 == 0 else inner) * math.sin(math.radians(90 + 180 * k / n))) for k in range(2 * n)]


def heart(R, n=36):
    pts = []
    for k in range(n):
        t = TAU * k / n
        pts.append((R * 16 * math.sin(t) ** 3 / 17, R * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17 + 0.15 * R))
    return pts[::-1]


def ellipse(w, h, n=24, pointed=1.0):
    return [(w * math.copysign(abs(math.sin(TAU * k / n)) ** pointed, math.sin(TAU * k / n)), h * math.cos(TAU * k / n)) for k in range(n)][::-1]


def polar(fn, n=48):
    """Contour (x, z) donné par un rayon fonction de l'angle (0 = vers le haut)."""
    return [(fn(TAU * k / n) * math.sin(TAU * k / n), fn(TAU * k / n) * math.cos(TAU * k / n)) for k in range(n)][::-1]


# ------------------------------------------------------------------ repères sur le personnage (pose de liaison)
def dome(a, e, out=0.0):
    """Point de la calotte (a : azimut depuis l'avant, positif vers sa gauche ; e : élévation) et sa normale."""
    a, e = math.radians(a), math.radians(e)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    n = (HAT.to_3x3() @ d).normalized()
    return HAT @ (d * HR * 1.03) + n * out, n


def facing(pos, n, roll=0.0):
    """Repère posé en pos, dont la face (-Y local) regarde le long de n."""
    y = -n; x = y.cross(Vector((0, 0, 1)))
    if x.length < 1e-4: x = Vector((1, 0, 0))
    x.normalize(); z = x.cross(y).normalized()
    return Matrix.Translation(pos) @ Matrix((x, y, z)).transposed().to_4x4() @ Matrix.Rotation(math.radians(roll), 4, 'Y')


def body_rx(z):
    for (z0, r0), (z1, r1) in zip(BODY, BODY[1:]):
        if z0 <= z <= z1: return lerp(r0, r1, (z - z0) / (z1 - z0))
    return BODY[-1][1] if z > BODY[-1][0] else BODY[0][1]


def body_pt(th, z, k=1.0):
    """Point de la surface du corps (th : azimut depuis l'avant, positif vers sa gauche)."""
    rx = body_rx(z)
    ff, fb = depth_factors(z); c = math.cos(th)
    return Vector((rx * math.sin(th) * k, -rx * c * (ff if c > 0 else fb) * k, z))


def body_n(th):
    return Vector((math.sin(th), -math.cos(th), 0))


def face_pt(x, z, out=0.0):
    """Point du visage à l'aplomb (x, z) de la vue de face, décollé de out, et sa normale (horizontale)."""
    th = math.asin(max(-0.985, min(0.985, x / body_rx(z))))
    n = body_n(th)
    return body_pt(th, z) + n * out, n


OR, OR_F, ROUGE, BLANC, CREME = "#F4BC2E", "#D9952B", "#E0453F", "#FFFFFF", "#FBF3E4"
VERT_F, VERT_C, ROSE, JAUNE, BLEU_F, VIOLET, ORANGE, BRUN, NOIR = "#4E9A52", "#8CCB7E", "#F29BB2", "#F7D24B", "#2B5DAA", "#9163C6", "#F08A24", "#8A5A33", "#2B2B33"
VERT_E, VERT_EF = "#85C595", "#5FA574"                  # le vert de l'écharpe et sa nuance foncée : accessoires de saison
EAU = "#7FC4EE"
EXTRA, REST_M = [], {}


def reg(ob, bone=""):
    ob.hide_render = True; ob["os"] = bone; EXTRA.append(ob); REST_M[ob.name] = ob.matrix_world.copy()
    return ob


def clone(ob):
    c = bpy.data.objects.new(ob.name + ".c", ob.data); coll.objects.link(c)
    return reg(c, ob["os"])


def feather(b, col, base, ang, L, W, curl=0.25, quill="#FFF4D6"):
    """Plume dans le plan XZ du repère, partant de base, inclinée de ang (degrés, positif vers +X), recourbée."""
    a = math.radians(ang); ax, az = Vector((math.sin(a), 0, math.cos(a))), Vector((math.cos(a), 0, -math.sin(a)))
    sp = [Vector(base) + ax * (L * t) + az * (curl * L * t * t) for t in (i / 16 for i in range(17))]
    b.tube(col, sp[1:], lambda t: (0.016 + 0.014 * math.sin(math.pi * t), W * math.sin(math.pi * min(1.0, 0.04 + t) ** 0.7) ** 0.75 * (1 - 0.1 * max(0.0, math.sin(11 * math.pi * t)) ** 6) + 0.004), seg=10, up=(0, -1, 0), rough=0.8)
    b.tube(quill, [p + Vector((0, -0.016, 0)) for p in sp[:15]], lambda t: 0.013 * (1 - 0.6 * t), seg=6)


def leaf(b, col, p0, p1, W, bend=(0, 0, 0), th=0.012, n=10):
    """Feuille en ruban de p0 à p1, cintrée de bend au milieu, large de 2 W au plus."""
    p0, p1, bend = Vector(p0), Vector(p1), Vector(bend)
    sp = [p0.lerp(p1, t) + bend * math.sin(math.pi * t) for t in (i / n for i in range(n + 1))]
    b.tube(col, sp, lambda t: (th, W * math.sin(math.pi * min(1.0, 0.06 + 0.94 * t)) ** 0.65 + 0.004), seg=8, up=(0, -1, 0))


# ================================================================== TENUES (portées en permanence pendant la période)
T = {}

# étoile et cœur : épinglés sur le devant de la casquette, bien bombés
T["etoile"] = reg(B("Etoile", facing(*dome(-36, 40, 0.04))).pillow(OR, chaikin(star(0.3, 5, 0.52), 2), 0.17, emit=0.18, rough=0.4).done(), "head")
T["coeur"] = reg(B("CoeurCasquette", facing(*dome(-36, 40, 0.045))).pillow(ROUGE, heart(0.26), 0.18, rough=0.35, emit=0.05).done(), "head")

# cocarde : rosette plissée bleu, blanc, rouge et ses deux rubans
b = B("Cocarde", facing(*dome(-42, 24, 0.035), roll=8))
for sx, col in ((-1, BLEU_F), (1, ROUGE)):
    b.tube(col, [(0.05 * sx, -0.02, -0.1), (0.11 * sx, -0.05, -0.34), (0.2 * sx, -0.1, -0.62)], (0.016, 0.085), seg=8, up=(0, -1, 0))
b.lathe(ROUGE, [(0, 0), (0.3, 0.0), (0.32, 0.03), (0.22, 0.06), (0, 0.06)], rot=(90, 0, 0), seg=44,
        wob=lambda a, i, r, z: (r * (1 + 0.035 * math.cos(11 * a)), z + 0.03 * math.cos(11 * a) * (r / 0.3)))
b.lathe(BLANC, [(0, 0.05), (0.2, 0.05), (0.215, 0.075), (0.15, 0.1), (0, 0.1)], rot=(90, 0, 0), seg=44,
        wob=lambda a, i, r, z: (r * (1 + 0.03 * math.cos(11 * a + 1)), z + 0.02 * math.cos(11 * a + 1) * (r / 0.2)))
b.sphere(BLEU_F, (0, -0.105, 0), 0.115, (1, 0.45, 1), rough=0.45)
T["cocarde"] = reg(b.done(), "head")

# lunettes de soleil relevées sur la casquette (monture au vert de l'écharpe)
b = B("Lunettes", facing(*dome(0, 47, 0.065)))
VERRE = chaikin([(-0.24, 0.16), (0.24, 0.17), (0.21, -0.14), (-0.18, -0.15)], 3)
for sx in (1, -1):
    b.pillow(VERT_EF, [(x * sx, z) for x, z in VERRE][::sx], 0.1, loc=(0.27 * sx, 0, 0), edge=0.3, rough=0.5)
    b.pillow("#25303F", [(x * sx * 0.8, z * 0.78) for x, z in VERRE][::sx], 0.125, loc=(0.27 * sx, -0.005, 0.002), edge=0.5, rough=0.12)
    b.pillow(BLANC, ellipse(0.035, 0.07, 12), 0.02, loc=(0.27 * sx - 0.09, -0.066, 0.05), rot=(0, 35, 0), emit=0.6)
    b.tube(VERT_EF, [(0.5 * sx, 0.0, 0.08), (0.6 * sx, 0.2, 0.12), (0.66 * sx, 0.44, 0.1)], 0.035, seg=8)
b.tube(VERT_EF, [(-0.07, -0.01, 0.07), (0, -0.02, 0.1), (0.07, -0.01, 0.07)], 0.035, seg=8)
T["lunettes"] = reg(b.done(), "head")

# plumes de carnaval : trois grandes plumes sur le côté droit de la casquette
b = B("Plumes", Matrix.Translation(dome(-58, 30, -0.03)[0]) @ Matrix.Rotation(math.radians(-20), 4, 'Z'))
feather(b, VERT_F, (0.0, 0.03, 0.0), -86, 0.8, 0.2, -0.3)
feather(b, VIOLET, (0.0, 0.0, 0.0), -50, 1.05, 0.22, -0.28)
feather(b, "#F5A93A", (0.0, -0.03, 0.0), -16, 1.12, 0.2, -0.2)
b.sphere(OR, (-0.02, -0.07, 0.03), 0.085, (1, 0.6, 1), emit=0.15, rough=0.4)
T["plumes"] = reg(b.done(), "head")

# oreilles de lapin sur un serre-tête
b = B("Oreilles", HAT)
b.tube("#8FC7E8", [(0.875 * math.sin(math.radians(a)), -0.04, 0.875 * math.cos(math.radians(a))) for a in range(-64, 65, 8)], (0.03, 0.065), seg=8, up=(0, -1, 0))
for sx in (1, -1):
    e_ = b.sub(Matrix.Translation((0.3 * sx, -0.04, 0.8)) @ Matrix.Rotation(math.radians(17 * sx), 4, 'Y'))
    e_.sphere(BLANC, (0, 0, 0.42), 1.0, (0.2, 0.11, 0.5), seg=20)
    e_.pillow("#F7A8BF", ellipse(0.105, 0.36, 24, 1.2), 0.07, loc=(0, -0.085, 0.43))
    b.sphere(OR, (0.45 * sx, -0.11, 0.74), 0.055, rough=0.4)
T["oreilles"] = reg(b.done(), "head")


# couronne des rois : bandeau évasé à cinq pointes, perles et pierres, posée autour du haut de la casquette
def build_crown(b, r0=0.57, hb=0.2, hp=0.3, flare=0.3, th=0.045, gems=True):
    def top(a): return hb + hp * (0.5 + 0.5 * math.cos(5 * a)) ** 1.7

    def fn(u, v):
        a = TAU * u; z = v * top(a); r = r0 + flare * z * z
        return Vector((r * math.sin(a), -r * math.cos(a), z)), Vector((math.sin(a), -math.cos(a), 0))
    b.sheet(OR, fn, 80, 5, th, wrap=True, emit=0.1, rough=0.38)
    b.torus(OR_F, (0, 0, 0.015), r0 + 0.005, 0.042, rough=0.38, emit=0.1)
    b.torus(OR_F, (0, 0, hb), r0 + flare * hb * hb + 0.012, 0.022, rough=0.38, emit=0.1)
    for k in range(5):
        a = TAU * k / 5; z = top(a); r = r0 + flare * z * z
        b.sphere(OR, (r * math.sin(a), -r * math.cos(a), z + 0.03), 0.062, emit=0.15, rough=0.35)
        if not gems: continue
        g = b.sub(Matrix.Translation(((r0 + 0.03) * math.sin(a), -(r0 + 0.03) * math.cos(a), hb * 0.52)) @ Matrix.Rotation(a, 4, 'Z'))
        if k == 0: g.pillow(ROUGE, chaikin([(0, 0.105), (0.075, 0), (0, -0.105), (-0.075, 0)], 1), 0.09, rough=0.2, emit=0.2)
        else: g.sphere("#3D7FD9" if k in (1, 4) else "#3FAE6B", (0, 0, 0), 0.062, (1, 0.6, 1), rough=0.2, emit=0.2)
        a2 = a + TAU / 10
        b.sphere(OR, ((r0 + 0.035) * math.sin(a2), -(r0 + 0.035) * math.cos(a2), hb * 0.52), 0.026, rough=0.35, emit=0.1)


b = B("Couronne", HAT @ Matrix.Translation((0, 0, 0.6)) @ Matrix.Rotation(math.radians(-5), 4, 'Y')); build_crown(b)
T["couronne"] = reg(b.done(), "head")

# toque de chef : bandeau droit et haut bouffant plissé
b = B("Toque", HAT @ Matrix.Translation((0, 0.02, 0.72)) @ Matrix.Rotation(math.radians(6), 4, 'Y'))
b.lathe(BLANC, [(0, 0), (0.37, 0.0), (0.385, 0.03), (0.39, 0.3), (0.37, 0.33), (0, 0.33)], seg=32)
def _plis(v):
    k = 1 + 0.06 * math.cos(9 * math.atan2(v.co.y, v.co.x)) * (1 - (v.co.z / 0.5) ** 2)
    v.co.x *= k; v.co.y *= k


b.sphere("#FAFAFA", (0, 0, 0.55), 0.5, (1, 1, 0.66), seg=30, fn=_plis)
T["toque"] = reg(b.done(), "head")


def build_muguet(b, s=1.0):
    """Brin de muguet : les tiges serrées passent dans le poing (origine = point de prise), feuilles et clochettes au-dessus."""
    for dx in (-0.018, 0.0, 0.018): b.tube(VERT_F, [(dx * s, 0, -0.3 * s), (dx * 0.5 * s, 0, 0.24 * s)], 0.016 * s, seg=6)
    for k, (bend, L, nb) in enumerate(((0.44, 1.0, 5), (-0.22, 0.84, 4))):
        sp = [Vector((bend * t ** 2.2 * s, -0.03 * k * s, (0.2 + (L - 0.2) * t - 0.1 * t ** 3) * s)) for t in (i / 14 for i in range(15))]
        b.tube(VERT_F, sp, lambda t: 0.017 * s * (1 - 0.45 * t), seg=6)
        for i in range(nb):
            p = sp[14 - 2 * i - (1 if k else 0)]; sd = 1 if bend > 0 else -1; sz = (0.85 + 0.07 * i) * s
            q = p + Vector((0.075 * sd * s, -0.015, -0.07 * s))
            b.tube(VERT_F, [p, p + Vector((0.06 * sd * s, -0.01, -0.015 * s)), q], 0.008 * s, seg=5)
            b.lathe(BLANC, [(0, 0.035), (0.03, 0.03), (0.047, 0.0), (0.052, -0.035), (0.064, -0.055), (0.046, -0.05), (0, -0.04)], loc=q + Vector((0, 0, -0.03 * s)), scale=sz, seg=12,
                    wob=lambda a, i_, r, z: (r * (1 + (0.16 * math.cos(6 * a) if i_ in (4, 5) else 0)), z), rough=0.5)
    leaf(b, VERT_F, (0.0, 0.03 * s, 0.2 * s), (-0.3 * s, 0.07 * s, 0.8 * s), 0.11 * s, (-0.07 * s, 0, 0), 0.014 * s)
    leaf(b, "#5CAB5E", (0.0, 0.04 * s, 0.2 * s), (0.2 * s, 0.09 * s, 0.7 * s), 0.1 * s, (0.08 * s, 0, 0), 0.014 * s)


def build_note(b, col="#3A2A24", s=1.0, double=False):
    """Croche (ou deux croches liées), origine au centre de la tête de note."""
    heads = [(0, 0)] + ([(0.3 * s, 0.07 * s)] if double else [])
    for hx, hz in heads:
        b.sphere(col, (hx, 0, hz), 0.1 * s, (1.2, 0.7, 0.85), rot=(0, 22, 0), seg=16, rough=0.4)
        b.tube(col, [(hx + 0.1 * s, 0, hz + 0.02 * s), (hx + 0.1 * s, 0, hz + 0.5 * s)], 0.021 * s, seg=6, rough=0.4)
    if double:
        b.tube(col, [(0.1 * s, 0, 0.5 * s), (0.4 * s, 0, 0.57 * s)], (0.022 * s, 0.045 * s), seg=6, up=(0, -1, 0), rough=0.4)
    else:
        b.tube(col, [(0.1 * s, 0, 0.5 * s), (0.2 * s, 0, 0.42 * s), (0.25 * s, 0, 0.3 * s), (0.22 * s, 0, 0.18 * s)], lambda t: (0.02 * s, 0.05 * s * (1 - 0.75 * t)), seg=6, up=(0, -1, 0), rough=0.4)


b = B("MuguetCasquette", facing(*dome(-40, 34, 0.05), roll=-18)); build_muguet(b, 0.5); T["muguet_pin"] = reg(b.done(), "head")
b = B("NoteCasquette", facing(*dome(-62, 16, 0.06), roll=-8)); build_note(b, OR, 0.85); T["note_pin"] = reg(b.done(), "head")

# chapeau de sorcière : remplace la casquette pendant la période
b = B("ChapeauSorciere", HAT)
b.lathe(VIOLET, [(0, 0.0), (0.8, 0.0), (1.2, -0.02), (1.5, 0.0), (1.57, 0.045), (1.5, 0.09), (1.2, 0.08), (0.88, 0.13), (0, 0.13)], seg=56,
        wob=lambda a, i, r, z: (r * (1 + 0.035 * math.sin(3 * a + 0.6) * (r / 1.5) ** 2), z + (0.11 * math.sin(3 * a + 0.6) + 0.06 * math.sin(5 * a)) * (r / 1.5) ** 2.5))
SPN = [Vector((0.62 * t_ ** 2.6 - 0.04 * math.sin(6 * t_), 0.12 * t_ ** 2, 0.1 + 1.9 * t_ - 0.5 * t_ ** 3)) for t_ in (i / 26 for i in range(27))]
b.tube(VIOLET, SPN, lambda t: (0.87 * (1 - t) ** 0.82 + 0.02) * (1 + 0.035 * math.sin(26 * t) * (t > 0.16)), seg=32, up=(0, -1, 0))
b.tube(NOIR, SPN[:5], lambda t: 0.87 * (1 - t * 4 / 26) ** 0.82 + 0.045, seg=32, up=(0, -1, 0))
bk = b.sub(Matrix.Translation((0.0, -0.9, 0.24)) @ Matrix.Rotation(math.radians(-6), 4, 'X'))
for dx, dz, sx_, sz_ in ((0, 0.115, 0.36, 0.07), (0, -0.115, 0.36, 0.07), (0.145, 0, 0.07, 0.3), (-0.145, 0, 0.07, 0.3)):
    bk.rbox(OR, (dx, 0, dz), (sx_, 0.08, sz_), r=0.4, emit=0.15, rough=0.38)
T["sorciere"] = reg(b.done(), "head")

# guirlande lumineuse autour du ventre
b = B("Guirlande")
BULBS = [ROUGE, JAUNE, "#4FA3D1", VERT_C, ORANGE]
for loop_, (z0, amp, k_, ph) in enumerate(((1.02, 0.13, 3, 0.0), (0.66, 0.12, 2, 1.3))):
    pts = [body_pt(TAU * i / 48, z0 + amp * math.sin(k_ * TAU * i / 48 + ph), 1.035) for i in range(49)]
    b.tube("#2F6B3A", pts[:-1] + [pts[0], pts[1]], 0.02, seg=6)
    for i in range(0, 48, 3):
        nrm_ = Vector((pts[i].x, pts[i].y, 0)).normalized()
        b.sphere(BULBS[(i // 3 + loop_) % len(BULBS)], pts[i] + nrm_ * 0.055 + Vector((0, 0, -0.07)), 0.068, (1, 1, 1.4), emit=2.2, seg=12)
        b.cone("#2F6B3A", pts[i] + nrm_ * 0.055 + Vector((0, 0, -0.01)), 0.04, 0.03, 0.045, seg=8)
T["guirlande"] = reg(b.done(), "body")

# bottes de pluie, au vert de l'écharpe
for s_, sx in (("L", 1), ("R", -1)):
    b = B("Botte." + s_, Matrix.Translation((0.28 * sx, -0.01, 0)))
    b.lathe(VERT_E, [(0, 0.02), (0.24, 0.02), (0.272, 0.06), (0.276, 0.3), (0.29, 0.43), (0.3, 0.47), (0.28, 0.5), (0.2, 0.49), (0, 0.49)], scale=(1, 1.19, 1), seg=28, rough=0.5)
    b.sphere(VERT_E, (0, -0.24, 0.16), 1.0, (0.272, 0.34, 0.165), seg=22, rough=0.5)
    b.sphere(VERT_EF, (0, -0.15, 0.035), 1.0, (0.3, 0.49, 0.06), seg=22, rough=0.6)
    b.torus(VERT_EF, (0, 0, 0.47), 0.292, 0.04, scale=(1, 1.19, 1), rough=0.5)
    T["botte_" + s_] = reg(b.done(), "leg_" + s_)

# gilet d'automne sans manches, au vert de l'écharpe : ouvert devant, liseré, deux poches à rabat
b = B("Gilet")
GZ0, GZ1, GA0 = 0.48, 1.42, 26


def _gilet(u, v):
    th = math.radians(GA0 + (360 - 2 * GA0) * u); z = GZ0 + (GZ1 - GZ0) * v
    return body_pt(th, z, 1.05 - 0.02 * abs(z - 0.95)), body_n(th)


b.sheet(VERT_E, _gilet, 48, 12, 0.05, rough=0.8)
for u in (0.0, 1.0): b.tube(VERT_EF, [_gilet(u, v / 12)[0] + _gilet(u, v / 12)[1] * 0.012 for v in range(13)], 0.04, seg=8)
for v in (0.0, 1.0): b.tube(VERT_EF, [_gilet(u / 48, v)[0] + _gilet(u / 48, v)[1] * 0.012 for u in range(49)], 0.036, seg=8)
for sx in (1, -1):
    th = math.radians(50 * sx); p = body_pt(th, 0.8, 1.085)
    pk = b.sub(facing(p, body_n(th)))
    pk.rbox(VERT_EF, (0, 0, -0.02), (0.32, 0.06, 0.26), r=0.45, rough=0.8).rbox(VERT_E, (0, -0.025, 0.1), (0.35, 0.06, 0.11), r=0.45, rough=0.8)
    pk.sphere(VERT_EF, (0, -0.06, 0.08), 0.03, (1, 0.6, 1))
T["gilet"] = reg(b.done(), "body")

# ================================================================== OBJETS (sortis de temps en temps)
O_ = {}

# flûte de champagne : prise au milieu du pied
b = B("Coupe")
b.lathe("#FFF8E6", [(0, -0.17), (0.105, -0.17), (0.11, -0.155), (0.03, -0.145), (0.017, -0.12), (0.017, 0.15), (0.035, 0.18), (0, 0.18)], seg=20, rough=0.2)
b.lathe("#F7D873", [(0, 0.17), (0.04, 0.18), (0.092, 0.28), (0.112, 0.42), (0.108, 0.54), (0, 0.54)], seg=20, rough=0.2, emit=0.45)
b.lathe("#FFF8E6", [(0, 0.535), (0.108, 0.535), (0.104, 0.62), (0.094, 0.625), (0.09, 0.55), (0, 0.55)], seg=20, rough=0.2, emit=0.1)
for bx, bz in ((0.03, 0.58), (-0.04, 0.61), (0.01, 0.65), (0.05, 0.68), (-0.02, 0.71)): b.sphere("#FFF2B8", (bx, -0.02, bz), 0.016, emit=1.0, seg=8)
O_["coupe"] = reg(b.done())

# galette des rois sur son plat (origine : dessous du plat, au centre)
b = B("Galette")
b.lathe(CREME, [(0, 0), (0.5, 0.0), (0.58, 0.035), (0.59, 0.055), (0.5, 0.05), (0, 0.045)], seg=40, rough=0.4)
b.lathe("#E2A440", [(0, 0.045), (0.43, 0.045), (0.465, 0.09), (0.455, 0.16), (0.4, 0.2), (0, 0.21)], seg=40, rough=0.55,
        wob=lambda a, i, r, z: (r * (1 + 0.018 * math.cos(18 * a)), z))
b.lathe("#C9832E", [(0, 0.212), (0.36, 0.206), (0.39, 0.19), (0, 0.19)], seg=40, rough=0.5)
for k in range(8):
    a0 = TAU * k / 8
    b.tube("#A8661F", [(r_ * math.cos(a0 + 1.1 * r_), r_ * math.sin(a0 + 1.1 * r_), 0.214) for r_ in (0.05 + 0.3 * i / 7 for i in range(8))], 0.011, seg=5)
O_["galette"] = reg(b.done())

# fève : petite figurine de porcelaine qui brille (origine : sa base)
b = B("Feve")
b.pillow(OR, chaikin(star(0.24, 4, 0.28), 1), 0.05, loc=(0, 0.03, 0.1), emit=1.6).pillow(JAUNE, chaikin(star(0.15, 4, 0.3), 1), 0.05, loc=(0, 0.02, 0.1), rot=(0, 45, 0), emit=1.6)
b.sphere(CREME, (0, -0.02, 0.1), 0.085, (0.78, 0.7, 1.2), rough=0.25).sphere(CREME, (0, -0.03, 0.21), 0.052, rough=0.25)
O_["feve"] = reg(b.done())

# poêle : prise sur le manche (origine), la poêle part vers -Y
b = B("Poele")
b.lathe(NOIR, [(0, -0.03), (0.3, -0.03), (0.365, 0.05), (0.38, 0.075), (0.355, 0.078), (0.3, 0.005), (0, 0.005)], loc=(0, -0.72, 0), seg=36, rough=0.38)
b.lathe("#4A4A55", [(0, 0.008), (0.29, 0.008), (0.3, 0.012), (0, 0.012)], loc=(0, -0.72, 0), seg=36, rough=0.3)
b.tube(NOIR, [(0, -0.38, 0.045), (0, -0.2, 0.02), (0, 0.0, 0.0), (0, 0.16, 0.005)], lambda t: (0.03, 0.03 + 0.016 * t), seg=10, up=(0, 0, 1), rough=0.45)
b.sphere(NOIR, (0, 0.17, 0.005), 0.046, (1, 1, 0.66), rough=0.45)
O_["poele"] = reg(b.done())
b = B("Crepe")
b.lathe("#F3C76B", [(0, 0), (0.27, 0.0), (0.295, 0.013), (0.27, 0.026), (0, 0.026)], seg=36, rough=0.6,
        wob=lambda a, i, r, z: (r * (1 + 0.07 * math.cos(3 * a + 1) + 0.04 * math.cos(5 * a)), z + 0.014 * math.sin(4 * a) * (r / 0.3)))
for a_, r_, s__ in ((0.4, 0.12, 0.05), (2.1, 0.16, 0.04), (3.5, 0.1, 0.045), (4.9, 0.17, 0.035), (5.8, 0.05, 0.03), (1.2, 0.02, 0.035)):
    b.sphere("#CB8B3B", (r_ * math.cos(a_), r_ * math.sin(a_), 0.022), s__, (1, 0.8, 0.14), rough=0.6)
O_["crepe"] = reg(b.done())

# enveloppe au cœur (origine au centre), cœurs qui s'envolent
b = B("Enveloppe"); b.rbox(CREME, (0, 0, 0), (0.7, 0.07, 0.47), r=0.45, rough=0.6)
for sx in (1, -1): b.tube("#D8C7A8", [(0.33 * sx, -0.036, 0.215), (0.0, -0.04, -0.03)], 0.011, seg=5)
b.pillow(ROUGE, heart(0.12), 0.07, loc=(0, -0.045, -0.02), rough=0.35)
O_["enveloppe"] = reg(b.done())
b = B("Coeur"); b.pillow(ROUGE, heart(0.17), 0.14, rough=0.3, emit=0.3); O_["coeur"] = reg(b.done()); O_["coeur2"] = clone(O_["coeur"]); O_["coeur3"] = clone(O_["coeur"])


# loup vénitien : épouse le visage, deux ouvertures en amande, liseré et volutes dorés, manche doré côté droit
def build_masque(b, out=0.075, th=0.05):
    ec, hole = (EYE_X, EYE_Z), (0.25, 0.278)                              # l'œil fait 0,212 x 0,247 : il reste visible en entier
    cont = chaikin([(0.0, 2.262), (0.1, 2.31), (0.28, 2.385), (0.5, 2.4), (0.68, 2.36), (0.83, 2.44), (0.8, 2.2), (0.79, 1.96), (0.72, 1.76),
                    (0.54, 1.665), (0.34, 1.67), (0.2, 1.745), (0.125, 1.87), (0.06, 1.94), (0.0, 1.958)], 2, closed=False)
    poly = cont + [cont[0]]                                               # refermé par la couture du milieu (x = 0)

    def hit(a):
        d = (math.sin(a), math.cos(a)); best = None
        for (x0, z0), (x1, z1) in zip(poly, poly[1:]):
            ex, ez = x1 - x0, z1 - z0; den = d[0] * ez - d[1] * ex
            if abs(den) < 1e-9: continue
            t = ((x0 - ec[0]) * ez - (z0 - ec[1]) * ex) / den; w = ((x0 - ec[0]) * d[1] - (z0 - ec[1]) * d[0]) / den
            if t > 0 and -1e-6 <= w <= 1 + 1e-6 and (best is None or t < best): best = t
        return (ec[0] + d[0] * best, ec[1] + d[1] * best)
    for sx in (1, -1):
        def fn(u, v, sx=sx):
            a = TAU * u; hx, hz = ec[0] + hole[0] * math.sin(a), ec[1] + hole[1] * math.cos(a); ox, oz = hit(a)
            return face_pt(sx * lerp(hx, ox, v), lerp(hz, oz, v), out)
        b.sheet(VIOLET, fn, 72, 3, th, wrap=True, rough=0.55)
        b.tube(OR, [face_pt(sx * x, z, out + th / 2 + 0.004)[0] for x, z in cont], 0.021, seg=8, emit=0.15, rough=0.38)
        ring = [face_pt(sx * (ec[0] + hole[0] * math.sin(TAU * k / 40)), ec[1] + hole[1] * math.cos(TAU * k / 40), out + th / 2 + 0.004)[0] for k in range(40)]
        b.tube(OR, ring + ring[:2], 0.017, seg=8, emit=0.15, rough=0.38)
        for (cx, cz, r1, turns, ph) in ((0.722, 2.0, 0.062, 1.6, 0.5), (0.74, 2.29, 0.04, 1.3, 2.4)):       # volutes
            sw = [(cx + r1 * (i / 22) * math.sin(ph + TAU * turns * i / 22), cz + r1 * (i / 22) * math.cos(ph + TAU * turns * i / 22)) for i in range(2, 23)]
            b.tube(OR, [face_pt(sx * x, z, out + th / 2 + 0.006)[0] for x, z in sw], 0.0095, seg=6, emit=0.15, rough=0.38)
        for x, z in ((0.3, 1.7), (0.42, 1.688), (0.54, 1.7), (0.2, 2.345), (0.4, 2.378)):
            b.sphere(OR, face_pt(sx * x, z, out + th / 2 + 0.006)[0], 0.016, emit=0.15, rough=0.38, seg=8)
    p, n_ = face_pt(0.0, 2.19, out + th / 2 + 0.004)
    b.sub(facing(p, n_)).pillow(OR, chaikin([(0, 0.055), (0.04, 0), (0, -0.055), (-0.04, 0)], 1), 0.03, emit=0.15, rough=0.38)
    top = face_pt(-0.775, 1.82, out)[0]; bot = top + Vector((-0.1, -0.1, -0.74))                    # manche
    b.tube(OR, [top, top.lerp(bot, 0.5) + Vector((-0.012, 0, 0)), bot], 0.024, seg=8, emit=0.12, rough=0.38)
    b.sphere(OR, bot, 0.042, emit=0.12, rough=0.38)
    return top.lerp(bot, 0.74)


b = B("Masque"); MASK_GRIP = build_masque(b)
O_["masque"] = reg(b.done(), "head")
CONF = [VERT_C, "#4FA3D1", ORANGE, JAUNE, BLANC, ROSE, VIOLET]


def cloud(name, cols, n=40, emit=0.35, streamers=0, stars=0):
    """Nuage de confettis : pastilles, petits rectangles cintrés, serpentins et étoiles."""
    b = B(name)

    def spot():
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
        if d.length > 1: d.normalize()
        return Vector((d.x * 1.5, d.y * 0.7, d.z * 0.95)), (rnd.uniform(0, 180), rnd.uniform(0, 180), rnd.uniform(0, 180))
    for i in range(n):
        p, rot = spot(); col = cols[i % len(cols)]
        if i % 3 == 0: b.pillow(col, ellipse(0.07, 0.07, 10), 0.022, loc=p, rot=rot, edge=0.3, n=2, emit=emit)
        else: b.pillow(col, chaikin([(-0.09, 0.045), (0.09, 0.045), (0.09, -0.045), (-0.09, -0.045)], 1), 0.022, loc=p, rot=rot, edge=0.25, n=2, emit=emit)
    for i in range(stars):
        p, rot = spot(); b.pillow(cols[i % len(cols)], chaikin(star(0.1, 5, 0.5), 1), 0.04, loc=p, rot=(rot[0] * 0.2, rot[1], 0), n=2, emit=emit)
    for i in range(streamers):
        p, rot = spot(); M_ = TRS(p, rot); L_, R_ = rnd.uniform(0.5, 0.75), rnd.uniform(0.06, 0.085)
        b.tube(cols[i % len(cols)], [M_ @ Vector((R_ * math.cos(13 * t), R_ * math.sin(13 * t), L_ * (t - 0.5))) for t in (j / 22 for j in range(23))],
               (0.008, 0.036), seg=6, up=tuple(M_.to_3x3() @ Vector((0, 0, 1))), emit=emit, rough=0.4)
    return reg(b.done())


O_["confettis"] = cloud("Confettis", CONF, 40, 0.35, streamers=3)
O_["confettis_or"] = cloud("ConfettisOr", [OR, JAUNE, "#FFE9A8"], 16, 0.6, streamers=6, stars=6)

# œuf de Pâques décoré (origine au centre)
b = B("Oeuf")
OEUF = [(0.3 * math.cos(math.radians(p)), (0.36 if p < 0 else 0.45) * math.sin(math.radians(p))) for p in range(-90, 91, 9)]
OEUF_C = ["#F6B6CB"] * 3 + ["#F9DE7A"] * 2 + ["#F6B6CB"] + ["#8FD3EA"] * 3 + ["#F28A8A"] + ["#F9DE7A"] * 2 + ["#F6B6CB"] * 3 + ["#C8A2E0"] * 2 + ["#F6B6CB"] * 4
b.lathe("#F6B6CB", [(0, OEUF[0][1])] + OEUF[1:-1] + [(0, OEUF[-1][1])], seg=36, rough=0.45,
        colfn=lambda i, j: OEUF_C[min(len(OEUF_C) - 1, i + (1 if (j // 2) % 2 and i in (4, 8, 11, 15) else 0))])
for k in range(9):
    a = TAU * k / 9
    b.sphere(BLANC, (0.292 * math.cos(a), 0.292 * math.sin(a), -0.03), 0.028, rough=0.4, seg=8)
    b.sphere("#F28A8A", (0.19 * math.cos(a + 0.35), 0.19 * math.sin(a + 0.35), 0.36), 0.022, rough=0.4, seg=8)
O_["oeuf"] = reg(b.done())
b = B("Muguet"); build_muguet(b, 1.0); O_["muguet"] = reg(b.done())

# petite guitare (origine au centre de la caisse, manche vers +X)
b = B("Guitare"); BOIS, BOIS_C, BOIS_F = "#C9772E", "#EDBE7B", "#7A4A24"


def _caisse(a):
    best = 0.0
    for cx, r in ((-0.15, 0.345), (0.24, 0.26)):
        dx, dz = math.sin(a), math.cos(a); bq = -dx * cx; cq = cx * cx - r * r; disc = bq * bq - cq
        if disc > 0: best = max(best, -bq + math.sqrt(disc))
    return best


CAISSE = chaikin(polar(_caisse, 36), 1)
b.pillow(BOIS, CAISSE, 0.21, edge=0.2, n=3, rough=0.5).pillow(BOIS_C, [(x * 0.93, z * 0.92) for x, z in CAISSE], 0.225, edge=0.12, n=2, rough=0.5)
b.lathe(BOIS_F, [(0, 0), (0.085, 0.0), (0.09, 0.006), (0, 0.006)], loc=(0.1, -0.113, 0), rot=(90, 0, 0), seg=24, rough=0.5)
b.torus(BOIS, (0.1, -0.113, 0), 0.098, 0.01, rot=(90, 0, 0), seg=24, rs=6)
b.rbox(BOIS_F, (-0.22, -0.118, 0), (0.06, 0.03, 0.19), r=0.4)
b.rbox(BOIS_F, (0.8, -0.05, 0), (0.74, 0.075, 0.095), r=0.4).rbox(BOIS, (1.25, -0.05, 0), (0.24, 0.075, 0.17), r=0.4)
for fx in (0.56, 0.7, 0.83, 0.95, 1.06): b.rbox("#E8D9B0", (fx, -0.09, 0), (0.012, 0.012, 0.09), r=0.3)
for dz in (-0.03, -0.01, 0.01, 0.03):
    b.tube("#FFF6E0", [(-0.22, -0.137, dz), (1.2, -0.094, dz * 1.3)], 0.0045, seg=4)
for px, pz in ((1.2, 0.1), (1.3, 0.1), (1.2, -0.1), (1.3, -0.1)): b.sphere("#E8D9B0", (px, -0.05, pz), 0.028, seg=8)
O_["guitare"] = reg(b.done())
b = B("Note"); build_note(b); O_["note"] = reg(b.done())
b = B("Note2"); build_note(b, double=True); O_["note2"] = reg(b.done())

# drapeau tricolore qui flotte : prise sur la hampe (origine)
b = B("Drapeau")
b.tube(OR, [(0, 0, -0.34), (0, 0, 1.06)], 0.028, seg=10, rough=0.38, emit=0.1).sphere(OR, (0, 0, 1.09), 0.062, rough=0.38, emit=0.1).sphere(OR, (0, 0, -0.34), 0.036, rough=0.38)
b.sheet(BLANC, lambda u, v: (Vector((0.025 + 0.74 * u, 0.075 * math.sin(TAU * (1.25 * u + 0.12 * v)) * (0.25 + 0.75 * u), 0.56 + 0.47 * v + 0.03 * math.sin(TAU * u) * u)), Vector((0, -1, 0))),
        24, 6, 0.028, colfn=lambda i, j: (BLEU_F, BLANC, ROUGE)[min(2, i // 8)], rough=0.6)
O_["drapeau"] = reg(b.done())


# citrouille d'Halloween (origine au centre)
def ribs(v):
    th = math.atan2(v.co.y, v.co.x); k = 1 + 0.075 * math.cos(9 * th) * (1 - (abs(v.co.z) / 0.37) ** 2)
    v.co.x *= k; v.co.y *= k


b = B("Citrouille"); b.sphere(ORANGE, (0, 0, 0), 0.37, (1, 1, 0.84), fn=ribs, seg=36, rough=0.5)
b.tube("#5D8A3A", [(0, 0, 0.27), (0.01, 0, 0.36), (0.06, -0.01, 0.43), (0.12, -0.02, 0.45)], lambda t: 0.055 * (1 - 0.45 * t), seg=8)
for sx in (1, -1): b.pillow("#FFE27A", [(-0.085, -0.05), (0.085, -0.05), (0.02 * sx, 0.085)][::-1], 0.07, loc=(0.14 * sx, -0.338, 0.07), rot=(0, 0, 14 * sx), edge=0.25, n=2, emit=3.0)
b.pillow("#FFE27A", [(-0.21, 0.02), (-0.13, -0.035), (-0.065, 0.01), (0.0, -0.04), (0.065, 0.01), (0.13, -0.035), (0.21, 0.02), (0.13, -0.12), (0, -0.155), (-0.13, -0.12)][::-1], 0.07,
         loc=(0, -0.352, -0.07), edge=0.2, n=2, emit=3.0)
O_["citrouille"] = reg(b.done())

# cadeau de Noël (origine au centre)
b = B("Cadeau"); b.rbox(ROUGE, (0, 0, 0), (0.58, 0.58, 0.52), r=0.14, rough=0.5)
b.rbox(OR, (0, 0, 0), (0.13, 0.595, 0.535), r=0.14, emit=0.12, rough=0.4).rbox(OR, (0, 0, 0), (0.595, 0.13, 0.535), r=0.14, emit=0.12, rough=0.4)
for sx in (1, -1):
    b.tube(OR, [(0.02 * sx, 0, 0.27), (0.14 * sx, 0, 0.42), (0.27 * sx, 0, 0.4), (0.25 * sx, 0, 0.3), (0.04 * sx, 0, 0.27)], (0.055, 0.02), seg=8, up=(0, -1, 0), emit=0.12, rough=0.4)
    b.tube(OR, [(0.03 * sx, -0.02, 0.27), (0.16 * sx, -0.12, 0.275), (0.26 * sx, -0.2, 0.262)], (0.012, 0.045), seg=6, up=(0, 0, 1), emit=0.12, rough=0.4)
b.sphere(OR, (0, 0, 0.29), 0.062, (1, 1, 0.8), emit=0.12, rough=0.4)
O_["cadeau"] = reg(b.done())


# tulipes : prise sur les tiges (origine)
def _tulipe(b, col, base, d):
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_matrix().to_4x4()
    b.sub(Matrix.Translation(base) @ q).lathe(col, [(0, 0), (0.06, 0.01), (0.118, 0.08), (0.128, 0.17), (0.11, 0.26), (0.075, 0.32), (0, 0.29)], seg=24, rough=0.5,
                                               wob=lambda a, i, r, z: (r * (1 + 0.13 * math.cos(3 * a) * (z / 0.32) ** 2), z + 0.035 * math.cos(3 * a + math.pi) * (z / 0.32) ** 2))


b = B("Tulipes")
for k, (ang, col, L) in enumerate(((-17, ROSE, 0.78), (5, JAUNE, 0.92), (24, "#F2707F", 0.74))):
    d = Vector((math.sin(math.radians(ang)), -0.06 * k, math.cos(math.radians(ang))))
    b.tube(VERT_F, [Vector((0.02 * (k - 1), 0, -0.3)), Vector((0.012 * (k - 1), 0, 0.2)), d * L], 0.02, seg=7)
    _tulipe(b, col, d * (L - 0.02), d)
    sd = 1 if ang > 0 else -1
    leaf(b, VERT_F if k != 1 else "#5CAB5E", (0.012 * (k - 1), 0.02, 0.2), d * 0.62 + Vector((0.17 * sd, 0.05, 0)), 0.07, (0.04 * sd, 0, 0))
O_["tulipes"] = reg(b.done())

# cornet de glace : prise sur le cornet (origine)
b = B("Glace")
b.lathe("#E8B974", [(0, -0.16), (0.03, -0.13), (0.135, 0.24), (0.148, 0.27), (0.13, 0.275), (0, 0.275)], seg=20, rough=0.65)
for k in range(3):
    b.tube("#C98F45", [(0.012 + (0.03 + 0.105 * t_) * math.cos(TAU * (k / 3 + 1.4 * t_)), (0.03 + 0.105 * t_) * math.sin(TAU * (k / 3 + 1.4 * t_)), -0.13 + 0.38 * t_) for t_ in (i / 14 for i in range(15))], 0.007, seg=4)
b.torus("#F59BB6", (0, 0, 0.285), 0.125, 0.05, scale=(1, 1, 0.8), rough=0.5).sphere("#F59BB6", (0, 0, 0.385), 0.175, seg=22, rough=0.5)
b.torus("#FFF1C9", (0, 0, 0.5), 0.1, 0.04, scale=(1, 1, 0.8), rough=0.5).sphere("#FFF1C9", (0, 0, 0.585), 0.145, seg=20, rough=0.5)
b.sphere(ROUGE, (0.02, 0, 0.745), 0.052, rough=0.25).tube(BOIS_F, [(0.02, 0, 0.79), (0.035, 0, 0.84), (0.07, 0, 0.87)], 0.007, seg=4)
O_["glace"] = reg(b.done())

# bouée canard (origine au centre de l'anneau)
b = B("Bouee"); b.torus(JAUNE, (0, 0, 0), 1.08, 0.33, scale=(1, 1, 0.9), seg=44, rs=14, rough=0.45)
b.sphere(JAUNE, (0.85, -0.95, 0.47), 0.34, seg=22, rough=0.45).sphere(JAUNE, (0.8, -0.9, 0.2), 0.27, (1, 1, 1), seg=16, rough=0.45)
dk = b.sub(Matrix.Translation((0.98, -1.2, 0.42)) @ Matrix.Rotation(math.radians(28), 4, 'Z'))
dk.sphere(ORANGE, (0, -0.12, 0.02), 1.0, (0.13, 0.19, 0.045), rough=0.45).sphere("#E27818", (0, -0.1, -0.03), 1.0, (0.11, 0.15, 0.035), rough=0.45)
for sx in (1, -1): b.sphere(NOIR, (0.9 + 0.2 * sx, -1.2 + 0.07 * sx, 0.6), 0.045, rough=0.2).sphere(BLANC, (0.9 + 0.2 * sx - 0.012, -1.235 + 0.07 * sx, 0.615), 0.016, emit=0.5, seg=8)
b.sub(Matrix.Translation((-0.22, -1.39, 0.03)) @ Matrix.Rotation(math.radians(18), 4, 'Y')).pillow(VERT_E, chaikin([(-0.27, 0.06), (-0.05, 0.17), (0.25, 0.12), (0.3, -0.02), (0.12, -0.08), (0.1, -0.15), (-0.06, -0.1), (-0.1, -0.17), (-0.25, -0.1)], 2), 0.12, rough=0.5)
O_["bouee"] = reg(b.done())

# châtaigne brillante (origine : sa base)
b = B("Marron")
b.lathe("#6B3A1E", [(0, 0), (0.1, 0.0), (0.175, 0.05), (0.195, 0.13), (0.16, 0.24), (0.06, 0.315), (0.012, 0.345), (0, 0.35)], scale=(1, 0.86, 1), seg=24, rough=0.22,
        colfn=lambda i, j: "#D7B48A" if i < 2 else "#6B3A1E")
b.sphere(BLANC, (-0.07, -0.13, 0.2), 0.03, (1, 0.4, 1.6), emit=0.4, seg=8)
O_["marron"] = reg(b.done())


def build_leaf(name, col, col2):
    """Feuille d'automne lobée, nervure et queue."""
    b = B(name)
    out_ = chaikin(polar(lambda a: 0.3 * (0.5 + 0.34 * math.cos(a / 2) ** 2 + 0.2 * abs(math.cos(2.5 * a)) ** 0.7), 40), 1)
    b.pillow(col, out_, 0.04, edge=0.5, n=3, rough=0.7)
    b.tube(col2, [(0, -0.012, -0.36), (0.01, -0.024, -0.1), (0, -0.024, 0.24)], lambda t: 0.014 * (1 - 0.6 * t), seg=5)
    for sx in (1, -1):
        for z0, dz, L in ((-0.05, 0.1, 0.16), (0.06, 0.09, 0.12)): b.tube(col2, [(0, -0.024, z0), (L * sx, -0.022, z0 + dz)], 0.007, seg=4)
    return reg(b.done())


O_["feuille"] = build_leaf("Feuille", ORANGE, "#B4571A"); O_["feuille2"] = build_leaf("Feuille2", "#D9542B", "#9C3415"); O_["feuille3"] = build_leaf("Feuille3", JAUNE, "#C99A1E")


def _bosses(amp, k=5.0):
    def fn(v):
        d = 1 + amp * (math.sin(k * v.co.x + 1.3) * math.sin(k * v.co.y + 0.4) + math.sin(k * 0.8 * v.co.z + 2.1))
        v.co.x *= d; v.co.y *= d; v.co.z *= d
    return fn


b = B("Boule"); b.sphere("#F3F8FD", (0, 0, 0), 0.2, seg=20, fn=_bosses(0.035, 14), rough=0.85); O_["boule"] = reg(b.done()); O_["boule2"] = clone(O_["boule"])
b = B("TasNeige")
b.sphere(BLANC, (0, 0, 0.02), 1.0, (0.62, 0.5, 0.25), emit=0.1, seg=22, rough=0.85).sphere(BLANC, (0.36, 0.1, 0.02), 1.0, (0.4, 0.34, 0.17), emit=0.1, rough=0.85).sphere(BLANC, (-0.32, -0.1, 0.0), 1.0, (0.35, 0.3, 0.14), emit=0.1, rough=0.85)
O_["neige"] = reg(b.done())
b = B("Flaque")
b.pillow(EAU, chaikin(polar(lambda a: 1.1 * (1 + 0.12 * math.cos(3 * a) + 0.07 * math.cos(5 * a + 1)), 40), 1), 0.035, rot=(90, 0, 0), scale=(1, 1, 0.75), edge=0.25, n=3, rough=0.15, emit=0.15)
O_["flaque"] = reg(b.done())
b = B("Gouttes")
for i in range(14):
    a = TAU * i / 14 + rnd.uniform(-0.2, 0.2); R_ = rnd.uniform(1.0, 1.5); s__ = rnd.uniform(0.75, 1.25)
    b.lathe(EAU, [(0, -0.075), (0.045, -0.055), (0.062, -0.01), (0.042, 0.05), (0.013, 0.105), (0, 0.125)], loc=(R_ * math.cos(a), 0.7 * R_ * math.sin(a), rnd.uniform(0.25, 1.0)),
            rot=(0, -25 * math.cos(a), 0), scale=s__, seg=10, emit=0.3, rough=0.2)
O_["gouttes"] = reg(b.done())
b = B("Papillon"); b.tube(BRUN, [(0, 0, -0.1), (0, 0, 0.1)], lambda t: 0.024 * (0.5 + math.sin(math.pi * t) * 0.6), seg=6)
for sx in (1, -1):
    b.pillow(ROSE, [(x * sx, z) for x, z in chaikin([(0.0, 0.0), (0.05, 0.17), (0.2, 0.2), (0.22, 0.06), (0.1, -0.01)], 2)][::sx], 0.03, loc=(0.012 * sx, 0, 0.02), rot=(0, 0, 22 * sx))
    b.pillow(JAUNE, [(x * sx, z) for x, z in chaikin([(0.0, 0.0), (0.1, 0.0), (0.16, -0.1), (0.07, -0.16), (0.01, -0.08)], 2)][::sx], 0.03, loc=(0.012 * sx, 0, -0.01), rot=(0, 0, 22 * sx))
    b.tube(BRUN, [(0.01 * sx, 0, 0.1), (0.04 * sx, 0, 0.17), (0.08 * sx, 0, 0.2)], 0.006, seg=4)
O_["papillon"] = reg(b.done())


def firework(name, col):
    b = B(name)
    for k in range(14):
        d = Vector((math.cos(TAU * k / 14), 0, math.sin(TAU * k / 14)))
        b.tube(col, [d * 0.25, d * (0.75 + 0.2 * (k % 2))], lambda t: 0.012 + 0.014 * t, seg=5, emit=4.0).sphere(BLANC, d * (0.85 + 0.2 * (k % 2)), 0.035, emit=4.0, seg=8)
    return reg(b.done())


O_["feu1"] = firework("Feu1", ROUGE); O_["feu2"] = firework("Feu2", "#4FA3D1"); O_["feu3"] = firework("Feu3", OR)

# ------------------------------------------------------------------ prises et bras (partagés avec sherlock_themes.py)
HAND_IN = 0.17                                           # le centre du poing est en retrait du bout du bras


def carry(w, y=-1.0, z=1.2, e=(0.86, -0.72, 1.06)):
    """Bras qui portent à deux mains un objet large de w : les poings viennent contre ses flancs."""
    hc_ = Vector((w / 2 + 0.16, y, z)); e = Vector(e)
    return dict(Sh=(0.6, -0.3, 1.2), E=e, T=hc_ + (hc_ - e).normalized() * HAND_IN)


A_HOLD = dict(Sh=(0.6, -0.3, 1.2), E=(0.84, -0.8, 1.1), T=(0.52, -1.14, 1.28))     # porte devant le ventre
A_SHOW = dict(E=(1.0, -0.32, 1.3), T=(1.22, -0.66, 1.62))                           # présente sur le côté
A_HIGH = dict(E=(1.02, -0.12, 1.6), T=(1.22, -0.32, 2.05))                          # lève haut
A_FACE = dict(Sh=(0.58, -0.35, 1.2), E=(0.66, -0.98, 1.4), T=(0.36, -1.08, 1.78))  # porte au visage
A_SNIFF = dict(Sh=(0.6, -0.3, 1.2), E=(0.95, -0.8, 1.15), T=(0.78, -1.12, 1.4))    # porte des fleurs sous le nez
A_OFFER = dict(Sh=(0.6, -0.3, 1.2), E=(0.86, -0.78, 1.28), T=(0.74, -1.32, 1.55))  # tend vers vous
A_GROUND = dict(Sh=(0.6, -0.32, 1.1), E=(0.84, -0.78, 0.8), T=(0.7, -1.12, 0.42))  # se baisse
A_PAW = dict(Sh=(0.58, -0.35, 1.2), E=(0.58, -0.92, 1.28), T=(0.36, -1.04, 1.6))   # pattes repliées
A_CLAW = dict(E=(1.0, -0.3, 1.62), T=(0.86, -0.78, 2.02))                           # griffes en l'air
A_THROW = dict(E=(0.98, 0.26, 1.74), T=(0.92, 0.6, 2.2))                            # bras armé en arrière
A_AIM = dict(Sh=(0.6, -0.3, 1.2), E=(0.82, -0.78, 1.32), T=(0.56, -1.3, 1.52))     # vise devant
A_NECK = dict(E=(1.02, -0.5, 1.22), T=(1.02, -0.98, 1.5))                           # main sur le manche
A_STRUM = dict(Sh=(0.6, -0.3, 1.2), E=(0.78, -0.8, 1.06), T=(0.26, -1.12, 1.1))    # main qui gratte
_mg = Vector((-MASK_GRIP.x, MASK_GRIP.y, MASK_GRIP.z)); _me = Vector((1.03, -0.3, 1.17))     # avant-bras en travers du manche
A_MASK = dict(Sh=(0.6, -0.3, 1.2), E=_me, T=_mg + (_mg - _me).normalized() * HAND_IN)  # tient le manche du masque
A_EAR = dict(E=(1.06, -0.3, 1.5), T=(0.98, -0.62, 1.98))                            # porte à l'oreille
A_LICK = dict(Sh=(0.6, -0.3, 1.2), E=(0.9, -0.8, 1.12), T=(0.6, -1.18, 1.38))      # tient devant la bouche
A_RELEASE = dict(Sh=(0.6, -0.3, 1.25), E=(0.8, -0.82, 1.55), T=(0.55, -1.42, 1.85)) # bras lancé vers l avant
HAPPY, WIDE, CALM = dict(closed="happy"), dict(h=1.15, w=1.15), dict(closed="sleep")

# objets portés à deux mains : (bras, décalage par rapport au milieu des poings, rotation, échelle)
PORTE = {"galette": (carry(0.48, -1.15, 1.12), (0, -0.05, 0.19), (13, 0, 0), 1.0),          # poings sous le plat
         "enveloppe": (carry(0.735, -0.98, 1.22), (0, 0, 0), (-14, 0, 0), 1.05),
         "oeuf": (carry(0.69, -1.07, 1.2), (0, 0, 0.02), (8, 0, 8), 1.15),
         "citrouille": (carry(0.96, -1.2, 1.15), (0, 0, 0.12), (0, 0, -20), 1.3),
         "cadeau": (carry(0.68, -1.03, 1.18), (0, 0, 0.06), (0, 0, 14), 1.0)}

# ================================================================== RENDU : pose, tenue, objets
ad.use_nla = False; ad.action = None
arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0); arm.scale = (1, 1, 1)
for grp, names in (("vg_echarpe", ("Echarpe_vert",)), ("vg_casquette", ("Casquette_bleu", "Casquette_couture"))):
    idx = {i for i, m in enumerate(me.materials) if m.name in names}
    vg = mesh.vertex_groups.new(name=grp)
    vg.add(sorted({v for p in me.polygons if p.material_index in idx for v in p.vertices}), 1.0, 'REPLACE')
    md = mesh.modifiers.new("Masque_" + grp, 'MASK'); md.vertex_group = grp; md.invert_vertex_group = True; md.show_render = False
# sans écharpe, l'ombre cuite qu'elle laissait sur le corps doit disparaître : seconde couche d'occlusion « Col_nu »
_src = me.color_attributes["Col"]; _nu = me.color_attributes.new("Col_nu", 'BYTE_COLOR', 'CORNER')
_pate = [i for i, m in enumerate(me.materials) if m.name == "Pate_blanche"][0]
for pl in me.polygons:
    for li in pl.loop_indices:
        c = _src.data[li].color[0]
        if pl.material_index == _pate:
            z = me.vertices[me.loops[li].vertex_index].co.z
            c += (max(c, 0.97) - c) * smooth(0.6, 0.8, z) * (1 - smooth(1.72, 1.92, z))
        _nu.data[li].color = (c, c, c, 1.0)
AO_NODE = [m for m in me.materials if m.name == "Pate_blanche"][0].node_tree.nodes["AO_att"]


def D(bone): return P[bone].matrix @ arm_d.bones[bone].matrix_local.inverted()


def wear(*obs):
    for ob in obs:
        ob.hide_render = False; ob.matrix_world = D(ob["os"]) @ REST_M[ob.name]


def fore(side):
    pb = P["forearm_" + side]; h_, t_ = arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail
    return t_, (t_ - h_).normalized()


def hand(side, d=0.0):
    """Centre du poing (d = 0), ou un point plus loin le long de l'avant-bras (d > 0 : vers le bout et au-delà)."""
    t_, dr = fore(side)
    return t_ + dr * (d - HAND_IN)


def put(ob, loc, rot=(0, 0, 0), s=1.0):
    ob.hide_render = False; ob.matrix_world = TRS(loc, rot, s)


def hold(ob, side="L", rot=(0, 0, 0), off=(0, 0, 0), s=1.0): put(ob, hand(side) + Vector(off), rot, s)


def mids(off=(0, 0, 0)): return (hand("L") + hand("R")) / 2 + Vector(off)


BASES = {"hiver": (True, []), "printemps": (False, ["botte_L", "botte_R"]), "ete": (False, ["lunettes"]), "automne": (False, ["gilet"])}


def porte(n): put(O_[n], mids(PORTE[n][1]), PORTE[n][2], PORTE[n][3])


def bras(n): return dict(L=PORTE[n][0], R=PORTE[n][0])


# mise en place des objets, une fois la pose appliquée
def c_coupe(): hold(O_["coupe"], "L", rot=(0, 0, 0), s=1.5)
def c_trinque(): hold(O_["coupe"], "L", rot=(0, 14, 0), s=1.5); put(O_["confettis_or"], (0.1, -0.5, 3.8)); put(O_["confettis"], (0.0, -0.3, 3.7), rot=(0, 0, 40), s=1.1)
def c_galette(): porte("galette")
def c_feve(): put(O_["feve"], hand("L", 0.2), s=1.7)
def c_poele(): hold(O_["poele"], "L", rot=(6, 0, 38), s=1.05); put(O_["crepe"], O_["poele"].matrix_world @ Vector((0, -0.72, 0.012)), rot=(6, 0, 38), s=1.05)
def c_crepe(): hold(O_["poele"], "L", rot=(16, 0, 38), s=1.05); put(O_["crepe"], O_["poele"].matrix_world @ Vector((0, -0.72, 0.0)) + Vector((-0.1, 0, 1.2)), rot=(62, 18, 30), s=1.05)
def c_lettre(): porte("enveloppe")
def c_coeurs(): put(O_["coeur"], hand("L", 0.42) + Vector((0.05, -0.05, 0.1)), rot=(0, 10, 0), s=0.8); put(O_["coeur2"], hand("L") + Vector((0.55, -0.3, 1.0)), rot=(0, -12, 0), s=1.15); put(O_["coeur3"], hand("L") + Vector((0.6, -0.5, 1.65)), rot=(0, 8, 0), s=1.35)
def c_masque(): wear(O_["masque"])
def c_confettis(): put(O_["confettis"], (0, -0.5, 3.75))
def c_oeuf(): porte("oeuf")
def c_lapin(): put(O_["oeuf"], (1.55, -0.7, 0.42), rot=(0, -10, 0), s=1.15)
def c_muguet(): hold(O_["muguet"], "L", rot=(-12, -6, 0), s=1.25)
def c_respire(): hold(O_["muguet"], "L", rot=(-8, -50, 0), s=1.25)
def c_guitare(): put(O_["guitare"], (0.1, -1.02, 1.18), rot=(-8, -22, 0), s=0.95)
def c_joue(): c_guitare(); put(O_["note"], (1.25, -0.9, 2.9), rot=(0, -10, 0), s=1.15); put(O_["note2"], (1.6, -0.7, 3.5), rot=(0, 12, 0), s=0.9)
def c_drapeau(): hold(O_["drapeau"], "L", rot=(0, 6, 0), s=1.25)
def c_feu(): hold(O_["drapeau"], "L", rot=(0, 18, 0), s=1.25); put(O_["feu1"], (-1.7, 1.5, 3.9), s=0.9); put(O_["feu2"], (2.0, 1.5, 3.2), s=0.7); put(O_["feu3"], (0.1, 1.5, 4.35), s=0.5)
def c_citrouille(): porte("citrouille")
def c_bouh(): put(O_["citrouille"], (1.2, -0.5, 0.4), rot=(0, 0, -12), s=1.3)
def c_cadeau(): porte("cadeau")
def c_secoue(): put(O_["cadeau"], hand("L", 0.4) + Vector((0, -0.05, 0.1)), rot=(0, 18, 20), s=0.8)
def c_tulipes(): hold(O_["tulipes"], "L", rot=(-8, -4, 0), s=1.15); put(O_["papillon"], (-0.95, -0.7, 3.45), rot=(0, 20, 0), s=1.3)
def c_flaque(): put(O_["flaque"], (0, -0.15, 0.0)); put(O_["gouttes"], (0, -0.15, 0.0)); put(O_["papillon"], (1.6, -0.5, 3.2), rot=(0, -25, 0), s=1.3)
def c_glace(): hold(O_["glace"], "L", rot=(0, -8, 0), s=1.35)
def c_bouee(): put(O_["bouee"], (0, 0, 0.92)); put(O_["gouttes"], (0, -0.1, 0.55), s=1.1)
def c_marron(): put(O_["marron"], hand("L", 0.2), s=1.35)
def c_feuille(): put(O_["feuille"], dome(15, 78, 0.06)[0], rot=(70, 10, 30), s=1.4); put(O_["feuille2"], (1.45, -0.4, 3.75), rot=(20, 35, 0), s=1.2); put(O_["feuille3"], (-1.5, -0.6, 2.9), rot=(-15, -40, 20), s=1.0)
def c_neige(): h_ = hand("L"); put(O_["neige"], (h_.x + 0.1, h_.y + 0.15, 0.0), s=1.2); put(O_["boule"], hand("L", 0.3), s=0.9)
def c_lance(): h_ = hand("L"); put(O_["boule"], h_ + Vector((-0.3, -0.9, 0.3)) * 1.5, s=1.05); put(O_["neige"], (1.5, 0.2, 0.0), s=0.9)


# thème : (clé, titre, période, saison de base, tenue, [(légende, pose, mise en place)])
THEMES = [
    ("nouvel_an", "Nouvel An", "31 déc. au 2 janv.", "hiver", ["etoile"], [
        ("Il sort sa coupe", dict(L=A_SHOW), c_coupe),
        ("Il trinque, les confettis explosent", dict(L=A_HIGH, R=A_SPREAD, eyes=HAPPY, mouth="happy", up=0.05, tilt=4, flap=-4), c_trinque)]),
    ("epiphanie", "Épiphanie", "1re quinzaine de janvier", "hiver", ["couronne"], [
        ("Il apporte la galette", bras("galette"), c_galette),
        ("Il a la fève !", dict(L=A_HIGH, R=A_SPREAD, eyes=WIDE, mouth="A", up=0.07, w=0.98, h=1.03, nod=-4), c_feve)]),
    ("chandeleur", "Chandeleur", "2 février", "hiver", ["toque"], [
        ("Il sort sa poêle", dict(L=A_SHOW), c_poele),
        ("Il fait sauter la crêpe", dict(L=shift(A_SHOW, dT=(0, 0, 0.18), dE=(0, 0, 0.1)), R=A_SPREAD, eyes=WIDE, mouth="o", nod=-9, h=1.02), c_crepe)]),
    ("saint_valentin", "Saint-Valentin", "14 février", "hiver", ["coeur"], [
        ("Il tient une lettre", dict(bras("enveloppe"), tilt=3), c_lettre),
        ("Il envoie des cœurs vers la souris", dict(L=A_OFFER, eyes=HAPPY, mouth="happy", tilt=6, lean=4), c_coeurs)]),
    ("mardi_gras", "Mardi gras", "semaine du mardi gras", "hiver", ["plumes"], [
        ("Il sort son masque", dict(R=A_MASK), c_masque),
        ("Il lance des confettis", dict(L=A_UP, R=A_UP, eyes=HAPPY, mouth="happy", up=0.09, w=0.98, h=1.03, flap=-6), c_confettis)]),
    ("paques", "Pâques", "week-end de Pâques", "printemps", ["oreilles"], [
        ("Il a trouvé un œuf", bras("oeuf"), c_oeuf),
        ("Il sautille comme un lapin", dict(L=A_PAW, R=A_PAW, up=0.38, w=0.96, h=1.06, eyes=HAPPY, mouth="happy", legs=(22, 22), flap=-10, nod=-3), c_lapin)]),
    ("premier_mai", "1er mai", "1er mai", "printemps", ["muguet_pin"], [
        ("Il offre un brin de muguet", dict(L=A_OFFER, tilt=3), c_muguet),
        ("Il le respire", dict(L=A_SNIFF, eyes=CALM, mouth="small", nod=7, tilt=7), c_respire)]),
    ("musique", "Fête de la musique", "21 juin", "ete", ["note_pin"], [
        ("Il sort sa guitare", dict(L=A_NECK, R=A_STRUM), c_guitare),
        ("Il joue, les notes s'envolent", dict(L=A_NECK, R=shift(A_STRUM, dT=(0, 0, -0.1)), eyes=HAPPY, mouth="A", tilt=-7, side=3, legs=(0, 16)), c_joue)]),
    ("quatorze_juillet", "14 juillet", "13 et 14 juillet", "ete", ["cocarde"], [
        ("Il sort son drapeau", dict(L=A_SHOW), c_drapeau),
        ("Il l'agite sous le feu d'artifice", dict(L=A_HIGH, R=A_SPREAD, eyes=WIDE, mouth="A", nod=-7, h=1.02), c_feu)]),
    ("halloween", "Halloween", "dernière semaine d'octobre", "automne", ["sorciere"], [
        ("Il porte sa citrouille", bras("citrouille"), c_citrouille),
        ("Bouh !", dict(L=A_CLAW, R=A_CLAW, lean=8, eyes=dict(h=1.2, w=1.2), mouth="A", up=0.05, w=0.98, h=1.03), c_bouh)]),
    ("noel", "Noël", "décembre", "hiver", ["guirlande"], [
        ("Il apporte un cadeau", bras("cadeau"), c_cadeau),
        ("Il le secoue pour deviner", dict(L=A_EAR, hturn=14, tilt=9, mouth="pensive", side=3), c_secoue)]),
    ("printemps", "Printemps", "20 mars au 20 juin", "printemps", [], [
        ("Il cueille des tulipes", dict(L=A_SHOW, tilt=3), c_tulipes),
        ("Il saute dans une flaque", dict(L=shift(A_SPREAD, dT=(0, 0, 0.25)), R=shift(A_SPREAD, dT=(0, 0, 0.25)), w=1.08, h=0.9, eyes=HAPPY, mouth="A", flap=8, flap_out=6), c_flaque)]),
    ("ete", "Été", "21 juin au 22 sept.", "ete", [], [
        ("Il mange une glace", dict(L=A_LICK, eyes=HAPPY, mouth="A", tilt=7, hturn=8), c_glace),
        ("Il barbote dans sa bouée", dict(L=A_UP, R=A_WAVE, legs=(72, 72), eyes=HAPPY, mouth="A", up=0.1, nod=-4), c_bouee)]),
    ("automne", "Automne", "23 sept. au 20 déc.", "automne", [], [
        ("Il inspecte une châtaigne", dict(R=A_LOUPE, L=A_LICK, lean=8, nod=4, mouth="o", props={"prop_loupe": 1.0}), c_marron),
        ("Une feuille lui tombe sur la tête", dict(L=shift(A_SPREAD, dT=(-0.1, 0, -0.1)), R=shift(A_SPREAD, dT=(-0.1, 0, -0.1)), eyes=WIDE, mouth="o", nod=-5, h=0.98, w=1.01), c_feuille)]),
    ("hiver", "Hiver", "21 déc. au 19 mars", "hiver", [], [
        ("Il ramasse de la neige", dict(L=A_GROUND, R=A_BACK, lean=30, nod=10, mouth="small"), c_neige),
        ("Il lance une boule vers la souris", dict(L=A_RELEASE, R=A_BACK, lean=11, turn=-8, mouth="happy", eyes=dict(h=0.92), legs=(-12, 14)), c_lance)]),
]

# ------------------------------------------------------------------ rendu
nsv = {}
exec(compile(open(os.path.join(OUTD, "scripts", "sherlock_views.py"), encoding="utf-8").read(), "sherlock_views.py", "exec"), nsv)
nsv["setup_light"]()
sc.eevee.taa_render_samples = 24
cam = bpy.data.objects["Camera"]; cam.data.type = 'PERSP'; cam.data.lens = 84
CAM_D, CAM_YAW = 12.0, math.radians(20)
cam.location = (-CAM_D * math.sin(CAM_YAW), -CAM_D * math.cos(CAM_YAW), 3.4)
bpy.data.objects["Cible_camera"].location = (0, 0, 2.2)
sc.camera = cam
sc.render.resolution_x = sc.render.resolution_y = 420; sc.render.resolution_percentage = 100
sc.frame_set(1)


def shot(key, i, saison, tenue, pose_kw, fn):
    echarpe, base = BASES[saison]
    mesh.modifiers["Masque_vg_echarpe"].show_render = not echarpe
    AO_NODE.layer_name = "Col" if echarpe else "Col_nu"
    mesh.modifiers["Masque_vg_casquette"].show_render = "sorciere" in tenue
    d = pose(**pose_kw)                                   # calculée d'abord : le solveur des bras remet la pose à zéro
    rest_all()
    for (b_, ch), v in d.items(): setattr(P[b_], PATH[ch], v)
    vl.update()
    for ob in EXTRA: ob.hide_render = True
    wear(*[T[n] for n in base + tenue if not ("sorciere" in tenue and n == "lunettes")])
    if fn: fn()
    vl.update()
    sc.render.filepath = os.path.join(OUT, "%s_%d.png" % (key, i))
    bpy.ops.render.render(write_still=True)


catalogue = []
for key, titre, periode, saison, tenue, cells in THEMES:
    catalogue.append({"cle": key, "titre": titre, "periode": periode, "saison": saison, "tenue": tenue, "legendes": ["Tenue portée en permanence"] + [c[0] for c in cells]})
    if FILTRE and key not in FILTRE: continue
    shot(key, 0, saison, tenue, dict(), None)
    for i, (legende, pose_kw, fn) in enumerate(cells, 1): shot(key, i, saison, tenue, pose_kw, fn)
json.dump(catalogue, open(os.path.join(OUT, "catalogue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
result = {"themes": len(THEMES), "rendus": len(FILTRE) or len(THEMES), "accessoires": len(EXTRA)}
