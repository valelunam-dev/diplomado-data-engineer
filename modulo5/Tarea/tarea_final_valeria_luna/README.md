# Tarea Final — Módulo 5

```bash
# 0) Crear entorno virtual (opcional pero recomendado)
python -m venv venv
# Linux/Mac:  source venv/bin/activate
# Windows:    venv\Scripts\activate

# 1) Instalar dependencias
pip install -r requirements.txt

# 2) Gatillar el Scheduler para generar datos en la base de datos
python scheduler.py

# 3) Para consultar contenidos 
uvicorn main:app --reload 
# Para probar los endpoints: http://127.0.0.1:8000/docs
```