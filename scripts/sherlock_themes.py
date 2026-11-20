# Sherlock - saisons et fêtes animées : un fichier .glb par thème.
#
# Exécuté deux fois dans le même espace de noms :
#   THEME_STAGE = "pre"   après sherlock_build.py : construit la tenue et les objets du thème, déclare leurs os ;
#   THEME_STAGE = "post"  après sherlock_rig.py et sherlock_anim.py : crée les deux animations du thème.
#
# Chaque fichier contient Sherlock avec sa tenue (portée en permanence), ses objets (un os « prop_* » chacun,
# échelle 0 = caché), les 30 animations de base et deux animations propres au thème :
#   theme_objet    il sort son objet, puis le range ;
#   theme_special  l'animation spéciale de la saison ou de la fête.
# Les deux partent de la pose neutre et y reviennent, comme les autres réactions.
#
# Un objet tenu est LIÉ À L'AVANT-BRAS : son point de prise reste au centre du poing et il tourne avec la main.

# thème : (saison de base, tenue de la fête, objets)
THEMES = {
    "printemps": ("printemps", [], ["tulipes", "papillon", "flaque", "gouttes"]),
    "ete": ("ete", [], ["glace", "bouee", "gouttes"]),
    "automne": ("automne", [], ["marron", "feuille", "feuille2", "feuille3"]),
    "hiver": ("hiver", [], ["neige", "boule"]),
    "nouvel_an": ("hiver", ["etoile"], ["coupe", "confettis_or", "confettis"]),
    "epiphanie": ("hiver", ["couronne"], ["galette", "feve"]),
    "chandeleur": ("hiver", ["toque"], ["poele", "crepe"]),
    "saint_valentin": ("hiver", ["coeur"], ["enveloppe", "coeur", "coeur2", "coeur3"]),
    "mardi_gras": ("hiver", ["plumes"], ["masque", "confettis"]),
    "paques": ("printemps", ["oreilles"], ["oeuf"]),
    "premier_mai": ("printemps", ["muguet_pin"], ["muguet"]),
    "musique": ("ete", ["note_pin"], ["guitare", "note", "note2"]),
    "quatorze_juillet": ("ete", ["cocarde"], ["drapeau", "feu1", "feu2", "feu3"]),
    "halloween": ("automne", ["sorciere"], ["citrouille"]),
    "noel": ("hiver", ["guirlande"], ["cadeau"]),
}
BASES = {"hiver": (True, []), "printemps": (False, ["botte_L", "botte_R"]), "ete": (False, ["lunettes"]), "automne": (False, ["gilet"])}
SAISON, TENUE, OBJETS = THEMES[THEME]

if THEME_STAGE == "pre":
    # tenues, objets et préréglages de bras : mêmes formes que les planches de validation (haut de sherlock_saisons.py)
    SAISONS_OUT, SAISONS_FILTRE = os.path.join(HERE, "..", "saisons", "images"), ""
    exec(compile(open(os.path.join(HERE, "sherlock_saisons.py"), encoding="utf-8").read().split("# ================================================================== RENDU")[0],
                 "sherlock_saisons.py", "exec"), globals())
    echarpe, base = BASES[SAISON]
    tenue = [n for n in base + TENUE if not ("sorciere" in TENUE and n == "lunettes")]
    garde = [T[n] for n in tenue] + [O_[n] for n in OBJETS]
    for ob in list(EXTRA):
        if ob not in garde: bpy.data.objects.remove(ob, do_unlink=True)
    EXTRA_PARTS = {}
    for n in tenue: EXTRA_PARTS[T[n].name] = T[n]["os"]                 # tenue : rigide sur la tête, le corps ou une jambe
    for n in OBJETS:
        PROPS["prop_" + n] = (Vector((0, -0.99, 2.06)), "head") if n == "masque" else (Vector((0, 0, 0)), "root")
        EXTRA_PARTS[O_[n].name] = "prop_" + n
    SKIP_PARTS = set()
    if not echarpe: SKIP_PARTS |= {"Echarpe", "Noeud", "Echarpe.Bout.1", "Echarpe.Bout.2"}
    if "sorciere" in TENUE: SKIP_PARTS |= {"Casquette", "Casquette.Bord", "Visiere", "Bouton", "Rabat.L", "Rabat.R"}
    TOP_REST = dome(15, 78, 0.06)[0]
    result = {"tenue": tenue, "objets": OBJETS, "retire": sorted(SKIP_PARTS)}

