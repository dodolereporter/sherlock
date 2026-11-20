# Pilote « en direct » : installé une fois dans le Blender ouvert (module shl, conservé entre les appels du pont MCP).
#   shl.NS            espace de noms partagé par les scripts sherlock_*.py
#   shl.run(nom)      exécute un script du dossier scripts dans cet espace
#   shl.start(gen)    lance un travail long en plusieurs pas (un pas par tic du minuteur : Blender reste vivant et affiche)
#   shl.state         avancement du travail en cours
import bpy, os, sys, types, time, traceback

shl = sys.modules.get("shl") or types.ModuleType("shl")
sys.modules["shl"] = shl
shl.S = r"D:\ItHome\ithome-sherlock\docs\personnage\3d\scripts"
shl.NS = getattr(shl, "NS", {})
shl.state = getattr(shl, "state", {"done": True, "err": None, "step": "", "n": 0, "result": None})


def new():
    shl.NS = {"__name__": "sherlock_live"}
    return shl.NS


def run(name, cut=None, **vars_):
    src = open(os.path.join(shl.S, name), encoding="utf-8").read()
    if cut: src = src.split(cut)[0]
    shl.NS.update(vars_)
    exec(compile(src, name, "exec"), shl.NS)


def start(gen_fn, pause=0.05):
    st = shl.state
    if not st.get("done", True): raise RuntimeError("un travail est déjà en cours : " + str(st.get("step")))
    st.update(done=False, err=None, step="départ", n=0, result=None, t0=time.time())
    g = gen_fn()

    def tick():
        try:
            st["step"] = str(next(g)); st["n"] += 1
            return pause
        except StopIteration as e:
            st["result"] = e.value
        except Exception:
            st["err"] = traceback.format_exc()
        st["done"] = True; st["dt"] = round(time.time() - st["t0"], 1)
        return None
    bpy.app.timers.register(tick, first_interval=0.1)


def view(shading="RENDERED", camera=True):
    """Met les vues 3D en rendu, à travers la caméra, pour suivre le travail à l'écran."""
    n = 0
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas:
            if a.type != 'VIEW_3D': continue
            sp = a.spaces.active
            sp.shading.type = shading
            sp.overlay.show_overlays = False
            if camera: sp.region_3d.view_perspective = 'CAMERA'
            a.tag_redraw(); n += 1
    return n


def redraw():
    for w in bpy.context.window_manager.windows:
        for a in w.screen.areas: a.tag_redraw()


shl.new, shl.run, shl.start, shl.view, shl.redraw = new, run, start, view, redraw
result = {"shl": "prêt", "blender": bpy.app.version_string, "fichier": bpy.data.filepath or "(non enregistré)",
          "objets": len(bpy.data.objects), "travail_en_cours": not shl.state.get("done", True)}
