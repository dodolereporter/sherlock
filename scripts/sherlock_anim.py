# Sherlock - toutes les animations. Exécuté À LA SUITE de sherlock_build.py et sherlock_rig.py, dans le même espace de noms.
#
# Principe : chaque image clé est une POSE complète décrite en clair (cibles des mains dans l'espace, penché du corps,
# expression...). N = pose neutre = image 0 de « repos ». Une action ne reçoit de clés que sur les canaux qui s'écartent
# de la pose de liaison (T-pose) : les couches ne touchent donc qu'au visage, et aucune action ne touche eye_L / eye_R.
import json
from mathutils import Quaternion

P = arm.pose.bones
ad = arm.animation_data_create()
for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
ad.use_nla = False                                                      # sinon les pistes déjà créées faussent le calcul des bras
for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
FPS = 24
XA, YA, ZA = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
REST_Q = {b.name: b.matrix_local.to_quaternion() for b in arm_d.bones}
REST = {'loc': Vector((0, 0, 0)), 'quat': Quaternion((1, 0, 0, 0)), 'scale': Vector((1, 1, 1))}
PATH = {'loc': 'location', 'quat': 'rotation_quaternion', 'scale': 'scale'}
TAU = 2 * math.pi
BLINK = 0.07


def Rw(axis, deg): return Quaternion(axis, math.radians(deg))          # rotation autour d'un axe du monde


def wq(bone, q):                                                        # ... convertie dans le repère de l'os
    r = REST_Q[bone]; return r.inverted() @ q @ r


def wl(bone, v): return REST_Q[bone].inverted() @ Vector(v)             # déplacement du monde -> repère de l'os


def rest_all():
    for pb in P:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)


def mix(*frs):
    d = {}
    for f in frs: d.update(f)
    return d


# ------------------------------------------------------------------ bras : épaule -> coude -> bout de la main, donnés en coordonnées « bras gauche »
S0 = Vector((SHOULDER_X, ARM_Y, ARM_Z))
ARM_LEN_F = (Vector(A["forearm_L"][1]) - Vector(A["forearm_L"][0])).length
_arm_cache = {}


def arm_pose(side, E, T, Sh=None):
    """Bras à deux os : le haut du bras s'étire jusqu'au coude E (pâte à modeler), l'avant-bras vise le bout T."""
    key = (side, tuple(round(c, 4) for c in E), tuple(round(c, 4) for c in T), tuple(round(c, 4) for c in (Sh or S0)))
    if key in _arm_cache: return _arm_cache[key]
    sx = 1 if side == "L" else -1
    Sh, E, T = (Vector((v[0] * sx, v[1], v[2])) for v in (Sh or S0, E, T))
    rest_all(); vl.update()
    pa, pf = P["arm_" + side], P["forearm_" + side]
    m0 = pa.matrix.to_3x3()
    R = (m0.col[1].normalized().rotation_difference((E - Sh).normalized())).to_matrix() @ m0
    pa.matrix = Matrix.Translation(Sh) @ R.to_4x4(); vl.update()
    m1 = pf.matrix.to_3x3().normalized()
    d2 = T - E; s = d2.length / ARM_LEN_F
    R2 = (m1.col[1].normalized().rotation_difference(d2.normalized())).to_matrix() @ m1
    pf.matrix = Matrix.Translation(E) @ R2.to_4x4() @ Matrix.Diagonal((1, s, 1, 1)); vl.update()
    out = {("arm_" + side, 'loc'): pa.location.copy(), ("arm_" + side, 'quat'): pa.rotation_quaternion.copy(),
           ("forearm_" + side, 'loc'): pf.location.copy(), ("forearm_" + side, 'quat'): pf.rotation_quaternion.copy(),
           ("forearm_" + side, 'scale'): pf.scale.copy()}
    rest_all()
    _arm_cache[key] = out
    return out


def shift(a, dT=(0, 0, 0), dE=(0, 0, 0), dS=(0, 0, 0)):
    d = {"E": Vector(a["E"]) + Vector(dE), "T": Vector(a["T"]) + Vector(dT)}
    if "Sh" in a or any(dS): d["Sh"] = Vector(a.get("Sh", S0)) + Vector(dS)
    return d


