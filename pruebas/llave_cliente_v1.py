# llave_cliente.py
import urllib.request, urllib.parse

HOST = "10.242.43.135"  # IP ZeroTier de la RPi
PORT = 8088
TOKEN = "MI_CLAVE"
TOKEN_ACTIVO = False    # ← por defecto apagado

def activar_token():
    global TOKEN_ACTIVO
    TOKEN_ACTIVO = True
    print("[HTTP] Token ACTIVADO (se permiten acciones).")

def desactivar_token():
    global TOKEN_ACTIVO
    TOKEN_ACTIVO = False
    print("[HTTP] Token DESACTIVADO (no se permiten acciones).")

def call(action: str):
    if not TOKEN_ACTIVO:
        print("[HTTP] Token inactivo, no se permite enviar acción:", action)
        return
    path = "/status" if action == "status" else "/set"
    qs = urllib.parse.urlencode({"action": action, "token": TOKEN})
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
