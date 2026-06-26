import pandas as pd
import json

print("=== CSV Santiago ===")
df = pd.read_csv("data/inputs/ventas_santiago.csv")
print(df.head())

print("\n=== Parquet Lima ===")
df = pd.read_parquet("data/inputs/ventas_lima.parquet")
print(df.head())

print("\n=== JSON Buenos Aires ===")

with open(
    "data/inputs/ventas_buenos_aires.json",
    encoding="utf-8"
) as f:

    for linea in f:
        print(json.loads(linea))