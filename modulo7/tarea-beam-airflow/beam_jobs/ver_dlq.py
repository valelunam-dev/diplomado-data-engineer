from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

errores = list(
    (BASE_DIR / "data" / "errors").rglob("*.json")
)

for archivo in errores:

    print("=" * 60)
    print(archivo)

    with open(archivo, encoding="utf-8") as f:

        for linea in f:
            print(linea)