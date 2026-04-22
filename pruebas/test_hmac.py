import urllib.request, urllib.parse
import hmac, hashlib, time, uuid

HOST       = "10.242.43.135"
PORT       = 8088
SHARED_KEY = b"HMAC_UTP_2026"

def _firmar(action):
    ts    = str(int(time.time()))
    nonce = uuid.uuid4().hex
    msg   = f"{action}{ts}{nonce}".encode()
    sig   = hmac.new(SHARED_KEY, msg, hashlib.sha256).hexdigest()
    return ts, nonce, sig

def test(action):
    ts, nonce, sig = _firmar(action)
    qs  = urllib.parse.urlencode({"action": action, "ts": ts, "nonce": nonce, "sig": sig})
    url = f"http://{HOST}:{PORT}/set?{qs}"
    print("URL:", url)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            print("Respuesta:", r.read().decode())
    except Exception as e:
        print("ERROR:", e)

test("status")