DN = Vector((0.682, 0, -0.731))                                          # bras baissés, 47° sous l'horizontale
A_DOWN = dict(E=S0 + DN * 0.28, T=S0 + DN * 0.603)
A_WAVE = dict(E=(1.02, 0.08, 1.55), T=(1.18, 0.0, 1.93))                 # main levée (coucou)
A_UP = dict(E=(1.0, 0.1, 1.68), T=(1.12, 0.05, 2.08))                    # bras en l'air (joie)
A_TALK = dict(E=(1.0, -0.25, 1.22), T=(1.2, -0.5, 1.45))                 # geste d'explication
A_POINT = dict(E=(1.0, -0.3, 1.45), T=(1.08, -0.42, 1.88))               # doigt levé
A_CHIN = dict(Sh=(0.55, -0.4, 1.2), E=(0.45, -0.92, 1.38), T=(0.2, -0.8, 1.68))       # main au menton
A_LOUPE = dict(Sh=(0.6, -0.3, 1.2), E=(0.86, -0.85, 1.22), T=(0.74, -1.13, 1.56))      # tient la loupe
A_CHEEK = dict(Sh=(0.62, -0.15, 1.22), E=(0.86, -0.62, 1.42), T=(0.6, -0.66, 1.78))   # main près de la joue
A_CLASP = dict(Sh=(0.6, -0.3, 1.18), E=(0.5, -0.95, 1.1), T=(0.1, -1.05, 1.06))       # mains jointes
A_CROSS_L = dict(Sh=(0.6, -0.3, 1.15), E=(0.5, -0.98, 1.0), T=(0.05, -1.07, 0.98))    # bras croisés
A_CROSS_R = dict(Sh=(0.6, -0.3, 1.2), E=(0.5, -0.96, 1.12), T=(0.05, -1.08, 1.14))
A_BEHIND = dict(E=(1.02, 0.3, 1.68), T=(0.9, 0.42, 2.08))                # main derrière la tête
A_SPREAD = dict(E=(0.92, 0.16, 1.32), T=(1.22, 0.16, 1.46))              # bras écartés
A_KNOT = dict(Sh=(0.62, -0.2, 1.2), E=(0.85, -0.7, 1.15), T=(0.5, -0.9, 1.38))        # main au nœud de l'écharpe
A_STRETCH = dict(E=(1.0, 0.1, 1.72), T=(1.06, 0.05, 2.14))               # bras étiré vers le haut
A_BACK = dict(E=(0.86, 0.3, 1.08), T=(1.0, 0.42, 0.84))                  # bras en arrière (équilibre)


# ------------------------------------------------------------------ fragments de pose
def F_body(lean=0, side=0, turn=0, w=1.0, h=1.0, up=0.0):
    """lean > 0 : penché en avant ; side > 0 : vers sa gauche ; turn > 0 : tourné vers sa gauche ; w, h : largeur, hauteur."""
    return {("body", 'quat'): wq("body", Rw(ZA, turn) @ Rw(YA, side) @ Rw(XA, lean)), ("body", 'scale'): Vector((w, h, w)),
            ("root", 'loc'): wl("root", (0, 0, up))}


def F_head(nod=0, tilt=0, turn=0):
    return {("head", 'quat'): wq("head", Rw(ZA, turn) @ Rw(YA, tilt) @ Rw(XA, nod))}


def F_flaps(swing=0, out=0):
    return {("hat_flap_L", 'quat'): wq("hat_flap_L", Rw(XA, swing) @ Rw(YA, -out)),
            ("hat_flap_R", 'quat'): wq("hat_flap_R", Rw(XA, swing) @ Rw(YA, out))}


def F_legs(l=0, r=0):
    """Angle > 0 : pied vers l'avant."""
    return {("leg_L", 'quat'): wq("leg_L", Rw(XA, -l)), ("leg_R", 'quat'): wq("leg_R", Rw(XA, -r))}


def sway(ph, amp=1.0):
    """Balancement des deux bouts d'écharpe (périodique en ph)."""
    w = TAU * ph
    return {("scarf_end_1", 'quat'): wq("scarf_end_1", Rw(YA, 4 * amp * math.sin(w)) @ Rw(XA, 2 * amp * math.sin(w + 1.5))),
            ("scarf_end_1_tip", 'quat'): wq("scarf_end_1_tip", Rw(YA, 6 * amp * math.sin(w - 0.8))),
            ("scarf_end_2", 'quat'): wq("scarf_end_2", Rw(YA, 4 * amp * math.sin(w + 0.9)) @ Rw(XA, 2 * amp * math.sin(w + 2.4))),
            ("scarf_end_2_tip", 'quat'): wq("scarf_end_2_tip", Rw(YA, 6 * amp * math.sin(w + 0.1)))}


