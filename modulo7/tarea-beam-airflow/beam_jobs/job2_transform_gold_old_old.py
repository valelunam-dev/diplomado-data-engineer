"""
Job 2 de Apache Beam: Transformacion (T) y Validacion de Contratos.

Consume la capa PSA generada por el Job 1 y:
  1. Valida cada registro contra el Contrato de Datos (Data Contract):
       - monto_original debe ser estrictamente numerico y mayor a cero (> 0).
       - ciudad solo puede ser 'Santiago', 'Lima' o 'Buenos Aires'.
  2. Los registros que FALLAN el contrato se desvian a una Dead-Letter Queue (DLQ)
     en formato JSON Lines, usando SALIDAS ETIQUETADAS (Tagged Outputs), sin botar
     el pipeline (los registros validos siguen su curso normal).
  3. Los registros validos se cruzan con el maestro de tipos de cambio
     (tipo_cambio.csv) mediante un SIDE INPUT distribuido para convertir el monto
     local (CLP / PEN / ARS) a USD.
  4. El resultado final, enriquecido y DEDUPLICADO por id_transaccion, se escribe en
     la capa Gold en formato Parquet, particionado por proc_date.

Uso:
    python job2_transform_gold.py --proc_date 2026-06-10 \
        --psa_dir ../data/psa --gold_dir ../data/gold \
        --errors_dir ../data/errors --tipo_cambio ../data/inputs/tipo_cambio.csv
"""
import argparse
import csv
import glob
import io
import json

import apache_beam as beam
import pyarrow as pa
from apache_beam import pvalue
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromParquet, ReadFromText, WriteToParquet, WriteToText


CIUDADES_VALIDAS = {"Santiago", "Lima", "Buenos Aires"}

# Esquema de la capa Gold.
GOLD_SCHEMA = pa.schema([
    ("id_transaccion", pa.string()),
    ("ciudad", pa.string()),
    ("monto_usd", pa.float64()),
    ("fecha_compras", pa.string()),
])

# Etiquetas para las salidas multiples (Tagged Outputs).
TAG_VALIDOS = "validos"
TAG_RECHAZADOS = "rechazados"


class ValidarContrato(beam.DoFn):
    """Aplica el Data Contract y separa validos vs. rechazados (DLQ)."""

    def process(self, registro):
        monto_texto = registro.get("monto_original")

        # Regla 1: el monto debe ser un numero valido (float/int).
        try:
            monto = float(monto_texto)
        except (TypeError, ValueError):
            yield pvalue.TaggedOutput(TAG_RECHAZADOS, {
                "raw_record": registro,
                "motivo_rechazo": "Monto no corresponde a un formato numerico valido (float/int)",
            })
            return

        # Regla 2: monto > 0  Y  ciudad autorizada en el contrato regional.
        if monto <= 0 or registro.get("ciudad") not in CIUDADES_VALIDAS:
            yield pvalue.TaggedOutput(TAG_RECHAZADOS, {
                "raw_record": registro,
                "motivo_rechazo": "Ciudad no autorizada en contrato regional o monto menor a cero",
            })
            return

        # Registro valido: pasa por la salida principal.
        yield registro


class ConvertirAUSD(beam.DoFn):
    """Cruza el registro valido con el tipo de cambio (Side Input) y arma la fila Gold."""

    def process(self, registro, tasas):
        # 'tasas' es un dict {codigo_moneda: factor_usd} entregado como Side Input.
        factor = tasas[registro["moneda_origen"]]
        monto_usd = float(registro["monto_original"]) * factor
        yield {
            "id_transaccion": registro["id_transaccion"],
            "ciudad": registro["ciudad"],
            "monto_usd": round(monto_usd, 6),
            "fecha_compras": registro["fecha_transaccion"],
        }


def parsear_tipo_cambio(linea):
    """Convierte una linea del CSV de tipo de cambio en (codigo_moneda, factor_usd)."""
    codigo, _pais, factor = next(csv.reader(io.StringIO(linea)))
    return (codigo, float(factor))


def deduplicar(clave_valores):
    """Toma el primer registro de cada id_transaccion (deduplicacion)."""
    _id, registros = clave_valores
    return list(registros)[0]


