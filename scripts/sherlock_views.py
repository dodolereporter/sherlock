# Sherlock - vues orthographiques en T-pose à l'échelle de la planche + planches de comparaison à 50 %.
# Lancé par un minuteur (bpy.app.timers) : écrit VIEWS_DONE.txt à la fin.
import bpy, math, os
import numpy as np
from mathutils import Vector, Matrix

SCR = r"C:\Users\breuilla\AppData\Local\Temp\claude\851202e51721bef7\4117ccba-52cf-45a4-bebf-96650bfc65c0\scratchpad"
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
SHEET = os.path.join(OUTD, "reference-tpose.png")
PX = 131.2                       # pixels de la planche par unité (hauteur 3,40 u = 446 px)
W, H = 512, 480
FEET_Y = 466                     # ligne des pieds dans chaque case
sc = bpy.context.scene

VIEWS = {   # nom : (direction de visée, haut)
    "face": (Vector((0, 1, 0)), Vector((0, 0, 1))),
    "profil_gauche": (Vector((-1, 0, 0)), Vector((0, 0, 1))),
    "dos": (Vector((0, -1, 0)), Vector((0, 0, 1))),
    "profil_droit": (Vector((1, 0, 0)), Vector((0, 0, 1))),
    "dessus": (Vector((0, 0, -1)), Vector((0, 1, 0))),
    "dessous": (Vector((0, 0, 1)), Vector((0, -1, 0))),
}


WORLD, KEY = 0.74, 560


def place_lights(fwd, up):
    """Place les lumières par rapport à la caméra : clé en haut à gauche, débouchage à droite, contre-jour derrière."""
    right = fwd.cross(up).normalized()
    c = Vector((0, 0, 2.0))
    bpy.data.objects["Lumiere_cle"].location = c - fwd * 7.5 - right * 6.5 + up * 6.0
    bpy.data.objects["Lumiere_debouchage"].location = c - fwd * 6.0 + right * 6.0 + up * 0.5
    bpy.data.objects["Lumiere_contre"].location = c + fwd * 6.0 + right * 3.0 + up * 4.0


def setup_light():
    """Lumière large et douce venant du haut à gauche, ambiance claire : modelé « pâte à modeler »."""
    for o_ in (bpy.data.objects["Camera"], bpy.data.objects["Cible_camera"]):
        if o_.animation_data: o_.animation_data_clear()
    try: sc.render.image_settings.media_type = "IMAGE"
    except Exception: pass
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    nt_ = sc.world.node_tree; nt_.nodes.clear()
    o1_ = nt_.nodes.new("ShaderNodeOutputWorld"); b1_ = nt_.nodes.new("ShaderNodeBackground"); nt_.links.new(b1_.outputs[0], o1_.inputs[0])
    bg = b1_
    bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = WORLD
    k = bpy.data.lights["Cle"]; k.energy = KEY; k.size = 14
    bpy.data.lights["Debouchage"].energy = 90
    bpy.data.lights["Contre"].energy = 60
    place_lights(Vector((0.29, 0.957, 0)), Vector((0, 0, 1)))    # par défaut : caméra 3/4
    sol = bpy.data.objects.get("Sol_ombre")
    if sol: sol.hide_render = True
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0
    sc.render.film_transparent = True
    sc.eevee.taa_render_samples = 32
    try:
        sc.eevee.use_raytracing = True                # occlusion douce dans les creux
    except Exception:
        pass


def cam_matrix(fwd, up, target, dist):
    right = fwd.cross(up).normalized(); up2 = right.cross(fwd).normalized()
    rot = Matrix((right, up2, -fwd)).transposed()
    return Matrix.Translation(target - fwd * dist) @ rot.to_4x4()


def render_views(names):
    setup_light()
    cd = bpy.data.cameras.get("Cam_vues") or bpy.data.cameras.new("Cam_vues")
    cd.type = 'ORTHO'; cd.ortho_scale = W / PX; cd.clip_end = 100
    cam = bpy.data.objects.get("Cam_vues") or bpy.data.objects.new("Cam_vues", cd)
    if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
    old_cam, old_res = sc.camera, (sc.render.resolution_x, sc.render.resolution_y)
    sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = W, H
    arm = bpy.data.objects.get("Rig")
    if arm: arm.data.pose_position = 'REST'          # T-pose
    zc = (FEET_Y - H / 2) / PX
    for name in names:
        fwd, up = VIEWS[name]
        tgt = Vector((0, 0, zc)) if name not in ("dessus", "dessous") else Vector((0, 0, 1.7))
        cam.matrix_world = cam_matrix(fwd, up, tgt, 30)
        place_lights(fwd, up)
        sc.render.filepath = os.path.join(SCR, "vue_%s.png" % name)
        bpy.ops.render.render(write_still=True)
    if arm: arm.data.pose_position = 'POSE'
    sc.camera = old_cam; sc.render.resolution_x, sc.render.resolution_y = old_res
    bpy.data.objects.remove(cam)


def load_rgba(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1].copy()
    bpy.data.images.remove(img)
    return a


def over_white(a):
    return a[..., :3] * a[..., 3:4] + (1 - a[..., 3:4])


