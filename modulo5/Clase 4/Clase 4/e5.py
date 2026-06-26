import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

log = logging.getLogger('etl')
log.setLevel(logging.DEBUG)

fmt = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
)

consola = logging.StreamHandler() 
consola.setLevel(logging.INFO)
consola.setFormatter(fmt)

archivo = RotatingFileHandler('etl.log', maxBytes=10_000_000, backupCount=5)
archivo.setLevel(logging.DEBUG)  
archivo.setFormatter(fmt)

diario = TimedRotatingFileHandler('etl_daily.log', when='midnight', backupCount=30)
diario.setLevel(logging.INFO)
diario.setFormatter(fmt)

log.addHandler(consola)
log.addHandler(archivo)
log.addHandler(diario)

log.info('Pipeline arranco')        
log.debug('Solo aparecera en archivo, no en consola') 