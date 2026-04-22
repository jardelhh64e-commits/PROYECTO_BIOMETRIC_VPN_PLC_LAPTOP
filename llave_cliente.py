# llave_cliente.py
import urllib.request, urllib.parse
import hmac, hashlib, time, uuid
import os
from pathlib import Path

# ── Cargar variables desde .env si existe (sin dependencias externas) ──
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

HOST = os.environ.get("ZEROTIER_HOST", "127.0.0.1")
PORT = int(os.environ.get("ZEROTIER_PORT", "8088"))
SHARED_KEY = os.environ.get("HMAC_KEY", "CAMBIAME").encode()
TOKEN_ACTIVO = False            # por defecto apagado; solo True tras biometría válida

def activar_token():
    global TOKEN_ACTIVO
    TOKEN_ACTIVO = True
    print("[HTTP] Token ACTIVADO (se permiten acciones).")

def desactivar_token():
    global TOKEN_ACTIVO
    TOKEN_ACTIVO = False
    print("[HTTP] Token DESACTIVADO (no se permiten acciones).")

def _firmar(action: str):
    ts    = str(int(time.time()))
    nonce = uuid.uuid4().hex
    msg   = f"{action}{ts}{nonce}".encode()
    sig   = hmac.new(SHARED_KEY, msg, hashlib.sha256).hexdigest()
    return ts, nonce, sig

def call(action: str):
    if not TOKEN_ACTIVO:
        print("[HTTP] Token inactivo, no se permite enviar acción:", action)
        return
    path = "/status" if action == "status" else "/set"
    ts, nonce, sig = _firmar(action)
    qs  = urllib.parse.urlencode({"action": action, "ts": ts, "nonce": nonce, "sig": sig})
    url = f"http://{HOST}:{PORT}{path}?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            print("[HTTP] Respuesta:", r.read().decode(errors="replace"))
    except Exception as e:
        print(f"[HTTP] ERROR llamando a {url} -> {e}")

if __name__ == "__main__":
    while True:
        op = input("\n1=activar, 0=desactivar, 2=status, q=salir: ").strip().lower()
        if op == "1":
            call("on")
        elif op == "0":
            call("off")
        elif op == "2":
            call("status")
        elif op == "q":
            print("Saliendo.")
            break
        else:
            print("Opción inválida.")
