# Sherlock - contrôle des animations du fichier sherlock.glb (Python pur, sans dépendance).
#
#   python sherlock_check.py [sherlock.glb] [animations.json] [verification-animations.md]
#
# Règles contrôlées, action par action :
#   - boucles : première image = dernière image (écart < 0,001 sur tous les os) et vitesse continue au raccord ;
#   - actions ponctuelles : départ et arrivée égaux à la pose neutre N (image 0 de « repos ») ;
#   - entrées : départ = N, arrivée = première image de la boucle visée ; sorties : l'inverse ;
#   - couches : aucune clé hors des os autorisés, départ (et arrivée, sauf tenue) = N sur ces os ;
#   - partout : aucune clé sur eye_L / eye_R, et root immobile horizontalement.
import json, struct, sys, os

TOL = 1e-3
TOL_V = 0.05         # marge sur le saut de vitesse au raccord d une boucle (unités par seconde)
LAYER_BONES = {"cligne": ("eyelid_",), "yeux_fermes": ("eyelid_", "eye_happy_"), "bouche_parle": ("mouth",)}
REST = {"translation": (0.0, 0.0, 0.0), "rotation": (0.0, 0.0, 0.0, 1.0), "scale": (1.0, 1.0, 1.0)}
NCOMP = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}


def load(glb_path):
    data = open(glb_path, "rb").read()
    jlen = struct.unpack_from("<I", data, 12)[0]
    j = json.loads(data[20:20 + jlen])
    return j, data, 20 + jlen + 8, len(data)


def read_acc(j, data, bin0, i):
    a = j["accessors"][i]; v = j["bufferViews"][a["bufferView"]]
    n = NCOMP[a["type"]]
    off = bin0 + v.get("byteOffset", 0) + a.get("byteOffset", 0)
    flat = struct.unpack_from("<%df" % (a["count"] * n), data, off)
    return [flat[k * n:(k + 1) * n] for k in range(a["count"])]


def dist(path, a, b):
    d = max(abs(x - y) for x, y in zip(a, b))
    if path == "rotation": d = min(d, max(abs(x + y) for x, y in zip(a, b)))     # q et -q : même rotation
    return d