def F_eyes(h=1.0, w=1.0, slant=0.0, closed=None):
    """h, w : hauteur et largeur de l'oeil ; slant : yeux en biais (inquiet) ; closed : 'happy' (arcs ∩) ou 'sleep' (arcs ∪)."""
    d = {}
    for s, sg in (("L", 1), ("R", -1)):
        if closed:
            d[("eyelid_" + s, 'scale')] = Vector((0.02, 0.02, 0.02))
            d[("eye_happy_" + s, 'loc')] = Vector((0, HAPPY_DEPTH, 0))
            if closed == 'sleep': d[("eye_happy_" + s, 'quat')] = Quaternion((0, 1, 0), math.pi)
        else:
            d[("eyelid_" + s, 'scale')] = Vector((w, 1, h))
            d[("eyelid_" + s, 'loc')] = Vector((0, 0.03 * max(0.0, 1 - h), 0))      # ressort un peu quand il s'écrase
            d[("eyelid_" + s, 'quat')] = Quaternion((0, 1, 0), math.radians(slant * sg))
    return d


MOUTH_SHAPES = {"A": (0.9, 0.9), "E": (1.0, 0.45), "O": (0.5, 0.62), "A2": (0.8, 0.8), "E2": (0.9, 0.28),
                "happy": (1.05, 0.85), "o": (0.45, 0.55), "yawn": (0.8, 1.25)}


def F_mouth(kind):
    if kind == "pensive": return {("mouth", 'scale'): Vector((0.5, 1, 0.3)), ("mouth", 'loc'): wl("mouth", (0.07, 0, 0))}
    if kind == "frown": return {("mouth", 'scale'): Vector((0.8, 1, -0.7))}
    if kind == "gene": return {("mouth", 'scale'): Vector((0.75, 1, 0.7)), ("mouth", 'quat'): Quaternion((0, 1, 0), math.radians(10))}
    if kind == "small": return {("mouth", 'scale'): Vector((0.75, 1, 0.8))}
    w, h = kind if isinstance(kind, tuple) else MOUTH_SHAPES[kind]        # bouche ouverte (forme nommée ou libre) : le sourire se replie, le fond sombre sort
    return {("mouth", 'scale'): Vector((0.02, 0.02, 0.02)), ("mouth_open", 'loc'): Vector((0, MO_DEPTH, 0)),
            ("mouth_open", 'scale'): Vector((w, 1, h))}


def F_prop(name, s, off=(0, 0, 0)):
    return {(name, 'scale'): Vector((s, s, s)), (name, 'loc'): wl(name, off)}


PROPS0 = mix(*[F_prop(n_, 0.0) for n_ in PROPS])                          # tous les accessoires cachés


def pose(L=None, R=None, lean=0, side=0, turn=0, w=1.0, h=1.0, up=0.0, nod=0, tilt=0, hturn=0, eyes=None, mouth=None,
         props=None, flap=0, flap_out=0, legs=None, sc=0.0, sc_amp=1.0):
    """Pose complète du corps. L, R : cibles des bras (coordonnées bras gauche) ; le reste : voir les fragments."""
    fr = [PROPS0, arm_pose("L", **(L or A_DOWN)), arm_pose("R", **(R or A_DOWN)), F_body(lean, side, turn, w, h, up),
          F_head(nod, tilt, hturn), F_flaps(flap, flap_out), sway(sc, sc_amp)]
    if legs: fr.append(F_legs(*legs))
    if eyes: fr.append(F_eyes(**eyes))
    if mouth: fr.append(F_mouth(mouth))
    for k_, v_ in (props or {}).items(): fr.append(F_prop(k_, *v_) if isinstance(v_, tuple) else F_prop(k_, v_))
    return mix(*fr)


# ------------------------------------------------------------------ fabrication des actions
META = {}        # nom -> {famille, type, cible, duree}


def _differs(ch, v):
    r = REST[ch]
    if ch == 'quat': return 1 - abs(r.dot(v)) > 1e-9
    return (Vector(v) - r).length > 1e-7


def fcurves_of(act):
    try:
        if len(act.fcurves): return list(act.fcurves)
    except Exception:
        pass
    return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]


