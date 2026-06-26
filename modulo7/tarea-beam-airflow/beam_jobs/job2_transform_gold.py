import apache_beam as beam
import pandas as pd
import json
import os
import argparse

from datetime import date


# =========================
# PARAMETROS
# =========================

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


# =========================
# RUTAS
# =========================

psa_file = (
    f"data/psa/proc_date={proc_date}/"
    f"ventas_unificadas.parquet"
)

tipo_cambio_file = (
    "data/inputs/tipo_cambio.csv"
)


# =========================
# CLASE VALIDACION
# =========================

class ValidarContrato(beam.DoFn):

    TAG_ERROR = "errores"

    def process(self, registro):

        ciudades_validas = {
            "Santiago",
            "Lima",
            "Buenos Aires"
        }

        # Validar ciudad

        if registro["ciudad"] not in ciudades_validas:

            yield beam.pvalue.TaggedOutput(
                self.TAG_ERROR,
                {
                    "raw_record": registro,
                    "motivo_rechazo":
                        "Ciudad no autorizada"
                }
            )

            return

        # Validar monto numerico

        try:

            monto = float(
                registro["monto_original"]
            )

        except Exception:

            yield beam.pvalue.TaggedOutput(
                self.TAG_ERROR,
                {
                    "raw_record": registro,
                    "motivo_rechazo":
                        "Monto no numerico"
                }
            )

            return

        # Validar monto positivo

        if monto <= 0:

            yield beam.pvalue.TaggedOutput(
                self.TAG_ERROR,
                {
                    "raw_record": registro,
                    "motivo_rechazo":
                        "Monto menor o igual a cero"
                }
            )

            return

        registro["monto_original"] = monto

        yield registro


# =========================
# LEER PSA
# =========================

df_psa = pd.read_parquet(psa_file)

registros = df_psa.to_dict("records")


# =========================
# TIPO DE CAMBIO
# =========================

df_tc = pd.read_csv(tipo_cambio_file)

factores = (
    df_tc
    .set_index("codigo_moneda")
    ["factor_usd"]
    .to_dict()
)


# =========================
# LISTAS RESULTADO
# =========================

validos_lista = []
errores_lista = []


# =========================
# CAPTURA RESULTADOS
# =========================

class GuardarValidos(beam.DoFn):

    def process(self, elemento):

        validos_lista.append(elemento)

        yield elemento


class GuardarErrores(beam.DoFn):

    def process(self, elemento):

        errores_lista.append(elemento)

        yield elemento


# =========================
# PIPELINE
# =========================

with beam.Pipeline() as p:

    datos = (
        p
        | "CrearRegistros"
        >> beam.Create(registros)
    )

    resultado = (

        datos

        | "ValidarContrato"

        >> beam.ParDo(
            ValidarContrato()
        )

        .with_outputs(
            ValidarContrato.TAG_ERROR,
            main="validos"
        )
    )

    validos = resultado.validos

    errores = resultado.errores

    (
        validos
        | "GuardarValidos"
        >> beam.ParDo(
            GuardarValidos()
        )
    )

    (
        errores
        | "GuardarErrores"
        >> beam.ParDo(
            GuardarErrores()
        )
    )


# =========================
# GOLD
# =========================

gold = []

for r in validos_lista:

    factor = factores[
        r["moneda_origen"]
    ]

    monto_usd = (
        r["monto_original"]
        * factor
    )

    gold.append({

        "id_transaccion":
            r["id_transaccion"],

        "ciudad":
            r["ciudad"],

        "monto_usd":
            monto_usd,

        "fecha_compra":
            r["fecha_transaccion"]

    })


df_gold = pd.DataFrame(gold)

# Deduplicacion

df_gold = (
    df_gold
    .drop_duplicates(
        subset=["id_transaccion"]
    )
)


# =========================
# GUARDAR GOLD
# =========================

ruta_gold = (
    f"data/gold/proc_date={proc_date}"
)

os.makedirs(
    ruta_gold,
    exist_ok=True
)

df_gold.to_parquet(
    f"{ruta_gold}/ventas_gold.parquet",
    index=False
)


# =========================
# GUARDAR DLQ
# =========================

ruta_error = (
    f"data/errors/proc_date={proc_date}"
)

os.makedirs(
    ruta_error,
    exist_ok=True
)

with open(
    f"{ruta_error}/dlq.json",
    "w",
    encoding="utf-8"
) as f:

    for e in errores_lista:

        f.write(
            json.dumps(
                e,
                ensure_ascii=False,
                default=str
            )
            + "\n"
        )


# =========================
# RESUMEN
# =========================
print("JOB 2 FINALIZADO:")
print(f"Registros válidos : {len(df_gold)}")
print(f"Registros error   : {len(errores_lista)}")
print(f"Gold              : {ruta_gold}")
print(f"DLQ               : {ruta_error}")

