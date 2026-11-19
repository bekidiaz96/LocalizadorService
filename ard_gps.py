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
    if lat_dir == "S":
        lat_decimal *= -1

    lon_grados = int(nmea_lon[:3])
    lon_min = float(nmea_lon[3:])
    lon_decimal = lon_grados + (lon_min / 60)
    if lon_dir == "W":
        lon_decimal *= -1

    return round(lat_decimal, 6), round(lon_decimal, 6)

def leer_gps():
    # Leer hasta 15 líneas para cubrir un paquete NMEA completo (~11-13 líneas/seg)
    for _ in range(15):
        line = gps_serial.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue

        data = line.split(',')

        # 1. Tramas GGA ($GNGGA / $GPGGA)
        if line.startswith(('$GNGGA', '$GPGGA')):
            # data[6] es la calidad del Fix ('0' = sin señal, '1' o '2' = válido)
            if len(data) > 6 and data[2] and data[4] and data[6] != '0':
                return convertir_nmea_a_decimal(data[2], data[3], data[4], data[5])

        # 2. Tramas GLL ($GNGLL / $GPGLL)
        elif line.startswith(('$GNGLL', '$GPGLL')):
            # data[6] es el estado ('A' = Activo/Válido, 'V' = Inválido)
            if len(data) > 6 and data[1] and data[3] and data[6] == 'A':
                return convertir_nmea_a_decimal(data[1], data[2], data[3], data[4])

        # 3. Tramas RMC ($GNRMC / $GPRMC)
        elif line.startswith(('$GNRMC', '$GPRMC')):
            # data[2] es el estado ('A' = Activo/Válido, 'V' = Inválido)
            if len(data) > 6 and data[3] and data[5] and data[2] == 'A':
                return convertir_nmea_a_decimal(data[3], data[4], data[5], data[6])

    return None, None

print(f"Iniciando captura de datos para el Vehículo ID: {vehiculo_id}")

while True:
    try:
        # Limpiar búferes seriales para leer siempre datos en tiempo real
        arduino_serial.reset_input_buffer()
        gps_serial.reset_input_buffer()

        # 1. Intentar leer del Arduino (descartar posible línea cortada tras limpiar búfer)
        arduino_line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
        if not arduino_line or len(arduino_line.split(',')) < 6:
            arduino_line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()

        # 2. Detectar si la lectura está vacía (silencio del Arduino)
        if not arduino_line:
            logger.warning("No se están recibiendo datos del Arduino (Timeout de 1s).")
            print("[WARNING] No hay datos. ¿Está el Arduino encendido y enviando por el puerto correcto?")
            time.sleep(2)
            continue

        # 3. Imprimir el dato crudo para depuración
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

        # 5. Leer coordenadas GPS y validar
        lat, lon = leer_gps()
        if lat is None or lon is None:
            logger.warning("GPS inválido o sin señal. Omitiendo registro.")
            print("[WARNING] GPS sin señal válida aún. Omitiendo guardado...")
            continue

        ubicacion = f"{lat},{lon}"
        print(f"[DEBUG] Ubicacion: '{ubicacion}'")

        registro = (
            vehiculo_id, temperatura_arduino, temperatura_interior1,
            temperatura_interior2, puerta1, puerta2, humedad, ubicacion
        )

        insertar_registro(registro)
        logger.info(f"Registro insertado: {registro}")
        print(f"[SUCCESS] Registro guardado en SQLite: {registro}")
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