def make_action(name, keys, cyclic, famille, typ, cible=None):
    """keys : [(image, pose)]. Seuls les canaux qui s'écartent de la pose de liaison dans au moins une clé sont créés."""
    chans = {c for _f, p_ in keys for c, v in p_.items() if _differs(c[1], v)}
    if not typ.startswith("couche"): chans |= {(n_, "scale") for n_ in PROPS}      # accessoires toujours explicites (0 = caché, 1 = montré)
    chans = sorted(chans)
    act = bpy.data.actions.new(name); ad.action = act
    lastq = {}
    for f, p_ in keys:
        for (b, ch) in chans:
            v = p_.get((b, ch), REST[ch]).copy()
            if ch == 'quat':
                if b in lastq and lastq[b].dot(v) < 0: v.negate()
                lastq[b] = v
            setattr(P[b], PATH[ch], v)
            P[b].keyframe_insert(PATH[ch], frame=f)
    for fc in fcurves_of(act):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        if cyclic: fc.modifiers.new('CYCLES')
        fc.update()
    act.use_frame_range = True
    act.frame_start, act.frame_end = keys[0][0], keys[-1][0]
    tr = ad.nla_tracks.new(); tr.name = name
    tr.strips.new(name, 1, act)
    ad.action = None
    rest_all()
    META[name] = {"famille": famille, "type": typ, "cible": cible, "duree": round((keys[-1][0] - keys[0][0]) / FPS, 3),
                  "os": sorted({b for b, _c in chans})}
    return act


def loop(name, fn, seconds, famille, typ="boucle", step=3):
    n = int(round(seconds * FPS))
    keys = [(1 + f, fn(f / n)) for f in range(0, n, step)] + [(1 + n, fn(0.0))]
    return make_action(name, keys, True, famille, typ)


def shot(name, tl, famille, typ="ponctuelle", cible=None):
    return make_action(name, [(1 + int(round(t * FPS)), p_) for t, p_ in tl], False, famille, typ, cible)


def cosw(ph, k=1): return math.cos(TAU * k * ph)


def sinw(ph, k=1): return math.sin(TAU * k * ph)


def hump(ph, k=1): return 0.5 - 0.5 * math.cos(TAU * k * ph)          # 0 -> 1 -> 0, vitesse nulle aux extrémités


def breath(b, amp=1.0): return dict(w=1 - 0.014 * b * amp, h=1 + 0.03 * b * amp)


# ================================================================== BOUCLES D'ÉTAT
def repos_fn(ph):
    b = hump(ph)
    return pose(nod=-1.2 * b, flap=2.5 * b, sc=ph, **breath(b))


N = repos_fn(0.0)                                                        # pose neutre = image 0 de « repos »
loop("repos", repos_fn, 3.0, "boucles")


def reflechit_fn(ph):
    b, tap = hump(ph), hump(ph, 2)                                       # deux petits tapotements par boucle
    return pose(R=shift(A_CHIN, dT=(0.03 * tap, -0.07 * tap, -0.03 * tap)), lean=-2, nod=-5, tilt=-5 + 1.5 * cosw(ph), hturn=5,
                mouth="pensive", flap=2 * b, sc=ph, sc_amp=0.6, **breath(b))


loop("reflechit", reflechit_fn, 2.0, "boucles")


def enquete_fn(ph):
    b, sw = hump(ph), cosw(ph)
    dx = 0.14 * sw                                                        # la loupe balaie devant l'oeil
    return pose(R=shift(A_LOUPE, dT=(-dx, 0, 0.02 * sinw(ph)), dE=(-0.5 * dx, 0, 0)), L=A_BACK, lean=11, turn=2.5 * sw, nod=3, hturn=4 * sw,
                mouth="o", props={"prop_loupe": (1.0, (dx, 0, 0.02 * sinw(ph)))}, flap=2 * b, sc=ph, sc_amp=0.8, **breath(b))


loop("enquete", enquete_fn, 2.0, "boucles")


def parle_fn(ph):
    b, c1, g = hump(ph), cosw(ph), hump(ph, 2)
    return pose(L=shift(A_TALK, dT=(0.06 * c1, -0.05 * g, 0.10 * g), dE=(0.02 * c1, 0, 0.03 * g)), turn=1.5 * c1, nod=2.5 * g, hturn=3 * c1,
                flap=2 * b, sc=ph, sc_amp=0.7, **breath(b))


loop("parle", parle_fn, 2.0, "boucles")


