# Sherlock - images de contrôle des animations : pour chaque action, les images 0, milieu et fin (PNG transparents).
# Les planches par famille sont assemblées ensuite (assembler-planches.ps1).
import bpy, os, math, json

SCR = r"C:\Users\breuilla\AppData\Local\Temp\claude\851202e51721bef7\4117ccba-52cf-45a4-bebf-96650bfc65c0\scratchpad"
OUTD = r"D:\ItHome\ithome-sherlock\docs\personnage\3d"
FRAMES_DIR = os.path.join(SCR, "planches")
os.makedirs(FRAMES_DIR, exist_ok=True)
sc = bpy.context.scene


def solo(names):
    for tr in bpy.data.objects["Rig"].animation_data.nla_tracks: tr.mute = names is not None and tr.name not in names


def render_frames(setup_light, names, size=320, samples=20):
    """Rend les images début / milieu / fin des actions données, en vue 3/4 (même caméra que repos.png)."""
    meta = json.load(open(os.path.join(OUTD, "animations.json"), encoding="utf-8"))
    setup_light()
    sc.eevee.taa_render_samples = samples
    cam = bpy.data.objects["Camera"]; cam.data.type = "PERSP"; cam.data.lens = 100
    d, th = 12.0, math.radians(20)
    cam.location = (-d * math.sin(th), -d * math.cos(th), 3.6)
    bpy.data.objects["Cible_camera"].location = (0, 0, 2.1)
    sc.camera = cam
    sc.render.resolution_x = sc.render.resolution_y = size
    for n in names:
        m = meta[n]
        nf = int(round(m["duree"] * 24))
        solo(("repos", n) if m["type"].startswith("couche") else (n,))
        for k, f in enumerate((1, 1 + nf // 2, 1 + nf)):
            for pb in bpy.data.objects["Rig"].pose.bones:      # les canaux non animés reviennent à la pose de liaison
                pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
            sc.frame_set(f)
            sc.render.filepath = os.path.join(FRAMES_DIR, "%s_%d.png" % (n, k))
            bpy.ops.render.render(write_still=True)
    solo(None)
    sc.frame_set(1)
    sc.render.resolution_x = sc.render.resolution_y = 512
    sc.eevee.taa_render_samples = 32
