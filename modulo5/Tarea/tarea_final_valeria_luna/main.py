from fastapi import FastAPI
from fastapi import Query
import sqlite3


app = FastAPI(
    title='API Ventas M5'
)
# Configuracion de la base de datos
DB_FILE = 'ventas.db'
# generamos el status ok de la raiz de la API para verificar que esta corriendo
# correctamente
@app.get('/')
def root():

    return {
        'status': 'ok',
        'modulo': 'tarea modulo 5'
    }

# RESUMEN: obtenemos el resumen de ventas mas reciente de la base de datos
# y lo devolvemos en formato JSON
@app.get('/resumen')
def obtener_resumen():

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT *
        FROM resumen
        ORDER BY timestamp DESC
        LIMIT 1
        '''
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)

    return {
        'mensaje': 'No hay datos'
    }

# TOP PRODUCTOS: obtenemos el top N productos mas vendidos de la base de datos
# y los devolvemos en formato JSON
@app.get('/top-productos')
def obtener_top_productos(

    n: int = Query(5, ge=1, le=50)

):

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT *
        FROM top_productos
        WHERE run_id = (
            SELECT run_id
            FROM resumen
            ORDER BY timestamp DESC
            LIMIT 1
    )
        ORDER BY total_vendido DESC
        LIMIT ?
        ''',
        (n,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]