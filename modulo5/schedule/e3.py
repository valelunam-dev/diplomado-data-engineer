from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
 
logging.basicConfig(level=logging.INFO)
 
sched = BlockingScheduler(
    jobstores={'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')},
    executors={'default': ThreadPoolExecutor(max_workers=10)},
    job_defaults={'coalesce': True, 'max_instances': 1, 'misfire_grace_time': 300},
    timezone='America/Santiago'
)
 
def etl_diario():
    print(f'[{datetime.now()}] Corriendo ETL diario...')
 
def chequeo_salud():
    print(f'[{datetime.now()}] Health check...')
 
def reporte_lunes():
    print(f'[{datetime.now()}] Reporte semanal...')
 
if __name__ == '__main__':
    # replace_existing=True evita errores si el job ya existe en jobs.db tras un reinicio
    pass