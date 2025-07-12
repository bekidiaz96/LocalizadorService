
# LocalizadorService - Sincronización de Datos con PostgreSQL

Este proyecto permite sincronizar datos desde un servicio Python hacia una base de datos PostgreSQL.

---

## Requisitos

- Python 3.x
- PostgreSQL
- Módulo `psycopg2-binary`

---

## Configuración del entorno en Linux

### 1. Abrir la terminal y ubicarse en el proyecto

```bash
cd ~/Desktop/LocalizadorService-main
```

### 2. Crear un entorno virtual (si no existe)

```bash
python3 -m venv venv
```

Esto crea una carpeta `venv` con un entorno virtual independiente.

### 3. Activar el entorno virtual

```bash
source venv/bin/activate
```

Verás que el nombre del entorno aparece al inicio de la línea:

```bash
(venv) /LocalizadorService-main$
```

### 4. Instalar dependencias necesarias

```bash
pip install psycopg2-binary
```

Esto instala el módulo necesario para conectarse a PostgreSQL desde Python.

### 5. Ejecutar el script de sincronización

```bash
python3 sync_service.py
```

---

## ❓ Solución de errores comunes

### Error: `ModuleNotFoundError: No module named 'psycopg2'`

- Verificá que el entorno virtual esté activado (`(venv)` en la terminal).
- Instalá el módulo con:

```bash
pip install psycopg2-binary
```

---

## Cómo salir del entorno virtual

Cuando termines de trabajar, podés desactivar el entorno virtual con:

```bash
deactivate
```

---

## Estructura esperada del proyecto

```
LocalizadorService-main/
├── sync_service.py
├── venv/               # (creado por el entorno virtual)
└── README.md
```

---

## Autor

Rebeca Díaz  
Proyecto para sincronización de datos desde Raspberry Pi/Arduino hacia base de datos PostgreSQL.
