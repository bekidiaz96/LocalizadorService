# sync_service.py
import time
import psycopg2
from db_handler import obtener_no_sincronizados, marcar_como_sincronizado

# Configuración de la base de datos PostgreSQL del servidor central
POSTGRES_CONFIG = {
    "host": "100.126.119.25",     # IP del servidor
    "port": 5432,
    "dbname": "db_rsb",
    "user": "postgres",
    "password": "123"
}


# Función para conectarse a PostgreSQL
def conectar_postgres():
    return psycopg2.connect(
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"]
    )


# Insertar un registro en la base PostgreSQL
def insertar_en_postgres(conn, registro):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO localizaciones (
                id, vehiculo_id, temperatura_arduino, temperatura_interior1,
                temperatura_interior2, puerta1, puerta2, ubicacion, 
                sincronizado, humedad
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            --ON CONFLICT (id, vehiculo_id) DO NOTHING;
        """, (
            registro[0],  # id
            registro[1],  # vehiculo_id
            registro[2],  # temperatura_arduino
            registro[3],  # temperatura_interior1
            registro[4],  # temperatura_interior2
            registro[5],  # puerta1
            registro[6],  # puerta2            
            registro[7],  # ubicacion
            registro[8],  # sincronizado
            registro[9],  # humedad
        ))


def run_sync_service():
    while True:
        registros = obtener_no_sincronizados()
        if not registros:
            ptint("No se recuperaron ningun registro")
            time.sleep(30)
            continue

        try:
            conn = conectar_postgres()
        except Exception as e:
            print(f"[ERROR] No se pudo conectar al servidor PostgreSQL: {e}")
            time.sleep(30)
            continue

        with conn:
            for reg in registros:
                try:
                    insertar_en_postgres(conn, reg)
                    marcar_como_sincronizado(reg[0])
                    print(f"[SYNC] ID {reg[0]} sincronizado con el servidor.")
                except Exception as e:
                    print(f"[ERROR] Fallo al sincronizar ID {reg[0]}: {e}")

        conn.close()
        time.sleep(30)


if __name__ == "__main__":
    run_sync_service()
