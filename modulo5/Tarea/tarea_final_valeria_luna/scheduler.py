import schedule
import time

from etl import run_etl

contador = 0

# JOB: generamos un contador para  limitar el numero de corridas del scheduler, 
# y una funcion job que ejecuta el ETL y muestra el numero de corrida
def job():

    global contador

    contador += 1

    print(f'Corrida {contador}')

    run_etl()

# SCHEDULER: cada 60 segundos ejecutamos la funcion job que corre el ETL y
# muestra el numero de corrida en la consola
schedule.every(60).seconds.do(job)

print('Scheduler iniciado')
print('Presiona Ctrl+C para detener')

try:

    while contador < 5:

        schedule.run_pending()

        time.sleep(1)

except KeyboardInterrupt:

    print('\nScheduler detenido manualmente')#por si apretamos ctrl+c para detener el scheduler antes de las 5 corridas programadas