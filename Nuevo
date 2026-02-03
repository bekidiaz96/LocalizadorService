import serial
import time
import re
from logger_setup import setup_logger  ## guardar eventos de la ejecucion ./logs
from db_handler import init_db, insertar_registro ## insertar en la base de datos local SQLite
# Inicializar logger
logger = setup_logger()
init_db()
# Serial del Arduino (ajustá si estás usando otro UART)
arduino_serial = serial.Serial("/dev/ttyAMA0", 9600, timeout=1)

# Serial del GPS (usando UART4)
gps_serial = serial.Serial("/dev/ttyAMA4", 9600, timeout=1)

vehiculo_id = 2

def convertir_nmea_a_decimal(nmea_lat, lat_dir, nmea_lon, lon_dir):
    # Latitud
    lat_grados = int(nmea_lat[:2])
    lat_min = float(nmea_lat[2:])
    lat_decimal = lat_grados + (lat_min / 60)
    if lat_dir == "S":
        lat_decimal *= -1

    # Longitud
    lon_grados = int(nmea_lon[:3])
    lon_min = float(nmea_lon[3:])
    lon_decimal = lon_grados + (lon_min / 60)
    if lon_dir == "W":
        lon_decimal *= -1

    return round(lat_decimal, 6), round(lon_decimal, 6)

def leer_gps():
    while True:
        line = gps_serial.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('$GPGGA'):
            data = line.split(',')
            if data[2] and data[4]:  # hay datos válidos
                lat, lat_dir = data[2], data[3]
                lon, lon_dir = data[4], data[5]
                return convertir_nmea_a_decimal(lat, lat_dir, lon, lon_dir)
        time.sleep(0.1)

print("Iniciando lectura...")

while True:
    try:
        # Leer línea del Arduino
        arduino_line = arduino_serial.readline().decode('utf-8', errors='ignore').strip()
        if not arduino_line:
            continue
        
        datos = arduino_line.split(',')
        print("Datos Aaaarduino:", arduino_line, len(datos))

        # Validar estructura
        #if 6 > 4:
        #    logger.warning(f"Línea inválida: {arduino_line}")
        #   continue

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
        if lat is None or lon is None or (lat == 0 and lon == 0):
            logger.warning("GPS inválido o sin señal.")
            continue

        ubicacion = f"{lat},{lon}"

        # Crear y registrar el dato válido
        registro = (
            vehiculo_id,
            temperatura_arduino,
            temperatura_interior1,
            temperatura_interior2,
            puerta1,
            puerta2,
            humedad,    
            ubicacion
        )

        insertar_registro(registro)
        logger.info(f"Registro insertado: {registro}")

        print("Esperando 10 segundos...\n")
        time.sleep(10)
    except Exception as e:
        logger.error(f"Error: {e}")
    except KeyboardInterrupt:
        print("Detenido por el usuario.")
        arduino_serial.close()
        gps_serial.close()
        break
