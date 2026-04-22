import snap7
from snap7.util import set_bool

# Configuración de conexión
PLC_IP = '192.168.0.1'   # Dirección IP del PLC (real o virtual con NetToPLCSim/Advanced)
RACK = 0                 # Generalmente 0 en S7-1200
SLOT = 1                 # Generalmente 1 en S7-1200

# Crear cliente Snap7
plc = snap7.client.Client()

try:
    plc.connect(PLC_IP, RACK, SLOT)
except Exception as e:
    print(f"Error al conectar con el PLC: {e}")
    exit()

if plc.get_connected():
    print("✅ Conexión exitosa al PLC")

    # Solicitar entrada del usuario
    entrada = input("Ingresa 1 para True o 0 para False: ").strip()

    if entrada == "1":
        valor_bool = True
    elif entrada == "0":
        valor_bool = False
    else:
        print("Entrada no válida. Debes ingresar 1 o 0.")
        plc.disconnect()
        exit()

    # Dirección de la variable en TIA Portal
    DB_NUMBER = 1       # DB1
    START_OFFSET = 0    # Byte 0
    BIT_OFFSET = 0      # Bit 0 (DB1.DBX0.0)

    # Crear buffer con el valor booleano
    data = bytearray(1)
    set_bool(data, 0, BIT_OFFSET, valor_bool)

    # Lectura previa
    try:
        result = plc.db_read(DB_NUMBER, START_OFFSET, 1)
        print("Lectura de prueba:", result)
    except Exception as e:
        print("Error al leer la DB:", e)

    # Escritura
    try:
        plc.db_write(DB_NUMBER, START_OFFSET, data)
        print(f"✅ Valor {valor_bool} escrito en DB{DB_NUMBER}.DBX{START_OFFSET}.{BIT_OFFSET}")
    except Exception as e:
        print(f"Error al escribir en la DB: {e}")

    # Cerrar conexión
    plc.disconnect()
else:
    print("❌ No se pudo conectar al PLC.")
