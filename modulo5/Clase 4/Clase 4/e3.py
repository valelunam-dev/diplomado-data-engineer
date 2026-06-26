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

@sched.scheduled_job(CronTrigger(hour=6, minute=0))
def etl_diario():
    print('Corriendo ETL diario...')
 
@sched.scheduled_job(IntervalTrigger(minutes=15))
def chequeo_salud():
    print('Health check...')
 
@sched.scheduled_job(CronTrigger(day_of_week='mon', hour=9))
def reporte_lunes():
    print('Reporte semanal...')
 
if __name__ == '__main__':
    sched.start()  # bloquea hasta Ctrl+C

