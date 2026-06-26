import apache_beam as beam
import pandas as pd
import json
import os
import argparse

from datetime import datetime, date

# PARAMETROS -- use IA en esto para que el job sea reutilizable y pueda ser ejecutado con diferentes fechas de proceso (proc_date)

parser = argparse.ArgumentParser()

parser.add_argument(
    "--proc_date",
    required=False
)

args = parser.parse_args()

proc_date = (
    args.proc_date
    if args.proc_date
    else date.today().strftime("%Y-%m-%d")
)

ingestado_at = datetime.now().isoformat()

# LECTURA CSV

def leer_santiago():

    df = pd.read_csv(
        "data/inputs/ventas_santiago.csv"
    )

    for _, row in df.iterrows():

        yield {
            "id_transaccion": str(row["id_transaccion"]),
            "ciudad": str(row["ciudad"]),
            "monto_original": str(row["monto"]),
            "moneda_origen": "CLP",
            "fecha_transaccion": str(row["fecha"]),
            "ingestado_at": ingestado_at,
            "proc_date": proc_date
        }

# LECTURA PARQUET

def leer_lima():

    df = pd.read_parquet(
        "data/inputs/ventas_lima.parquet"
    )

    for _, row in df.iterrows():

        yield {
            "id_transaccion": str(row["transaction_id"]),
            "ciudad": str(row["city"]),
            "monto_original": str(row["local_value"]),
            "moneda_origen": "PEN",
            "fecha_transaccion": str(row["sales_date"]),
            "ingestado_at": ingestado_at,
            "proc_date": proc_date
        }

# LECTURA JSON

def leer_buenos_aires():

    with open(
        "data/inputs/ventas_buenos_aires.json",
        encoding="utf-8"
    ) as archivo:

        for linea in archivo:

            row = json.loads(linea)

            yield {
                "id_transaccion": str(row["tx_id"]),
                "ciudad": str(row["sucursal"]),
                "monto_original": str(row["total"]),
                "moneda_origen": "ARS",
                "fecha_transaccion": str(row["timestamp"]),
                "ingestado_at": ingestado_at,
                "proc_date": proc_date
            }

# HOMOGENEIZACION

datos_unificados = (
    list(leer_santiago())
    + list(leer_lima())
    + list(leer_buenos_aires())
)

# PIPELINE BEAM

with beam.Pipeline() as p:

    (
        p
        | "CrearDatos" >> beam.Create(datos_unificados)
        | "Mostrar" >> beam.Map(print)
    )

# PSA PARQUET

ruta_psa = f"data/psa/proc_date={proc_date}"

os.makedirs(
    ruta_psa,
    exist_ok=True
)

df = pd.DataFrame(datos_unificados)

df.to_parquet(
    f"{ruta_psa}/ventas_unificadas.parquet",
    index=False
)

print(f"\nPSA creada en: {ruta_psa}")