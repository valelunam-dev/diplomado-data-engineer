import logging

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

log = logging.getLogger('etl')
log.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

consola = logging.StreamHandler()
consola.setLevel(logging.INFO)
consola.setFormatter(fmt)

archivo = RotatingFileHandler('etl.log', maxBytes=5*1024*1024, backupCount=5)

diario = TimedRotatingFileHandler('etl_diario.log', when='midnight', backupCount=30)
diario.setLevel(logging.INFO)
diario.setFormatter(fmt)

log.addHandler(consola)
log.addHandler(archivo)
log.addHandler(diario)

log.info('ETL iniciado')
log.debug('Solo aparece en archivo y no en consola')
