# db_handler.py
import sqlite3

DB_PATH = './vehiculos.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
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
            temperatura NUMERIC NOT NULL,
            ubicacion varchar not null, 
            sincronizado INTEGER DEFAULT (0) NOT NULL
            
        );
    """)
    conn.commit()
    conn.close()


def insertar_registro(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO localizaciones (
            vehiculo_id, temperatura_arduino, temperatura_interior1,
            temperatura_interior2, puerta1, puerta2, temperatura, ubicacion, sincronizado
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, data)
    conn.commit()
    conn.close()


def obtener_no_sincronizados():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM localizaciones WHERE sincronizado = 0")
    resultados = cursor.fetchall()
    conn.close()
    return resultados


def marcar_como_sincronizado(id_):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE localizaciones SET sincronizado = 1 WHERE id = ?", (id_,))
    conn.commit()
    conn.close()
