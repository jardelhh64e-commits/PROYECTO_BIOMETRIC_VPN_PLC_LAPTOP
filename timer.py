"""
timer.py — Timers simples por nombre para rate-limiting de acciones.
"""
import time
from typing import Dict

_last_ts: Dict[str, float] = {}

def should_run(name: str, interval_s: float) -> bool:
    """
    Devuelve True si han pasado al menos `interval_s` segundos desde
    la última vez que se permitió ejecutar este `name`.
    """
    now = time.time()
    last = _last_ts.get(name, 0.0)
    if (now - last) >= interval_s:
        _last_ts[name] = now
        return True
    return False
