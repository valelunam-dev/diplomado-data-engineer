# SDD - Pipeline Datos Titanic

# 1. Fuente de datos
Dataset Titanic:
https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv

# 2. Transformación
- Contar pasajeros por clase
- Ordenar de mayor a menor
- Resultado la columnas seran cantidad de pasajeros - clase

# 3.Destino
- reporte_clases.txt
- errores.log

## Flujo

```mermaid
graph TD
    A[CSV Titanic] --> B[raw]
    B --> C[pipeline.sh]
    C --> D[reporte_clases.txt]
    C --> E[errores.log]