def ref_boxes(sheet):
    """Boîte 512 x 480 de chaque vue sur la planche, calée sur l'axe du personnage et la ligne des pieds (libellés exclus)."""
    al = sheet[..., 3] > 0.5
    panels = {"face": (0, 512, 0, 470), "dos": (512, 1024, 0, 470), "profil_gauche": (1024, 1536, 0, 470),
              "profil_droit": (0, 512, 500, 970), "dessus": (512, 1024, 500, 970), "dessous": (1024, 1536, 500, 970)}
    boxes = {}
    for n, (x0, x1, y0, y1) in panels.items():
        m = al[y0:y1, x0:x1].copy()
        rows = m.sum(axis=1) > 2
        best, cur, start = (0, 0), 0, 0
        for i, r in enumerate(list(rows) + [False]):
            if r and cur == 0: start = i
            cur = cur + 1 if r else 0
            if r and cur > best[1] - best[0]: best = (start, i + 1)
        m[:best[0]] = False; m[best[1]:] = False
        ys, xs = np.where(m)
        if n in ("dessus", "dessous"):
            cy = (ys.min() + ys.max()) / 2 + y0; cx = (xs.min() + xs.max()) / 2 + x0
            boxes[n] = (int(round(cx - W / 2)), int(round(cy - H / 2)), int(xs.max() - xs.min()))
        else:
            bot = ys.max() + y0
            rx = np.where(m[int(bot - 0.2 * PX - y0)])[0]       # axe = milieu des jambes
            cx = (rx.min() + rx.max()) / 2 + x0
            boxes[n] = (int(round(cx - W / 2)), int(round(bot - FEET_Y)))
    return boxes


def crop(img, x0, y0):
    out = np.zeros((H, W, 4), np.float32)
    h, w = img.shape[:2]
    sx0, sy0 = max(0, x0), max(0, y0); sx1, sy1 = min(w, x0 + W), min(h, y0 + H)
    out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
    return out


def save_png(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("tmp_save", w, h, alpha=True)
    rgba = np.concatenate([arr, np.ones((h, w, 1), np.float32)], axis=2) if arr.shape[2] == 3 else arr
    img.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)


def rescale(img, s):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sy = (yy - h / 2) / s + h / 2; sx = (xx - w / 2) / s + w / 2
    x0 = np.clip(np.floor(sx).astype(int), 0, w - 2); y0 = np.clip(np.floor(sy).astype(int), 0, h - 2)
    fx = np.clip(sx - x0, 0, 1)[..., None]; fy = np.clip(sy - y0, 0, 1)[..., None]
    out = (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
           + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)
    inside = ((sx >= 0) & (sx < w - 1) & (sy >= 0) & (sy < h - 1))[..., None]
    return out * inside


def recentre(img):
    ys, xs = np.where(img[..., 3] > 0.5)
    dy = int(round(H / 2 - (ys.min() + ys.max()) / 2)); dx = int(round(W / 2 - (xs.min() + xs.max()) / 2))
    return np.roll(np.roll(img, dy, axis=0), dx, axis=1), xs.max() - xs.min()


def compose(names, out_name):
    """Une ligne par vue : référence | rendu | superposition à 50 %."""
    sheet = load_rgba(SHEET)
    boxes = ref_boxes(sheet)
    rows = []; stats = {}
    for n in names:
        ours_a = load_rgba(os.path.join(SCR, "vue_%s.png" % n))
        if n in ("dessus", "dessous"):                   # cases dessinées à une autre échelle : largeur et centre recalés
            x0, y0, ref_w = boxes[n]
            ours_a, our_w = recentre(ours_a)
            ours_a = rescale(ours_a, ref_w / our_w)
            ref_a = crop(sheet, x0, y0)
        else:
            ref_a = crop(sheet, *boxes[n])
        ref, ours = over_white(ref_a), over_white(ours_a)
        a, b = ref_a[..., 3] > 0.5, ours_a[..., 3] > 0.5
        stats[n] = round(float((a & b).sum() / max(1, (a | b).sum())), 3)      # recouvrement des silhouettes
        if n == "face":                                   # couleurs médianes : référence / rendu
            for im, tag in ((ref_a, "ref"), (ours_a, "moi")):
                r_, g_, b_ = im[..., 0], im[..., 1], im[..., 2]; so = im[..., 3] > 0.5
                cls = {"casquette": so & (b_ - r_ > 0.1) & (g_ > 0.27) & (r_ < 0.5), "echarpe": so & (g_ - b_ > 0.06) & (g_ - r_ > 0.03),
                       "corps": so & (np.minimum(np.minimum(r_, g_), b_) > 0.5) & ~((g_ - b_ > 0.06) & (g_ - r_ > 0.03))}
                for k_, m_ in cls.items():
                    med = np.median(im[m_][:, :3], axis=0) if m_.sum() > 50 else (0, 0, 0)
                    stats["%s_%s" % (k_, tag)] = "#%02X%02X%02X" % tuple(int(round(float(v) * 255)) for v in med)
        row = np.concatenate([ref, ours, 0.5 * ref + 0.5 * ours], axis=1)
        if n not in ("dessus", "dessous"): row[FEET_Y, :, :] = (0.86, 0.16, 0.16)
        rows.append(row)
    save_png(np.concatenate(rows, axis=0), os.path.join(OUTD, out_name))
    return stats


def job(names=("face", "profil_gauche", "dos"), out_name="validation-face-profil-dos.png"):
    render_views(names)
    st = compose(names, out_name)
    open(os.path.join(SCR, "VIEWS_DONE.txt"), "w").write(str(st))
    return None
