import logging
from pythonjsonlogger import jsonlogger

log = logging.getLogger('etljson')
log.setLevel(logging.INFO)

h = logging.StreamHandler()

h.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
log.addHandler(h)

log.info('extracción iniciada', extra=
    {
        'filas': 12340,
        'duration_seg': 23.4,
        'fuente': 'api-shopify'
    }
)