import logging
 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
 
log = logging.getLogger(__name__)
 
log.info('ETL iniciado')
log.warning('Stock proyectado negativo SKU-42')
log.error('Falló conexión a Postgres, reintentando...')
 
# Salida:
# 2026-05-15 10:23:01 | INFO     | __main__ | ETL iniciado
