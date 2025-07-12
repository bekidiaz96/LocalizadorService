# logger_setup.py

import os
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    # Crear carpeta "logs" si no existe
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "monitor.log")  # Nombre base

    # Crear el logger
    logger = logging.getLogger("MonitorLogger")
    logger.setLevel(logging.INFO)

    # Evitar duplicar handlers si ya fue configurado
    if not logger.handlers:
        # Crear handler rotativo diario
        handler = TimedRotatingFileHandler(
            filename=log_path,
            when='midnight',        # Rotar a la medianoche
            interval=1,             # Cada 1 día
            backupCount=7,          # Guardar últimos 7 archivos
            encoding='utf-8',
            utc=False               # Si querés hora local
        )

        # Formato del archivo rotado: monitor.log.2025-06-21
        handler.suffix = "%Y-%m-%d"

        formatter = logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger
