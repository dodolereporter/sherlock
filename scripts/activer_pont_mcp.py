# À lancer une fois dans la console Python de Blender :  exec(open(r"<ce fichier>").read())
# Réactive l'add-on MCP (déjà présent sur le disque), démarre son pont sur localhost:9876 et enregistre les préférences,
# pour que le pont reparte tout seul aux prochains lancements de Blender.
import bpy, sys, traceback

_p = bpy.context.preferences
_mod = "bl_ext.lab_blender_org.mcp"
_fait = []
try:
    if not any(r.module == "lab_blender_org" for r in _p.extensions.repos):
        _p.extensions.repos.new(name="Blender Lab", module="lab_blender_org", remote_url="https://lab.blender.org/")
        _fait.append("dépôt d'extensions Blender Lab déclaré")
    if not _p.system.use_online_access:
        _p.system.use_online_access = True          # exigé par l'add-on, même pour un pont purement local
        _fait.append("accès en ligne autorisé")
    if _mod not in _p.addons:
        bpy.ops.preferences.addon_enable(module=_mod)
        _fait.append("add-on MCP activé")
    _srv = sys.modules[_mod + ".mcp_to_blender_server"]
    if not _srv.is_running():
        bpy.ops.blmcp.server_start()
        _fait.append("pont démarré")
    bpy.ops.wm.save_userpref()
    print("PONT MCP :", "EN MARCHE" if _srv.is_running() else "ARRÊTÉ", "|", ", ".join(_fait) or "rien à changer", "| préférences enregistrées")
except Exception:
    print("PONT MCP : ÉCHEC après [%s]" % ", ".join(_fait))
    traceback.print_exc()
