# Sherlock - vidéo de présentation de 15 s (1280 x 720, 24 i/s). Exécuté À LA SUITE de sherlock_build.py, sherlock_rig.py
# et sherlock_anim.py, dans le même espace de noms. Ne modifie pas sherlock.glb : c'est un montage des actions existantes.
#
#   prepare()            met en place le montage (pistes NLA, caméra, textes, fond)
#   still(frame, path)   rend une image de contrôle
#   render_video(path)   rend la vidéo MP4
FRAMES = 360
CAM_YAW = math.radians(14)
HUD_Z = -6.0                                   # distance des textes devant la caméra

# enchaînement : (action, image de départ) ; les entrées, boucles et sorties se suivent sans trou
BODY = [("salut", 13), ("enquete_entree", 59), ("enquete", 73), ("enquete_sortie", 121), ("reflechit_entree", 135),
        ("reflechit", 147), ("reflechit_sortie", 195), ("idee", 208), ("parle_entree", 246), ("parle", 253),
        ("parle_sortie", 301), ("reussite", 310)]
FACE = [("cligne", 52, 1), ("cligne", 100, 1), ("cligne", 170, 1), ("bouche_parle", 253, 4), ("yeux_fermes", 349, 1)]
# caméra : (image, distance, hauteur visée, décalage du personnage vers la gauche de l'image)
CAM = [(1, 12.5, 1.9, 1.1), (53, 12.5, 1.9, 1.1), (73, 8.4, 1.95, 0.85), (121, 8.4, 1.95, 0.85), (137, 8.2, 2.1, 0.8), (197, 8.2, 2.1, 0.8),
       (210, 8.6, 2.45, 0.8), (240, 8.6, 2.45, 0.8), (250, 8.2, 2.1, 0.8), (300, 8.2, 2.1, 0.8), (314, 12.5, 1.95, 1.1), (360, 12.2, 1.95, 1.1)]
# textes : (texte, x, y, taille, couleur, image d'apparition, image de disparition)
BLEU, MARINE, VERT = "#226891", "#1F3D5C", "#4E9A63"
TEXTS = [("Voici Sherlock", 0.25, 0.18, 0.36, BLEU, 16, 50), ("l'IA d'ITHome", 0.27, -0.2, 0.19, MARINE, 22, 50),
         ("Il enquête", 0.45, 0.1, 0.3, BLEU, 76, 121), ("Il réfléchit", 0.45, 0.1, 0.3, BLEU, 148, 197),
         ("Il a des idées", 0.45, 0.0, 0.3, BLEU, 216, 242), ("Il vous répond", 0.45, 0.1, 0.3, BLEU, 255, 302),
         ("Il fête vos réussites", 0.2, 0.15, 0.3, VERT, 316, 344),
         ("Sherlock", 0.25, 0.3, 0.44, BLEU, 348, 400), ("le compagnon IA d'ITHome", 0.27, -0.12, 0.19, MARINE, 351, 400),
         ("OPAC SAVOIE", 0.27, -0.46, 0.15, MARINE, 354, 400)]


