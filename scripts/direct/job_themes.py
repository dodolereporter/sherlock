# Travail 2, en direct dans Blender : pour chaque thème de shl.todo, reconstruit Sherlock avec sa tenue et ses objets,
# crée theme_objet et theme_special, exporte saisons\sherlock-<thème>.glb, le vérifie, rend les images de contrôle
# (une image sur deux) et enregistre une copie .blend du thème.
import bpy, os, sys, json, math
shl = sys.modules["shl"]
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
SAIS = os.path.join(OUTD, "saisons"); IMG = os.path.join(SAIS, "images-animations"); BL = os.path.join(SAIS, "blend")
TODO = list(shl.todo)
PAS = 2                                   # une image sur deux pour la vidéo de contrôle (12 images par seconde)


def src(name): return compile(open(os.path.join(shl.S, name), encoding="utf-8").read(), name, "exec")


def job():
    for d in (IMG, BL): os.makedirs(d, exist_ok=True)
    chk = {"__name__": "chk"}; exec(src("sherlock_check.py"), chk)
    bilan_p = os.path.join(SAIS, "bilan.json")
    bilan = json.load(open(bilan_p, encoding="utf-8")) if os.path.exists(bilan_p) else {}
    meta = os.path.join(OUTD, "animations.json")
    for th in TODO:
        ns = shl.new(); garde = open(meta, "rb").read()
        for f_ in os.listdir(IMG):                                 # les images d'un rendu précédent de ce thème
            if f_.startswith(th + "_a_") or f_.startswith(th + "_b_"): os.remove(os.path.join(IMG, f_))
        shl.run("sherlock_build.py"); yield th + " : modèle"
        shl.run("sherlock_themes.py", THEME=th, HERE=shl.S, THEME_STAGE="pre"); shl.redraw(); yield th + " : tenue et objets"
        shl.run("sherlock_rig.py"); yield th + " : squelette"
        try:
            shl.run("sherlock_anim.py")
        finally:
            open(meta, "wb").write(garde)                      # le fichier livré avec sherlock.glb ne bouge pas
        yield th + " : 30 animations de base"
        shl.run("sherlock_themes.py", THEME=th, HERE=shl.S, THEME_STAGE="post"); post = dict(ns["result"])
        yield th + " : animations du thème"
        # ---- export et vérification
        ex = {"__name__": "ex"}; exec(src("sherlock_export.py"), ex)
        ex["GLB"] = os.path.join(SAIS, "sherlock-%s.glb" % th)
        ex["export_glb"](ns["ao_links"])
        mj = os.path.join(SAIS, "sherlock-%s.json" % th)
        json.dump(ns["META"], open(mj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        res = chk["check"](ex["GLB"], mj, None)
        bilan[th] = {"ko": res["size_ko"], "os": len(res["bones"]), "animations": len(res["rows"]), "conforme": res["ok"],
                     "ecarts": [list(r) for r in res["rows"] if r[3] != "OK"], "durees": post.get("durees"),
                     "os_objets": [b for b in res["bones"] if b.startswith("prop_") and b[5:] in ns["OBJETS"]]}
        json.dump(bilan, open(bilan_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        yield th + " : glb exporté et vérifié"
        # ---- images de contrôle : même cadrage que les planches
        nsv = {"__name__": "views"}; exec(src("sherlock_views.py"), nsv); nsv["setup_light"]()
        sc = bpy.context.scene; sc.eevee.taa_render_samples = 16
        cam = bpy.data.objects["Camera"]; cam.data.type = 'PERSP'; cam.data.lens = 84
        cam.location = (-12.0 * math.sin(math.radians(20)), -12.0 * math.cos(math.radians(20)), 3.4)
        bpy.data.objects["Cible_camera"].location = (0, 0, 2.2); sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = 480; sc.render.resolution_percentage = 100
        shl.view()
        ad = ns["ad"]; ad.use_nla = False
        for tag, name in (("a", "theme_objet"), ("b", "theme_special")):
            act = bpy.data.actions[name]; ad.action = act
            try:
                if ad.action_slot is None and len(act.slots): ad.action_slot = act.slots[0]
            except Exception:
                pass
            n = int(act.frame_end)
            for f in list(range(1, n, PAS)) + [n]:
                sc.frame_set(f)
                sc.render.filepath = os.path.join(IMG, "%s_%s_%03d.png" % (th, tag, f))
                bpy.ops.render.render(write_still=True)
                yield "%s : %s image %d/%d" % (th, name, f, n)
        ad.action = None; ns["rest_all"](); ad.use_nla = True; sc.frame_set(1)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BL, "sherlock-%s.blend" % th), copy=True)
        yield th + " : terminé"
    return {t: {k: bilan[t][k] for k in ("ko", "os", "animations", "conforme")} for t in TODO}


shl.start(job, pause=0.02)
result = {"lancé": TODO}
