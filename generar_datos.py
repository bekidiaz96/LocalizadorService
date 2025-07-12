# generar_datos.py
import random
from db_handler import init_db, insertar_registro


def generar_dato_vehiculo():
    return (
        random.randint(1, 10),  # vehiculo_id
        round(random.uniform(20, 40), 2),  # temperatura_arduino
        round(random.uniform(22, 30), 2),  # temperatura_interior1
        round(random.uniform(22, 30), 2),  # temperatura_interior2
        random.randint(0, 1),  # puerta1
        random.randint(0, 1),  # puerta2
        round(random.uniform(15, 45), 2),  # temperatura (promedio o sensor extra)
        "0,0", ##ubicacion
    )


if __name__ == "__main__":
    init_db()
    for _ in range(5):
        dato = generar_dato_vehiculo()
        insertar_registro(dato)
        print(f"Registro insertado: {dato}")
