# Sherlock - film de présentation de 30 s (1920 x 1080, 60 i/s). Exécuté À LA SUITE de sherlock_build.py, sherlock_rig.py et
# sherlock_anim.py, dans le même espace de noms. Ne touche ni à sherlock.glb ni à animations.json.
#
# Déroulé : la boîte arrive et s'ouvre dans une pluie de confettis, Sherlock en sort, court partout, puis enquête sur quatre
# écrans inspirés d'ITHome (journaux, documentation, assistant, tableau de bord). Les écrans sont redessinés, sans donnée réelle.
#
#   film_still(t, chemin)      image de contrôle          film_tick()   rend quelques images (minuteur, reprise possible)
#   film_encode(chemin)        assemble les images en MP4
import random

SCR = r"C:\Users\breuilla\AppData\Local\Temp\claude\851202e51721bef7\4117ccba-52cf-45a4-bebf-96650bfc65c0\scratchpad"
FILM_DIR = os.path.join(SCR, "film"); os.makedirs(FILM_DIR, exist_ok=True)
FPS_F, DUR = 60, 30.0
NF = int(FPS_F * DUR)
TS = FPS_F / 24.0                                   # les actions sont écrites à 24 i/s : étirées de 2,5 dans le film
rnd = random.Random(7)
INTERP = []                                         # (objet, canal, image, interpolation) à appliquer à la fin


def fr(t): return 1 + int(round(t * FPS_F))


def kf(ob, path, t, value, interp=None):
    setattr(ob, path, value); ob.keyframe_insert(path, frame=fr(t))
    if interp: INTERP.append((ob, path, fr(t), interp))


def kscale(ob, keys):
    for t, s_ in keys: kf(ob, "scale", t, (s_, s_, s_) if not isinstance(s_, tuple) else s_)


def pop(ob, t, d=0.22, s1=1.0):
    """Apparition avec un petit rebond."""
    kscale(ob, [(0, 0.0), (t - 1 / FPS_F, 0.0), (t + 0.6 * d, 1.1 * s1), (t + d, s1)])


def vanish(ob, t, d=0.12): kscale(ob, [(t, 1.0), (t + d, 0.0)])


# ------------------------------------------------------------------ matières
def emat(hexcol, strength=1.0):
    name = "F_e_%s_%d" % (hexcol.lstrip("#"), int(strength * 100))
    m = M.get(name)
    if m: return m
    m = M.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = tuple(hex2lin(hexcol)) + (1,); em.inputs[1].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


def pmat(hexcol, rough=0.6, emit=0.0):
    name = "F_p_%s_%d" % (hexcol.lstrip("#"), int(emit * 100))
    m = M.get(name)
    if m: return m
    m = M.new(name); m.use_nodes = True
    P_ = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"][0]
    P_.inputs["Base Color"].default_value = tuple(hex2lin(hexcol)) + (1,); P_.inputs["Roughness"].default_value = rough
    if emit: P_.inputs["Emission Color"].default_value = tuple(hex2lin(hexcol)) + (1,); P_.inputs["Emission Strength"].default_value = emit
    return m


FONT_B = FONT_N = None
for fp_ in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
    if os.path.exists(fp_): FONT_B = bpy.data.fonts.load(fp_, check_existing=True); break
for fp_ in (r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"):
    if os.path.exists(fp_): FONT_N = bpy.data.fonts.load(fp_, check_existing=True); break


def new_obj(name, data, parent=None, loc=(0, 0, 0)):
    ob = bpy.data.objects.new("Film." + name, data); coll.objects.link(ob)
    if parent: ob.parent = parent
    ob.location = loc
    return ob


def rrect(w, h, r, seg=5, origin_left=False):
    """Rectangle arrondi dans le plan XZ, face vers -Y."""
    r = min(r, w / 2, h / 2)
    pts = []
    for cx, cz, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a) + (w / 2 if origin_left else 0), 0.0, cz + r * math.sin(a)))
    me_ = bpy.data.meshes.new("F_rect"); me_.from_pydata(pts, [], [list(range(len(pts)))]); me_.update()
    return me_


def text_obj(name, s, size, hexcol, parent, loc, align="LEFT", bold=True, upright=True):
    cu = bpy.data.curves.new("F_txt", 'FONT'); cu.body = s; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'
    f_ = FONT_B if bold else FONT_N
    if f_: cu.font = f_
    cu.materials.append(emat(hexcol))
    ob = new_obj(name, cu, parent, loc)
    if upright: ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.visible_shadow = False
    return ob


class UI:
    """Écran flottant : coordonnées en unités, origine en haut à gauche, y vers le bas."""
    def __init__(self, name, w, h, pos, yaw=0.0, base="#F7F9FC", radius=0.16):
        self.name, self.w, self.h, self.n = name, w, h, 0
        self.root = new_obj(name, None, None, pos); self.root.rotation_euler = (0, 0, math.radians(yaw))
        self.base = self.rect(0, 0, w, h, base, radius, layer=0)

    def _loc(self, x, y, layer): return (x - self.w / 2, -0.014 * layer, self.h / 2 - y)

    def rect(self, x, y, w, h, color, r=0.06, layer=1, left=False, strength=0.95):
        self.n += 1
        me_ = rrect(w, h, r, origin_left=left); me_.materials.append(emat(color, strength))
        ob = new_obj("%s.%d" % (self.name, self.n), me_, self.root, self._loc(x + (0 if left else w / 2), y + h / 2, layer))
        ob.visible_shadow = False
        return ob

    def text(self, s, x, y, size, color, layer=2, align="LEFT", bold=True):
        self.n += 1
        return text_obj("%s.%d" % (self.name, self.n), s, size, color, self.root, self._loc(x, y, layer), align, bold)

    def check(self, x, y, size=0.16, layer=3):
        """Pastille verte avec une coche blanche."""
        d = self.rect(x - size, y - size, 2 * size, 2 * size, "#3FAE6B", size, layer)
        bm_ = bmesh.new(); k = size * 0.55
        rod(bm_, (-k, 0, 0.0), (-0.25 * k, 0, -0.6 * k), size * 0.14, 6); rod(bm_, (-0.25 * k, 0, -0.6 * k), (k, 0, 0.6 * k), size * 0.14, 6)
        me_ = bpy.data.meshes.new("F_check"); bm_.to_mesh(me_); bm_.free(); me_.materials.append(emat("#FFFFFF"))
        c = new_obj("%s.coche" % self.name, me_, d, (0, -0.02, 0)); c.visible_shadow = False
        return d

    def show(self, t0, t1):
        kf(self.root, "scale", 0, (0, 0, 0), 'CONSTANT'); kf(self.root, "scale", t0, (1, 1, 1), 'CONSTANT'); kf(self.root, "scale", t1, (0, 0, 0), 'CONSTANT')


