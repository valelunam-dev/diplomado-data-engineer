import pandas as pd
import sqlite3
import uuid
import time
import argparse
import logging

from datetime import datetime
from pythonjsonlogger import jsonlogger

# CONFIG: variables para llamar el csv de ventas y la base de datos
CSV_FILE = 'ventas_marzo.csv'
DB_FILE = 'ventas.db'

# LOGGING JSON: configuracion de logger para escribir logs en formato JSON
log = logging.getLogger('etl')
log.setLevel(logging.INFO)

handler = logging.FileHandler('etl.log')

formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(message)s'
)

handler.setFormatter(formatter)

log.addHandler(handler)

# ALERTAS: funcion para escribir alertas en un archivo de 
# texto plano para casos de error en el ETL
def escribir_alerta(run_id, etapa, error):

    with open('alertas.log', 'a', encoding='utf-8') as f:

        f.write(
            f'[ALERTA] '
            f'run_id={run_id} '
            f'etapa={etapa} '
            f'timestamp={datetime.now().astimezone().isoformat()} '
            f'error={str(error)}\n'
        )

# ETL
def run_etl(forzar_fallo=False):

    run_id = uuid.uuid4().hex[:8]

    try:

        # EXTRACT: usamos pandas para leer el csv de ventas y cargarlo en un 
        # dataframe, ademas escribimos en el log el tiempo que demora esta etapa

        inicio = time.time()

        if forzar_fallo:
            raise Exception('Fallo provocado manualmente')

        df = pd.read_csv(CSV_FILE)

        duracion = round((time.time() - inicio) * 1000, 2)

        log.info(
            'extract_ok',
            extra={
                'run_id': run_id,
                'etapa': 'extract',
                'duracion_ms': duracion,
                'status': 'OK'
            }
        )

        # TRANSFORM: procesamos los datos extraídos para crear las tablas de la base de datos,
        # ademas escribimos en el log el tiempo que demora esta etapa
        
        inicio = time.time()

        resumen = pd.DataFrame([
            {
                'run_id': run_id,
                'timestamp': datetime.now().astimezone().isoformat(),
                'total_ventas': df['total'].sum(),
                'n_transacciones': len(df),
                'ticket_promedio': df['total'].mean(),
                'clientes_unicos': df['cliente_id'].nunique()
            }
        ])

        top_productos = (
                df.groupby(['sku', 'producto'])['total']
                .sum()
                .reset_index()
                .rename(columns={'total': 'total_vendido'})
                .sort_values(by='total_vendido', ascending=False)
            )

        top_productos['run_id'] = run_id

        top_productos['timestamp'] = datetime.now().astimezone().isoformat()

        duracion = round((time.time() - inicio) * 1000, 2)

        log.info(
            'transform_ok',
            extra={
                'run_id': run_id,
                'etapa': 'transform',
                'duracion_ms': duracion,
                'status': 'OK'
            }
        )

        # LOAD: cargamos los datos procesados en la base de datos,
        # ademas escribimos en el log el tiempo que demora esta etapa
        inicio = time.time()

        conn = sqlite3.connect(DB_FILE)

        resumen.to_sql(
            'resumen',
            conn,
            if_exists='append',
            index=False
        )

        top_productos.to_sql(
            'top_productos',
            conn,
            if_exists='append',
            index=False
        )

        conn.close()

        duracion = round((time.time() - inicio) * 1000, 2)

        log.info(
            'load_ok',
            extra={
                'run_id': run_id,
                'etapa': 'load',
                'duracion_ms': duracion,
                'status': 'OK'
            }
        )

        print(f'ETL OK | run_id={run_id}')

    except Exception as e:

        log.error(
            'etl_error',
            extra={
                'run_id': run_id,
                'etapa': 'run',
                'duracion_ms': 0,
                'status': 'ERROR'
            }
        )

        escribir_alerta(run_id, 'run', str(e))

        print(f'ERROR: {e}')

# MAIN: permite ejecutar el ETL desde la linea de comandos,
# con una opcion para forzar un fallo y probar el manejo de errores y alertas
if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--fallo',
        action='store_true'
    )

    args = parser.parse_args()

    run_etl(forzar_fallo=args.fallo)    