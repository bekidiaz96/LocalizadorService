import os
import time
import psycopg2
from dotenv import load_dotenv
from db_handler import obtener_no_sincronizados, marcar_como_sincronizado

load_dotenv()

def conectar_postgres():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

def obtener_siguiente_vehiculo_id():
    """Consulta el max(vehiculo_id) en PostgreSQL y retorna max + 1."""
    try:
        conn = conectar_postgres()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(vehiculo_id), 0) FROM localizaciones;")
            max_id = cursor.fetchone()[0]
            siguiente_id = max_id + 1
            print(f"[INFO] Siguiente vehiculo_id asignado: {siguiente_id}")
            return siguiente_id
    except Exception as e:
        print(f"[ERROR] No se pudo obtener el vehiculo_id del servidor: {e}")
        return 1 # ID de respaldo en caso de fallo de conexión
    finally:
        if 'conn' in locals():
            conn.close()

def insertar_en_postgres(conn, registro):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO localizaciones (
                id, vehiculo_id, temperatura_arduino, temperatura_interior1,
                temperatura_interior2, puerta1, puerta2, ubicacion, sincronizado, humedad
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, registro)

def run_sync_service():
    while True:
        registros = obtener_no_sincronizados()
        if not registros:
            print("No se recuperaron ningun registro")
            time.sleep(30)
            continue

        try:
            conn = conectar_postgres()
            with conn:
                for reg in registros:
                    try:
                        insertar_en_postgres(conn, reg)
                        marcar_como_sincronizado(reg[0])
                        print(f"[SYNC] ID {reg[0]} sincronizado con el servidor.")
                    except Exception as e:
                        print(f"[ERROR] Fallo al sincronizar ID {reg[0]}: {e}")
            conn.close()
        except Exception as e:
            print(f"[ERROR] No se pudo conectar al servidor PostgreSQL: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    run_sync_service()