GRIS, GRIS_C, MARINE, BLEU, VERT = "#B9C4D0", "#E9EEF4", "#1F3D5C", "#226891", "#85C595"

# ================================================================== DÉCOR : plateau sombre, projecteurs
for n_ in ("Lumiere_cle", "Lumiere_debouchage", "Lumiere_contre", "Sol_ombre"):
    o_ = bpy.data.objects.get(n_)
    if o_: o_.hide_render = True
prof = [(-45.0, 0.0), (7.0, 0.0)] + [(7.0 + 5 * math.sin(math.radians(a)), 5.0 - 5 * math.cos(math.radians(a))) for a in range(10, 91, 10)] + [(12.0, 18.0)]
vs_ = [(x, y, z) for (y, z) in prof for x in (-50.0, 50.0)]
fs_ = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
me_ = bpy.data.meshes.new("F_cyclo"); me_.from_pydata(vs_, [], fs_); me_.update()
for p_ in me_.polygons: p_.use_smooth = True
me_.materials.append(pmat("#1B4466", 0.8))
cyclo = new_obj("Plateau", me_)


def light(name, kind, loc, aim, energy, size=1.0, color=(1, 1, 1), spot=None):
    ld = bpy.data.lights.new("F_" + name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.shape = 'DISK'; ld.size = size
    if kind == 'SPOT': ld.spot_size = math.radians(spot); ld.spot_blend = 0.85; ld.shadow_soft_size = size
    ob = new_obj(name, ld, None, loc)
    ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob


light("Cle", "AREA", (-6, -9, 9), (0, 0, 1.6), 900, 11)
light("Face", "AREA", (5, -11, 3.5), (0, 0, 1.8), 260, 9)
light("Contre", "AREA", (5, 6.5, 7), (0, 0, 2.0), 650, 6, (0.62, 0.82, 1.0))
light("Poursuite", "SPOT", (0, -3, 13), (0, -0.5, 0), 2600, 1.6, spot=70)
nt_ = sc.world.node_tree; nt_.nodes.clear()
o1_ = nt_.nodes.new("ShaderNodeOutputWorld"); b1_ = nt_.nodes.new("ShaderNodeBackground"); nt_.links.new(b1_.outputs[0], o1_.inputs[0])
b1_.inputs[0].default_value = (0.75, 0.85, 1.0, 1); b1_.inputs[1].default_value = 0.3

# ================================================================== LA BOÎTE
BW, BH = 1.75, 1.5


def box_mesh(sx, sy, sz, z0=0.0):
    bm_ = bmesh.new(); bmesh.ops.create_cube(bm_, size=1.0)
    for v in bm_.verts: v.co = Vector((v.co.x * sx, v.co.y * sy, (v.co.z + 0.5) * sz + z0))
    me_ = bpy.data.meshes.new("F_box"); bm_.to_mesh(me_); bm_.free()
    return me_


boite = new_obj("Boite", None)
m_ = box_mesh(BW, BW, BH); m_.materials.append(pmat("#226891", 0.55)); corps_b = new_obj("Boite.corps", m_, boite)
for sx_, sy_ in ((0.3, BW + 0.03), (BW + 0.03, 0.3)):
    m_ = box_mesh(sx_, sy_, BH + 0.004); m_.materials.append(pmat("#85C595", 0.5, 0.15)); new_obj("Boite.ruban", m_, corps_b)
couv = new_obj("Boite.couvercle", None, boite, (0, 0, BH))
m_ = box_mesh(BW + 0.18, BW + 0.18, 0.34, -0.06); m_.materials.append(pmat("#2A78A6", 0.5)); new_obj("Boite.couv", m_, couv)
for sx_, sy_ in ((0.3, BW + 0.21), (BW + 0.21, 0.3)):
    m_ = box_mesh(sx_, sy_, 0.345, -0.062); m_.materials.append(pmat("#85C595", 0.5, 0.15)); new_obj("Boite.ruban2", m_, couv)
for sx_ in (1, -1):                                  # nœud du ruban
    bm_ = superellipsoid(16, 10, 0.32, 0.17, 0.2)
    me_ = bpy.data.meshes.new("F_noeud"); bm_.to_mesh(me_); bm_.free(); me_.materials.append(pmat("#85C595", 0.5, 0.15))
    for p_ in me_.polygons: p_.use_smooth = True
    o_ = new_obj("Boite.noeud", me_, couv, (0.27 * sx_, 0, 0.42)); o_.rotation_euler = (0, math.radians(-28 * sx_), 0)
T_BURST = 3.0
for t, z in ((0.0, 10.0), (0.25, 6.5), (0.5, 0.0)): kf(boite, "location", t, (0, 0, z))
for t, s_ in ((0.5, (1, 1, 1)), (0.58, (1.14, 1.14, 0.78)), (0.74, (0.95, 0.95, 1.07)), (0.9, (1, 1, 1)), (2.76, (1, 1, 1)), (2.96, (1.1, 1.1, 0.84)), (3.06, (0.96, 0.96, 1.1)), (3.2, (1, 1, 1))):
    kf(boite, "scale", t, s_)
wob = [(1.25, 0), (1.34, 7), (1.44, -7), (1.54, 5), (1.64, 0), (2.05, 0), (2.13, 11), (2.21, -11), (2.29, 11), (2.37, -11), (2.45, 9), (2.53, -9), (2.62, 0)]
for t, a in wob: kf(boite, "rotation_euler", t, (0, math.radians(a), 0))
for t, z in ((2.05, 0), (2.17, 0.28), (2.29, 0), (2.41, 0.32), (2.53, 0), (2.7, 0)): kf(boite, "location", t, (0, 0, z))
kscale(corps_b, [(0, 1.0), (3.35, 1.0), (3.75, 0.0)])
for t, loc_, rot_ in ((T_BURST, (0, 0, BH), (0, 0, 0)), (3.25, (0.4, 1.6, BH + 4.2), (3.5, 0.6, 0)), (3.6, (0.9, 4.0, BH + 5.2), (8.0, 1.4, 0)), (4.1, (1.4, 7.5, 0.6), (13.0, 2.2, 0))):
    kf(couv, "location", t, loc_); kf(couv, "rotation_euler", t, rot_)
kscale(couv, [(0, 1.0), (3.9, 1.0), (4.15, 0.0)])

# ================================================================== CONFETTIS : gerbe à l'ouverture, pluie à la fin
COULEURS = ["#85C595", "#4FA3D1", "#E5A13A", "#F7D24B", "#FFFFFF", "#F28B82"]
m_rect = box_mesh(0.2, 0.012, 0.11, -0.055); m_ball = bpy.data.meshes.new("F_ball")
bm_ = bmesh.new(); bmesh.ops.create_uvsphere(bm_, u_segments=12, v_segments=8, radius=0.065); bm_.to_mesh(m_ball); bm_.free()
for p_ in m_ball.polygons: p_.use_smooth = True
bm_ = bmesh.new(); rod(bm_, (-0.09, 0, 0.0), (-0.02, 0, -0.07), 0.025, 6); rod(bm_, (-0.02, 0, -0.07), (0.1, 0, 0.08), 0.025, 6)
m_chk = bpy.data.meshes.new("F_chk"); bm_.to_mesh(m_chk); bm_.free()
bm_ = bmesh.new(); rod(bm_, (-0.08, 0, 0), (0.08, 0, 0), 0.025, 6); rod(bm_, (0, 0, -0.08), (0, 0, 0.08), 0.025, 6)
m_plus = bpy.data.meshes.new("F_plus"); bm_.to_mesh(m_plus); bm_.free()
SHAPES = [m_rect] * 6 + [m_ball] * 2 + [m_chk, m_plus]


def simulate(p0, v0, t0, t1, drag, g):
    pts, p, v, t, k = [], Vector(p0), Vector(v0), t0, 0
    while t <= t1:
        if k % 4 == 0: pts.append((t, p.copy()))
        v.z -= g / FPS_F; v *= (1 - drag / FPS_F); p += v / FPS_F
        if p.z < 0.03:
            p.z = 0.03; pts.append((t, p.copy())); break
        t += 1 / FPS_F; k += 1
    return pts


for i in range(130):
    src = SHAPES[i % len(SHAPES)]
    ob = new_obj("Confetti.%03d" % i, src.copy()); ob.data.materials.append(pmat(COULEURS[i % len(COULEURS)], 0.5, 0.45))
    te = T_BURST + rnd.uniform(0.0, 0.14)
    az_, tilt = rnd.uniform(0, 2 * math.pi), math.radians(rnd.uniform(4, 58)); sp = rnd.uniform(7.5, 13.5)
    v0 = (sp * math.sin(tilt) * math.cos(az_), sp * math.sin(tilt) * math.sin(az_) * 0.8 - 0.8, sp * math.cos(tilt))
    pts = simulate((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 1.5), v0, te, 5.5, rnd.uniform(0.7, 1.7), 15.0)
    tr = 26.45 + rnd.uniform(0.0, 2.6)                 # pluie finale
    pts2 = simulate((rnd.uniform(-7.5, 7.5), rnd.uniform(-4.0, 3.0), rnd.uniform(6.5, 9.5)), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.4, 0.4), -1.5), tr, 30.2, 1.7, 4.2)
    kscale(ob, [(0, 0.0), (te - 1 / FPS_F, 0.0), (te, 1.0), (5.25, 1.0), (5.6, 0.0), (tr - 1 / FPS_F, 0.0), (tr, rnd.uniform(0.9, 1.5))])
    for t, p in pts + pts2: kf(ob, "location", t, p)
    r0 = Vector((rnd.uniform(0, 6), rnd.uniform(0, 6), rnd.uniform(0, 6))); w_ = Vector((rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))
    for t in (te, pts[-1][0], tr, 30.2): kf(ob, "rotation_euler", t, tuple(r0 + w_ * (t - te) * (1.0 if t < 20 else 0.35)), 'LINEAR')

