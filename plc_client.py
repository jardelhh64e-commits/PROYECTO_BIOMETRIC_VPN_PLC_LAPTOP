"""
plc_client.py — Wrapper mínimo para probar conexión al PLC (snap7).
- connect() -> True/False
- is_connected() -> bool
- disconnect()
No escribe bits/DB. Solo reporta estado y errores de conexión.
"""
class PLCClient:
    def __init__(self, ip: str, rack: int, slot: int):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = None
        self._available = True

        try:
            import snap7  # type: ignore
            self._snap7 = snap7
        except Exception as e:
            print(f"[PLC] snap7 no disponible: {e}")
            self._available = False
            return

        try:
            self.client = self._snap7.client.Client()
        except Exception as e:
            print(f"[PLC] Error creando cliente Snap7: {e}")
            self._available = False

    def connect(self) -> bool:
        if not self._available or self.client is None:
            print("[PLC] Librería snap7 no disponible o cliente no creado.")
            return False
        try:
            self.client.connect(self.ip, self.rack, self.slot)
        except Exception as e:
            print(f"[PLC] No se pudo conectar al PLC: {e}")
            return False

        if self.client.get_connected():
            print("[PLC] Conexión exitosa al PLC.")
            return True
        else:
            print("[PLC] No se pudo conectar al PLC (get_connected=False).")
            return False

    def is_connected(self) -> bool:
        try:
            return bool(self.client and self.client.get_connected())
        except Exception:
            return False

    def disconnect(self):
        try:
            if self.client:
                self.client.disconnect()
                print("[PLC] Desconectado.")
        except Exception:
            pass
