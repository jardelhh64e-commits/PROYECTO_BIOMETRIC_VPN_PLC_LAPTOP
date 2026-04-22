import subprocess, re, numpy as np

TARGET = "192.168.0.1"  # ZeroTier Raspberry
COUNT = 300               # prueba rápida (sube a 300 si quieres)
TIMEOUT_MS = 1000         # 1s por ping

cmd = ["ping", "-n", str(COUNT), "-w", str(TIMEOUT_MS), TARGET]

# timeout total aprox: COUNT+20 segundos
out = subprocess.check_output(
    cmd,
    text=True,
    errors="ignore",
    encoding="utf-8",
    timeout=COUNT + 20
)

rtts = []
for line in out.splitlines():
    m = re.search(r"(tiempo|time)[=<]\s*(\d+)\s*ms", line)
    if m:
        rtts.append(int(m.group(2)))

sent = COUNT
recv = len(rtts)
loss = (sent - recv) / sent * 100.0

arr = np.array(rtts, dtype=float)
avg = float(np.mean(arr)) if recv else 0.0
p95 = float(np.percentile(arr, 95)) if recv else 0.0
p99 = float(np.percentile(arr, 99)) if recv else 0.0
jitter = float(np.mean(np.abs(np.diff(arr)))) if recv >= 2 else 0.0

print(f"Target: {TARGET}")
print(f"Sent={sent} Recv={recv} Loss={loss:.2f}%")
print(f"RTT ms: avg={avg:.2f} p95={p95:.2f} p99={p99:.2f} jitter={jitter:.2f}")
