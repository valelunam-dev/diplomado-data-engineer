# Tarea Final — Módulo 5

## Cómo arrancar (3 comandos)

```bash
# 1) Crear entorno virtual (opcional pero recomendado)
python -m venv venv
# Linux/Mac:  source venv/bin/activate
# Windows:    venv\Scripts\activate

# 2) Instalar dependencias
pip install -r requirements.txt

# 3) Correr el ETL una vez para verificar que el CSV se procesa
python etl.py
```

Si todo funciona, debería aparecer un archivo `ventas.db` (base SQLite) y un `etl.log` con líneas JSON.

## Archivos que recibes

- `ventas_marzo.csv` — dataset de entrada con 450 filas de ventas de marzo 2026
- `requirements.txt` — librerías sugeridas (puedes agregar lo que necesites)
- `Enunciado_Tarea_Final.docx` — descripción detallada de qué construir
- `Pauta_Evaluacion.docx` — cómo serás evaluado

## Archivos que debes crear

- `etl.py` — el ETL principal
- `main.py` — la API FastAPI
- `scheduler.py` — el agendador
- `etl.log` — logs JSON generados por tu ETL
- `alertas.log` — al menos una alerta provocada a propósito
- `ventas.db` — base SQLite generada

## Cómo entregar

Comprime toda la carpeta en un ZIP llamado `tarea_final_<TU_NOMBRE>.zip` y súbelo a la plataforma del curso.

**Deadline:** 7 días después de la última clase.

**Dudas:** envíame correo a ivan.espinoza.m@gmail.com o pregunta en el canal de Slack del curso.
