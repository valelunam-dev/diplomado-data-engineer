"""
Job 1 de Apache Beam: Ingestion y Creacion de la Capa PSA (Persistent Staging Area).

Fase E + L (Extraccion + Carga). Lee en PARALELO las tres fuentes heterogeneas
(CSV de Santiago, Parquet de Lima y JSON Lines de Buenos Aires), las homogeneiza
bajo un Esquema Comun de Transicion y escribe el resultado en formato Apache Parquet
dentro de una estructura de carpetas historica particionada por fecha de proceso
(proc_date=YYYY-MM-DD).

REGLAS IMPORTANTES (segun el enunciado):
  - El Job 1 NO aplica reglas de negocio ni filtra filas. Solo mapea/homogeneiza.
  - El campo monto_original se guarda OBLIGATORIAMENTE como String (texto), para
    permitir el ingreso de datos "ruidosos" (ej: "NULO_ERROR") sin romper la ingesta.
  - La salida en la capa PSA es OBLIGATORIAMENTE Apache Parquet (regla FinOps).

Uso:
    python job1_ingest_to_psa.py --proc_date 2026-06-10 \
        --input_dir ../data/inputs --psa_dir ../data/psa
"""
import argparse
import csv
import io
import json
from datetime import datetime, timezone

import apache_beam as beam
import pyarrow as pa
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io import ReadFromText, ReadFromParquet, WriteToParquet


# Esquema Comun de Transicion: TODAS las columnas son String (texto).
# pyarrow lo necesita para escribir el archivo Parquet de salida.
PSA_SCHEMA = pa.schema([
    ("id_transaccion", pa.string()),
    ("ciudad", pa.string()),
    ("monto_original", pa.string()),   # se guarda como texto a proposito
    ("moneda_origen", pa.string()),
    ("fecha_transaccion", pa.string()),
    ("ingestado_at", pa.string()),
])


def _ahora_iso():
    """Marca de tiempo computacional del momento exacto de ejecucion del pipeline."""
    return datetime.now(timezone.utc).isoformat()


class ParsearSantiago(beam.DoFn):
    """CSV de Santiago -> Esquema Comun. Moneda inyectada: CLP."""

    def process(self, linea):
        # Se usa el modulo csv para respetar comas dentro de campos entre comillas.
        fila = next(csv.reader(io.StringIO(linea)))
        id_transaccion, ciudad, monto, fecha = fila[0], fila[1], fila[2], fila[3]
        yield {
            "id_transaccion": id_transaccion,
            "ciudad": ciudad,
            "monto_original": str(monto),   # se mantiene como texto
            "moneda_origen": "CLP",
            "fecha_transaccion": fecha,
            "ingestado_at": _ahora_iso(),
        }


class ParsearLima(beam.DoFn):
    """Parquet de Lima (ya viene como dict) -> Esquema Comun. Moneda inyectada: PEN."""

    def process(self, registro):
        yield {
            "id_transaccion": str(registro["transaction_id"]),
            "ciudad": str(registro["city"]),
            "monto_original": str(registro["local_value"]),
            "moneda_origen": "PEN",
            "fecha_transaccion": str(registro["sales_date"]),
            "ingestado_at": _ahora_iso(),
        }


class ParsearBuenosAires(beam.DoFn):
    """JSON Lines de Buenos Aires -> Esquema Comun. Moneda inyectada: ARS."""

    def process(self, linea):
        registro = json.loads(linea)
        yield {
            "id_transaccion": str(registro["tx_id"]),
            "ciudad": str(registro["sucursal"]),
            # total puede ser numero o texto ruidoso; se conserva tal cual como String.
            "monto_original": str(registro["total"]),
            "moneda_origen": "ARS",
            "fecha_transaccion": str(registro["timestamp"]),
            "ingestado_at": _ahora_iso(),
        }


def construir_pipeline(opciones, args):
    proc_date = args.proc_date
    # Se normalizan los separadores a '/' (Beam usa '/' incluso en Windows).
    input_dir = args.input_dir.replace("\\", "/").rstrip("/")
    psa_dir = args.psa_dir.replace("\\", "/").rstrip("/")
    # Estructura de carpetas historica (PSA), particionada por fecha de proceso.
    salida_prefijo = f"{psa_dir}/proc_date={proc_date}/ventas"

    with beam.Pipeline(options=opciones) as p:
        # --- Lectura EN PARALELO de las tres fuentes (cada una es una rama) ---
        santiago = (
            p
            | "LeerSantiagoCSV" >> ReadFromText(
                f"{input_dir}/ventas_santiago.csv", skip_header_lines=1)
            | "MapSantiago" >> beam.ParDo(ParsearSantiago())
        )

        lima = (
            p
            | "LeerLimaParquet" >> ReadFromParquet(f"{input_dir}/ventas_lima.parquet")
            | "MapLima" >> beam.ParDo(ParsearLima())
        )

        buenos_aires = (
            p
            | "LeerBuenosAiresJSON" >> ReadFromText(f"{input_dir}/ventas_buenos_aires.json")
            | "MapBuenosAires" >> beam.ParDo(ParsearBuenosAires())
        )

        # --- Union de las tres ramas en una sola PCollection homogeneizada ---
        (
            (santiago, lima, buenos_aires)
            | "UnificarFuentes" >> beam.Flatten()
            | "EscribirPSA_Parquet" >> WriteToParquet(
                file_path_prefix=salida_prefijo,
                schema=PSA_SCHEMA,
                file_name_suffix=".parquet",
            )
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Job 1 - Ingesta a la capa PSA")
    parser.add_argument("--proc_date", required=True,
                        help="Fecha de proceso YYYY-MM-DD (macro {{ ds }} de Airflow)")
    parser.add_argument("--input_dir", default="data/inputs",
                        help="Carpeta con las fuentes de entrada")
    parser.add_argument("--psa_dir", default="data/psa",
                        help="Carpeta destino de la capa PSA")
    args, beam_args = parser.parse_known_args(argv)

    opciones = PipelineOptions(beam_args)
    construir_pipeline(opciones, args)


if __name__ == "__main__":
    main()