def construir_pipeline(opciones, args):
    proc_date = args.proc_date
    # Se normalizan los separadores a '/' (Beam usa '/' en su sistema de archivos,
    # incluso en Windows; mezclar '\' rompe el patron glob).
    psa_dir = args.psa_dir.replace("\\", "/").rstrip("/")
    gold_dir = args.gold_dir.replace("\\", "/").rstrip("/")
    errors_dir = args.errors_dir.replace("\\", "/").rstrip("/")
    psa_glob = f"{psa_dir}/proc_date={proc_date}/ventas*.parquet"
    gold_prefijo = f"{gold_dir}/proc_date={proc_date}/ventas_usd"
    dlq_prefijo = f"{errors_dir}/proc_date={proc_date}/rechazados"

    with beam.Pipeline(options=opciones) as p:
        # Side Input: maestro de tipos de cambio como dict distribuido.
        tasas = beam.pvalue.AsDict(
            p
            | "LeerTipoCambio" >> ReadFromText(args.tipo_cambio, skip_header_lines=1)
            | "ParsearTipoCambio" >> beam.Map(parsear_tipo_cambio)
        )

        # Lectura de la capa PSA generada por el Job 1.
        # NOTA: el conector ReadFromParquet de Beam tiene un bug de glob con el
        # filesystem local en Windows; por eso se resuelven los archivos concretos
        # con glob de Python y se lee cada shard, uniendolos con Flatten. En un
        # runner distribuido (Dataflow/Flink) se pasaria directamente el patron.
        archivos_psa = [f.replace("\\", "/") for f in glob.glob(psa_glob)]
        if not archivos_psa:
            raise FileNotFoundError(f"No se encontraron archivos PSA en: {psa_glob}")
        lecturas = [
            p | f"LeerPSA_{i}" >> ReadFromParquet(ruta)
            for i, ruta in enumerate(archivos_psa)
        ]
        psa = lecturas | "UnirShardsPSA" >> beam.Flatten()

        # Validacion con salidas etiquetadas (Tagged Outputs).
        resultado = psa | "ValidarContrato" >> beam.ParDo(ValidarContrato()).with_outputs(
            TAG_RECHAZADOS, main=TAG_VALIDOS)

        validos = resultado[TAG_VALIDOS]
        rechazados = resultado[TAG_RECHAZADOS]

        # --- Rama de error: Dead-Letter Queue en JSON Lines ---
        (
            rechazados
            | "SerializarDLQ" >> beam.Map(lambda r: json.dumps(r, ensure_ascii=False))
            | "EscribirDLQ" >> WriteToText(
                file_path_prefix=dlq_prefijo,
                file_name_suffix=".json",
                shard_name_template="",  # nombre fijo -> idempotente al re-ejecutar
            )
        )

        # --- Rama valida: conversion a USD + deduplicacion + capa Gold ---
        (
            validos
            | "ConvertirAUSD" >> beam.ParDo(ConvertirAUSD(), tasas)
            | "ClavearPorId" >> beam.Map(lambda r: (r["id_transaccion"], r))
            | "AgruparPorId" >> beam.GroupByKey()
            | "Deduplicar" >> beam.Map(deduplicar)
            | "EscribirGold_Parquet" >> WriteToParquet(
                file_path_prefix=gold_prefijo,
                schema=GOLD_SCHEMA,
                file_name_suffix=".parquet",
            )
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Job 2 - Transformacion a capa Gold")
    parser.add_argument("--proc_date", required=True,
                        help="Fecha de proceso YYYY-MM-DD (macro {{ ds }} de Airflow)")
    parser.add_argument("--psa_dir", default="data/psa", help="Carpeta de la capa PSA")
    parser.add_argument("--gold_dir", default="data/gold", help="Carpeta destino Gold")
    parser.add_argument("--errors_dir", default="data/errors", help="Carpeta destino DLQ")
    parser.add_argument("--tipo_cambio", default="data/inputs/tipo_cambio.csv",
                        help="Ruta del maestro de tipos de cambio")
    args, beam_args = parser.parse_known_args(argv)

    opciones = PipelineOptions(beam_args)
    construir_pipeline(opciones, args)


if __name__ == "__main__":
    main()
