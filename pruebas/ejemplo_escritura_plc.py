import snap7
from snap7.util import set_bool
from snap7.types import Areas

plc = snap7.client.Client()

# IP DEL PLC o PLCSIM Advanced
plc.connect('192.168.0.10', 0, 1)

# Leer 1 byte del DB1 (byte 0)
data = plc.read_area(
    Areas.DB,   # Área DB
    1,          # DB número 1
    0,          # Byte 0
    1           # Leer 1 byte
)

# =========================
# ACTIVAR → 1
# =========================
set_bool(data, 0, 0, True)  # DBX0.0
plc.write_area(Areas.DB, 1, 0, data)

print("DB1.DBX0.0 ACTIVADO")

# =========================
# DESACTIVAR → 0
# =========================
set_bool(data, 0, 0, False)
plc.write_area(Areas.DB, 1, 0, data)

print("DB1.DBX0.0 DESACTIVADO")

plc.disconnect()