# ================================================================== ÉCRANS inspirés d'ITHome (aucune donnée réelle)
PANEL_POS = (1.9, 2.4, 2.45)
T_TAPE = 12.9                                       # instant où Sherlock tape la ligne en erreur
PD = (-1.35, 2.0)                                  # sa place : au bord gauche des écrans, tout contre

# ---- journaux
ui = UI("Journaux", 5.2, 3.3, PANEL_POS, -7)
ui.text("Journaux", 0.3, 0.3, 0.2, MARINE)
ui.rect(3.25, 0.19, 1.65, 0.22, GRIS_C, 0.11)
for i_, c_ in enumerate(("#DDEFE3", "#FDF0DC", "#FBE3E1")): ui.rect(1.75 + i_ * 0.45, 0.22, 0.38, 0.16, c_, 0.08)
NIV = [("INFO", "#DDEFE3", "#3C9A5F"), ("INFO", "#DDEFE3", "#3C9A5F"), ("WARN", "#FDF0DC", "#C98A1E"), ("INFO", "#DDEFE3", "#3C9A5F"),
       ("ERREUR", "#FBE3E1", "#D2504A"), ("INFO", "#DDEFE3", "#3C9A5F"), ("INFO", "#DDEFE3", "#3C9A5F"), ("WARN", "#FDF0DC", "#C98A1E")]
for i_, (lab, bg, fg) in enumerate(NIV):
    y_ = 0.6 + i_ * 0.32; tp = 8.95 + i_ * 0.06
    if lab == "ERREUR":                                # repérée à la loupe (10,8 s), validée d'une tape (12,9 s)
        err = ui.rect(0.2, y_ - 0.03, 4.8, 0.31, "#E5645E", 0.09, layer=1); pop(err, 10.8, 0.2)
        for t, s_ in ((11.0, 1.0), (11.25, 1.03), (11.5, 1.0), (11.75, 1.03), (12.0, 1.0), (12.25, 1.03), (12.5, 1.0), (12.8, 1.0), (12.92, 0.0)): kscale(err, [(t, s_)])
        okr = ui.rect(0.2, y_ - 0.03, 4.8, 0.31, "#3FAE6B", 0.09, layer=1); pop(okr, T_TAPE, 0.2)
        okc = ui.check(4.72, y_ + 0.125, 0.15, layer=4); pop(okc, T_TAPE + 0.05, 0.25)
    row = ui.rect(0.24, y_, 4.72, 0.25, "#F1F5F9" if lab != "ERREUR" else "#FFF5F4", 0.07, layer=2); pop(row, tp, 0.18)
    for ob_ in (ui.rect(0.4, y_ + 0.09, 0.5, 0.07, GRIS, 0.035, layer=3), ui.rect(1.05, y_ + 0.045, 0.62, 0.16, bg, 0.08, layer=3),
                ui.text(lab, 1.36, y_ + 0.125, 0.085, fg, layer=4, align="CENTER"),
                ui.rect(1.85, y_ + 0.09, rnd.uniform(1.3, 2.6), 0.07, GRIS if lab != "ERREUR" else "#E7A19C", 0.035, layer=3)):
        pop(ob_, tp + 0.04, 0.18)
