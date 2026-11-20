# Travail « base », en direct dans Blender : reconstruit Sherlock et ses 30 animations, rend les images de contrôle
# des actions demandées (shl.controle), exporte un .glb candidat et le vérifie. Ne remplace rien dans le dossier livré.
import bpy, os, sys, json, math
shl = sys.modules["shl"]
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
SCR = r"C:\Users\breuilla\AppData\Local\Temp\claude\851202e51721bef7\4117ccba-52cf-45a4-bebf-96650bfc65c0\scratchpad"
CAND = os.path.join(SCR, "base"); IMG = os.path.join(CAND, "images")
ACTIONS = list(getattr(shl, "controle", None) or [])


def src(name): return compile(open(os.path.join(shl.S, name), encoding="utf-8").read(), name, "exec")


def job():
    os.makedirs(IMG, exist_ok=True)
    ns = shl.new()
    meta = os.path.join(OUTD, "animations.json"); garde = open(meta, "rb").read()
    shl.run("sherlock_build.py"); yield "modèle"
    shl.run("sherlock_rig.py"); yield "squelette"
    try:
        shl.run("sherlock_anim.py")
        open(os.path.join(CAND, "animations.json"), "wb").write(open(meta, "rb").read())      # version candidate
    finally:
        open(meta, "wb").write(garde)
    yield "30 animations"
    ex = {"__name__": "ex"}; exec(src("sherlock_export.py"), ex)
    ex["GLB"] = os.path.join(CAND, "sherlock.glb")
    ex["export_glb"](ns["ao_links"])
    chk = {"__name__": "chk"}; exec(src("sherlock_check.py"), chk)
    res = chk["check"](ex["GLB"], os.path.join(CAND, "animations.json"), os.path.join(CAND, "verification-animations.md"))
    yield "glb candidat exporté et vérifié"
    nsv = {"__name__": "views"}; exec(src("sherlock_views.py"), nsv); nsv["setup_light"]()
    sc = bpy.context.scene; sc.eevee.taa_render_samples = 16
    cam = bpy.data.objects["Camera"]; cam.data.type = 'PERSP'; cam.data.lens = 84
    cam.location = (-12.0 * math.sin(math.radians(20)), -12.0 * math.cos(math.radians(20)), 3.4)
    bpy.data.objects["Cible_camera"].location = (0, 0, 2.2); sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = 480; sc.render.resolution_percentage = 100
    shl.view()
    ad = ns["ad"]; ad.use_nla = False
    for name in ACTIONS:
        act = bpy.data.actions[name]; ad.action = act
        try:
            if ad.action_slot is None and len(act.slots): ad.action_slot = act.slots[0]
        except Exception:
            pass
        n = int(act.frame_end)
        for f in range(1, n + 1):
            sc.frame_set(f); sc.render.filepath = os.path.join(IMG, "%s_%03d.png" % (name, f)); bpy.ops.render.render(write_still=True)
            yield "%s image %d/%d" % (name, f, n)
    ad.action = None; ns["rest_all"](); ad.use_nla = True; sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAND, "sherlock-repos.blend"), copy=True)
    return {"conforme": res["ok"], "ko": res["size_ko"], "os": len(res["bones"]), "animations": len(res["rows"]),
            "ecarts": [list(r) for r in res["rows"] if r[3] != "OK"], "dossier": CAND}


shl.start(job, pause=0.02)
result = {"lancé": "base", "controle": ACTIONS}