def inquiet_fn(ph):
    b, c, s_ = hump(ph), cosw(ph), sinw(ph)
    wr = 0.02 * cosw(ph, 2)                                              # les mains se tordent un peu
    return pose(L=shift(A_CLASP, dT=(0, 0, wr)), R=shift(A_CLASP, dT=(0, 0, -wr)), side=2.5 * c, nod=3, tilt=-2 * c, hturn=6 * s_,
                eyes=dict(slant=17, h=0.94), mouth="frown", flap=2 * b, sc=ph, sc_amp=0.8, **breath(b))


loop("inquiet", inquiet_fn, 2.0, "boucles")


def z_env(u):
    """Apparition, tenue puis disparition d'un « z » sur un cycle (nul au début et à la fin : le retour est invisible)."""
    if u < 0.05 or u > 0.85: return 0.0
    if u < 0.25: return smooth(0.05, 0.25, u)
    if u < 0.6: return 1.0
    return 1 - smooth(0.6, 0.85, u)


def dort_fn(ph):
    b = hump(ph)                                                          # une respiration lente et profonde
    zs = {}
    for i, n_ in enumerate(("prop_z", "prop_z_2", "prop_z_3")):
        u = (ph + i / 3.0) % 1.0
        g_ = (u - 0.05) / 0.8 if 0.05 <= u <= 0.85 else 1 - smooth(0.0, 1.0, ((u - 0.85) % 1.0) / 0.2)   # montée, puis retour caché
        zs[n_] = (z_env(u), (-0.14 * g_, 0, 0.5 * g_))
    return pose(L=A_CROSS_L, R=A_CROSS_R, lean=3, nod=9 - 2 * b, tilt=5, eyes=dict(closed="sleep"), mouth="small", props=zs,
                flap=3 * b, sc=0.0, sc_amp=0.0, **breath(b, 1.6))


loop("dort", dort_fn, 4.0, "boucles")


A_FLAIL_HI = dict(E=(1.0, 0.0, 1.6), T=(1.2, -0.1, 2.0))                 # panique : bras en haut...
A_FLAIL_LO = dict(E=(0.95, -0.05, 1.22), T=(1.3, -0.15, 1.14))           # ... et en bas


def flail(u, c):
    """Bras en moulinet : u de 0 (bas) à 1 (haut), c de -1 à 1 (arrière, avant)."""
    return dict(E=Vector(A_FLAIL_LO["E"]).lerp(Vector(A_FLAIL_HI["E"]), u) + Vector((0, -0.08 * c, 0)),
                T=Vector(A_FLAIL_LO["T"]).lerp(Vector(A_FLAIL_HI["T"]), u) + Vector((0, -0.24 * c, 0)))


def souleve_fn(ph):
    """Soulevé par la souris : il panique, les bras moulinent et les pieds pédalent dans le vide (deux battements par boucle)."""
    s1, c1, s2, c2 = sinw(ph), cosw(ph), sinw(ph, 2), cosw(ph, 2)
    return pose(L=flail(0.5 + 0.5 * s2, c2), R=flail(0.5 - 0.5 * s2, -c2), side=3.5 * s1, turn=3 * c1, w=0.975 + 0.012 * c2, h=1.045 - 0.018 * c2,
                nod=-4 + 2 * c2, tilt=3.5 * s2, hturn=9 * s1, eyes=dict(h=1.24, w=1.16, slant=13), mouth=(1.15, 1.3 + 0.14 * c2), flap=7 * c2, flap_out=13,
                legs=(42 * s2, -42 * s2), sc=2 * ph, sc_amp=2.6)


loop("souleve", souleve_fn, 1.0, "boucles", step=2)

# ================================================================== ENTRÉES ET SORTIES
R0, E0, P0, I0, D0, SO0 = reflechit_fn(0), enquete_fn(0), parle_fn(0), inquiet_fn(0), dort_fn(0), souleve_fn(0)

shot("reflechit_entree", [(0, N), (0.15, pose(R=shift(A_DOWN, dT=(0.03, -0.05, -0.02)), nod=2)), (0.5, R0)], "entrees_sorties", "entree", "reflechit")
shot("reflechit_sortie", [(0, R0), (0.45, N)], "entrees_sorties", "sortie", "reflechit")

shot("enquete_entree", [(0, N), (0.15, pose(lean=-2, w=1.02, h=0.98)),
                        (0.42, mix(E0, F_prop("prop_loupe", 1.18, (0.14, 0, 0)))), (0.6, E0)], "entrees_sorties", "entree", "enquete")