ui.show(8.5, 13.6)
for t, x in ((8.5, 13.0), (8.9, 1.75), (9.05, PANEL_POS[0])): kf(ui.root, "location", t, (x, PANEL_POS[1], PANEL_POS[2]))

# ---- documentation
ui = UI("Doc", 5.2, 3.3, PANEL_POS, -7)
ui.text("Documentation", 0.3, 0.3, 0.2, MARINE)
ui.rect(0.2, 0.55, 1.3, 2.55, "#F1F5F9", 0.1)
for i_ in range(7):
    if i_ == 2: ui.rect(0.28, 0.66 + i_ * 0.33, 1.14, 0.24, BLEU, 0.08, layer=2); ui.rect(0.4, 0.75 + i_ * 0.33, 0.7, 0.06, "#FFFFFF", 0.03, layer=3)
    else: ui.rect(0.4, 0.75 + i_ * 0.33, rnd.uniform(0.5, 0.9), 0.06, GRIS, 0.03, layer=2)
ui.rect(1.75, 0.7, 2.1, 0.14, MARINE, 0.05, layer=2)
ui.rect(3.75, 1.1, 1.2, 0.75, "#DCE9F5", 0.08, layer=2)
for i_ in range(9):
    wl_ = (1.8 if i_ < 4 else 3.1) * rnd.uniform(0.8, 1.0); y_ = 1.12 + i_ * 0.21
    if i_ in (4, 5, 6):
        hl = ui.rect(1.72, y_ - 0.055, wl_ + 0.06, 0.17, "#FFE48A", 0.04, layer=2, left=True)
        t0 = 14.8 + (i_ - 4) * 0.42
        kf(hl, "scale", 0, (0, 1, 1)); kf(hl, "scale", t0, (0, 1, 1)); kf(hl, "scale", t0 + 0.36, (1, 1, 1))
    ui.rect(1.75, y_, wl_, 0.06, GRIS if i_ not in (4, 5, 6) else "#8A97A6", 0.03, layer=3)
card = new_obj("Doc.extrait", None, ui.root, (0.55, -0.9, -0.35))
for me_, loc_ in ((rrect(2.9, 1.35, 0.14), (0, 0, 0)), (rrect(2.78, 1.23, 0.1), (0, -0.012, 0))):
    me_.materials.append(emat(VERT if loc_[1] == 0 else "#FFFFFF", 0.97)); new_obj("Doc.extrait.f", me_, card, loc_).visible_shadow = False
me_ = rrect(1.5, 0.13, 0.05); me_.materials.append(emat(MARINE)); new_obj("Doc.extrait.t", me_, card, (-0.45, -0.024, 0.38)).visible_shadow = False
for i_, w_ in enumerate((2.3, 2.1, 1.5)):
    me_ = rrect(w_, 0.065, 0.03); me_.materials.append(emat("#8A97A6")); new_obj("Doc.extrait.l", me_, card, (-1.2 + w_ / 2, -0.024, 0.1 - i_ * 0.22)).visible_shadow = False
pop(card, 16.95, 0.3)
for t, loc_ in ((16.95, (0.9, -0.2, 0.2)), (17.35, (0.55, -0.9, -0.35))): kf(card, "location", t, loc_)
ui.show(13.6, 18.6)

# ---- assistant
ui = UI("Assistant", 5.2, 3.3, PANEL_POS, -7)
ui.rect(0.25, 0.16, 0.3, 0.3, BLEU, 0.08)
ui.text("SHERLOCK", 0.68, 0.24, 0.15, "#0E1F30"); ui.text("ASSISTANT", 1.63, 0.24, 0.15, BLEU)
ui.rect(0.68, 0.38, 1.9, 0.045, GRIS, 0.02)
q = ui.text("On enquête sur quoi ?", 3.1, 1.45, 0.24, "#0E1F30", align="CENTER"); pop(q, 18.75, 0.25); vanish(q, 19.15)
bar = ui.rect(1.3, 2.72, 3.6, 0.36, "#EEF3F8", 0.18); vanish(bar, 21.6)
bt_ = ui.text("Posez votre question à Sherlock", 1.55, 2.9, 0.1, "#8A97A6", bold=False); vanish(bt_, 21.6)
ui.rect(4.53, 2.77, 0.26, 0.26, "#8DB9D4", 0.09, layer=2)
ub = ui.rect(2.55, 0.72, 2.35, 0.5, BLEU, 0.2); pop(ub, 19.25, 0.25)
for i_, w_ in enumerate((1.8, 1.2)): pop(ui.rect(2.8, 0.86 + i_ * 0.16, w_, 0.06, "#FFFFFF", 0.03, layer=2), 19.3, 0.22)
tb = ui.rect(1.35, 1.4, 0.9, 0.4, "#EEF3F8", 0.18); pop(tb, 19.65, 0.2); kscale(tb, [(20.35, 1.0), (20.45, 0.0)])
for i_ in range(3):
    dot = ui.rect(1.57 + i_ * 0.17, 1.55, 0.11, 0.11, "#8A97A6", 0.055, layer=2); pop(dot, 19.7, 0.15)
    for k_ in range(3):
        t0 = 19.8 + k_ * 0.2 + i_ * 0.06
        kscale(dot, [(t0, 1.0), (t0 + 0.07, 1.5), (t0 + 0.14, 1.0)])
    kscale(dot, [(20.35, 1.0), (20.42, 0.0)])
ab = ui.rect(1.35, 1.4, 3.55, 1.15, "#EEF3F8", 0.2); pop(ab, 20.42, 0.28)
for i_, w_ in enumerate((3.0, 2.8, 3.1, 2.3)):
    ln = ui.rect(1.6, 1.58 + i_ * 0.21, w_, 0.065, "#5F7186", 0.03, layer=2, left=True)
    t0 = 20.6 + i_ * 0.26
    kf(ln, "scale", 0, (0, 1, 1)); kf(ln, "scale", t0, (0, 1, 1)); kf(ln, "scale", t0 + 0.24, (1, 1, 1))
chip = ui.rect(1.35, 2.7, 1.5, 0.32, "#DDEFE3", 0.16); pop(chip, 21.8, 0.25)
pop(ui.text("Source vérifiée", 2.1, 2.86, 0.095, "#3C9A5F", layer=2, align="CENTER"), 21.85, 0.22)
pop(ui.check(3.12, 2.86, 0.16, layer=3), 22.0, 0.25)
ui.show(18.6, 23.0)

