import urllib.request, urllib.parse

HOST = "10.242.43.135"  # IP ZeroTier de la RPi
PORT = 8088
TOKEN = "MI_CLAVE"

def call(action):
    path = "/status" if action == "status" else "/set"
    qs = urllib.parse.urlencode({"action": action, "token": TOKEN})
    url = f"http://{HOST}:{PORT}{path}?{qs}"
    with urllib.request.urlopen(url, timeout=8) as r:
        print(r.read().decode())

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
1