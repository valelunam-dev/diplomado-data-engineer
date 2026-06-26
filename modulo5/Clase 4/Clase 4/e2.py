from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import logging
 
logging.basicConfig(level=logging.INFO)
sched = BlockingScheduler(timezone='America/Santiago')
 
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