# ---- tableau de bord
DW, DH = 8.6, 4.5
ui = UI("Tableau", DW, DH, (0, 3.6, 2.55), 0, base="#F4F6F9", radius=0.2)
tw = 23.02                                           # les éléments arrivent en vague
side = ui.rect(0.12, 0.12, 1.5, DH - 0.24, "#FFFFFF", 0.14); pop(side, tw, 0.2)
pop(ui.rect(0.3, 0.3, 0.26, 0.26, "#2E7FA6", 0.07, layer=2), tw + 0.05, 0.2); pop(ui.text("IT Home", 0.64, 0.43, 0.15, "#0E1F30", layer=2), tw + 0.05, 0.2)
MENU = ["Tableau de bord", "Sherlock", "Boîte d'envoi", "FileFlow", "Dataflow", "TrackOps", "Sondes", "Enovacom", "Outils"]
for i_, lab in enumerate(MENU):
    y_ = 0.85 + i_ * 0.36
    if i_ == 0: pop(ui.rect(0.22, y_ - 0.13, 1.3, 0.26, BLEU, 0.1, layer=2), tw + 0.1, 0.2)
    pop(ui.rect(0.32, y_ - 0.045, 0.09, 0.09, "#FFFFFF" if i_ == 0 else "#8FA3B5", 0.03, layer=3), tw + 0.1 + i_ * 0.02, 0.18)
    pop(ui.text(lab, 0.48, y_, 0.092, "#FFFFFF" if i_ == 0 else "#33475B", layer=3), tw + 0.1 + i_ * 0.02, 0.18)
x0 = 1.78
for i_, lab in enumerate(("TRACKOPS", "FILEFLOW", "DATAFLOW", "SONDES", "ENOVACOM", "SERVEURS")):
    x_ = x0 + i_ * 1.115; t0 = tw + 0.15 + i_ * 0.04
    pop(ui.rect(x_, 0.14, 1.03, 0.44, "#FFFFFF", 0.1), t0, 0.2); pop(ui.rect(x_ + 0.08, 0.22, 0.28, 0.28, "#A9D3B4", 0.08, layer=2), t0 + 0.03, 0.2)
    pop(ui.text(lab, x_ + 0.42, 0.3, 0.062, "#33475B", layer=2), t0 + 0.03, 0.2); pop(ui.rect(x_ + 0.42, 0.4, 0.45, 0.04, GRIS, 0.02, layer=2), t0 + 0.03, 0.2)