def prepare():
    sc.frame_start, sc.frame_end = 1, FRAMES
    # ---------------- pistes NLA : pose de base, respiration, enchaînement du corps, couches du visage
    for tr in ad.nla_tracks: tr.mute = True
    for nm in ("pres_base", "pres_repos", "pres_corps", "pres_visage"):
        old = ad.nla_tracks.get(nm)
        if old: ad.nla_tracks.remove(old)
    old = bpy.data.actions.get("pres_base")
    if old: bpy.data.actions.remove(old)
    base = bpy.data.actions.new("pres_base")
    ad.use_nla = False; ad.action = base
    for f in (1, FRAMES + 1):                  # pose neutre complète : tout canal sans piste active y revient
        for pb in P:
            for ch, path in PATH.items():
                setattr(pb, path, N.get((pb.name, ch), REST[ch]).copy())
                pb.keyframe_insert(path, frame=f)
    for f, s_ in ((1, 0.001), (8, 1.1), (12, 1.0), (FRAMES + 1, 1.0)):      # entrée : il surgit en grandissant
        arm.scale = (s_, s_, s_); arm.keyframe_insert("scale", frame=f)
    base.use_frame_range = True; base.frame_start, base.frame_end = 1, FRAMES + 1
    ad.action = None; rest_all(); arm.scale = (1, 1, 1)

    def strip(track, name, start, repeat=1, blend=0, hold=False):
        st = track.strips.new("%s_%d" % (name, start), start, bpy.data.actions[name])
        st.extrapolation = 'HOLD_FORWARD' if hold else 'NOTHING'
        st.use_auto_blend = False; st.blend_in = st.blend_out = blend
        if repeat != 1: st.repeat = repeat
        return st

    t = ad.nla_tracks.new(); t.name = "pres_base"; strip(t, "pres_base", 1, hold=True)
    t = ad.nla_tracks.new(); t.name = "pres_repos"; strip(t, "repos", 1, repeat=5)
    t = ad.nla_tracks.new(); t.name = "pres_corps"
    for name, start in BODY: strip(t, name, start)
    t = ad.nla_tracks.new(); t.name = "pres_visage"
    for name, start, rep in FACE: strip(t, name, start, repeat=rep, hold=(name == "yeux_fermes"))
    ad.use_nla = True

    # ---------------- caméra : travellings doux, personnage au tiers gauche
    cam = bpy.data.objects["Camera"]; tgt = bpy.data.objects["Cible_camera"]
    cam.data.type = 'PERSP'; cam.data.lens = 47; cam.data.clip_start = 0.1
    for o in (cam, tgt):
        if o.animation_data: o.animation_data_clear()
    right = Vector((math.cos(CAM_YAW), -math.sin(CAM_YAW), 0))
    for f, d, zt, s_ in CAM:
        tgt.location = right * s_ + Vector((0, 0, zt))
        cam.location = tgt.location + Vector((-d * math.sin(CAM_YAW), -d * math.cos(CAM_YAW), 0.1 * d))
        tgt.keyframe_insert("location", frame=f); cam.keyframe_insert("location", frame=f)
    sc.camera = cam

    # ---------------- textes, fixés devant la caméra
    for o in [o for o in bpy.data.objects if o.name.startswith("Texte.")]:
        bpy.data.objects.remove(o, do_unlink=True)
    font = None
    for fp in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"):
        if os.path.exists(fp): font = bpy.data.fonts.load(fp, check_existing=True); break
    for i, (body, x, y, size, color, f_in, f_out) in enumerate(TEXTS):
        m = M.get("Texte_" + color) or M.new("Texte_" + color)
        m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = tuple(hex2lin(color)) + (1,); nt.links.new(em.outputs[0], out.inputs[0])
        cu = bpy.data.curves.new("Texte.%d" % i, 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'LEFT'; cu.align_y = 'CENTER'
        if font: cu.font = font
        cu.materials.append(m)
        ob = bpy.data.objects.new("Texte.%d" % i, cu); sc.collection.objects.link(ob)
        ob.parent = cam; ob.location = (x, y, HUD_Z); ob.visible_shadow = False
        for f, s_ in ((1, 0.0), (f_in - 1, 0.0), (f_in + 3, 1.06), (f_in + 6, 1.0), (f_out, 1.0), (f_out + 3, 0.0)):
            ob.scale = (s_, s_, s_); ob.keyframe_insert("scale", frame=f)
        ob.scale = (0, 0, 0)

    # ---------------- fond clair vu par la caméra (l'éclairage reste blanc), ombre de contact au sol
    w = sc.world; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); mix = nt.nodes.new("ShaderNodeMixShader"); lp = nt.nodes.new("ShaderNodeLightPath")
    light = nt.nodes.new("ShaderNodeBackground"); light.inputs[0].default_value = (1, 1, 1, 1); light.inputs[1].default_value = 0.74
    back = nt.nodes.new("ShaderNodeBackground"); back.inputs[0].default_value = tuple(hex2lin("#E6EFF5")) + (1,); back.inputs[1].default_value = 1.0
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); nt.links.new(light.outputs[0], mix.inputs[1]); nt.links.new(back.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    k = bpy.data.lights["Cle"]; k.energy = 560; k.size = 14
    bpy.data.lights["Debouchage"].energy = 90; bpy.data.lights["Contre"].energy = 60
    fwd = Vector((math.sin(CAM_YAW), math.cos(CAM_YAW), 0)); rgt = fwd.cross(Vector((0, 0, 1))).normalized(); c = Vector((0, 0, 2.0))
    bpy.data.objects["Lumiere_cle"].location = c - fwd * 7.5 - rgt * 6.5 + Vector((0, 0, 6.0))
    bpy.data.objects["Lumiere_debouchage"].location = c - fwd * 6.0 + rgt * 6.0 + Vector((0, 0, 0.5))
    bpy.data.objects["Lumiere_contre"].location = c + fwd * 6.0 + rgt * 3.0 + Vector((0, 0, 4.0))
    sol = bpy.data.objects.get("Sol_ombre")
    if sol: sol.hide_render = False; sol.location = (0, -0.05, 0.004)
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
    sc.render.fps = 24
    sc.eevee.taa_render_samples = 16
    try: sc.eevee.use_raytracing = True
    except Exception: pass


def still(frame, path, scale=50):
    sc.render.resolution_percentage = scale
    try: sc.render.image_settings.media_type = 'IMAGE'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'
    sc.frame_set(frame); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.render.resolution_percentage = 100


def render_video(path):
    try: sc.render.image_settings.media_type = 'VIDEO'
    except Exception: pass
    sc.render.image_settings.file_format = 'FFMPEG'
    ff = sc.render.ffmpeg
    ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.ffmpeg_preset = 'GOOD'; ff.gopsize = 24
    ff.audio_codec = 'NONE'
    sc.frame_start, sc.frame_end = 1, FRAMES
    sc.render.filepath = path
    bpy.ops.render.render(animation=True)


result = {"images": FRAMES}


def hold_last_frame(src, dst, seconds=4):
    """Rallonge une vidéo déjà rendue en tenant sa dernière image (remontage seul, sans nouveau rendu 3D)."""
    ms = bpy.data.scenes.new("Montage")
    st = ms.sequence_editor_create().strips.new_movie("presentation", src, 1, 1)
    st.frame_final_duration = st.frame_final_duration + int(seconds * 24)
    ms.frame_start, ms.frame_end = 1, st.frame_final_duration
    r = ms.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = 1280, 720, 100, 24
    r.use_sequencer = True
    try: r.image_settings.media_type = 'VIDEO'
    except Exception: pass
    r.image_settings.file_format = 'FFMPEG'
    ff = r.ffmpeg; ff.format = 'MPEG4'; ff.codec = 'H264'; ff.constant_rate_factor = 'HIGH'; ff.gopsize = 24; ff.audio_codec = 'NONE'
    ms.view_settings.view_transform = 'Standard'
    r.filepath = dst
    bpy.ops.render.render(animation=True, scene="Montage")
    bpy.data.scenes.remove(ms)
