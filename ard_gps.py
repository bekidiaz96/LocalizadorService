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

# Limpiar cualquier dato residual acumulado antes de iniciar el ciclo
arduino_serial.reset_input_buffer()
gps_serial.reset_input_buffer()


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
    # Descartar tramas viejas del GPS para capturar la posición exacta de este instante
    gps_serial.reset_input_buffer()

    # Leer hasta 15 líneas para cubrir un paquete NMEA completo (~11-13 líneas/seg)
    for _ in range(15):
        line = gps_serial.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue

        data = line.split(',')

        # 1. Tramas GGA ($GNGGA / $GPGGA)
        if line.startswith(('$GNGGA', '$GPGGA')):
            if len(data) > 6 and data[2] and data[4] and data[6] != '0':
                return convertir_nmea_a_decimal(data[2], data[3], data[4], data[5])

        # 2. Tramas GLL ($GNGLL / $GPGLL)
        elif line.startswith(('$GNGLL', '$GPGLL')):
            if len(data) > 6 and data[1] and data[3] and data[6] == 'A':
                return convertir_nmea_a_decimal(data[1], data[2], data[3], data[4])

        # 3. Tramas RMC ($GNRMC / $GPRMC)
        elif line.startswith(('$GNRMC', '$GPRMC')):
            if len(data) > 6 and data[3] and data[5] and data[2] == 'A':
                return convertir_nmea_a_decimal(data[3], data[4], data[5], data[6])

    return None, None


print(f"Iniciando captura orientada a eventos para el Vehículo ID: {vehiculo_id}")

while True:
    try:
        # 1. Esperar de forma pasiva hasta que el Arduino envíe datos (timeout=1s)
        # No se usa reset_input_buffer() aquí para no perder cambios rápidos de puerta
        arduino_line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()

        # Si pasaron 1s sin datos (normal entre intervalos de 10s o con switch apagado), seguir esperando
        if not arduino_line:
            continue

        print(f"[DEBUG] Línea recibida del Arduino: '{arduino_line}'")

        # Capturar la fecha y hora exacta en el instante en que llega el dato del Arduino
        hora_captura = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[DEBUG] ({hora_captura}) Línea recibida del Arduino: '{arduino_line}'")

        # 2. Detectar mensajes de control del switch físico del Arduino
        if arduino_line in ("MONITOREO ACTIVADO", "MONITOREO DESACTIVADO"):
            logger.info(f"Estado del sistema Arduino: {arduino_line}")
            print(f"[INFO] {arduino_line}")
            continue

        # 3. Validar estructura CSV (temp1,temp2,tempDHT,humDHT,puerta1,puerta2)
        datos = arduino_line.split(',')
        if len(datos) < 6:
            logger.warning(f"Trama incompleta recibida: {arduino_line}")
            continue

        try:
            temperatura_interior1 = float(datos[0])
            temperatura_interior2 = float(datos[1])
            temperatura_arduino = float(datos[2])
            humedad = float(datos[3])
            # El Arduino envía 1 (cerrado) o 0 (abierto) directamente
            puerta1 = int(datos[4].strip())
            puerta2 = int(datos[5].strip())
        except ValueError:
            logger.warning(f"Valores no numéricos en trama Arduino: {datos[:6]}")
            continue

        # 4. Capturar coordenadas GPS en tiempo real para este evento
        lat, lon = leer_gps()
        if lat is None or lon is None:
            logger.warning("GPS inválido o sin señal. Omitiendo registro.")
            print("[WARNING] GPS sin señal válida aún. Omitiendo guardado...")
            continue

        ubicacion = f"{lat},{lon}"
        print(f"[DEBUG] Ubicacion: '{ubicacion}' | Puertas: P1={puerta1}, P2={puerta2}")

        registro = (
            vehiculo_id, temperatura_arduino, temperatura_interior1,
            temperatura_interior2, puerta1, puerta2, humedad, ubicacion, hora_captura
        )

        insertar_registro(registro)
        logger.info(f"Registro insertado: {registro}")
        print(f"[SUCCESS] Registro guardado en SQLite: {registro}")

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
        time.sleep(1)
