from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "valeria",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="pipeline_beam_airflow",
    description="Pipeline ETL con Apache Beam",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule="@daily",
    catchup=False,
    tags=["beam", "etl", "diplomado"],
) as dag:

    job1 = BashOperator(
        task_id="job1_ingest_to_psa",
        cwd="/opt/airflow",
        bash_command="""
python beam_jobs/job1_ingest_to_psa.py \
--proc_date {{ ds }}
""",
    )

    job2 = BashOperator(
        task_id="job2_transform_gold",
        cwd="/opt/airflow",
        bash_command="""
python beam_jobs/job2_transform_gold.py \
--proc_date {{ ds }}
""",
    )

    job1 >> job2