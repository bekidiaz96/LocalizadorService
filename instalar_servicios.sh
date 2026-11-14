#!/bin/bash

# Detener ejecución si ocurre algún error
set -e

# Detectar automáticamente la ruta absoluta del proyecto y el usuario actual
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER="$(whoami)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python"

echo "========================================================"
echo "  Instalador de Servicios - LocalizadorService (Tesis)"
echo "========================================================"
echo "Directorio del proyecto : $PROJECT_DIR"
echo "Usuario de ejecución    : $CURRENT_USER"
echo ""

# 1. Verificar archivos principales
if [ ! -f "$PROJECT_DIR/ard_gps.py" ] || [ ! -f "$PROJECT_DIR/sync_service.py" ]; then
    echo "[ERROR] No se encontraron ard_gps.py o sync_service.py en $PROJECT_DIR"
    exit 1
fi

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "[WARNING] No se encontró el archivo .env en $PROJECT_DIR."
    echo "          Asegúrate de crearlo antes de iniciar los servicios."
fi

# 2. Verificar/crear entorno virtual e instalar dependencias
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creando entorno virtual Python en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "[1/4] Entorno virtual existente detectado."
fi

echo "[2/4] Instalando/actualizando dependencias en el entorno virtual..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install python-dotenv psycopg2-binary pyserial -q

# 3. Asegurar permisos de puertos seriales para el usuario
echo "[3/4] Verificando permisos de grupo dialout para $CURRENT_USER..."
sudo usermod -a -G dialout "$CURRENT_USER"

# 4. Crear los archivos de servicio systemd
echo "[4/4] Configurando servicios en /etc/systemd/system/..."

# Servicio 1: Captura de datos (Arduino + GPS)
sudo bash -c "cat > /etc/systemd/system/tesis_captura.service" <<EOF
[Unit]
Description=Servicio de Captura de Datos GPS y Sensores (Tesis)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_BIN -u $PROJECT_DIR/ard_gps.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Servicio 2: Sincronización con PostgreSQL (Tailscale)
sudo bash -c "cat > /etc/systemd/system/tesis_sync.service" <<EOF
[Unit]
Description=Servicio de Sincronizacion PostgreSQL (Tesis)
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_BIN -u $PROJECT_DIR/sync_service.py
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd, habilitar arranque automático e iniciar ambos servicios
sudo systemctl daemon-reload
sudo systemctl enable tesis_captura.service
sudo systemctl enable tesis_sync.service
sudo systemctl restart tesis_captura.service
sudo systemctl restart tesis_sync.service

echo ""
echo "========================================================"
echo "  ¡Instalación completada con éxito!"
echo "========================================================"
echo "Comandos útiles para monitoreo:"
echo "  Estado captura  : sudo systemctl status tesis_captura.service"
echo "  Estado sync     : sudo systemctl status tesis_sync.service"
echo "  Logs captura    : journalctl -u tesis_captura.service -f"
echo "  Logs sync       : journalctl -u tesis_sync.service -f"
echo "========================================================"