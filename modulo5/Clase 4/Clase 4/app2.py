import logging
from logging.handlers import RotatingFileHandler   # handler con rotacion por tamano

log = logging.getLogger('mi_etl')
log.setLevel(logging.DEBUG)

fmt = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',   # hora | nivel | logger | mensaje
    datefmt='%Y-%m-%d %H:%M:%S'                                  # formato de la hora
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(fmt)


archivo = RotatingFileHandler('mi_etl.log', maxBytes=200_000, backupCount=3)
archivo.setLevel(logging.DEBUG)
archivo.setFormatter(fmt)

log.addHandler(console)
log.addHandler(archivo)

log.debug('debug: detalles internos (solo va al archivo)') 
log.info('info: ETL arrancando')  
log.warning('warning: hubo 2 filas con NaN')      
log.error('error: la API externa devolvio 500')    
log.critical('critical: la base de datos no responde') 

try:
    1/0
except ZeroDivisionError:
    log.exception('exception: division por cero - traceback completo abajo')