shot("enquete_sortie", [(0, E0), (0.3, pose(R=shift(A_LOUPE, dT=(0.1, 0.25, -0.35), dE=(0.05, 0.2, -0.1)), lean=4)), (0.5, N)],
     "entrees_sorties", "sortie", "enquete")

shot("parle_entree", [(0, N), (0.3, P0)], "entrees_sorties", "entree", "parle")
shot("parle_sortie", [(0, P0), (0.3, N)], "entrees_sorties", "sortie", "parle")

shot("inquiet_entree", [(0, N), (0.18, pose(w=0.99, h=1.02, nod=-2, eyes=dict(slant=6), L=shift(A_DOWN, dT=(0, -0.1, 0.05)), R=shift(A_DOWN, dT=(0, -0.1, 0.05)))),
                        (0.5, I0)], "entrees_sorties", "entree", "inquiet")
shot("inquiet_sortie", [(0, I0), (0.45, N)], "entrees_sorties", "sortie", "inquiet")

shot("dort_entree", [(0, N), (0.3, pose(nod=5, tilt=2, eyes=dict(h=0.45), L=shift(A_DOWN, dT=(-0.1, -0.15, 0.03)), R=shift(A_DOWN, dT=(-0.1, -0.15, 0.03)))),
                     (0.55, pose(L=A_CROSS_L, R=A_CROSS_R, nod=10, tilt=4, lean=2, eyes=dict(closed="sleep"), mouth="small", sc_amp=0.0)),
                     (0.8, D0)], "entrees_sorties", "entree", "dort")
shot("dort_sortie", [(0, D0),
                     (0.14, pose(L=shift(A_CROSS_L, dT=(0.2, 0, 0.05)), R=shift(A_CROSS_R, dT=(0.2, 0, 0.05)), w=0.98, h=1.035, nod=-3,
                                 eyes=dict(h=1.1, w=1.1), flap=-4, flap_out=5)),
                     (0.4, pose(L=shift(A_SPREAD, dT=(-0.05, 0, 0.05)), R=shift(A_SPREAD, dT=(-0.05, 0, -0.1)), w=0.985, h=1.025, nod=-4)),
                     (0.7, N)], "entrees_sorties", "sortie", "dort")

shot("souleve_entree", [(0, N), (0.08, pose(w=1.05, h=0.95, eyes=dict(h=1.1, w=1.1))),
                        (0.17, pose(L=flail(0.9, 0), R=flail(0.9, 0), w=0.96, h=1.07, nod=-6, eyes=dict(h=1.25, w=1.18, slant=8), mouth="o", flap=-6, flap_out=10, legs=(-14, -14))),
                        (0.3, SO0)], "entrees_sorties", "entree", "souleve")
shot("atterrit", [(0, SO0), (0.1, pose(w=1.08, h=0.9, nod=3, flap=5, flap_out=4, L=shift(A_DOWN, dT=(0.06, 0, 0.04)), R=shift(A_DOWN, dT=(0.06, 0, 0.04)))),
                  (0.26, pose(w=0.985, h=1.025, nod=-1, flap=-2)), (0.5, N)], "entrees_sorties", "sortie", "souleve")

# ================================================================== RÉACTIONS PONCTUELLES (N -> N)
HAPPY = dict(closed="happy")
W_OUT, W_IN = shift(A_WAVE, dT=(0.14, 0, -0.05)), shift(A_WAVE, dT=(-0.12, 0, 0.02))
shot("salut", [(0, N),
               (0.1, pose(w=1.025, h=0.975, L=shift(A_DOWN, dT=(0.05, 0, 0.05)))),
               (0.28, pose(L=A_WAVE, w=0.985, h=1.03, up=0.04, eyes=HAPPY, mouth="happy", nod=-3, tilt=3, flap=-4)),
               (0.42, pose(L=W_OUT, eyes=HAPPY, mouth="happy", nod=-2, tilt=4, flap=3)),
               (0.58, pose(L=W_IN, eyes=HAPPY, mouth="happy", nod=-2, tilt=2)),
               (0.74, pose(L=W_OUT, eyes=HAPPY, mouth="happy", nod=-2, tilt=4)),
               (0.90, pose(L=W_IN, eyes=HAPPY, mouth="happy", nod=-2, tilt=2)),
               (1.08, pose(L=A_WAVE, eyes=HAPPY, mouth="happy", nod=-1, tilt=1)),
               (1.30, pose(L=shift(A_DOWN, dT=(0.08, 0, 0.1)), w=1.01, h=0.99)),
               (1.5, N)], "reactions")

