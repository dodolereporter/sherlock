# Assemble les images du film en MP4 avec la musique (fondu de fin). À lancer hors interface :
#   blender -b --factory-startup --python film_encode_cli.py -- <dossier images> <musique> <sortie.mp4> [ips] [pas] [fondu_debut] [fondu_fin]
import bpy, os, sys, time

a = sys.argv[sys.argv.index("--") + 1:]
frames_dir, music, dst = a[0], a[1], a[2]
fps = int(a[3]) if len(a) > 3 else 60
step = int(a[4]) if len(a) > 4 else 1
fade0 = float(a[5]) if len(a) > 5 else 28.0
fade1 = float(a[6]) if len(a) > 6 else 30.0
t0 = time.time()
names = sorted(f for f in os.listdir(frames_dir) if f.lower().endswith(".jpg"))[::step]
sc = bpy.context.scene
se = sc.sequence_editor_create()
st = se.strips.new_image("film", os.path.join(frames_dir, names[0]), 1, 1)
for n in names[1:]: st.elements.append(n)
snd = se.strips.new_sound("musique", music, 2, 1)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1920, 1080, 100, fps
sc.frame_start, sc.frame_end = 1, len(names)
for t, v in ((0.0, 1.0), (fade0, 1.0), (fade1, 0.0)):
    snd.volume = v; snd.keyframe_insert("volume", frame=1 + int(round(t * fps)))
r.use_sequencer = True
try: r.image_settings.media_type = 'VIDEO'
except Exception: pass
r.image_settings.file_format = 'FFMPEG'
ff = r.ffmpeg
ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = fps // 2
ff.audio_codec = 'AAC'; ff.audio_bitrate = 192; ff.audio_mixrate = 48000; ff.audio_channels = 'STEREO'
sc.view_settings.view_transform = 'Standard'
r.filepath = dst
bpy.ops.render.render(animation=True)
print("ENCODAGE_OK images=%d ips=%d duree=%.1f s en %.0f s" % (len(names), fps, len(names) / fps, time.time() - t0))
