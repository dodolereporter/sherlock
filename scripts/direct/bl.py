# Envoie du code Python au Blender ouvert, par le pont de l'add-on MCP (même protocole que le serveur blender-mcp :
# JSON {"type": "execute", "code": ..., "strict_json": false} terminé par un octet nul, sur localhost:9876).
# Usage : python bl.py <fichier.py>        exécute le fichier
#         python bl.py -c "code"           exécute le code
#         python bl.py --wait [minutes]    attend la fin du travail lancé par shl.start() et affiche son état
import json, socket, sys, time

def send(code, timeout=280.0):
    req = json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(("localhost", 9876))
        s.sendall(req.encode("utf-8"))
        buf = bytearray()
        while b"\0" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
    return json.loads(bytes(buf).partition(b"\0")[0].decode("utf-8"))

STATE = "import sys; st = sys.modules['shl'].state; result = {k: st.get(k) for k in ('done', 'err', 'step', 'n', 'result', 'dt')}"

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "--wait":
        fin = time.time() + 60 * float(sys.argv[2] if len(sys.argv) > 2 else 8)
        last = None
        while True:
            try:
                st = send(STATE, timeout=120.0).get("result", {})
            except OSError as ex:
                st = {"done": False, "step": "(pont occupé : %s)" % ex}
            if st.get("step") != last:
                last = st.get("step"); print("%s  pas %s : %s" % (time.strftime("%H:%M:%S"), st.get("n"), last), flush=True)
            if st.get("done"):
                print(json.dumps(st, ensure_ascii=False, indent=1)[:6000]); sys.exit(1 if st.get("err") else 0)
            if time.time() > fin:
                print("toujours en cours"); sys.exit(3)
            time.sleep(2.0)
    code = sys.argv[2] if sys.argv[1] == "-c" else open(sys.argv[1], encoding="utf-8").read()
    try:
        r = send(code)
    except OSError as ex:
        print("INJOIGNABLE :", ex); sys.exit(2)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:6000])
    sys.exit(0 if r.get("status") == "ok" else 1)
