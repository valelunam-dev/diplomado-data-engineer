# ============================================================
# GENERACIÓN DEL DATASET SEMANAL
# CORPORACIÓN FAVORITA
#
# Entrada:
#   train.csv
#
# Salidas:
#   favorita_weekly.csv
#   favorita_weekly.parquet
#
# Unidad de análisis:
#   año ISO + semana ISO + tienda + producto
# ============================================================

from pathlib import Path
from time import time
import gc
import shutil

import pandas as pd


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

CARPETA = Path(__file__).resolve().parent

RUTA_ENTRADA = CARPETA / "train.csv"

RUTA_SALIDA_CSV = CARPETA / "favorita_weekly.csv"

RUTA_SALIDA_PARQUET = CARPETA / "favorita_weekly.parquet"

CARPETA_TEMPORAL = CARPETA / "temporales_semanales"

# Cantidad de filas que se procesarán en cada bloque
TAMANO_BLOQUE = 1_000_000


# ============================================================
# 2. VALIDACIONES INICIALES
# ============================================================

if not RUTA_ENTRADA.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo:\n{RUTA_ENTRADA}"
    )

# Eliminar archivos temporales de una ejecución anterior
if CARPETA_TEMPORAL.exists():
    shutil.rmtree(CARPETA_TEMPORAL)

CARPETA_TEMPORAL.mkdir(
    parents=True,
    exist_ok=True
)

inicio = time()

print("=" * 70)
print("GENERACIÓN DEL DATASET SEMANAL")
print("=" * 70)

print(f"Archivo de entrada : {RUTA_ENTRADA}")
print(f"Tamaño de bloque   : {TAMANO_BLOQUE:,} filas")
print()


# ============================================================
# 3. LECTURA DEL ARCHIVO POR BLOQUES
# ============================================================

lector = pd.read_csv(
    RUTA_ENTRADA,
    usecols=[
        "date",
        "store_nbr",
        "item_nbr",
        "unit_sales",
        "onpromotion"
    ],
    dtype={
        "store_nbr": "int16",
        "item_nbr": "int32",
        "unit_sales": "float32"
    },
    parse_dates=["date"],
    chunksize=TAMANO_BLOQUE,
    low_memory=False
)


total_filas = 0
archivos_temporales = []


# ============================================================
# 4. PROCESAMIENTO DE CADA BLOQUE
# ============================================================