shot("reussite", [(0, N),
                  (0.12, pose(w=1.05, h=0.94, L=shift(A_DOWN, dT=(0, 0.05, -0.02)), R=shift(A_DOWN, dT=(0, 0.05, -0.02)))),
                  (0.32, pose(L=A_UP, R=A_UP, w=0.96, h=1.06, up=0.22, eyes=HAPPY, mouth="happy", nod=-4, flap=-6, flap_out=6, sc_amp=2.0)),
                  (0.45, pose(L=A_UP, R=A_UP, w=0.98, h=1.03, up=0.1, eyes=HAPPY, mouth="happy", nod=-3, flap_out=3, props={"prop_coche": 1.2})),
                  (0.56, pose(L=A_UP, R=A_UP, w=1.06, h=0.93, eyes=HAPPY, mouth="happy", flap=5, props={"prop_coche": 1.0})),
                  (0.74, pose(L=A_UP, R=A_UP, w=0.985, h=1.025, eyes=HAPPY, mouth="happy", nod=-2, props={"prop_coche": 1.0})),
                  (1.05, pose(L=shift(A_UP, dT=(0.03, 0, -0.06)), R=shift(A_UP, dT=(0.03, 0, -0.06)), eyes=HAPPY, mouth="happy", props={"prop_coche": 1.0})),
                  (1.28, pose(L=shift(A_DOWN, dT=(0.1, 0, 0.15)), R=shift(A_DOWN, dT=(0.1, 0, 0.15)), props={"prop_coche": 0.0})),
                  (1.5, N)], "reactions")

WIDE = dict(h=1.14, w=1.14)
shot("alerte", [(0, N),
                (0.1, pose(L=A_CHEEK, R=A_CHEEK, w=0.97, h=1.05, up=0.07, eyes=WIDE, mouth="o", nod=-3, flap=-5, flap_out=8, sc_amp=2.0)),
                (0.2, pose(L=A_CHEEK, R=A_CHEEK, w=1.0, h=1.0, eyes=WIDE, mouth="o", nod=-2, flap_out=5, props={"prop_exclamation": 1.25})),
                (0.3, pose(L=A_CHEEK, R=A_CHEEK, w=1.025, h=0.975, eyes=WIDE, mouth="o", flap=3, props={"prop_exclamation": 1.0})),
                (0.5, pose(L=shift(A_CHEEK, dT=(0.01, 0, 0.01)), R=shift(A_CHEEK, dT=(-0.01, 0, 0.01)), eyes=WIDE, mouth="o", side=0.8, props={"prop_exclamation": 1.0})),
                (0.7, pose(L=shift(A_CHEEK, dT=(-0.01, 0, 0)), R=shift(A_CHEEK, dT=(0.01, 0, 0)), eyes=WIDE, mouth="o", side=-0.8, props={"prop_exclamation": 1.0})),
                (0.85, pose(L=A_CHEEK, R=A_CHEEK, eyes=dict(h=1.08, w=1.08), mouth="o", props={"prop_exclamation": 1.0})),
                (1.02, pose(L=shift(A_DOWN, dT=(0, -0.08, 0.12)), R=shift(A_DOWN, dT=(0, -0.08, 0.12)), props={"prop_exclamation": 0.0})),
                (1.2, N)], "reactions")

SORRY = dict(L=A_BEHIND, lean=8, nod=7, tilt=7, eyes=dict(h=0.55), mouth="gene")
shot("desole", [(0, N),
                (0.15, pose(nod=-2, w=1.01, h=0.99)),
                (0.5, pose(**SORRY)),
                (0.75, pose(**dict(SORRY, L=shift(A_BEHIND, dT=(0, 0.05, 0.05))))),
                (1.0, pose(**dict(SORRY, L=shift(A_BEHIND, dT=(0, -0.04, -0.04)), lean=9))),
                (1.25, pose(**dict(SORRY, L=shift(A_BEHIND, dT=(0, 0.05, 0.05))))),
                (1.5, pose(**dict(SORRY, lean=7))),
                (1.78, pose(L=shift(A_DOWN, dT=(0.08, 0.05, 0.12)), lean=2, nod=2, tilt=2, eyes=dict(h=0.85))),
                (2.0, N)], "reactions")