def check(glb_path, meta_path, out_md=None):
    j, data, bin0, size = load(glb_path)
    meta = json.load(open(meta_path, encoding="utf-8"))
    nodes = j["nodes"]
    joints = [nodes[i]["name"] for i in j["skins"][0]["joints"]]
    rest = {(n["name"], p): tuple(n.get(p, REST[p])) for n in nodes if "name" in n for p in REST}
    anims = {}
    for a in j["animations"]:
        ch = {}
        for c in a["channels"]:
            s = a["samplers"][c["sampler"]]
            t = [x[0] for x in read_acc(j, data, bin0, s["input"])]
            ch[(nodes[c["target"]["node"]]["name"], c["target"]["path"])] = (t, read_acc(j, data, bin0, s["output"]))
        anims[a["name"]] = ch

    def state(name, which, keys=None):
        """Valeur de chaque canal à la première (0) ou dernière (-1) image ; canal absent = pose de liaison."""
        ch = anims[name]
        return {k: (ch[k][1][which] if k in ch else rest[k]) for k in (keys or rest) if k[0] in joints}

    def gap(s1, s2):
        worst, where = 0.0, ""
        for k in s1:
            d = dist(k[1], s1[k], s2[k])
            if d > worst: worst, where = d, "%s.%s" % k
        return worst, where

    N = state("repos", 0)
    rows, ok_all = [], True
    for name in meta:
        m = meta[name]; typ = m["type"]; notes = []
        if name not in anims:
            rows.append((name, typ, "-", "KO", "absente du .glb")); ok_all = False; continue
        ch = anims[name]
        dur = max(t[-1] for t, _v in ch.values())
        first, last = state(name, 0), state(name, -1)

        def want(label, s1, s2):
            d, where = gap(s1, s2)
            if d >= TOL: notes.append("%s : écart %.4f sur %s" % (label, d, where))

        if typ in ("boucle", "couche_boucle"):
            want("raccord", first, last)
            # vitesse au raccord : le saut de vitesse entre la dernière et la première image ne doit pas dépasser
            # celui qu'on trouve entre deux images quelconques de la boucle (sinon, c'est un à-coup)
            for k, (t, v) in ch.items():
                if len(t) < 4: continue
                v = [list(x) for x in v]
                if k[1] == "rotation":                                   # q et -q : même rotation, on aligne les signes
                    for i in range(1, len(v)):
                        if sum(a * b for a, b in zip(v[i - 1], v[i])) < 0: v[i] = [-x for x in v[i]]
                vel = [[(b - a) / (t[i + 1] - t[i]) for a, b in zip(v[i], v[i + 1])] for i in range(len(t) - 1)]
                seam = max(abs(a - b) for a, b in zip(vel[0], vel[-1]))
                inner = max(max(abs(a - b) for a, b in zip(vel[i], vel[i + 1])) for i in range(len(vel) - 1))
                if seam > 1.5 * inner + TOL_V:
                    notes.append("vitesse au raccord : saut %.2f/s sur %s.%s (max ailleurs %.2f/s)" % (seam, k[0], k[1], inner))
                    break
        if typ == "ponctuelle":
            want("départ ≠ N", first, N); want("arrivée ≠ N", last, N)
        if typ == "entree":
            want("départ ≠ N", first, N); want("arrivée ≠ boucle %s" % m["cible"], last, state(m["cible"], 0))
        if typ == "sortie":
            want("départ ≠ boucle %s" % m["cible"], first, state(m["cible"], 0)); want("arrivée ≠ N", last, N)
        if typ.startswith("couche"):
            allowed = LAYER_BONES[name]
            bad = sorted({k[0] for k in ch if not k[0].startswith(allowed)})
            if bad: notes.append("clés hors des os autorisés : %s" % ", ".join(bad))
            own = list(ch)
            want("départ ≠ N", state(name, 0, own), {k: N.get(k, rest[k]) for k in own})
            if typ == "couche": want("arrivée ≠ N", state(name, -1, own), {k: N.get(k, rest[k]) for k in own})
        eye = sorted({k[0] for k in ch if k[0] in ("eye_L", "eye_R")})
        if eye: notes.append("clés sur %s" % ", ".join(eye))
        if ("root", "translation") in ch:                        # glTF : Y vers le haut, X et Z horizontaux
            hz = max(max(abs(v[0] - rest[("root", "translation")][0]), abs(v[2] - rest[("root", "translation")][2])) for v in ch[("root", "translation")][1])
            if hz >= TOL: notes.append("root se déplace horizontalement (%.4f)" % hz)
        if ("root", "rotation") in ch or ("root", "scale") in ch: notes.append("root tourne ou change d'échelle")
        ok = not notes
        ok_all = ok_all and ok
        rows.append((name, typ, "%.2f s" % dur, "OK" if ok else "KO", " ; ".join(notes) or "%d canaux" % len(ch)))
    extra = sorted(set(anims) - set(meta))
    lines = ["# Vérification des animations de Sherlock", "",
             "Fichier contrôlé : `%s` (%.0f Ko, %d os, %d animations)." % (os.path.basename(glb_path), size / 1024, len(joints), len(anims)), "",
             "Résultat : **%s** (%d actions conformes sur %d)." % ("tout est conforme" if ok_all else "des écarts restent", sum(r[3] == "OK" for r in rows), len(rows)), "",
             "| Action | Type | Durée | Contrôle | Détail |", "|---|---|---|---|---|"]
    lines += ["| `%s` | %s | %s | %s | %s |" % r for r in rows]
    if extra: lines += ["", "Animations présentes dans le .glb mais absentes de la liste : %s." % ", ".join(extra)]
    text = "\n".join(lines) + "\n"
    if out_md: open(out_md, "w", encoding="utf-8").write(text)
    return {"ok": ok_all, "rows": rows, "size_ko": round(size / 1024, 1), "bones": joints, "text": text}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(here)
    glb = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, "sherlock.glb")
    meta = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base, "animations.json")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(base, "verification-animations.md")
    res = check(glb, meta, out)
    print(res["text"])
    sys.exit(0 if res["ok"] else 1)
