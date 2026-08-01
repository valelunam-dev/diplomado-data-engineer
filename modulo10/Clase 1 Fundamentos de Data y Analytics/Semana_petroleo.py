from pathlib import Path
import gc

import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

CARPETA = Path(__file__).resolve().parent

RUTA_WEEKLY = CARPETA / "favorita_weekly.parquet"
RUTA_OIL = CARPETA / "oil.csv"

RUTA_SALIDA = CARPETA / "favorita_weekly_oil.parquet"


# ============================================================
# 1. LEER DATASET SEMANAL
# ============================================================

print("Leyendo ventas semanales...")

weekly = pd.read_parquet(RUTA_WEEKLY)

print(f"Filas: {len(weekly):,}")
print(f"Columnas iniciales: {weekly.shape[1]}")


# ============================================================
# 2. LEER PETRÓLEO
# ============================================================

print("\nLeyendo oil.csv...")

oil = pd.read_csv(
    RUTA_OIL,
    parse_dates=["date"],
    dtype={
        "dcoilwtico": "float32"
    }
)

print(f"Registros de petróleo: {len(oil):,}")
print(f"Nulos originales: {oil['dcoilwtico'].isna().sum():,}")


# ============================================================
# 3. ORDENAR Y COMPLETAR NULOS
# ============================================================

oil = oil.sort_values("date").reset_index(drop=True)

oil["dcoilwtico"] = (
    oil["dcoilwtico"]
    .interpolate(method="linear")
    .ffill()
    .bfill()
    .astype("float32")
)

print(
    f"Nulos después de completar: "
    f"{oil['dcoilwtico'].isna().sum():,}"
)


# ============================================================
# 4. CREAR AÑO, SEMANA Y FECHA SEMANAL
# ============================================================

calendario_iso = oil["date"].dt.isocalendar()

oil["anio"] = calendario_iso.year.astype("int16")
oil["semana"] = calendario_iso.week.astype("int8")

oil["fecha_semana"] = (
    oil["date"]
    - pd.to_timedelta(
        oil["date"].dt.weekday,
        unit="D"
    )
)


# ============================================================
# 5. AGREGAR PETRÓLEO POR SEMANA
# ============================================================

oil_weekly = (
    oil
    .groupby(
        [
            "fecha_semana",
            "anio",
            "semana"
        ],
        as_index=False
    )
    .agg(
        oil_promedio_semana=("dcoilwtico", "mean"),
        oil_min_semana=("dcoilwtico", "min"),
        oil_max_semana=("dcoilwtico", "max")
    )
)


# ============================================================
# 6. OPTIMIZAR TIPOS
# ============================================================

oil_weekly["anio"] = oil_weekly["anio"].astype("int16")
oil_weekly["semana"] = oil_weekly["semana"].astype("int8")

oil_weekly["oil_promedio_semana"] = (
    oil_weekly["oil_promedio_semana"]
    .astype("float32")
)

oil_weekly["oil_min_semana"] = (
    oil_weekly["oil_min_semana"]
    .astype("float32")
)

oil_weekly["oil_max_semana"] = (
    oil_weekly["oil_max_semana"]
    .astype("float32")
)


# ============================================================
# 7. VALIDAR PETRÓLEO SEMANAL
# ============================================================

duplicados_oil = oil_weekly.duplicated(
    subset=[
        "fecha_semana",
        "anio",
        "semana"
    ]
).sum()

print("\nPetróleo semanal:")
print(f"Semanas: {len(oil_weekly):,}")
print(f"Duplicados: {duplicados_oil:,}")

print(oil_weekly.head())


# ============================================================
# 8. INTEGRAR CON VENTAS
# ============================================================

print("\nIntegrando petróleo con ventas...")

weekly_oil = weekly.merge(
    oil_weekly,
    on=[
        "fecha_semana",
        "anio",
        "semana"
    ],
    how="left",
    validate="many_to_one"
)


# ============================================================
# 9. VALIDAR RESULTADO
# ============================================================

print("\nValidación final:")

print(f"Filas antes del merge : {len(weekly):,}")
print(f"Filas después         : {len(weekly_oil):,}")

print(
    "Filas sin petróleo   : "
    f"{weekly_oil['oil_promedio_semana'].isna().sum():,}"
)

print(f"Columnas finales      : {weekly_oil.shape[1]}")


# ============================================================
# 10. GUARDAR RESULTADO
# ============================================================

weekly_oil.to_parquet(
    RUTA_SALIDA,
    index=False,
    compression="snappy"
)

print("\nArchivo generado:")
print(RUTA_SALIDA)


# ============================================================
# 11. MOSTRAR EJEMPLO
# ============================================================

print("\nPrimeros registros:")

print(
    weekly_oil[
        [
            "fecha_semana",
            "anio",
            "semana",
            "store_nbr",
            "item_nbr",
            "unit_sales",
            "oil_promedio_semana",
            "oil_min_semana",
            "oil_max_semana"
        ]
    ].head(10)
)


# ============================================================
# 12. LIBERAR MEMORIA
# ============================================================

del weekly
del oil
del oil_weekly
gc.collect()