TILES = [("#E7F4EB", "#5FAE7B", "SUCCÈS"), ("#FCEBE9", "#E07A72", "ERREURS"), ("#E9F0FB", "#5B8FD6", "EN COURS"), ("#FDF2E3", "#E2A04A", "EN ATTENTE")]
BADGES = []
for w_i, (title, vals) in enumerate((("FILEFLOW", ("57", "0", "0", "0")), ("DATAFLOW", ("4", "0", "0", "0")))):
    cx = x0 + w_i * 3.37; t0 = tw + 0.35 + w_i * 0.1
    pop(ui.rect(cx, 0.75, 3.27, 1.85, "#FFFFFF", 0.14), t0, 0.22); pop(ui.text(title, cx + 0.18, 0.95, 0.075, "#6B7C8F", layer=2), t0 + 0.04, 0.2)
    for k_, ((bg, fg, lab), val) in enumerate(zip(TILES, vals)):
        tx, ty = cx + 0.14 + (k_ % 2) * 1.53, 1.12 + (k_ // 2) * 0.72; t1 = t0 + 0.08 + k_ * 0.05
        pop(ui.rect(tx, ty, 1.46, 0.64, bg, 0.1, layer=2), t1, 0.2)
        pop(ui.text(val, tx + 0.73, ty + 0.26, 0.26, fg, layer=3, align="CENTER"), t1 + 0.03, 0.2)
        pop(ui.text(lab, tx + 0.73, ty + 0.5, 0.055, fg, layer=3, align="CENTER"), t1 + 0.03, 0.2)
        if k_ == 0: BADGES.append((tx + 1.3, ty + 0.14))
t0 = tw + 0.6
pop(ui.rect(x0, 2.76, 2.2, 1.6, "#FFFFFF", 0.14), t0, 0.22); pop(ui.text("SONDES", x0 + 0.18, 2.96, 0.075, "#6B7C8F", layer=2), t0 + 0.04, 0.2)
pop(ui.text("14/14", x0 + 1.1, 3.42, 0.3, "#5FAE7B", layer=2, align="CENTER"), t0 + 0.08, 0.2); pop(ui.rect(x0 + 0.25, 3.78, 1.7, 0.08, "#8DB9D4", 0.04, layer=2), t0 + 0.1, 0.2)
pop(ui.text("en ligne", x0 + 1.1, 4.05, 0.075, "#6B7C8F", layer=2, align="CENTER", bold=False), t0 + 0.1, 0.2)
BADGES.append((x0 + 1.95, 2.95))
pop(ui.rect(x0 + 2.32, 2.76, 4.32, 1.6, "#FFFFFF", 0.14), t0 + 0.06, 0.22); pop(ui.text("OUTILS", x0 + 2.5, 2.96, 0.075, "#6B7C8F", layer=2), t0 + 0.1, 0.2)
for k_ in range(8):
    tx, ty = x0 + 2.46 + (k_ % 4) * 1.03, 3.15 + (k_ // 4) * 0.58
    pop(ui.rect(tx, ty, 0.95, 0.5, "#F4F6F9", 0.09, layer=2), t0 + 0.12 + k_ * 0.03, 0.18); pop(ui.rect(tx + 0.36, ty + 0.12, 0.22, 0.22, "#8DB9D4", 0.06, layer=3), t0 + 0.14 + k_ * 0.03, 0.18)
TOP_Z = 2.55 + DH / 2; MINI = 0.5                    # Sherlock, en petit, court sur le bord supérieur de l écran
LAND = (2.3, -0.3)
RUN_T0, RUN_T1, RUN_X0, RUN_X1 = 23.05, 24.2, -4.3, 2.6
for bx, by in BADGES:                                # chaque coche apparaît quand il passe au-dessus
    tb_ = RUN_T0 + (bx - DW / 2 - RUN_X0) / (RUN_X1 - RUN_X0) * (RUN_T1 - RUN_T0)
    pop(ui.check(bx, by, 0.14, layer=4), max(23.4, tb_), 0.25)
ui.show(23.0, 26.6)

# ================================================================== SHERLOCK : actions propres au film (24 i/s, étirées ensuite)
ad.use_nla = False


def court_fn(ph):
    s_, c2 = sinw(ph), cosw(ph, 2)
    d = pose(L=shift(A_DOWN, dT=(0.02, 0.34 * s_, 0.14), dE=(0, 0.16 * s_, 0.05)), R=shift(A_DOWN, dT=(0.02, -0.34 * s_, 0.14), dE=(0, -0.16 * s_, 0.05)),
             lean=13, w=1 + 0.02 * c2, h=1 - 0.03 * c2, up=0.07 * (0.5 - 0.5 * c2), nod=-7, flap=16 + 5 * c2, legs=(33 * s_, -33 * s_),
             mouth="happy", sc_amp=0.0)
    for b_, a_ in (("scarf_end_1", 26), ("scarf_end_1_tip", 14), ("scarf_end_2", 30), ("scarf_end_2_tip", 16)):
        d[(b_, 'quat')] = wq(b_, Rw(XA, a_ + 6 * c2))
    return d


loop("film_court", court_fn, 0.32, "film", step=1)
HAPPY_ = dict(closed="happy")
shot("film_saut", [(0, pose(L=A_UP, R=A_UP, w=0.94, h=1.08, eyes=HAPPY_, mouth="happy", nod=-6, flap=-8, flap_out=6, sc_amp=2.0)),
                   (0.37, pose(L=shift(A_UP, dT=(0.12, 0, 0.04)), R=shift(A_UP, dT=(0.12, 0, 0.04)), w=0.98, h=1.03, eyes=HAPPY_, mouth="happy", nod=-4, legs=(18, -14), flap_out=10)),
                   (0.87, pose(L=shift(A_SPREAD, dT=(0, 0, -0.1)), R=shift(A_SPREAD, dT=(0, 0, -0.1)), w=1.1, h=0.88, eyes=HAPPY_, mouth="happy", nod=4, flap=8)),
                   (1.05, pose(w=0.98, h=1.03, mouth="happy", nod=-2)), (1.3, N)], "film")
shot("film_stop", [(0, pose(L=shift(A_SPREAD, dT=(0, -0.2, 0)), R=shift(A_SPREAD, dT=(0, -0.2, 0)), lean=-11, w=1.06, h=0.94, nod=-5, flap=-14, legs=(26, 20), eyes=dict(h=1.1, w=1.1), mouth="o")),
                   (0.2, pose(lean=6, w=0.99, h=1.02, nod=3, flap=10)), (0.42, N)], "film")
TAPE = dict(E=(1.0, 0.16, 1.66), T=(1.42, 0.16, 2.08))                   # bras gauche tendu vers l'écran
shot("film_tape", [(0, N), (0.14, pose(L=shift(A_DOWN, dT=(0.1, 0, 0.2)), side=-2, nod=-2, eyes=dict(h=1.08, w=1.08))),
                   (0.28, pose(L=TAPE, side=5, hturn=14, nod=-3, eyes=dict(h=1.08, w=1.08), mouth="happy", flap=-4)),
                   (0.36, pose(L=shift(TAPE, dT=(-0.06, 0, 0)), side=4, hturn=14, nod=-2, mouth="happy")),
                   (0.6, pose(L=TAPE, side=4, hturn=10, eyes=dict(closed="happy"), mouth="happy")), (0.85, N)], "film")
for n_ in ("film_court", "film_saut", "film_stop", "film_tape"): META.pop(n_, None)     # hors du catalogue web

# ================================================================== MONTAGE : pistes NLA et déplacements du personnage
for tr in ad.nla_tracks: tr.mute = True
base = bpy.data.actions.new("film_base"); ad.action = base
for f in (1, NF + 1):
    for pb in P:
        for ch, path in PATH.items():
            setattr(pb, path, N.get((pb.name, ch), REST[ch]).copy()); pb.keyframe_insert(path, frame=f)


def rig_key(t, x, y, z=0.0, yaw=None, cut=False, lin=False):
    it = 'CONSTANT' if cut else ('LINEAR' if lin else None)
    kf(arm, "location", t, (x, y, z), it)
    if yaw is not None: kf(arm, "rotation_euler", t, (0, 0, math.radians(yaw)), it)


kf(arm, "scale", 0, (0.001, 0.001, 0.001)); kf(arm, "scale", T_BURST, (0.001, 0.001, 0.001)); kf(arm, "scale", T_BURST + 0.08, (1, 1, 1))
kf(arm, "scale", 23.0 - 1 / FPS_F, (1, 1, 1), "CONSTANT"); kf(arm, "scale", 23.0, (MINI, MINI, MINI)); kf(arm, "scale", RUN_T1, (MINI, MINI, MINI))   # petit sur le tableau de bord...
kf(arm, "scale", RUN_T1 + 0.84, (1, 1, 1)); kf(arm, "scale", DUR, (1, 1, 1))                                                                 # ... il reprend sa taille en sautant
rig_key(0, 0, 0, 0.6, 0); rig_key(T_BURST, 0, 0, 0.6, 0, lin=True)
for i_ in range(1, 27):                              # sortie de la boîte : trajectoire balistique jusqu'à (0, -1,6)
    u = i_ / 26.0; t = 3.08 + 0.87 * u
    rig_key(t, 0, -1.6 * u, 0.9 + 8.6 * u - 9.5 * u * u, 0, lin=True)
rig_key(5.9, 0, -1.6, 0, 0); rig_key(6.05, 0, -1.6, 0, 90, lin=True)
rig_key(6.0, 0.0, -1.6, 0, None, lin=True); rig_key(6.85 - 1 / FPS_F, 7.6, -1.6, 0, 90, cut=True)                   # il file vers la droite
rig_key(6.85, 7.6, 1.6, 0, -90, lin=True); rig_key(7.65 - 1 / FPS_F, -7.6, 1.6, 0, -90, cut=True)                    # traverse le fond dans l'autre sens
rig_key(7.65, -2.4, 7.5, 0, 0, lin=True); rig_key(8.3, -1.8, -0.5, 0, 0, lin=True)             # arrive face caméra...
rig_key(8.5, -1.75, 0.0, 0, 180, lin=True); rig_key(9.05, PD[0], PD[1], 0, 170, lin=True)       # ... et file vers l écran
rig_key(9.35, PD[0], PD[1], 0, 68); rig_key(12.45, PD[0], PD[1], 0, 68); rig_key(12.72, PD[0], PD[1], 0, -6)
rig_key(13.6 - 1 / FPS_F, PD[0], PD[1], 0, -6, cut=True); rig_key(13.6, PD[0], PD[1], 0, 52)
rig_key(16.7, PD[0], PD[1], 0, 52); rig_key(17.0, PD[0], PD[1], 0, 12)
rig_key(18.6 - 1 / FPS_F, PD[0], PD[1], 0, 12, cut=True); rig_key(18.6, PD[0], PD[1], 0, 22)
rig_key(23.0 - 1 / FPS_F, PD[0], PD[1], 0, 22, cut=True)
rig_key(23.0, RUN_X0 - 0.3, 3.6, TOP_Z, 90, lin=True); rig_key(RUN_T1, RUN_X1, 3.6, TOP_Z, 90, lin=True)   # course sur le haut du tableau de bord
for i_ in range(1, 25):                              # saut jusque devant l'écran
    u = i_ / 24.0
    rig_key(RUN_T1 + 0.84 * u, RUN_X1 + (LAND[0] - RUN_X1) * u, 3.6 + (LAND[1] - 3.6) * u, TOP_Z * (1 - u) + 2.0 * u * (1 - u), 90 * (1 - u), lin=True)
rig_key(26.6 - 1 / FPS_F, LAND[0], LAND[1], 0, 0, cut=True); rig_key(26.6, -1.9, -0.5, 0, 0); rig_key(DUR, -1.9, -0.5, 0, 0)
base.use_frame_range = True; base.frame_start, base.frame_end = 1, NF + 1
ad.action = None; rest_all(); arm.scale = (1, 1, 1); arm.location = (0, 0, 0); arm.rotation_euler = (0, 0, 0)


def strip(track, name, t, repeat=1.0, hold=False, scale=TS):
    a_ = bpy.data.actions[name]
    st = track.strips.new("%s_%d" % (name, fr(t)), fr(t), a_)
    st.extrapolation = 'HOLD_FORWARD' if hold else 'NOTHING'
    st.use_auto_blend = False; st.blend_in = st.blend_out = 0
    st.scale = scale
    if repeat != 1.0: st.repeat = repeat
    return st


t_ = ad.nla_tracks.new(); t_.name = "film_base"; strip(t_, "film_base", 0, hold=True, scale=1.0)
t_ = ad.nla_tracks.new(); t_.name = "film_repos"; strip(t_, "repos", 0, repeat=10)
def strip_until(track, name, t0, t1):
    """Boucle répétée de t0 à t1."""
    a_ = bpy.data.actions[name]
    n_ = (a_.frame_end - a_.frame_start) * TS
    return strip(track, name, t0, max(0.1, (fr(t1) - fr(t0)) / n_))


t_ = ad.nla_tracks.new(); t_.name = "film_corps"
strip(t_, "film_saut", 3.08); strip(t_, "salut", 4.45)
strip_until(t_, "film_court", 5.98, 9.04); strip(t_, "film_stop", 9.06)
strip(t_, "enquete_entree", 9.5); strip(t_, "enquete", 10.1); strip(t_, "enquete_sortie", 12.1); strip(t_, "film_tape", T_TAPE - 0.28)
strip(t_, "reflechit_entree", 13.8); strip(t_, "reflechit", 14.3); strip(t_, "reflechit_sortie", 16.3); strip(t_, "idee", 16.85)
strip(t_, "parle_entree", 19.0); strip_until(t_, "parle", 19.3, 22.98)
strip_until(t_, "film_court", 23.0, RUN_T1 - 0.02); strip(t_, "film_saut", RUN_T1 + 0.0); strip_until(t_, "reussite", 25.52, 26.58)
strip(t_, "salut", 26.9)
t_ = ad.nla_tracks.new(); t_.name = "film_visage"
for name, t, rep in (("cligne", 9.35, 1), ("cligne", 15.0, 1), ("cligne", 18.9, 1), ("bouche_parle", 20.45, 5), ("cligne", 26.7, 1)):
    strip(t_, name, t, rep)
strip(t_, "yeux_fermes", 29.15, hold=True)
ad.use_nla = True

# ================================================================== CAMÉRA (une seule, coupes franches) et slogans
cam = bpy.data.objects["Camera"]; tgt = bpy.data.objects["Cible_camera"]
for o_ in (cam, tgt):
    if o_.animation_data: o_.animation_data_clear()
cam.data.type = 'PERSP'; cam.data.lens = 40; cam.data.clip_start = 0.1; cam.data.clip_end = 300
sc.camera = cam


def cam_key(t, pos, aim, cut=False):
    kf(cam, "location", t, pos, 'CONSTANT' if cut else None); kf(tgt, "location", t, aim, 'CONSTANT' if cut else None)


E_ = 1 / FPS_F
cam_key(0.0, (0, -15.5, 2.3), (0, 0, 1.5)); cam_key(2.9, (0, -10.8, 1.9), (0, 0, 1.25))
cam_key(3.12, (0, -11.6, 2.2), (0, -0.4, 2.4)); cam_key(3.5, (0, -13.0, 2.8), (0, -0.8, 3.3))
cam_key(4.3, (1.0, -11.8, 2.3), (1.0, -1.6, 1.9)); cam_key(5.9, (1.0, -11.6, 2.3), (1.0, -1.6, 1.9))
cam_key(6.85 - E_, (2.4, -12.2, 2.3), (2.8, -1.6, 1.7), cut=True)
cam_key(6.85, (0, -12.5, 7.0), (0, 1.2, 0.9)); cam_key(7.65 - E_, (0, -12.2, 6.8), (0, 1.2, 0.9), cut=True)
cam_key(7.65, (-1.3, -8.6, 1.25), (-1.6, 0.0, 1.35)); cam_key(8.35, (-1.1, -9.2, 1.5), (-1.3, 0.0, 1.4))
cam_key(9.2, (1.0, -8.6, 2.5), (1.25, 1.6, 2.15)); cam_key(13.6 - E_, (1.5, -8.0, 2.4), (1.3, 1.6, 2.15), cut=True)
cam_key(13.6, (2.0, -7.9, 2.35), (1.3, 1.6, 2.2)); cam_key(18.6 - E_, (1.4, -7.5, 2.35), (1.25, 1.6, 2.2), cut=True)
cam_key(18.6, (0.7, -8.4, 2.45), (1.25, 1.6, 2.15)); cam_key(23.0 - E_, (1.2, -7.9, 2.35), (1.3, 1.6, 2.15), cut=True)
cam_key(23.0, (0, -11.0, 3.1), (0, 3.6, 3.0)); cam_key(RUN_T1, (0, -10.7, 3.05), (0, 3.6, 2.95)); cam_key(25.3, (0.6, -10.2, 2.6), (0.6, 3.6, 2.25))
cam_key(26.6 - E_, (0.6, -9.9, 2.5), (0.6, 3.6, 2.25), cut=True)
cam_key(26.6, (1.0, -12.4, 2.3), (1.0, -0.5, 1.9)); cam_key(DUR, (1.0, -11.3, 2.2), (1.0, -0.5, 1.9))

HUD_Z = -6.0
BL = "#FFFFFF"
SLOGANS = [  # (texte, x, y, taille, couleur, alignement, début, fin)
    ("ITHOME PRÉSENTE", 0, 1.12, 0.13, "#9CC7E0", "CENTER", 0.55, 2.85),
    ("L'événement de l'année", 0, -1.08, 0.3, BL, "CENTER", 1.2, 2.85),
    ("Sherlock", 0.55, 0.3, 0.52, BL, "LEFT", 3.7, 5.85), ("Le compagnon IA d'ITHome", 0.58, -0.22, 0.2, "#9CC7E0", "LEFT", 4.1, 5.85),
    ("Curieux de tout.", 0, -1.1, 0.3, BL, "CENTER", 6.1, 8.3),
    ("Il fouille vos journaux.", -0.3, -1.2, 0.3, BL, "LEFT", 9.4, 11.9), ("Et trouve l'erreur.", -0.3, -1.2, 0.3, "#A8DDB5", "LEFT", 12.1, 13.45),
    ("Il connaît toute la documentation.", -0.3, -1.2, 0.3, BL, "LEFT", 14.1, 16.65), ("Et vous sort la bonne page.", -0.3, -1.2, 0.3, "#A8DDB5", "LEFT", 16.9, 18.45),
    ("Vous demandez.", -0.3, -1.2, 0.3, BL, "LEFT", 19.1, 20.3), ("Il répond.", -0.3, -1.2, 0.3, "#A8DDB5", "LEFT", 20.5, 22.85),
    ("Partout dans ITHome.", -0.6, -1.3, 0.32, BL, "CENTER", 23.5, 26.45),
    ("Sherlock", 0.5, 0.36, 0.56, BL, "LEFT", 26.9, 99), ("Le compagnon IA d'ITHome", 0.53, -0.2, 0.21, "#9CC7E0", "LEFT", 27.2, 99),
    ("OPAC SAVOIE", 0.54, -0.62, 0.17, "#A8DDB5", "LEFT", 27.5, 99)]
for i_, (s_, x, y, size, col, al, t0, t1) in enumerate(SLOGANS):
    ob = text_obj("Slogan.%d" % i_, s_, size, col, cam, (x, y, HUD_Z), al, True, upright=False)
    kscale(ob, [(0, 0.0), (t0 - E_, 0.0), (t0 + 0.14, 1.07), (t0 + 0.24, 1.0), (t1, 1.0), (t1 + 0.1, 0.0)])

# ------------------------------------------------------------------ interpolations demandées (coupes franches, mouvements linéaires)
for ob, path, frame, it in INTERP:
    a_ = ob.animation_data.action if ob.animation_data else None
    for a2 in ([a_] if a_ else []) + ([base] if ob is arm else []):
        for fc in fcurves_of(a2):
            if fc.data_path != path: continue
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.5: kp.interpolation = it

# ------------------------------------------------------------------ rendu
sc.frame_start, sc.frame_end = 1, NF
sc.render.fps = FPS_F
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0
sc.eevee.taa_render_samples = 8
try: sc.eevee.use_raytracing = False
except Exception: pass


def _image_out(fmt="JPEG"):
    try: sc.render.image_settings.media_type = 'IMAGE'
    except Exception: pass
    sc.render.image_settings.file_format = fmt
    sc.render.image_settings.color_mode = 'RGB'
    if fmt == "JPEG": sc.render.image_settings.quality = 95


def film_still(t, path, scale=25):
    _image_out("PNG"); sc.render.resolution_percentage = scale
    sc.frame_set(fr(t)); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.resolution_percentage = 100


def film_frame_path(f): return os.path.join(FILM_DIR, "f_%04d.jpg" % f)


def film_tick(n=5):
    """Rend les n prochaines images manquantes ; renvoie le délai avant le prochain appel (None quand tout est fait)."""
    todo = [f for f in range(1, NF + 1) if not os.path.exists(film_frame_path(f))][:n]
    if not todo:
        open(os.path.join(SCR, "FILM_DONE.txt"), "w").write("ok")
        return None
    _image_out("JPEG"); sc.render.resolution_percentage = 100
    for f in todo:
        sc.frame_set(f); sc.render.filepath = film_frame_path(f)
        bpy.ops.render.render(write_still=True)
    open(os.path.join(SCR, "FILM_PROGRESS.txt"), "w").write("%d/%d" % (todo[-1], NF))
    return 0.05


def film_encode(dst):
    ms = bpy.data.scenes.new("Montage")
    se = ms.sequence_editor_create()
    st = se.strips.new_image("film", film_frame_path(1), 1, 1)
    for f in range(2, NF + 1): st.elements.append(os.path.basename(film_frame_path(f)))
    ms.frame_start, ms.frame_end = 1, NF
    r = ms.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1920, 1080, 100, FPS_F
    r.use_sequencer = True
    try: r.image_settings.media_type = 'VIDEO'
    except Exception: pass
    r.image_settings.file_format = 'FFMPEG'
    ff = r.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 30; ff.audio_codec = 'NONE'
    ms.view_settings.view_transform = 'Standard'
    r.filepath = dst
    bpy.ops.render.render(animation=True, scene="Montage")
    bpy.data.scenes.remove(ms)


sc.frame_set(1)
result = {"images": NF, "objets": len(bpy.data.objects)}


def film_encode_music(dst, music, fade_from=28.0, fade_to=30.0):
    """Assemble les images en MP4 60 i/s avec la musique, fondue de fade_from à fade_to (secondes)."""
    ms = bpy.data.scenes.new("Montage")
    se = ms.sequence_editor_create()
    st = se.strips.new_image("film", film_frame_path(1), 1, 1)
    for f in range(2, NF + 1): st.elements.append(os.path.basename(film_frame_path(f)))
    snd = se.strips.new_sound("musique", music, 2, 1)
    ms.frame_start, ms.frame_end = 1, NF
    r = ms.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1920, 1080, 100, FPS_F
    for t, v in ((0.0, 1.0), (fade_from, 1.0), (fade_to, 0.0)):
        snd.volume = v; snd.keyframe_insert("volume", frame=1 + int(round(t * FPS_F)))
    r.use_sequencer = True
    try: r.image_settings.media_type = 'VIDEO'
    except Exception: pass
    r.image_settings.file_format = 'FFMPEG'
    ff = r.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 30
    ff.audio_codec = 'AAC'; ff.audio_bitrate = 192; ff.audio_mixrate = 48000; ff.audio_channels = 'STEREO'
    ms.view_settings.view_transform = 'Standard'
    r.filepath = dst
    bpy.ops.render.render(animation=True, scene="Montage")
    info = {"images": NF, "musique_s": round(snd.frame_duration / FPS_F, 2)}
    bpy.data.scenes.remove(ms)
    return info
