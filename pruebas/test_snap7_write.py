import snap7
from snap7.util import get_bool, set_bool

PLC_IP = "192.168.0.1"
RACK = 0
SLOT = 1

DB_NUM = 1
BYTE_OFFSET = 0
BIT_OFFSET = 0  # DB1.DBX0.0

def main():
    plc = snap7.client.Client()
    plc.connect(PLC_IP, RACK, SLOT)
    print("PLC conectado:", plc.get_connected())

    try:
        while True:
            cmd = input("Ingresa 1(TRUE), 0(FALSE) o q(salir): ").strip().lower()

            if cmd == "q":
                print("Saliendo...")
                break

            if cmd not in ("0", "1"):
                print("❌ Solo 1, 0 o q")
                continue

            estado = (cmd == "1")

            # Leer 1 byte, modificar solo el bit, y escribirlo de vuelta
            data = plc.db_read(DB_NUM, BYTE_OFFSET, 1)
            set_bool(data, 0, BIT_OFFSET, estado)
            plc.db_write(DB_NUM, BYTE_OFFSET, data)

            # Verificar
            verif = plc.db_read(DB_NUM, BYTE_OFFSET, 1)
            resultado = get_bool(verif, 0, BIT_OFFSET)
            print("✅ PLC DB{}.DBX{}.{} = {}".format(DB_NUM, BYTE_OFFSET, BIT_OFFSET, resultado))

    finally:
        plc.disconnect()
        print("PLC desconectado:", plc.get_connected())

if __name__ == "__main__":
    main()
