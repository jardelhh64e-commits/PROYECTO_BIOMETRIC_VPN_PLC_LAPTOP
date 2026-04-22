import time
import numpy as np
import snap7
from snap7.util import get_bool, set_bool
from snap7.types import Areas

PLC_IP = "192.168.0.1"
RACK, SLOT = 0, 1

DB_NUM = 1
CMD_BYTE, CMD_BIT = 0, 0   # DB1.DBX0.0

N = 50
Q_TIMEOUT_S = 1.5
POLL_S = 0.05

def p95(arr):
    arr = np.array(arr, dtype=float)
    return float(np.percentile(arr, 95)) if len(arr) else 0.0

client = snap7.client.Client()
client.connect(PLC_IP, RACK, SLOT)

def write_cmd(value: bool):
    data = bytearray(client.db_read(DB_NUM, CMD_BYTE, 1))
    set_bool(data, 0, CMD_BIT, value)
    client.db_write(DB_NUM, CMD_BYTE, data)

def read_cmd():
    data = bytearray(client.db_read(DB_NUM, CMD_BYTE, 1))
    return get_bool(data, 0, CMD_BIT)

def read_q0_0():
    data = client.read_area(Areas.PA, 0, 0, 1)  # Outputs byte 0
    return get_bool(bytearray(data), 0, 0)      # bit 0 => Q0.0

put_ms, get_ms, e2e_ms = [], [], []
ok_put_cnt = ok_get_cnt = ok_e2e_cnt = 0

for _ in range(N):
    t0 = time.perf_counter()

    ok_put = True
    try:
        write_cmd(True)
    except Exception:
        ok_put = False
    t1 = time.perf_counter()
    put_ms.append((t1 - t0) * 1000)

    ok_get = True
    try:
        _ = read_cmd()
    except Exception:
        ok_get = False
    t2 = time.perf_counter()
    get_ms.append((t2 - t1) * 1000)

    ok_e2e = False
    if ok_put:
        t_wait = time.perf_counter()
        while (time.perf_counter() - t_wait) <= Q_TIMEOUT_S:
            try:
                if read_q0_0():
                    ok_e2e = True
                    break
            except Exception:
                pass
            time.sleep(POLL_S)

    t3 = time.perf_counter()
    e2e_ms.append((t3 - t0) * 1000)

    ok_put_cnt += int(ok_put)
    ok_get_cnt += int(ok_get)
    ok_e2e_cnt += int(ok_put and ok_get and ok_e2e)

    try:
        write_cmd(False)
    except Exception:
        pass
    time.sleep(0.2)

client.disconnect()

print(f"Put éxito: {ok_put_cnt}/{N} = {ok_put_cnt/N*100:.2f}%")
print(f"Get éxito: {ok_get_cnt}/{N} = {ok_get_cnt/N*100:.2f}%")
print(f"E2E éxito (con Q0.0): {ok_e2e_cnt}/{N} = {ok_e2e_cnt/N*100:.2f}%")

print(f"Put ms: prom={np.mean(put_ms):.2f}, p95={p95(put_ms):.2f}")
print(f"Get ms: prom={np.mean(get_ms):.2f}, p95={p95(get_ms):.2f}")
print(f"E2E ms: prom={np.mean(e2e_ms):.2f}, p95={p95(e2e_ms):.2f}")