for numero_bloque, chunk in enumerate(
    lector,
    start=1
):

    total_filas += len(chunk)

    print(
        f"Procesando bloque {numero_bloque:03d} | "
        f"{len(chunk):,} filas | "
        f"Acumulado: {total_filas:,}"
    )

    # --------------------------------------------------------
    # 4.1 Convertir promoción a 0 y 1
    #
    # True  -> 1
    # False -> 0
    # Nulo  -> 0
    # --------------------------------------------------------

    chunk["onpromotion"] = (
        chunk["onpromotion"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map({
            "true": 1,
            "false": 0
        })
        .fillna(0)
        .astype("int8")
    )

    # --------------------------------------------------------
    # 4.2 Obtener año y semana ISO
    #
    # Esto evita mezclar, por ejemplo:
    # semana 1 de 2013 con semana 1 de 2014
    # --------------------------------------------------------

    calendario_iso = chunk["date"].dt.isocalendar()

    chunk["anio"] = (
        calendario_iso.year
        .astype("int16")
    )

    chunk["semana"] = (
        calendario_iso.week
        .astype("int8")
    )

    # --------------------------------------------------------
    # 4.3 Obtener el lunes de cada semana
    # --------------------------------------------------------

    chunk["fecha_semana"] = (
        chunk["date"]
        - pd.to_timedelta(
            chunk["date"].dt.weekday,
            unit="D"
        )
    )

    # --------------------------------------------------------
    # 4.4 Agregación semanal dentro del bloque
    # --------------------------------------------------------

    parcial = (
        chunk
        .groupby(
            [
                "fecha_semana",
                "anio",
                "semana",
                "store_nbr",
                "item_nbr"
            ],
            as_index=False,
            observed=True
        )
        .agg(
            unit_sales=(
                "unit_sales",
                "sum"
            ),
            dias_promocion=(
                "onpromotion",
                "sum"
            ),
            dias_con_venta=(
                "date",
                "nunique"
            )
        )
    )

    # --------------------------------------------------------
    # 4.5 Optimizar tipos del resultado parcial
    # --------------------------------------------------------

    parcial["anio"] = (
        parcial["anio"]
        .astype("int16")
    )

    parcial["semana"] = (
        parcial["semana"]
        .astype("int8")
    )

    parcial["store_nbr"] = (
        parcial["store_nbr"]
        .astype("int16")
    )

    parcial["item_nbr"] = (
        parcial["item_nbr"]
        .astype("int32")
    )

    parcial["unit_sales"] = (
        parcial["unit_sales"]
        .astype("float32")
    )

    parcial["dias_promocion"] = (
        parcial["dias_promocion"]
        .astype("int8")
    )

    parcial["dias_con_venta"] = (
        parcial["dias_con_venta"]
        .astype("int8")
    )

    # --------------------------------------------------------
    # 4.6 Guardar resultado parcial en disco
    # --------------------------------------------------------

    ruta_temporal = (
        CARPETA_TEMPORAL
        / f"bloque_{numero_bloque:03d}.parquet"
    )

    parcial.to_parquet(
        ruta_temporal,
        index=False,
        compression="snappy"
    )

    archivos_temporales.append(
        ruta_temporal
    )

    # --------------------------------------------------------
    # 4.7 Liberar memoria
    # --------------------------------------------------------

    del chunk
    del parcial
    gc.collect()


# ============================================================
# 5. RESUMEN DE LA PRIMERA ETAPA
# ============================================================

print()
print("=" * 70)
print("LECTURA DEL ARCHIVO COMPLETADA")
print("=" * 70)

print(
    f"Filas originales procesadas: "
    f"{total_filas:,}"
)

print(
    f"Archivos temporales creados : "
    f"{len(archivos_temporales)}"
)

print()


# ============================================================
# 6. LEER LOS ARCHIVOS TEMPORALES
# ============================================================

print("Leyendo resultados temporales...")

parciales = []

for numero_archivo, archivo in enumerate(
    archivos_temporales,
    start=1
):

    print(
        f"Leyendo temporal "
        f"{numero_archivo:03d} de "
        f"{len(archivos_temporales):03d}"
    )

    parcial = pd.read_parquet(
        archivo
    )

    parciales.append(
        parcial
    )


# ============================================================
# 7. UNIR LOS RESULTADOS TEMPORALES
# ============================================================

print()
print("Uniendo archivos temporales...")

weekly = pd.concat(
    parciales,
    ignore_index=True
)

del parciales
gc.collect()


# ============================================================
# 8. CONSOLIDACIÓN FINAL
# ============================================================

print("Realizando agrupación final...")

weekly = (
    weekly
    .groupby(
        [
            "fecha_semana",
            "anio",
            "semana",
            "store_nbr",
            "item_nbr"
        ],
        as_index=False,
        observed=True
    )
    .agg(
        unit_sales=(
            "unit_sales",
            "sum"
        ),
        dias_promocion=(
            "dias_promocion",
            "sum"
        ),
        dias_con_venta=(
            "dias_con_venta",
            "sum"
        )
    )
)


# ============================================================
# 9. OPTIMIZACIÓN FINAL DE TIPOS
# ============================================================

weekly["anio"] = (
    weekly["anio"]
    .astype("int16")
)

weekly["semana"] = (
    weekly["semana"]
    .astype("int8")
)

weekly["store_nbr"] = (
    weekly["store_nbr"]
    .astype("int16")
)

weekly["item_nbr"] = (
    weekly["item_nbr"]
    .astype("int32")
)

weekly["unit_sales"] = (
    weekly["unit_sales"]
    .astype("float32")
)

weekly["dias_promocion"] = (
    weekly["dias_promocion"]
    .astype("int8")
)

weekly["dias_con_venta"] = (
    weekly["dias_con_venta"]
    .astype("int8")
)


# ============================================================
# 10. ORDEN DE COLUMNAS
# ============================================================

weekly = weekly[
    [
        "fecha_semana",
        "anio",
        "semana",
        "store_nbr",
        "item_nbr",
        "unit_sales",
        "dias_promocion",
        "dias_con_venta"
    ]
]


# ============================================================
# 11. ORDENAR REGISTROS
# ============================================================

print("Ordenando registros...")

weekly = (
    weekly
    .sort_values(
        [
            "fecha_semana",
            "store_nbr",
            "item_nbr"
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# 12. VALIDACIÓN DE DUPLICADOS
# ============================================================

duplicados = weekly.duplicated(
    subset=[
        "anio",
        "semana",
        "store_nbr",
        "item_nbr"
    ]
).sum()


# ============================================================
# 13. GUARDAR ARCHIVO PARQUET
# ============================================================

print("Guardando archivo Parquet...")

weekly.to_parquet(
    RUTA_SALIDA_PARQUET,
    index=False,
    compression="snappy"
)


# ============================================================
# 14. GUARDAR ARCHIVO CSV
# ============================================================

print("Guardando archivo CSV...")

weekly.to_csv(
    RUTA_SALIDA_CSV,
    index=False
)


# ============================================================
# 15. VALIDACIONES DEL RESULTADO
# ============================================================

print()
print("=" * 70)
print("VALIDACIÓN DEL RESULTADO")
print("=" * 70)

print(
    f"Filas semanales       : "
    f"{len(weekly):,}"
)

print(
    f"Columnas              : "
    f"{weekly.shape[1]}"
)

print(
    f"Duplicados de la clave: "
    f"{duplicados:,}"
)

print(
    f"Año mínimo            : "
    f"{weekly['anio'].min()}"
)

print(
    f"Año máximo            : "
    f"{weekly['anio'].max()}"
)

print(
    f"Semana mínima         : "
    f"{weekly['semana'].min()}"
)

print(
    f"Semana máxima         : "
    f"{weekly['semana'].max()}"
)

print(
    f"Cantidad de tiendas   : "
    f"{weekly['store_nbr'].nunique():,}"
)

print(
    f"Cantidad de productos : "
    f"{weekly['item_nbr'].nunique():,}"
)


# ============================================================
# 16. MOSTRAR TIPOS DE DATOS
# ============================================================

print()
print("Tipos de datos:")

print(
    weekly.dtypes
)


# ============================================================
# 17. MOSTRAR PRIMEROS REGISTROS
# ============================================================

print()
print("Primeros registros:")

print(
    weekly.head(10)
)


# ============================================================
# 18. MOSTRAR TAMAÑO DE LOS ARCHIVOS
# ============================================================

tamano_csv_mb = (
    RUTA_SALIDA_CSV.stat().st_size
    / 1024**2
)

tamano_parquet_mb = (
    RUTA_SALIDA_PARQUET.stat().st_size
    / 1024**2
)

print()
print("Tamaño de los archivos:")

print(
    f"CSV     : "
    f"{tamano_csv_mb:,.2f} MB"
)

print(
    f"Parquet : "
    f"{tamano_parquet_mb:,.2f} MB"
)


# ============================================================
# 19. ELIMINAR ARCHIVOS TEMPORALES
# ============================================================

print()
print("Eliminando archivos temporales...")

shutil.rmtree(
    CARPETA_TEMPORAL
)


# ============================================================
# 20. RESUMEN FINAL
# ============================================================

tiempo_total = (
    time() - inicio
) / 60

print()
print("=" * 70)
print("PROCESO FINALIZADO CORRECTAMENTE")
print("=" * 70)

print(
    f"Tiempo total: "
    f"{tiempo_total:.2f} minutos"
)

print()
print("Archivos generados:")

print(
    f"- {RUTA_SALIDA_CSV}"
)

print(
    f"- {RUTA_SALIDA_PARQUET}"
)