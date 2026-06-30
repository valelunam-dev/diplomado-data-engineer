from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

gold_dir = BASE_DIR / "data" / "gold"

parquets = list(gold_dir.rglob("*.parquet"))

print("Archivos encontrados:")
for p in parquets:
    print(p)

print()

for p in parquets:
    print("=" * 60)
    print(p.name)

    df = pd.read_parquet(p)

    print(df)
    print(f"Registros: {len(df)}")