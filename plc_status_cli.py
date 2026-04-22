# plc_status_cli.py
import requests, json, datetime, sys

WEBHOOK_URL = "https://jardel64e.app.n8n.cloud/webhook/plc-status-prod"  # ← NUEVA URL
HTTP_METHOD = "PUT"
TIMEOUT_S = 10

def send_status(value: int):
    assert value in (0, 1)
    headers = {"Content-Type": "application/json"}
    payload = {"status": value, "source": "cli-python"}

    # DEBUG: imprime la URL REAL que estás usando
    print(f"USANDO URL: {WEBHOOK_URL}")

    call = requests.put if HTTP_METHOD.upper() == "PUT" else requests.post
    r = call(WEBHOOK_URL, headers=headers, json=payload, timeout=TIMEOUT_S)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        body = json.dumps(r.json(), ensure_ascii=False)
    except Exception:
        body = r.text
    print(f"[{ts}] Enviado status={value} → HTTP {r.status_code} | Respuesta: {body}")

if __name__ == "__main__":
    while True:
        cmd = input("> ").strip().lower()
        if cmd in ("q","quit","exit"): break
        if cmd in ("0","1"): send_status(int(cmd))
        else: print("Usa 1, 0 o q")
