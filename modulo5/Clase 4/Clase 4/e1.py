import schedule, time
from datetime import datetime
 
def trabajo():
    print(f'[{datetime.now()}] corriendo...')
 
schedule.every(1).minutes.do(trabajo)
schedule.every().hour.at(':30').do(trabajo)
schedule.every().day.at('06:00').do(trabajo)
schedule.every().monday.at('09:00').do(trabajo)
schedule.every(5).to(10).minutes.do(trabajo)
 
while True:
    schedule.run_pending()
    time.sleep(1)