if THEME_STAGE == "post":
    SQ, ST = dict(w=1.04, h=0.95), dict(w=0.97, h=1.04)          # écrasé, étiré (mesurés)

    def env(t, a, b, d=0.16):
        """Apparition avec un petit rebond à l'instant a, disparition à l'instant b."""
        if t <= a or t >= b + d: return 0.0
        if t < a + d: u = (t - a) / d; return 1.1 * smooth(0.0, 0.7, u) if u < 0.7 else lerp(1.1, 1.0, (u - 0.7) / 0.3)
        if t > b: return 1 - (t - b) / d
        return 1.0

    def val(v, t): return v(t) if callable(v) else v

    def hands():
        """État des mains à l'image courante : centre du poing, direction et matrice de chaque avant-bras."""
        H = {}
        for sd in "LR":
            pb = P["forearm_" + sd]; d = (pb.tail - pb.head).normalized()
            H[sd] = pb.tail - d * HAND_IN; H["d" + sd] = d; H["M" + sd] = pb.matrix.copy()
        H["mid"] = (H["L"] + H["R"]) / 2
        for bn in ("head", "body"): H[bn] = P[bn].matrix @ arm_d.bones[bn].matrix_local.inverted()
        return H

    def at_pose(kw):
        """État des mains dans une pose donnée (pour fixer une prise)."""
        d = pose(**kw); rest_all()
        for (b_, ch), v in d.items(): setattr(P[b_], PATH[ch], v)
        vl.update(); H = hands(); rest_all(); vl.update()
        return H

    def held(side, rot, s, key, d=0.0, off=(0, 0, 0), at=(0, 0, 0), spin=None, a=0.22, b=2.48):
        """Objet tenu : dans la pose « key », son origine est au centre du poing (+ d le long de l'avant-bras, + off),
        orienté par rot ; ensuite il suit l'avant-bras comme une pièce rigide. at : décalage dans le repère de l'objet."""
        H0 = at_pose(key)
        M0 = TRS(H0[side] + H0["d" + side] * d + Vector(off), rot, 1) @ Matrix.Translation(Vector(at) * s)
        ML = H0["M" + side].inverted() @ M0

        def fn(t, H):
            M_ = H["M" + side] @ ML
            if spin: M_ = M_ @ TRS((0, 0, 0), spin(t), 1)
            return (M_, None, s * env(t, a, b))
        fn.local = ML
        return fn

    def rigid(side, key, a=0.22, b=2.48):
        """Objet modelé à sa place finale (le masque sur le visage) : dans la pose « key » il y est, et il suit la main."""
        ML = at_pose(key)["M" + side].inverted()
        return lambda t, H: (H["M" + side] @ ML, None, env(t, a, b))

    def carried(off, rot=(0, 0, 0), s=1.0, a=0.22, b=2.48):
        """Objet porté à deux mains : posé entre les deux poings."""
        return lambda t, H: (H["mid"] + Vector(val(off, t)), val(rot, t), s * env(t, a, b))

    def fixed(loc, rot=(0, 0, 0), s=1.0, a=0.22, b=2.48):
        return lambda t, H: (Vector(val(loc, t)), val(rot, t), s * env(t, a, b))

    def on_body(loc, rot=(0, 0, 0), s=1.0, a=0.22, b=2.48):
        """Objet plaqué contre le corps (guitare) : il suit le buste."""
        return lambda t, H: (H["body"] @ TRS(loc, rot, 1), None, s * env(t, a, b))

    def local(a, b): return lambda t, H: ("local", env(t, a, b))

    def burst(c0, rise, t0, life, s=1.0, spin=50.0):
        """Gerbe (confettis, éclaboussures) : jaillit de c0, monte puis retombe en s'effaçant."""
        def fn(t, H):
            u = (t - t0) / life
            if u <= 0 or u >= 1: return (Vector(c0), (0, 0, 0), 0.0)
            z = rise * (1 - (1 - min(1.0, u * 3.5)) ** 2) - 0.7 * rise * max(0.0, u - 0.3)
            return (Vector(c0) + Vector((0, 0, z)), (0, 0, spin * u), s * (0.12 + 0.98 * min(1.0, u * 5)) * (1 - smooth(0.7, 1.0, u)))
        return fn

    def floaty(side, t0, life, d=(0.6, -0.4, 1.6), s=1.0, off=(0.12, -0.1, 0.35)):
        """Petit objet qui s'envole de la main (cœurs, notes) en grossissant, puis s'efface."""
        def fn(t, H):
            u = (t - t0) / life; p0 = H[side] + Vector(off)
            if u <= 0 or u >= 1: return (p0, (0, 0, 0), 0.0)
            return (p0 + Vector(d) * u + Vector((0.12 * math.sin(7 * u), 0, 0)), (0, 14 * math.sin(6 * u), 0), s * (0.55 + 0.7 * u) * min(1.0, u * 7) * (1 - smooth(0.78, 1.0, u)))
        return fn

    def flash(loc, t0, s=1.0, life=0.95):
        def fn(t, H):
            u = (t - t0) / life
            if u <= 0 or u >= 1: return (Vector(loc), (0, 0, 0), 0.0)
            return (Vector(loc), (0, 20 * u, 0), s * (0.1 + 0.9 * min(1.0, u * 3.2)) * (1 - smooth(0.6, 1.0, u)))
        return fn

    def bake(act, tracks):
        """Clés image par image des os d'objets : ils suivent la main sans glisser ; os au repos en début et fin."""
        ad.use_nla = False; ad.action = act
        n = int(act.frame_end); lastq = {}
        for f in range(1, n + 1):
            sc.frame_set(f); vl.update()
            t = (f - 1) / 24.0
            H = hands()
            for bone, fn in tracks.items():
                pb = P[bone]; r = fn(t, H)
                if r[0] == "local" or f in (1, n):
                    s = r[1] if r[0] == "local" else 0.0
                    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
                else:
                    loc, rot, s = r
                    pb.matrix = (loc if isinstance(loc, Matrix) else TRS(loc, rot, 1)) @ arm_d.bones[bone].matrix_local
                    q = pb.rotation_quaternion.copy()
                    if bone in lastq and lastq[bone].dot(q) < 0: q.negate(); pb.rotation_quaternion = q
                    lastq[bone] = q
                if f in (1, 2, n - 1, n): s = 0.0
                pb.scale = (s, s, s)
                for path in ("location", "rotation_quaternion", "scale"): pb.keyframe_insert(path, frame=f)
        for fc in fcurves_of(act):
            if any('"%s"' % b_ in fc.data_path for b_ in tracks):
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        ad.action = None; rest_all()

    def clip(name, tl, tracks):
        bake(shot(name, tl, "theme"), tracks)

    def objet_tl(kw, dur=2.8, sway=2.0):
        """Il sort l'objet, le montre en se balançant un peu, le range."""
        B_, B2 = pose(**kw), pose(**dict(kw, side=kw.get("side", 0) + sway, up=kw.get("up", 0) + 0.03))
        return [(0, N), (0.12, pose(w=1.02, h=0.98)), (0.42, B_), (1.0, B2), (1.55, B_), (2.05, B2), (dur - 0.4, B_), (dur, N)]

    def k(t, pts):
        """Valeur interpolée linéairement dans une liste (instant, valeur)."""
        if t <= pts[0][0]: return pts[0][1]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                return tuple(lerp(a, b, u) for a, b in zip(v0, v1)) if isinstance(v0, tuple) else lerp(v0, v1, u)
        return pts[-1][1]

    # ------------------------------------------------------------------ saisons
    def a_printemps():
        papillon = fixed(lambda t: (-0.95 + 0.35 * math.sin(2.4 * t), -0.7, 3.4 + 0.18 * math.sin(5 * t)), lambda t: (0, 20 + 25 * math.sin(9 * t), 0), 1.3)
        kw = dict(L=A_SHOW, tilt=3)
        clip("theme_objet", objet_tl(kw), {"prop_tulipes": held("L", (-8, -4, 0), 1.15, kw), "prop_papillon": papillon})
        J = dict(L=shift(A_SPREAD, dT=(0, 0, 0.25)), R=shift(A_SPREAD, dT=(0, 0, 0.25)), eyes=HAPPY, mouth="A")
        tl = [(0, N), (0.25, pose(**SQ)), (0.5, pose(**J, up=0.42, legs=(14, 14), **ST)), (0.8, pose(**J, w=1.09, h=0.89, flap=8, flap_out=6)), (0.95, pose(**J, **ST)),
              (1.2, pose(**J, **SQ)), (1.45, pose(**J, up=0.42, legs=(14, 14), **ST)), (1.75, pose(**J, w=1.09, h=0.89, flap=8, flap_out=6)), (1.92, pose(**J, **ST)),
              (2.35, pose(eyes=HAPPY, mouth="happy")), (2.8, N)]

        def gouttes(t, H):
            for t0 in (1.75, 0.8):
                if t >= t0: return burst((0, -0.15, -0.25), 0.45, t0, 0.5, 1.0, 20)(t, H)
            return (Vector((0, -0.15, 0)), (0, 0, 0), 0.0)
        clip("theme_special", tl, {"prop_flaque": fixed((0, -0.15, 0.0), a=0.15, b=2.5), "prop_gouttes": gouttes})

    def a_ete():
        B_ = dict(L=A_LICK, eyes=HAPPY, mouth="A", tilt=7, hturn=8)
        tl = [(0, N), (0.4, pose(L=A_LICK)), (0.75, pose(**B_)), (1.0, pose(**dict(B_, nod=5, mouth="small"))), (1.3, pose(**B_)), (1.6, pose(**dict(B_, nod=5, mouth="small"))),
              (1.95, pose(**B_)), (2.4, pose(L=A_LICK, eyes=HAPPY)), (2.8, N)]
        clip("theme_objet", tl, {"prop_glace": held("L", (0, -8, 0), 1.35, B_)})
        Sx = dict(R=A_WAVE, legs=(72, 72), eyes=HAPPY, mouth="A", nod=-4)
        tl = [(0, N), (0.3, pose(**SQ)), (0.62, pose(L=A_UP, up=0.16, **Sx))]
        for i, t in enumerate((0.95, 1.28, 1.61, 1.94, 2.27)):
            tl.append((t, pose(L=shift(A_UP, dT=(0.1 * (-1) ** i, 0, -0.05 * (i % 2))), up=0.08 + 0.08 * (i % 2), side=2.5 * (-1) ** i, **Sx)))
        tl += [(2.6, pose(**SQ)), (2.95, N)]
        bob = lambda t: (0, 0, 0.9 + 0.06 * math.sin(TAU * (t - 0.62) / 0.66))
        clip("theme_special", tl, {"prop_bouee": fixed(bob, lambda t: (0, 3 * math.sin(TAU * t / 0.66), 0), a=0.4, b=2.5),
                                   "prop_gouttes": fixed((0, -0.1, 0.55), s=1.0, a=0.6, b=2.4)})

    def a_automne():
        kw = dict(R=A_LOUPE, L=A_LICK, lean=8, nod=4, mouth="o", props={"prop_loupe": 1.0})
        tl = [(0, N), (0.45, pose(**kw)), (1.0, pose(**dict(kw, lean=11, nod=6, R=shift(A_LOUPE, dT=(-0.08, 0, 0.0))))), (1.6, pose(**dict(kw, R=shift(A_LOUPE, dT=(0.06, 0, 0.03))))),
              (2.1, pose(**dict(kw, lean=11, nod=6))), (2.5, pose(**dict(kw, mouth="happy"))), (2.9, N)]
        clip("theme_objet", tl, {"prop_marron": held("L", (0, 0, 0), 1.35, kw, d=0.2, b=2.55)})
        S_ = dict(L=shift(A_SPREAD, dT=(-0.1, 0, -0.1)), R=shift(A_SPREAD, dT=(-0.1, 0, -0.1)), eyes=WIDE, mouth="o")
        tl = [(0, N), (0.7, pose(nod=-4)), (1.1, pose(nod=-5)), (1.2, pose(**S_, nod=-3, w=1.03, h=0.96)), (1.36, pose(**S_, nod=-5)), (1.85, pose(hturn=10, mouth="o")),
              (2.1, pose(hturn=-13)), (2.3, pose(hturn=13)), (2.5, pose(eyes=HAPPY, mouth="happy")), (3.0, N)]
        A0 = Vector((0.9, -0.2, 4.7))

        def feuille(t, H):
            top = H["head"] @ TOP_REST
            if t < 0.2: return (A0, (70, 10, 30), 0.0)
            if t < 1.14:
                u = (t - 0.2) / 0.94
                return (A0.lerp(top, u) + Vector((0.55 * math.sin(u * 9) * (1 - u), 0, 0)), (70, 10 + 45 * math.sin(u * 9) * (1 - u), 30), 1.4 * min(1.0, u * 6))
            if t < 2.12: return (top, (70, 10, 30), 1.4)
            u = min(1.0, (t - 2.12) / 0.6)
            return (top + Vector((1.0 * u, -0.3 * u, -3.0 * u * u)), (70 + 220 * u, 10, 30), 1.4 * (1 - smooth(0.7, 1.0, u)))

        def derive(x, t0, life, s):
            def fn(t, H):
                u = (t - t0) / life
                if u <= 0 or u >= 1: return (Vector((x, -0.4, 4.6)), (0, 0, 0), 0.0)
                return (Vector((x + 0.45 * math.sin(u * 8), -0.4, 4.6 - 4.4 * u)), (20 + 60 * math.sin(u * 8), 35, 200 * u), s * min(1.0, u * 8) * (1 - smooth(0.85, 1.0, u)))
            return fn
        clip("theme_special", tl, {"prop_feuille": feuille, "prop_feuille2": derive(1.55, 0.25, 2.3, 1.2), "prop_feuille3": derive(-1.5, 0.7, 2.1, 1.0)})

    def a_hiver():
        G = dict(L=A_GROUND, R=A_BACK, lean=30, nod=10, mouth="small")
        S_ = dict(L=A_SHOW, mouth="happy")
        cap = {}

        def neige(a, b):
            def fn(t, H):
                if "n" not in cap and t >= 0.45: cap["n"] = Vector((H["L"].x + 0.1, H["L"].y + 0.15, 0.0))
                return (cap.get("n", Vector((0.9, -1.2, 0))), (0, 0, 0), 1.2 * env(t, a, b))
            return fn

        def paume(H): return H["L"] + H["dL"] * 0.3                                 # la boule repose dans le creux de la main

        def boule_main(t, H):
            z = 0.9 * 4 * ((t - 1.95) / 0.6) * (1 - (t - 1.95) / 0.6) if 1.95 < t < 2.55 else 0.0     # il la fait sauter dans sa main
            return (paume(H) + Vector((0, 0, z)), (0, 0, 0), 0.9 * env(t, 0.8, 2.7))
        tl = [(0, N), (0.42, pose(**G)), (0.7, pose(**dict(G, L=shift(A_GROUND, dT=(-0.08, 0, 0.04))))), (1.0, pose(**G)), (1.45, pose(**S_)), (1.9, pose(**dict(S_, L=shift(A_SHOW, dT=(0, 0, -0.1))))),
              (2.05, pose(**dict(S_, L=shift(A_SHOW, dT=(0, 0, 0.1)), eyes=WIDE))), (2.55, pose(**S_)), (2.75, pose(**dict(S_, eyes=HAPPY))), (3.1, N)]
        clip("theme_objet", tl, {"prop_neige": neige(0.5, 1.6), "prop_boule": boule_main})
        cap.clear()
        W = dict(L=A_THROW, R=A_AIM, lean=-7, turn=12, mouth="happy", eyes=dict(h=0.9), legs=(10, -8))
        Rl = dict(L=A_RELEASE, R=A_BACK, lean=11, turn=-8, mouth="A", legs=(-12, 14))
        tl = [(0, N), (0.4, pose(**G)), (0.75, pose(**dict(G, L=shift(A_GROUND, dT=(-0.08, 0, 0.04))))), (1.0, pose(**G)), (1.3, pose(**W)), (1.52, pose(**dict(W, lean=-10))), (1.64, pose(**Rl)),
              (2.0, pose(**dict(Rl, lean=8))), (2.35, pose(eyes=HAPPY, mouth="happy")), (2.8, N)]

        def boule_lance(t, H):
            if t < 0.8: return (paume(H), (0, 0, 0), 0.0)
            if t < 1.62: return (paume(H), (0, 0, 0), 0.9 * min(1.0, (t - 0.8) * 6))
            if "r" not in cap: cap["r"] = paume(H)
            u = (t - 1.62) / 0.5                                 # part droit devant lui : le code oriente Sherlock vers la souris
            if u >= 1: return (cap["r"], (0, 0, 0), 0.0)
            return (cap["r"] + Vector((-0.12, -1.0, 0.06)) * 7.5 * u, (0, 0, 0), (0.9 + 0.8 * u) * (1 - smooth(0.75, 1.0, u)))
        clip("theme_special", tl, {"prop_neige": neige(0.45, 2.3), "prop_boule": boule_lance})

    # ------------------------------------------------------------------ fêtes
    def a_nouvel_an():
        kw = dict(L=A_SHOW)
        clip("theme_objet", objet_tl(kw), {"prop_coupe": held("L", (0, 0, 0), 1.5, kw)})
        Tt = dict(L=A_HIGH, R=A_SPREAD, eyes=HAPPY, mouth="happy", flap=-4)
        tl = [(0, N), (0.3, pose(L=A_SHOW)), (0.6, pose(**Tt, tilt=4, up=0.08, **ST)), (0.78, pose(**Tt, tilt=4, **SQ)), (0.95, pose(**Tt, tilt=4)), (1.6, pose(**Tt, tilt=-2)),
              (2.3, pose(**Tt, tilt=4)), (2.65, pose(L=A_SHOW)), (3.0, N)]
        clip("theme_special", tl, {"prop_coupe": held("L", (0, 14, 0), 1.5, dict(Tt, tilt=4), a=0.2, b=2.7),
                                   "prop_confettis_or": burst((0.1, -0.5, 2.9), 0.95, 0.6, 2.1), "prop_confettis": burst((0.0, -0.3, 2.8), 0.9, 0.72, 2.1, 1.1, -40)})

    def a_epiphanie():
        Cg = dict(L=PORTE["galette"][0], R=PORTE["galette"][0])
        clip("theme_objet", objet_tl(Cg), {"prop_galette": carried(*PORTE["galette"][1:])})
        F = dict(L=A_HIGH, R=A_SPREAD, eyes=WIDE, mouth="A", nod=-4)
        tl = [(0, N), (0.3, pose(L=A_FACE, mouth="small")), (0.55, pose(L=A_FACE, eyes=WIDE, mouth="o", **SQ)), (0.8, pose(**F, up=0.08, **ST)), (0.97, pose(**F, **SQ)), (1.15, pose(**F)),
              (1.7, pose(**dict(F, tilt=4, eyes=HAPPY))), (2.3, pose(**F)), (2.8, N)]
        clip("theme_special", tl, {"prop_feve": held("L", (0, 0, 0), 1.7, F, d=0.2, spin=lambda t: (0, 0, 150 * t), a=0.5, b=2.45)})

    def a_chandeleur():
        kw = dict(L=A_SHOW); R_ = (6, 0, 38)
        clip("theme_objet", objet_tl(kw), {"prop_poele": held("L", R_, 1.05, kw), "prop_crepe": held("L", R_, 1.05, kw, at=(0, -0.72, 0.012))})
        S_ = dict(L=A_SHOW)
        U = dict(L=shift(A_SHOW, dT=(0, 0, 0.2), dE=(0, 0, 0.1)), R=A_SPREAD, eyes=WIDE, mouth="o", nod=-9)
        tl = [(0, N), (0.35, pose(**S_)), (0.58, pose(L=shift(A_SHOW, dT=(0, 0, -0.14)), h=0.97, w=1.02)), (0.72, pose(**U, h=1.03, w=0.98)), (1.15, pose(**dict(U, nod=-11))), (1.5, pose(**dict(U, nod=-5))),
              (1.64, pose(L=shift(A_SHOW, dT=(0, 0, -0.1)), h=0.97, w=1.02, eyes=WIDE)), (1.85, pose(**S_, eyes=HAPPY, mouth="happy")), (2.5, pose(**S_, eyes=HAPPY, mouth="happy")), (2.9, N)]
        sur = held("L", R_, 1.05, kw, at=(0, -0.72, 0.012), a=0.22, b=2.6)

        def crepe(t, H):
            M_, _r, s = sur(t, H)
            if 0.7 <= t <= 1.6:                                  # elle saute, fait un tour complet et retombe dans la poêle
                u = (t - 0.7) / 0.9
                M_ = Matrix.Translation((0, 0, 1.7 * 4 * u * (1 - u))) @ M_ @ Matrix.Rotation(TAU * u, 4, 'X')
            return (M_, None, s)
        clip("theme_special", tl, {"prop_poele": held("L", R_, 1.05, kw, a=0.22, b=2.6), "prop_crepe": crepe})

    def a_saint_valentin():
        Cl = dict(L=PORTE["enveloppe"][0], R=PORTE["enveloppe"][0], tilt=3)
        clip("theme_objet", objet_tl(Cl), {"prop_enveloppe": carried(*PORTE["enveloppe"][1:])})
        O2 = dict(L=A_OFFER, eyes=HAPPY, mouth="happy", lean=4)
        tl = [(0, N), (0.35, pose(L=A_FACE, eyes=HAPPY, mouth="small", tilt=3)), (0.55, pose(L=A_FACE, eyes=HAPPY, mouth="o", tilt=3)), (0.8, pose(**O2, tilt=6)), (1.3, pose(**O2, tilt=2)),
              (1.8, pose(**O2, tilt=6)), (2.4, pose(**O2, tilt=4)), (2.9, N)]
        clip("theme_special", tl, {"prop_coeur": floaty("L", 0.75, 1.5, s=0.9), "prop_coeur2": floaty("L", 1.05, 1.5, (0.75, -0.45, 1.7), 1.1), "prop_coeur3": floaty("L", 1.35, 1.45, (0.45, -0.5, 1.9), 1.25)})

    def a_mardi_gras():
        Mk = dict(R=A_MASK)                                       # la main vient sur le manche ; tête et bras bougent ensemble (buste)
        tl = [(0, N), (0.12, pose(w=1.02, h=0.98)), (0.42, pose(**Mk)), (1.0, pose(**Mk, side=2.5)), (1.55, pose(**Mk, side=-2.0)), (2.05, pose(**Mk, side=2.5)), (2.4, pose(**Mk)), (2.8, N)]
        clip("theme_objet", tl, {"prop_masque": rigid("R", Mk, 0.2, 2.5)})          # le masque monte et redescend avec la main
        Uu = dict(L=A_UP, R=A_UP, eyes=HAPPY, mouth="happy", flap=-6)
        tl = [(0, N), (0.25, pose(L=A_HOLD, R=A_HOLD, **SQ)), (0.5, pose(**Uu, up=0.12, **ST)), (0.68, pose(**Uu, **SQ)), (0.85, pose(**Uu)), (1.4, pose(**Uu, side=3)), (1.9, pose(**Uu, side=-3)),
              (2.3, pose(**Uu)), (2.8, N)]
        clip("theme_special", tl, {"prop_confettis": burst((0, -0.5, 2.5), 1.25, 0.48, 2.2, 1.05)})

    def a_paques():
        Co = dict(L=PORTE["oeuf"][0], R=PORTE["oeuf"][0])
        clip("theme_objet", objet_tl(Co), {"prop_oeuf": carried(*PORTE["oeuf"][1:])})
        Pw = dict(L=A_PAW, R=A_PAW)
        tl = [(0, N), (0.22, pose(**Pw, **SQ))]
        for i in range(3):
            t0 = 0.45 + 0.56 * i
            tl += [(t0, pose(**Pw, up=0.36, eyes=HAPPY, mouth="happy", legs=(22, 22), flap=-10, nod=-3, **ST)), (t0 + 0.3, pose(**Pw, eyes=HAPPY, mouth="happy", flap=8, nod=3, w=1.06, h=0.92))]
        tl += [(2.25, pose(**Pw, eyes=HAPPY, mouth="happy")), (2.7, N)]
        clip("theme_special", tl, {"prop_oeuf": fixed((1.55, -0.7, 0.42), (0, -10, 0), 1.15, a=0.2, b=2.3)})

    def a_premier_mai():
        kw = dict(L=A_OFFER, tilt=3)
        clip("theme_objet", objet_tl(kw), {"prop_muguet": held("L", (-12, -6, 0), 1.25, kw)})
        F = dict(L=A_SNIFF, eyes=CALM, mouth="small")
        tl = [(0, N), (0.4, pose(L=A_OFFER)), (0.9, pose(**F, nod=7, tilt=7)), (1.45, pose(**F, nod=9, tilt=7, h=1.025, w=0.985)), (2.0, pose(**F, nod=7, tilt=7)),
              (2.4, pose(L=A_OFFER, eyes=HAPPY, mouth="happy")), (2.9, N)]
        clip("theme_special", tl, {"prop_muguet": held("L", (-8, -50, 0), 1.25, dict(F, nod=7, tilt=7), a=0.22, b=2.55)})

    def a_musique():
        G = dict(L=A_NECK, R=A_STRUM)
        git = on_body((0.1, -1.02, 1.18), (-8, -22, 0), 0.95, 0.25, 2.7)
        tl = [(0, N), (0.4, pose(**G)), (1.0, pose(**dict(G, R=shift(A_STRUM, dT=(0, 0, -0.08)), tilt=-3))), (1.5, pose(**G)), (2.1, pose(**dict(G, R=shift(A_STRUM, dT=(0, 0, -0.08)), tilt=3))),
              (2.6, pose(**G)), (3.0, N)]
        clip("theme_objet", tl, {"prop_guitare": git})
        tl = [(0, N), (0.4, pose(**G))]
        for i in range(9):
            tl.append((0.62 + 0.22 * i, pose(L=A_NECK, R=shift(A_STRUM, dT=(0, 0, 0.06 - 0.16 * (i % 2))), eyes=HAPPY, mouth=("A", "happy")[i % 2], tilt=-7 + 12 * ((i // 2) % 2),
                                              side=3 * (-1) ** (i // 2), legs=(0, 16 * (i % 2)))))
        tl += [(2.7, pose(**G, eyes=HAPPY)), (3.1, N)]
        clip("theme_special", tl, {"prop_guitare": on_body((0.1, -1.02, 1.18), (-8, -22, 0), 0.95, 0.25, 2.8),
                                   "prop_note": floaty("L", 0.85, 1.5, (0.3, 0.1, 1.45), 1.1, (0.2, 0.0, 0.5)), "prop_note2": floaty("L", 1.45, 1.4, (0.6, 0.2, 1.7), 0.9, (0.2, 0.0, 0.5))})

    def a_quatorze_juillet():
        kw = dict(L=A_SHOW)
        clip("theme_objet", objet_tl(kw), {"prop_drapeau": held("L", (0, 6, 0), 1.25, kw)})
        Hh = dict(R=A_SPREAD, eyes=WIDE, mouth="A", nod=-7)
        tl = [(0, N), (0.35, pose(L=A_SHOW)), (0.7, pose(L=A_HIGH, **Hh))]
        for i in range(6): tl.append((0.95 + 0.25 * i, pose(L=shift(A_HIGH, dT=(0.13 * (-1) ** i, 0, 0)), side=1.5 * (-1) ** i, **Hh)))
        tl += [(2.5, pose(L=A_HIGH, eyes=HAPPY, mouth="happy")), (2.95, N)]
        clip("theme_special", tl, {"prop_drapeau": held("L", (0, 18, 0), 1.25, dict(L=A_HIGH, **Hh), spin=lambda t: (0, 10 * math.sin(TAU * (t - 0.7) / 0.5) * (0.7 < t < 2.5), 0), a=0.22, b=2.6),
                                   "prop_feu1": flash((-1.7, 1.5, 3.9), 0.8, 0.9), "prop_feu2": flash((2.0, 1.5, 3.2), 1.25, 0.7), "prop_feu3": flash((0.1, 1.5, 4.35), 1.7, 0.5)})

    def a_halloween():
        Cc = dict(L=PORTE["citrouille"][0], R=PORTE["citrouille"][0])
        clip("theme_objet", objet_tl(Cc), {"prop_citrouille": carried(*PORTE["citrouille"][1:])})
        C = dict(L=A_HOLD, R=A_HOLD, lean=12, nod=13, w=1.05, h=0.92)                     # il se cache sous son chapeau
        Bh = dict(L=A_CLAW, R=A_CLAW, lean=8, eyes=dict(h=1.2, w=1.2), mouth="A")
        tl = [(0, N), (0.35, pose(**C)), (0.6, pose(**dict(C, side=1.2))), (0.8, pose(**dict(C, side=-1.2))), (0.98, pose(**C)), (1.12, pose(**Bh, up=0.1, **ST)), (1.28, pose(**Bh, **SQ)),
              (1.45, pose(**Bh, side=3)), (1.65, pose(**Bh, side=-3)), (1.85, pose(**Bh)), (2.25, pose(eyes=HAPPY, mouth="happy")), (2.7, N)]
        clip("theme_special", tl, {"prop_citrouille": fixed((1.2, -0.5, 0.4), (0, 0, -12), 1.3, 1.05, 2.3)})

    def a_noel():
        Cc = dict(L=PORTE["cadeau"][0], R=PORTE["cadeau"][0])
        clip("theme_objet", objet_tl(Cc), {"prop_cadeau": carried(*PORTE["cadeau"][1:])})
        Ee = dict(hturn=14, tilt=9, side=3)
        tl = [(0, N), (0.38, pose(**Cc)), (0.8, pose(L=A_EAR, mouth="pensive", **Ee))]
        for i in range(6): tl.append((0.95 + 0.12 * i, pose(L=shift(A_EAR, dT=(0, 0, 0.09 * (-1) ** i)), mouth="pensive", **Ee)))
        tl += [(1.75, pose(L=A_EAR, eyes=WIDE, mouth="o", **Ee)), (2.15, pose(L=A_EAR, eyes=HAPPY, mouth="happy", **Ee)), (2.6, pose(**Cc, eyes=HAPPY)), (3.0, N)]
        w = lambda t: k(t, [(0.38, 0.0), (0.8, 1.0), (2.15, 1.0), (2.6, 0.0)])

        def cadeau(t, H):
            a = H["mid"] + Vector(PORTE["cadeau"][1]); b_ = H["L"] + H["dL"] * 0.4 + Vector((0, -0.05, 0.1)); u = smooth(0, 1, w(t))
            return (a.lerp(b_, u), (0, 18 * u, 14 + 6 * u), lerp(1.0, 0.8, u) * env(t, 0.22, 2.7))
        clip("theme_special", tl, {"prop_cadeau": cadeau})

    ad.use_nla = False
    globals()["a_" + THEME]()
    ad.use_nla = True
    sc.frame_set(1)
    result = {"theme": THEME, "actions": len(META), "os": len(arm_d.bones), "durees": {n: META[n]["duree"] for n in ("theme_objet", "theme_special")}}
