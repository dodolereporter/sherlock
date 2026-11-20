# Travail 3, en direct dans Blender : monte les images légendées (v_00001.jpg, ...) en MP4 dans une scène à part
# « Montage_controle », sans toucher à la scène de Sherlock.
import bpy, os, sys
shl = sys.modules["shl"]
FR, DST, FPS = shl.video_frames, shl.video_dst, 12


def job():
    names = sorted(f for f in os.listdir(FR) if f.lower().endswith(".jpg"))
    old = bpy.data.scenes.get("Montage_controle")
    if old: bpy.data.scenes.remove(old)
    sc = bpy.data.scenes.new("Montage_controle")
    se = sc.sequence_editor_create()
    st = se.strips.new_image("controle", os.path.join(FR, names[0]), 1, 1)
    for n in names[1:]: st.elements.append(n)
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 720, 720, 100, FPS
    sc.frame_start, sc.frame_end = 1, len(names)
    r.use_sequencer = True
    try: r.image_settings.media_type = 'VIDEO'
    except Exception: pass
    r.image_settings.file_format = 'FFMPEG'
    ff = r.ffmpeg
    ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = FPS
    ff.audio_codec = 'NONE'
    sc.view_settings.view_transform = 'Standard'
    r.filepath = DST
    yield "montage prêt : %d images" % len(names)
    bpy.ops.render.render(animation=True, scene=sc.name)
    return {"images": len(names), "duree_s": round(len(names) / FPS, 1), "fichier": DST, "ko": round(os.path.getsize(DST) / 1024)}


shl.start(job, pause=0.2)
result = {"lancé": "vidéo de contrôle"}
