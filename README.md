# PROYECTO_BIOMETRIC_VPN_PLC_LAPTOP

Sistema de autenticacion biometrica facial que habilita el control remoto
de un PLC Siemens S7 a traves de una VPN ZeroTier. Corresponde al lado
**laptop/cliente** del sistema descrito en el paper LACCEI 2026.

## Arquitectura

```
Webcam -> FaceMesh (MediaPipe) -> Clasificador Keras
      -> Liveness (parpadeo + giro)
      -> Anti-spoofing por desafio-respuesta
      -> Gate HMAC-SHA256 (ts + nonce + firma)
      -> HTTP sobre ZeroTier
      -> Gateway Raspberry Pi
      -> PLC Siemens S7 via Snap7
```

## Requisitos

- Python 3.10 o superior
- Webcam
- Red ZeroTier configurada, con una Raspberry Pi actuando como gateway
- Acceso al PLC Siemens desde la red del gateway

## Instalacion

```bash
# 1. Clonar el repo
git clone https://github.com/jardelhh64e-commits/PROYECTO_BIOMETRIC_VPN_PLC_LAPTOP.git
cd PROYECTO_BIOMETRIC_VPN_PLC_LAPTOP

# 2. Crear entorno virtual
python -m venv myenv
myenv\Scripts\activate            # Windows
# source myenv/bin/activate       # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Configuracion (paso obligatorio)

Las credenciales NO viven en el codigo. Se leen desde un archivo `.env`
local que NUNCA se sube al repositorio.

```bash
# Copiar la plantilla
copy .env.example .env             # Windows
# cp .env.example .env             # Linux / macOS
```

Editar `.env` y reemplazar los valores con los tuyos:

| Variable        | Descripcion                                                         |
|-----------------|---------------------------------------------------------------------|
| `HMAC_KEY`      | Clave pre-compartida entre laptop y gateway RPi. Debe ser identica. |
| `ZEROTIER_HOST` | IP ZeroTier de la Raspberry Pi que actua de gateway (ej. 10.x.x.x). |
| `ZEROTIER_PORT` | Puerto HTTP del gateway. Default: `8088`.                           |

Si no creas `.env`, el sistema arranca pero no se conecta al gateway
(usa valores placeholder seguros).

## Ejecutar

```bash
python main.py
```

Flujo:
1. Se abre la camara y arranca la deteccion facial.
2. Cuando la confianza de reconocimiento se mantiene alta por 5 segundos
   y se supera el modulo anti-spoofing, aparece un menu de consola:
   - `1` = encender PLC
   - `0` = apagar PLC
   - `2` = consultar estado
3. Cada comando se firma con HMAC-SHA256 (ts + nonce + sig) y se envia
   al gateway por ZeroTier.

## Modulos principales

| Archivo               | Rol                                                          |
|-----------------------|--------------------------------------------------------------|
| `main.py`             | Loop principal, maquina de estados, menu consola             |
| `config.py`           | Umbrales biometricos y parametros de camara                  |
| `classifier.py`       | Wrapper Keras para reconocimiento facial                     |
| `liveness.py`         | Prueba de vida: EAR (parpadeo) + yaw (giro de cabeza)        |
| `mediapipe_face_mesh.py` | Landmarks faciales con MediaPipe                          |
| `antispoof_video.py`  | Desafio-respuesta anti replay de video pregrabado            |
| `llave_cliente.py`    | Cliente HTTP con firma HMAC hacia el gateway ZeroTier        |
| `plc_client.py`       | Cliente Snap7 (solo para pruebas locales con el PLC)         |
| `ui.py`               | Overlays en pantalla                                         |
| `keras_model.h5`      | Modelo entrenado de reconocimiento facial                    |
| `labels.txt`          | Clases del modelo                                            |

## Seguridad

- El codigo NO contiene claves hardcoded. Todas viven en `.env` (ignorado).
- El protocolo HMAC incluye ventana temporal (~30s) y nonce anti-replay.
- Ver paper LACCEI 2026 para el analisis completo del esquema.

## Gateway Raspberry Pi

El codigo del gateway (servidor HTTP que recibe comandos, valida HMAC y
maneja iptables para abrir/cerrar el tunel al PLC) vive en un repositorio
aparte.

## Licencia

Uso academico.
