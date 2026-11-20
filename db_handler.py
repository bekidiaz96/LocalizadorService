# db_handler.py
import sqlite3

DB_PATH = './vehiculos.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS localizaciones (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            vehiculo_id INTEGER NOT NULL,
            temperatura_arduino NUMERIC NOT NULL,
            temperatura_interior1 NUMERIC NOT NULL,
            temperatura_interior2 NUMERIC NOT NULL,
            puerta1 INTEGER DEFAULT (0) NOT NULL,
            puerta2 INTEGER DEFAULT (0) NOT NULL,
            ubicacion varchar not null, 
            humedad integer not null,
            sincronizado INTEGER DEFAULT (0) NOT NULL,
            hora_registro TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def insertar_registro(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO localizaciones (
            vehiculo_id, temperatura_arduino, temperatura_interior1,
            temperatura_interior2, puerta1, puerta2, humedad, ubicacion, hora_registro, sincronizado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, data)
    conn.commit()
    conn.close()

def obtener_no_sincronizados():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, vehiculo_id, temperatura_arduino, temperatura_interior1,
               temperatura_interior2, puerta1, puerta2, ubicacion, sincronizado, humedad, hora_registro
        FROM localizaciones
        WHERE sincronizado = 0
    """)
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def marcar_como_sincronizado(id_):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE localizaciones SET sincronizado = 1 WHERE id = ?", (id_,))
    conn.commit()
    conn.close()
