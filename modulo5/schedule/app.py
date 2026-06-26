import schedule
import time
from datetime import datetime
ARCHIVO = 'pulso.log'  
def latir():
    momento = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ARCHIVO, 'a', encoding='utf-8') as f:
        f.write(f'{momento}  vivo\n') 
    print(f'[{momento}] latido escrito en {ARCHIVO}')
schedule.every(5).seconds.do(latir)
print('Scheduler arrancado. Ctrl-C para detener.')
while True: 
    schedule.run_pending()  
    time.sleep(1)