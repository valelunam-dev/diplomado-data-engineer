from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

psa_file = (
    BASE_DIR
    / "data"
    / "psa"
    / "proc_date=2026-06-29"
    / "ventas_unificadas.parquet"
)

print("Existe:", psa_file.exists())
print("Ruta:", psa_file)

df = pd.read_parquet(psa_file)

print("\nCantidad de registros:", len(df))
print("\nColumnas:")
print(df.columns.tolist())

print("\nPrimeros registros:")
print(df)