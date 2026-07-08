"""
DAG de orquestacion: Pipeline de Ventas LATAM (PSA -> Gold).

Coordina cronologicamente los dos Jobs de Apache Beam:
    Job 1 (Ingesta a PSA)  >>  Job 2 (Transformacion a Gold)

Estandares de produccion implementados:
  - Secuencialidad: el Job 2 NO inicia si el Job 1 no termino con exito (job1 >> job2).
  - Idempotencia: las rutas de lectura/escritura se parametrizan con el macro nativo
    {{ ds }} (fecha logica de ejecucion). Re-ejecutar el mismo dia de datos no duplica
    el resultado (los Jobs escriben sobre la misma particion proc_date y deduplican).
  - Resiliencia: 3 reintentos automaticos con 5 minutos de intervalo ante caidas.

El DAG corre cada dia a primera hora de la manana (schedule diario).
"""
from datetime import datetime, timedelta
import os

from airflow import DAG
from airflow.operators.bash import BashOperator

# Raiz del proyecto (carpeta que contiene 'beam_jobs/' y 'data/').
# Por defecto sube un nivel desde 'dags/'. Se puede sobreescribir con la variable
# de entorno PROYECTO_BEAM_DIR al desplegar en otro entorno.
PROYECTO_DIR = os.environ.get(
    "PROYECTO_BEAM_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)
BEAM_JOBS = os.path.join(PROYECTO_DIR, "beam_jobs")
DATA_DIR = os.path.join(PROYECTO_DIR, "data")
PYTHON_BIN = os.environ.get("PYTHON_BIN", "python")

default_args = {
    "owner": "data_engineering",
    "retries": 3,                          # maximo 3 reintentos
    "retry_delay": timedelta(minutes=5),   # intervalo de 5 minutos
}

with DAG(
    dag_id="dag_orden_ventas_latam",
    description="Pipeline ELT de ventas LATAM: ingesta PSA y transformacion a Gold en USD",
    start_date=datetime(2026, 6, 1),
    schedule_interval="0 6 * * *",         # todos los dias a las 06:00
    catchup=False,                         # poner True para backfill historico
    max_active_runs=1,
    default_args=default_args,
    tags=["beam", "elt", "latam", "ventas"],
) as dag:

    # Job 1: Ingesta y creacion de la capa PSA para la fecha logica {{ ds }}.
    job1_ingesta_psa = BashOperator(
        task_id="job1_ingesta_psa",
        bash_command=(
            f"{PYTHON_BIN} {BEAM_JOBS}/job1_ingest_to_psa.py "
            "--proc_date {{ ds }} "
            f"--input_dir {DATA_DIR}/inputs "
            f"--psa_dir {DATA_DIR}/psa"
        ),
    )

    # Job 2: Validacion de contrato, conversion a USD y escritura en Gold.
    job2_transform_gold = BashOperator(
        task_id="job2_transform_gold",
        bash_command=(
            f"{PYTHON_BIN} {BEAM_JOBS}/job2_transform_gold.py "
            "--proc_date {{ ds }} "
            f"--psa_dir {DATA_DIR}/psa "
            f"--gold_dir {DATA_DIR}/gold "
            f"--errors_dir {DATA_DIR}/errors "
            f"--tipo_cambio {DATA_DIR}/inputs/tipo_cambio.csv"
        ),
    )

    # Dependencia explicita: Job 1 debe finalizar con exito antes del Job 2.
    job1_ingesta_psa >> job2_transform_gold
