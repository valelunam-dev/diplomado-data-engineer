# -*- coding: utf-8 -*-
"""
Limpieza y preparacion del dataset - Grupo 6 (Valeria Luna Meza / Pedro Barraza Rivera)
Escenario 6: Datos Duplicados (identificar causas y efectos)
Modulo 8 - Fundamentos de Visualizacion de Datos
"""
import pandas as pd

ORIGEN = "Dataset.xlsx"
SALIDA_CSV = "Grupo6_Escenario6_Duplicados_limpio.csv"
SALIDA_XLSX = "Grupo6_Escenario6_Duplicados_limpio.xlsx"

# 1) Cargar y filtrar el escenario asignado
df = pd.read_excel(ORIGEN)
d = df[df["Escenario"] == 6].copy().reset_index(drop=True)

# 2) Tipado correcto
d["Fecha"] = pd.to_datetime(d["Fecha"], errors="coerce")
d["Hora_Inicio"] = d["Hora_Inicio"].astype(str).str.strip()
d["Hora_Fin"] = d["Hora_Fin"].astype(str).str.strip()

# Normalizar categoricas (quitar espacios, capitalizar consistente)
for c in ["Tipo_Pipeline", "Sistema_Origen", "Prioridad", "Severidad", "Region", "Estado"]:
    d[c] = d[c].astype(str).str.strip()

# 3) Quitar duplicados exactos por seguridad (aunque no haya)
antes = len(d)
d = d.drop_duplicates().reset_index(drop=True)
print(f"Filas duplicadas exactas eliminadas: {antes - len(d)}")

# 4) Columnas derivadas utiles para el tema "Datos Duplicados"
# Estimacion de registros duplicados a partir del % de duplicados
d["Registros_Duplicados_est"] = (d["Registros_Procesados"] * d["Duplicados"] / 100).round().astype(int)

# Nivel de duplicacion (para reglas de asociacion / historia)
def nivel_dup(p):
    if p <= 1:
        return "Bajo"
    elif p <= 3:
        return "Medio"
    return "Alto"
d["Nivel_Duplicados"] = d["Duplicados"].apply(nivel_dup)

# Variables temporales (para la historia en Flourish y mapa)
d["Mes"] = d["Fecha"].dt.month
d["Dia_Semana"] = d["Fecha"].dt.day_name()
d["Tiempo_min"] = (d["Tiempo_Ejecucion"] / 60).round(2)

# 5) Orden de columnas: primero el foco del escenario
orden = [
    "Fecha", "Mes", "Dia_Semana", "Hora_Inicio", "Hora_Fin", "Tiempo_Ejecucion", "Tiempo_min",
    "Tipo_Pipeline", "Sistema_Origen", "Prioridad",
    "Duplicados", "Nivel_Duplicados", "Registros_Duplicados_est",
    "Registros_Procesados", "Throughput", "Registros_Rechazados", "Reglas_Calidad", "Nulos",
    "Reintentos", "CPU", "RAM", "Disco", "Latencia",
    "Region", "Latitud", "Longitud",
    "Pipeline_ID", "Severidad", "Estado",
]
d = d[orden]

# 6) Exportar
d.to_csv(SALIDA_CSV, index=False, encoding="utf-8-sig")
d.to_excel(SALIDA_XLSX, index=False)

print(f"\nDataset limpio: {d.shape[0]} filas x {d.shape[1]} columnas")
print(f"Guardado en: {SALIDA_CSV} y {SALIDA_XLSX}")
print("\nResumen de la variable clave 'Duplicados' (%):")
print(d["Duplicados"].describe().round(2).to_string())
print("\nDistribucion Nivel_Duplicados:")
print(d["Nivel_Duplicados"].value_counts().to_string())
