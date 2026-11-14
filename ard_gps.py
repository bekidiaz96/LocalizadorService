import os
import serial
import time
from dotenv import load_dotenv
from logger_setup import setup_logger
from db_handler import init_db, insertar_registro
from sync_service import obtener_o_generar_vehiculo_id

load_dotenv()

# Inicialización
logger = setup_logger()
init_db()

# Obtener ID dinámico (desde archivo local o servidor)
vehiculo_id = obtener_o_generar_vehiculo_id()

# Configuración Serial
arduino_port = os.getenv("ARDUINO_PORT", "/dev/ttyAMA0")
gps_port = os.getenv("GPS_PORT", "/dev/ttyAMA4")
baud_rate = int(os.getenv("BAUD_RATE", 9600))

arduino_serial = serial.Serial(arduino_port, baud_rate, timeout=1)
gps_serial = serial.Serial(gps_port, baud_rate, timeout=1)

def convertir_nmea_a_decimal(nmea_lat, lat_dir, nmea_lon, lon_dir):
    lat_grados = int(nmea_lat[:2])
    lat_min = float(nmea_lat[2:])
    lat_decimal = lat_grados + (lat_min / 60)
    if lat_dir == "S": lat_decimal *= -1
    
    lon_grados = int(nmea_lon[:3])
    lon_min = float(nmea_lon[3:])
    lon_decimal = lon_grados + (lon_min / 60)
    if lon_dir == "W": lon_decimal *= -1

    return round(lat_decimal, 6), round(lon_decimal, 6)

def leer_gps():
    # Intento de lectura con timeout para no bloquear el proceso
    for _ in range(5):
        line = gps_serial.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('$GPGGA'):
            data = line.split(',')
            if len(data) > 5 and data[2] and data[4]:
                return convertir_nmea_a_decimal(data[2], data[3], data[4], data[5])
    return None, None

print(f"Iniciando captura de datos para el Vehículo ID: {vehiculo_id}")

while True:
    try:
        # 1. Intentar leer del Arduino
        arduino_line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
        
        # 2. Detectar si la lectura está vacía (silencio del Arduino)
        if not arduino_line:
            logger.warning("No se están recibiendo datos del Arduino (Timeout de 1s).")
            print("[WARNING] No hay datos. ¿Está el Arduino encendido y enviando por el puerto correcto?")
            time.sleep(2) # Pausa breve para no inundar la terminal
            continue

        # 3. Imprimir el dato crudo para ver si llega basura o caracteres extraños
        print(f"[DEBUG] Línea cruda recibida del Arduino: '{arduino_line}'")

        datos = arduino_line.split(',')
        
        # 4. Validar que vengan todos los datos esperados
        if len(datos) < 6:
            logger.warning(f"Trama incompleta recibida (esperaba al menos 6 valores, llegaron {len(datos)}): {arduino_line}")
            continue

        try:
            temperatura_interior1 = float(datos[0])
            temperatura_interior2 = float(datos[1])
            temperatura_arduino = float(datos[2])
            humedad = float(datos[3])
        except ValueError:
            logger.warning(f"Valores no convertibles a float: {datos[:4]}")
            continue

        puerta1 = 0 if datos[4].strip().upper() == 'CERRADA' else 1
        puerta2 = 0 if datos[5].strip().upper() == 'CERRADA' else 1

        # Leer coordenadas GPS y validar
        lat, lon = leer_gps()
        if lat is None or lon is None:
            logger.warning("GPS inválido o sin señal. Omitiendo registro.")
            continue

        ubicacion = f"{lat},{lon}"
        print(f"[DEBUG] Ubicacion: '{ubicacion}'")
        
        registro = (
            vehiculo_id, temperatura_arduino, temperatura_interior1,
            temperatura_interior2, puerta1, puerta2, humedad, ubicacion
        )

        insertar_registro(registro)
        logger.info(f"Registro insertado: {registro}")
        time.sleep(10)

    except serial.SerialException as e:
        logger.error(f"Se perdió la conexión física con el dispositivo serial: {e}")
        print("[ERROR CRÍTICO] Dispositivo desconectado. Verifica los cables.")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("Detenido por el usuario.")
        arduino_serial.close()
        gps_serial.close()
        break
    except Exception as e:
        logger.error(f"Error inesperado en bucle principal: {e}")
        time.sleep(2)