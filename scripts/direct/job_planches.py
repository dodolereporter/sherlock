# Travail 1, en direct dans Blender : construit Sherlock, son squelette, ses 30 animations, puis les tenues et objets
# des saisons et fêtes, et rend les images de validation (tenue, objet sorti, pose clé) thème par thème.
# Réglages optionnels : shl.filtre (liste de clés de thèmes), shl.res (taille des images), shl.dossier (sous-dossier de sortie).
import bpy, os, sys, json
shl = sys.modules["shl"]
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
IMAGES = os.path.join(OUTD, "saisons", getattr(shl, "dossier", None) or "images")
FILTRE = list(getattr(shl, "filtre", None) or [])
RES = int(getattr(shl, "res", None) or 420)


def job():
    ns = shl.new()
    meta = os.path.join(OUTD, "animations.json"); garde = open(meta, "rb").read()   # le fichier livré ne doit pas bouger
    shl.run("sherlock_build.py"); shl.redraw(); yield "modèle construit"
    shl.run("sherlock_rig.py"); shl.redraw(); yield "squelette posé"
    try:
        shl.run("sherlock_anim.py")
    finally:
        open(meta, "wb").write(garde)
    yield "30 animations de base créées"
    shl.run("sherlock_saisons.py", cut="\ncatalogue = []", SAISONS_OUT=IMAGES, SAISONS_FILTRE="")
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = RES
    shl.view(); yield "tenues et objets construits"
    cat = []
    for key, titre, periode, saison, tenue, cells in ns["THEMES"]:
        cat.append({"cle": key, "titre": titre, "periode": periode, "saison": saison, "tenue": tenue,
                    "legendes": ["Tenue portée en permanence"] + [c[0] for c in cells]})
        if FILTRE and key not in FILTRE: continue
        for i, (legende, kw, fn) in enumerate([("", dict(), None)] + list(cells)):
            ns["shot"](key, i, saison, tenue, kw, fn)
            for ob in ns["EXTRA"]: ob.hide_viewport = ob.hide_render             # la vue 3D montre ce que le rendu montre
            for md in ns["mesh"].modifiers:
                if md.name.startswith("Masque_"): md.show_viewport = md.show_render
            shl.redraw()
            yield "%s %d/2 %s" % (titre, i, legende)
    json.dump(cat, open(os.path.join(IMAGES, "catalogue.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in ns["EXTRA"]}
    return {"themes": len(cat), "accessoires": len(ns["EXTRA"]), "dossier": IMAGES, "triangles": tris}


shl.start(job, pause=0.3)
result = {"lancé": "planches de validation", "filtre": FILTRE, "res": RES}
