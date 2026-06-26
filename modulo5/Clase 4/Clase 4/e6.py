import logging
from pythonjsonlogger import jsonlogger 

log = logging.getLogger() 
log.setLevel(logging.INFO)  

h = logging.StreamHandler() 

h.setFormatter(jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
))
log.addHandler(h)

log.info('extraccion_completa', extra={
    'filas': 12340,
    'duracion_seg': 23.4,
    'fuente': 'api-shopify'
})