BRIGHT = dict(h=1.08, w=1.08)
shot("idee", [(0, N),
              (0.1, pose(w=1.025, h=0.975, nod=2)),
              (0.3, pose(L=A_POINT, w=0.985, h=1.03, eyes=BRIGHT, mouth="happy", nod=-3, flap=-4)),
              (0.4, pose(L=A_POINT, eyes=BRIGHT, mouth="happy", nod=-2, props={"prop_ampoule": 1.25})),
              (0.5, pose(L=A_POINT, eyes=BRIGHT, mouth="happy", nod=-2, flap=2, props={"prop_ampoule": 1.0})),
              (0.72, pose(L=shift(A_POINT, dT=(0, 0, 0.03)), eyes=BRIGHT, mouth="happy", nod=-2, props={"prop_ampoule": 1.1})),
              (0.92, pose(L=A_POINT, eyes=BRIGHT, mouth="happy", nod=-2, props={"prop_ampoule": 1.0})),
              (1.1, pose(L=A_POINT, eyes=BRIGHT, mouth="happy", nod=-1, props={"prop_ampoule": 1.0})),
              (1.3, pose(L=shift(A_DOWN, dT=(0.08, -0.05, 0.12)), props={"prop_ampoule": 0.0})),
              (1.5, N)], "reactions")

shot("ploc", [(0, N), (2 / 24, pose(w=1.1, h=0.87, flap=5, flap_out=4)), (4 / 24, pose(w=0.95, h=1.07, flap=-4)),
              (6 / 24, pose(w=1.02, h=0.985, flap=1)), (8 / 24, N)], "reactions")

shot("repos_variante_1", [(0, N),
                          (0.4, pose(hturn=17, tilt=2, turn=3)),
                          (0.65, pose(hturn=17, tilt=2, turn=3)),
                          (1.05, pose(hturn=-15, tilt=-2, turn=-3)),
                          (1.25, pose(hturn=-12, tilt=-2, turn=-2, L=shift(A_KNOT, dT=(0.1, 0.1, -0.15)))),
                          (1.5, pose(hturn=3, nod=5, L=A_KNOT)),
                          (1.7, pose(nod=6, L=shift(A_KNOT, dT=(-0.04, 0, 0.03)), sc=0.25, sc_amp=1.6)),
                          (1.9, pose(nod=5, L=shift(A_KNOT, dT=(0.03, 0, -0.02)), sc=0.75, sc_amp=1.6)),
                          (2.2, pose(nod=1, L=shift(A_DOWN, dT=(0.05, -0.1, 0.12)))),
                          (2.5, N)], "reactions")

YAWN = dict(R=A_STRETCH, w=0.975, h=1.045, nod=-8, tilt=-3, eyes=dict(h=0.3), mouth="yawn", flap=-5)
shot("repos_variante_2", [(0, N),
                          (0.3, pose(w=1.01, h=0.99, nod=2, eyes=dict(h=0.8))),
                          (0.85, pose(**YAWN)),
                          (1.3, pose(**dict(YAWN, R=shift(A_STRETCH, dT=(0.04, 0, 0.04)), nod=-9))),
                          (1.7, pose(R=shift(A_STRETCH, dT=(0.1, 0, -0.25), dE=(0, 0, -0.15)), w=1.01, h=0.99, nod=-2, eyes=dict(h=0.5), mouth="O")),
                          (2.1, pose(R=shift(A_DOWN, dT=(0.06, 0, 0.1)), nod=1, eyes=dict(h=0.9))),
                          (2.5, N)], "reactions")

# ================================================================== COUCHES (visage seul, par-dessus n'importe quel état)
shot("cligne", [(0, {}), (2 / 24, F_eyes(h=BLINK)), (3 / 24, F_eyes(h=BLINK)), (5 / 24, {})], "couches", "couche")
shot("yeux_fermes", [(0, {}), (2 / 24, F_eyes(h=BLINK)), (4 / 24, F_eyes(closed="happy")), (7 / 24, F_eyes(closed="happy"))], "couches", "couche_tenue")
make_action("bouche_parle", [(1, {}), (2, {}), (4, F_mouth("A")), (6, F_mouth("E")), (8, F_mouth("O")), (10, F_mouth("A2")), (12, {}), (13, {})],
            True, "couches", "couche_boucle")

ad.use_nla = True
sc.frame_start, sc.frame_end = 1, 73
sc.frame_set(1)
json.dump(META, open(os.path.join(OUTD, "animations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
result = {"actions": len(META), "bones": len(arm_d.bones), "noms": list(META)}
