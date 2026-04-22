import snap7
from snap7.util import *
from snap7.types import *

PLC_IP = '192.168.0.1'  # cambia por la IP real
RACK = 0
SLOT = 1

plc = snap7.client.Client()
plc.connect(PLC_IP, RACK, SLOT)

if plc.get_connected():
    print("✅ Conexión exitosa con el PLC")
else:
    print("❌ No se pudo conectar al PLC")

DB_NUMBER = 1

def write_button(db_num, byte_index, bit_index, value):
    data = plc.db_read(db_num, 0, 1)
    set_bool(data, byte_index, bit_index, value)
    plc.db_write(db_num, 0, data)

def read_button(db_num, byte_index, bit_index):
    data = plc.db_read(db_num, 0, 1)
    return get_bool(data, byte_index, bit_index)

while True:
    print("\n--- MENÚ ---")
    print("1 = Toggle Button1")
    print("2 = Toggle Button2")
    print("3 = Toggle Button3")
    print("0 = Apagar todos")
    print("q = Salir")
    op = input("Ingrese opción: ")

    if op == '1':
        estado_actual = read_button(DB_NUMBER, 0, 0)
        nuevo_estado = not estado_actual
        write_button(DB_NUMBER, 0, 0, nuevo_estado)
        print(f"Button1 ahora está {'ENCENDIDO' if nuevo_estado else 'APAGADO'}")

    elif op == '2':
        estado_actual = read_button(DB_NUMBER, 0, 1)
        nuevo_estado = not estado_actual
        write_button(DB_NUMBER, 0, 1, nuevo_estado)
        print(f"Button2 ahora está {'ENCENDIDO' if nuevo_estado else 'APAGADO'}")

    elif op == '3':
        estado_actual = read_button(DB_NUMBER, 0, 2)
        nuevo_estado = not estado_actual
        write_button(DB_NUMBER, 0, 2, nuevo_estado)
        print(f"Button3 ahora está {'ENCENDIDO' if nuevo_estado else 'APAGADO'}")

    elif op == '0':
        for i in range(3):
            write_button(DB_NUMBER, 0, i, False)
        print("Todos los botones APAGADOS")

    elif op.lower() == 'q':
        print("👋 Saliendo del programa...")
        break

    else:
        print("⚠️ Opción inválida. Intente nuevamente.")

    # Mostrar estado actual
    print("\nEstado actual:")
    for i in range(3):
        val = read_button(DB_NUMBER, 0, i)
        print(f"Button{i+1}: {'ON' if val else 'OFF'}")

plc.disconnect()
