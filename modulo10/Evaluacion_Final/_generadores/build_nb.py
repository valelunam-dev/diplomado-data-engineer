# -*- coding: utf-8 -*-
"""Genera el cuaderno de la Evaluacion Final (modulo 10)."""
import json, sys
from pathlib import Path

celdas = []
def md(texto):
    celdas.append({"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n")})
def code(texto):
    celdas.append({"cell_type": "code", "execution_count": None, "metadata": {},
                   "outputs": [], "source": texto.strip("\n")})

# ==========================================================================
md(r"""
# Evaluación Final — Diplomado en Data Engineer

**Universidad de Santiago de Chile — Facultad de Administración y Economía**

**Estudiante:** Valeria Luna
**Módulo:** 10 — Machine Learning para la escala masiva de datos
**Fecha:** agosto de 2026

---

## Predicción de la duración de viajes urbanos con Machine Learning

Este cuaderno desarrolla un proyecto completo de Machine Learning, desde la comprensión del
problema de negocio hasta la interpretación del modelo, utilizando **Python** y **scikit-learn**.

| Elemento | Detalle |
|---|---|
| **Dataset** | NYC TLC — *Yellow Taxi Trip Records*, enero 2024 |
| **Enlace oficial** | https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page |
| **Archivo utilizado** | https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet |
| **Tabla de zonas** | https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv |
| **Registros** | 2.964.624 viajes (muy por encima del mínimo de 100.000) |
| **Unidad de análisis** | Un viaje individual |
| **Variable objetivo** | `duracion_min` — duración del viaje en minutos |
| **Tipo de problema** | Aprendizaje supervisado — **Regresión** |
| **Licencia** | Datos públicos publicados por la NYC Taxi & Limousine Commission |

> El dataset no fue utilizado en las clases del diplomado (en clases se trabajó con
> *Corporación Favorita*, *Mall Customers* y *salarios*).
""")

# ==========================================================================
md(r"""
## 0. Configuración del entorno

Se utilizan las bibliotecas trabajadas durante el diplomado:

- `pandas` y `numpy` para manipulación y cálculo numérico.
- `pyarrow` para lectura eficiente de archivos **Parquet**.
- `plotly` para visualizaciones interactivas.
- `scikit-learn` para preprocesamiento, reducción de dimensionalidad, modelamiento y evaluación.
- `joblib` para la persistencia del modelo entrenado.

Se fija una semilla (`RANDOM_STATE = 42`) para garantizar la **reproducibilidad** de todos los
resultados: muestreo, división de datos, entrenamiento y validación cruzada.
""")

code(r"""
# En Google Colab estas bibliotecas ya vienen instaladas.
# Descomentar solo si el entorno lo requiere:
# !pip install -q pandas pyarrow plotly scikit-learn joblib kaleido
""")

code(r"""
import warnings
warnings.filterwarnings("ignore")

import json
from pathlib import Path
from time import perf_counter
from datetime import datetime
from urllib.request import urlretrieve

import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from sklearn.model_selection import train_test_split, KFold, cross_val_score, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, TargetEncoder
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.dummy import DummyRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    mean_absolute_percentage_error
)
import joblib
import sklearn

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", lambda x: f"{x:,.4f}")

print("pandas       :", pd.__version__)
print("numpy        :", np.__version__)
print("scikit-learn :", sklearn.__version__)
print("Semilla      :", RANDOM_STATE)
""")

md(r"""
### 0.1 Funciones auxiliares

Se definen dos utilidades transversales al cuaderno:

- `registrar_tiempo`: mide la duración de cada etapa del proceso, tal como se practicó en el
  laboratorio de Aprendizaje Supervisado. Permite evaluar la viabilidad computacional del
  proyecto sobre un volumen de datos masivo.
- `mostrar`: aplica un formato homogéneo a las figuras, las exporta como imagen (para el informe
  ejecutivo) y las despliega. **Todas las figuras del cuaderno incluyen título.**
""")

code(r"""
registro_tiempos = []
inicio_cuaderno = perf_counter()

def registrar_tiempo(proceso, inicio_perf):
    '''Registra la duración de una etapa del proyecto y la informa por pantalla.'''
    duracion = perf_counter() - inicio_perf
    registro_tiempos.append({"Proceso": proceso, "Duración (s)": duracion})
    print(f"[tiempo] {proceso}: {duracion:.2f} segundos")

CARPETA_FIGURAS = Path("figuras")
CARPETA_FIGURAS.mkdir(exist_ok=True)

def mostrar(fig, nombre=None, ancho=950, alto=480):
    '''Da formato uniforme a la figura, la exporta a PNG (si es posible) y la muestra.'''
    fig.update_layout(template="plotly_white", width=ancho, height=alto,
                      title_x=0.5, margin=dict(l=70, r=40, t=80, b=70))
    if nombre:
        try:
            fig.write_image(CARPETA_FIGURAS / f"{nombre}.png", scale=2)
        except Exception as error:
            print("Aviso: no fue posible exportar la figura como PNG:", type(error).__name__)
    fig.show()

def metricas_regresion(y_real, y_predicho):
    '''Calcula las métricas de regresión solicitadas en la evaluación.'''
    mae = mean_absolute_error(y_real, y_predicho)
    mse = mean_squared_error(y_real, y_predicho)
    return {"MAE": mae, "MSE": mse, "RMSE": np.sqrt(mse), "R2": r2_score(y_real, y_predicho)}

print("Funciones auxiliares definidas.")
""")

# ==========================================================================
md(r"""
## 1. Comprensión del problema  *(10 puntos)*

### 1.1 Problema de negocio

Las empresas de **transporte urbano de pasajeros** planifican su operación en función del tiempo
que demora cada servicio. Cuando la duración de un viaje se estima mal, se producen efectos en
cadena: conductores que quedan sin holgura entre servicios, incumplimiento de horarios
comprometidos con el cliente, sobredotación o subdotación de flota y tiempos muertos que se pagan
igual.

En la práctica, la estimación suele hacerse con reglas simples (por ejemplo, un promedio histórico
por ruta o una velocidad supuesta constante). Ese enfoque ignora que la duración depende
fuertemente de la **hora del día**, del **día de la semana**, del **origen y destino** y de si el
viaje involucra o no un **aeropuerto**.

El presente proyecto aborda ese problema utilizando los registros públicos de viajes de taxis
amarillos de la ciudad de Nueva York, que constituyen uno de los conjuntos de datos de movilidad
urbana más completos disponibles: cada fila corresponde a un viaje real con su origen, destino,
distancia, marca de tiempo y duración efectiva.

### 1.2 Objetivo del proyecto

**Objetivo general:** construir un modelo de Machine Learning capaz de predecir la duración de un
viaje urbano, en minutos, utilizando **únicamente información disponible al momento de iniciar el
servicio**.

**Objetivos específicos:**

1. Caracterizar la calidad y el comportamiento de la demanda de viajes mediante un análisis
   exploratorio sobre casi 3 millones de registros.
2. Preparar los datos y construir variables predictivas con sentido operacional.
3. Evaluar el aporte de la reducción de dimensionalidad al desempeño del modelo.
4. Comparar algoritmos de regresión y ajustar los hiperparámetros del mejor candidato.
5. Cuantificar el error del modelo en unidades de negocio (minutos) e interpretar sus resultados.

### 1.3 Variable objetivo

$$\text{duracion\_min} = \frac{\text{tpep\_dropoff\_datetime} - \text{tpep\_pickup\_datetime}}{60\ \text{segundos}}$$

Es una variable **numérica continua y positiva**, medida en minutos. No viene explícita en el
archivo original: se construye a partir de las marcas de tiempo de inicio y término del viaje.

### 1.4 Tipo de problema de Machine Learning

Se trata de un problema de **aprendizaje supervisado de regresión**, porque la variable objetivo es
continua y se dispone de su valor observado para cada registro histórico. No es un problema de
clasificación (no se predicen categorías) ni de aprendizaje no supervisado (existe una etiqueta).

### 1.5 Beneficio esperado para la organización

| Ámbito | Beneficio esperado |
|---|---|
| **Programación de servicios** | Estimar el tiempo de cada servicio antes de asignarlo permite construir turnos factibles y reducir la holgura improductiva. |
| **Compromiso con el cliente** | Informar un tiempo estimado de llegada (ETA) confiable mejora la experiencia y reduce reclamos. |
| **Dimensionamiento de flota** | Conocer la duración esperada por franja horaria y zona permite anticipar cuántos vehículos se requieren en cada momento. |
| **Control de gestión** | Comparar la duración real con la estimada convierte el modelo en una línea base objetiva para detectar desvíos operacionales. |
| **Costos** | El tiempo es el principal componente del costo variable (conductor y combustible); mejorar su estimación mejora directamente la estructura de costos. |

### 1.6 Restricción metodológica clave: información disponible al iniciar el viaje

El archivo original contiene variables que **solo se conocen cuando el viaje ya terminó**
(`fare_amount`, `total_amount`, `tip_amount`, `tolls_amount`, entre otras). La tarifa de un taxi se
calcula, precisamente, en función del tiempo y la distancia recorridos.

Incluir esas variables como predictores produciría **fuga de información** (*data leakage*): el
modelo mostraría un desempeño excelente en el cuaderno y sería inútil en producción, porque al
momento de predecir esos datos aún no existen. Por esta razón **se excluyen deliberadamente** del
conjunto de predictores, decisión que se documenta en la sección 3.
""")

code(r"""
# ============================================================
# Diccionario de las variables del archivo original
# ============================================================
diccionario = pd.DataFrame([
    ("VendorID",              "Proveedor tecnológico que registra el viaje",        "Categórica nominal", "Predictor"),
    ("tpep_pickup_datetime",  "Fecha y hora de inicio del viaje",                   "Temporal",           "Origen de variables derivadas"),
    ("tpep_dropoff_datetime", "Fecha y hora de término del viaje",                  "Temporal",           "Construcción del objetivo"),
    ("passenger_count",       "Cantidad de pasajeros declarada",                    "Numérica discreta",  "Predictor"),
    ("trip_distance",         "Distancia recorrida en millas (taxímetro)",           "Numérica continua",  "Predictor"),
    ("RatecodeID",            "Código de tarifa aplicada",                          "Categórica nominal", "Predictor"),
    ("store_and_fwd_flag",    "Viaje almacenado y enviado después (sin conexión)",   "Categórica binaria", "Predictor"),
    ("PULocationID",          "Zona de origen (260 zonas TLC)",                     "Identificador",      "Predictor (alta cardinalidad)"),
    ("DOLocationID",          "Zona de destino (261 zonas TLC)",                    "Identificador",      "Predictor (alta cardinalidad)"),
    ("payment_type",          "Medio de pago",                                      "Categórica nominal", "Predictor"),
    ("fare_amount",           "Tarifa calculada por el taxímetro",                  "Numérica continua",  "Excluida: fuga de información"),
    ("extra",                 "Recargos varios",                                    "Numérica continua",  "Excluida: fuga de información"),
    ("mta_tax",               "Impuesto MTA",                                       "Numérica continua",  "Excluida: fuga de información"),
    ("tip_amount",            "Propina",                                            "Numérica continua",  "Excluida: fuga de información"),
    ("tolls_amount",          "Peajes",                                             "Numérica continua",  "Excluida: fuga de información"),
    ("improvement_surcharge", "Recargo de mejoramiento",                            "Numérica continua",  "Excluida: fuga de información"),
    ("total_amount",          "Monto total cobrado",                                "Numérica continua",  "Excluida: fuga de información"),
    ("congestion_surcharge",  "Recargo por congestión",                             "Numérica continua",  "Excluida: fuga de información"),
    ("Airport_fee",           "Recargo de aeropuerto",                              "Numérica continua",  "Excluida: fuga de información"),
], columns=["variable", "descripcion", "nivel_medicion", "uso_en_el_proyecto"])

diccionario
""")

# ==========================================================================
md(r"""
## 2. Dataset y análisis exploratorio (EDA)  *(20 puntos)*

### 2.1 Carga de los datos

El archivo se publica en formato **Parquet**, formato columnar comprimido que permite leer casi
tres millones de registros en pocos segundos conservando los tipos de datos, ventaja trabajada en
el laboratorio del Módulo 10.

La celda siguiente descarga los archivos desde el sitio oficial de la NYC TLC si no están
presentes, de modo que el cuaderno se ejecuta de forma autónoma tanto en Google Colab como en un
entorno local.
""")

code(r"""
# ============================================================
# Descarga de los datos desde la fuente oficial (NYC TLC)
# ============================================================
URL_VIAJES = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
URL_ZONAS  = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

RUTA_VIAJES = Path("yellow_tripdata_2024-01.parquet")
RUTA_ZONAS  = Path("taxi_zone_lookup.csv")

inicio = perf_counter()
for url, ruta in [(URL_VIAJES, RUTA_VIAJES), (URL_ZONAS, RUTA_ZONAS)]:
    if not ruta.exists():
        print("Descargando", ruta.name, "...")
        urlretrieve(url, ruta)
    print(f"{ruta.name:40s} {ruta.stat().st_size / 1024**2:8.2f} MB")
registrar_tiempo("Descarga de los archivos", inicio)
""")

code(r"""
inicio = perf_counter()
df = pd.read_parquet(RUTA_VIAJES, engine="pyarrow")
zonas = pd.read_csv(RUTA_ZONAS)
registrar_tiempo("Lectura de los archivos", inicio)

print(f"Viajes cargados : {df.shape[0]:,} registros y {df.shape[1]} variables")
print(f"Zonas cargadas  : {zonas.shape[0]:,} zonas TLC")
df.head()
""")

code(r"""
# Tabla de zonas TLC: permite traducir los identificadores de origen y destino
# a información geográfica interpretable (comuna y tipo de zona de servicio).
zonas = zonas.rename(columns={
    "LocationID": "zona_id", "Borough": "borough", "Zone": "zona", "service_zone": "servicio"
})
zonas.head()
""")

# ==========================================================================
md(r"""
El análisis exploratorio se realiza **sobre el dataset completo** (2.964.624 viajes) y persigue tres
propósitos: conocer la estructura de los datos, detectar problemas de calidad que condicionen la
preparación posterior, y descubrir los patrones de negocio que el modelo deberá capturar.

### 2.2 Dimensiones, tipos de datos y consumo de memoria
""")

code(r"""
print(f"Cantidad de registros : {df.shape[0]:,}")
print(f"Cantidad de variables : {df.shape[1]}")
print(f"Memoria utilizada     : {df.memory_usage(deep=True).sum() / 1024**2:,.1f} MB")
print("\nCumple el requisito de al menos 100.000 registros:", df.shape[0] >= 100_000)

df.info(memory_usage="deep")
""")

code(r"""
resumen_tipos = pd.DataFrame({
    "tipo_de_dato": df.dtypes.astype(str),
    "valores_unicos": df.nunique(),
    "porcentaje_nulos": (df.isna().mean() * 100).round(2)
})
resumen_tipos
""")

md(r"""
**Interpretación.** El dataset ocupa más de 500 MB en memoria y combina tres familias de
variables: temporales (marcas de inicio y término), identificadores de zona almacenados como
enteros —que **no deben interpretarse como variables continuas**— y variables monetarias. La
presencia de identificadores numéricos obliga a tratarlos como categóricos en el modelamiento,
criterio aplicado en la sección 3.

### 2.3 Valores nulos
""")

code(r"""
reporte_nulos = pd.DataFrame({
    "cantidad_nulos": df.isna().sum(),
    "porcentaje_nulos": df.isna().mean() * 100
}).sort_values("porcentaje_nulos", ascending=False)
reporte_nulos
""")

code(r"""
nulos_grafico = reporte_nulos[reporte_nulos.cantidad_nulos > 0].reset_index()
nulos_grafico.columns = ["variable", "cantidad_nulos", "porcentaje_nulos"]

fig = px.bar(nulos_grafico, x="variable", y="porcentaje_nulos", text_auto=".2f",
             hover_data=["cantidad_nulos"],
             title="Porcentaje de valores nulos por variable",
             labels={"variable": "Variable", "porcentaje_nulos": "Nulos (%)"})
fig.update_layout(xaxis_tickangle=-30)
mostrar(fig, "eda_nulos")
""")

code(r"""
# ¿Los nulos se concentran en algún proveedor? Un patrón de este tipo indica
# un problema de registro en el origen y no una ausencia aleatoria.
patron_nulos = pd.crosstab(df.VendorID, df.passenger_count.isna(),
                           rownames=["VendorID"], colnames=["passenger_count nulo"])
patron_nulos["porcentaje_nulos"] = (patron_nulos[True] / patron_nulos.sum(axis=1) * 100).round(2)
patron_nulos
""")

md(r"""
**Interpretación.** Exactamente **140.162 registros (4,73 %)** presentan nulos, y siempre en el mismo
bloque de cinco variables (`passenger_count`, `RatecodeID`, `store_and_fwd_flag`,
`congestion_surcharge`, `Airport_fee`). Que la cantidad sea idéntica en las cinco columnas revela
que **no son ausencias independientes**, sino registros incompletos generados por un flujo de
captura distinto: se observan en los tres proveedores, con una incidencia total del proveedor 6.

Consecuencia para la preparación: los nulos afectan a variables secundarias, no al objetivo ni a la
distancia, por lo que **no corresponde eliminar esas filas** (equivaldría a descartar casi 5 % de la
información); se imputarán con criterio explícito en la sección 3.2.

### 2.4 Registros duplicados
""")

code(r"""
llave_negocio = ["tpep_pickup_datetime", "tpep_dropoff_datetime",
                 "PULocationID", "DOLocationID", "trip_distance", "total_amount"]

print(f"Duplicados exactos (todas las columnas) : {df.duplicated().sum():,}")
print(f"Duplicados según llave de negocio       : {df.duplicated(subset=llave_negocio).sum():,}")
print("\nLlave de negocio utilizada:", llave_negocio)
""")

md(r"""
**Interpretación.** No existen registros duplicados, ni considerando todas las columnas ni
considerando la llave de negocio (mismo instante de inicio y término, mismo origen-destino, misma
distancia y monto). La verificación es igualmente necesaria: confirma que cada fila corresponde a un
viaje distinto y que **la unidad de análisis está bien definida**, requisito para que las métricas de
evaluación no queden infladas por repeticiones.

### 2.5 Construcción de la variable objetivo
""")

code(r"""
df["duracion_min"] = (
    df.tpep_dropoff_datetime - df.tpep_pickup_datetime
).dt.total_seconds() / 60

print("Estadísticas de la duración del viaje (minutos), datos sin depurar:")
print(df.duracion_min.describe())

print("\nRegistros con valores imposibles o implausibles:")
print(f"  Duración negativa o nula (<= 0 min) : {(df.duracion_min <= 0).sum():,}")
print(f"  Duración menor a 1 minuto           : {(df.duracion_min < 1).sum():,}")
print(f"  Duración mayor a 2 horas            : {(df.duracion_min > 120).sum():,}")
print(f"  Duración mayor a 24 horas           : {(df.duracion_min > 1440).sum():,}")
print(f"  Distancia igual a cero              : {(df.trip_distance == 0).sum():,}")
print(f"  Distancia mayor a 100 millas        : {(df.trip_distance > 100).sum():,}")
print(f"  Cero pasajeros declarados           : {(df.passenger_count == 0).sum():,}")
print(f"  Monto total negativo                : {(df.total_amount < 0).sum():,}")
""")

md(r"""
**Interpretación.** La duración media es de 15,6 minutos, pero el máximo alcanza **9.455 minutos
(más de 6 días)** y existen **870 viajes con duración negativa** —el término anterior al inicio—, lo
que es físicamente imposible. Estos registros corresponden a errores del taxímetro o del sistema de
transmisión. Su presencia distorsiona cualquier estadístico y justifica los filtros de calidad de la
sección 3.1.

### 2.6 Estadísticas descriptivas
""")

code(r"""
variables_numericas = ["duracion_min", "trip_distance", "passenger_count", "fare_amount",
                       "total_amount", "tip_amount", "extra", "tolls_amount"]
df[variables_numericas].describe().T
""")

md(r"""
**Interpretación.** Las estadísticas descriptivas confirman anomalías en varias variables:

- `trip_distance` registra un máximo de **312.722 millas**, equivalente a más de doce veces la
  circunferencia de la Tierra en un solo viaje, y un mínimo de 0 millas (60.371 viajes con distancia
  cero).
- `fare_amount` y `total_amount` presentan **valores negativos** (hasta −900 USD), propios de
  anulaciones y reversos contables.
- La desviación estándar de `trip_distance` (225) es sesenta veces su mediana (1,68), señal
  inequívoca de valores extremos.

Estos hallazgos definen la agenda de la preparación de datos: sin depuración, ningún modelo puede
aprender la relación real entre distancia y duración.

### 2.7 Distribución de la variable objetivo
""")

code(r"""
# Para la visualización se recorta el eje a 90 minutos; los valores extremos se
# analizan aparte para no comprimir el histograma.
# Con casi tres millones de registros no se envían los datos crudos al gráfico:
# np.histogram cuenta cuántos valores caen en cada intervalo y devuelve esos conteos
# junto con los bordes de los intervalos, de modo que el gráfico transporta 90 barras
# en lugar de millones de puntos. Es la práctica que permite visualizar volúmenes
# masivos sin saturar el navegador.
duracion_visible = df.loc[df.duracion_min.between(0, 90), "duracion_min"]
conteo, bordes = np.histogram(duracion_visible, bins=90)
centros = (bordes[:-1] + bordes[1:]) / 2

fig = px.bar(x=centros, y=conteo,
             title="Distribución de la duración de los viajes (0 a 90 minutos)")
fig.update_layout(showlegend=False, bargap=0.02,
                  xaxis_title="Duración del viaje (minutos)",
                  yaxis_title="Cantidad de viajes")
mostrar(fig, "eda_objetivo_histograma")

percentiles = df.duracion_min.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999])
print("Percentiles de la duración (minutos):")
print(percentiles)
print(f"\nAsimetría (skewness) : {df.duracion_min.skew():,.2f}")
print(f"Curtosis             : {df.duracion_min.kurtosis():,.2f}")
""")

md(r"""
**Interpretación.** La distribución es **unimodal y asimétrica a la derecha**: la mayoría de los
viajes dura entre 5 y 20 minutos (mediana 11,6 min), con una cola larga de servicios extensos. El
percentil 99 se ubica en 60,5 minutos, mientras que el máximo supera los 9.000.

La asimetría medida (41,25) y la curtosis (3.248) son valores enormes para una variable de este
tipo: no describen la forma real del fenómeno, sino el efecto de un puñado de registros erróneos en
la cola. En una distribución de duraciones de viaje urbano cabría esperar una asimetría cercana a 2,
valor que efectivamente se obtiene una vez depurados los datos.

Implicancia para el modelamiento: la asimetría favorece a los modelos basados en árboles, que no
suponen normalidad ni relaciones lineales, frente a la regresión lineal clásica.

### 2.8 Distribución de las variables numéricas
""")

code(r"""
distancia_visible = df.loc[df.trip_distance.between(0, 25), "trip_distance"]
conteo, bordes = np.histogram(distancia_visible, bins=100)
centros = (bordes[:-1] + bordes[1:]) / 2

fig = px.bar(x=centros, y=conteo,
             title="Distribución de la distancia recorrida (0 a 25 millas)")
fig.update_layout(showlegend=False, bargap=0.02,
                  xaxis_title="Distancia recorrida (millas)",
                  yaxis_title="Cantidad de viajes")
mostrar(fig, "eda_distancia_histograma")
""")

code(r"""
conteo_pasajeros = (df.passenger_count.fillna(-1).astype(int)
                      .value_counts().sort_index().reset_index())
conteo_pasajeros.columns = ["passenger_count", "cantidad_viajes"]
conteo_pasajeros["passenger_count"] = conteo_pasajeros.passenger_count.replace({-1: "Nulo"}).astype(str)

fig = px.bar(conteo_pasajeros, x="passenger_count", y="cantidad_viajes", text_auto=".2s",
             title="Cantidad de viajes según número de pasajeros declarado",
             labels={"passenger_count": "Pasajeros declarados", "cantidad_viajes": "Cantidad de viajes"})
mostrar(fig, "eda_pasajeros")
""")

md(r"""
**Interpretación.** La distancia también es asimétrica: el 75 % de los viajes recorre menos de 3,11
millas, consistente con un patrón de movilidad intraurbana de trayectos cortos. En pasajeros, el
valor 1 concentra cerca del 70 % de los viajes y aparecen **29.423 registros con 0 pasajeros**, valor
inválido para un servicio de transporte que también deberá corregirse.

### 2.9 Análisis de las variables categóricas
""")

code(r"""
mapa_pago = {0: "0 · Desconocido", 1: "1 · Tarjeta de crédito", 2: "2 · Efectivo",
             3: "3 · Sin cargo", 4: "4 · Disputa", 5: "5 · Desconocido", 6: "6 · Viaje anulado"}
mapa_tarifa = {1: "1 · Tarifa estándar", 2: "2 · JFK", 3: "3 · Newark",
               4: "4 · Nassau/Westchester", 5: "5 · Tarifa negociada",
               6: "6 · Viaje compartido", 99: "99 · Desconocido"}

resumen_categoricas = []
for variable, mapa in [("payment_type", mapa_pago), ("RatecodeID", mapa_tarifa),
                       ("VendorID", None), ("store_and_fwd_flag", None)]:
    conteo = df[variable].value_counts(dropna=False).head(8)
    for categoria, cantidad in conteo.items():
        etiqueta = mapa.get(categoria, str(categoria)) if mapa else str(categoria)
        resumen_categoricas.append({
            "variable": variable, "categoria": etiqueta, "cantidad": cantidad,
            "porcentaje": round(cantidad / len(df) * 100, 2)
        })

pd.DataFrame(resumen_categoricas)
""")

code(r"""
mapa_borough = zonas.set_index("zona_id").borough.to_dict()
origen_borough = df.PULocationID.map(mapa_borough).fillna("Desconocido").value_counts().reset_index()
origen_borough.columns = ["borough", "cantidad_viajes"]

fig = px.bar(origen_borough, x="borough", y="cantidad_viajes", text_auto=".3s",
             title="Cantidad de viajes según comuna (borough) de origen",
             labels={"borough": "Comuna de origen", "cantidad_viajes": "Cantidad de viajes"})
fig.update_yaxes(type="log", title="Cantidad de viajes (escala logarítmica)")
mostrar(fig, "eda_borough")
""")

md(r"""
**Interpretación.** El 93 % de los viajes se paga con tarjeta de crédito o efectivo y el 89,8 %
utiliza tarifa estándar; las tarifas especiales de aeropuerto (JFK y Newark) constituyen un
segmento minoritario pero **operacionalmente distinto**, con viajes mucho más largos. La escala
logarítmica del gráfico por comuna revela una concentración extrema: **Manhattan explica la
inmensa mayoría de los orígenes**, seguido por Queens (donde se ubican los aeropuertos JFK y
LaGuardia), mientras Staten Island y EWR aportan apenas decenas de viajes.

Consecuencia: las zonas de origen/destino tienen 260 categorías con frecuencias muy desiguales, por
lo que una codificación *one-hot* directa generaría cientos de columnas dispersas. Se resuelve en la
sección 3 combinando agregación geográfica (comuna, tipo de zona) con codificación por objetivo.

### 2.10 Patrones temporales de la operación
""")

code(r"""
df["hora"] = df.tpep_pickup_datetime.dt.hour
df["dia_semana"] = df.tpep_pickup_datetime.dt.dayofweek

# Se calcula sobre viajes con duración plausible, para que los promedios sean informativos.
plausibles = df.duracion_min.between(1, 120)

resumen_hora = (df[plausibles].groupby("hora")
                .agg(cantidad_viajes=("duracion_min", "size"),
                     duracion_promedio=("duracion_min", "mean"),
                     distancia_promedio=("trip_distance", "median"))
                .reset_index())

fig = go.Figure()
fig.add_trace(go.Bar(x=resumen_hora.hora, y=resumen_hora.cantidad_viajes,
                     name="Cantidad de viajes", marker_color="#9ecae1"))
fig.add_trace(go.Scatter(x=resumen_hora.hora, y=resumen_hora.duracion_promedio,
                         name="Duración promedio (min)", yaxis="y2",
                         mode="lines+markers", line=dict(color="#d62728", width=3)))
fig.update_layout(
    title="Demanda y duración promedio de los viajes según hora de inicio",
    xaxis_title="Hora de inicio del viaje", yaxis_title="Cantidad de viajes",
    yaxis2=dict(title="Duración promedio (minutos)", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"))
mostrar(fig, "eda_hora")
resumen_hora
""")

code(r"""
nombres_dias = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
                4: "Viernes", 5: "Sábado", 6: "Domingo"}

matriz_duracion = (df[plausibles]
                   .pivot_table(index="dia_semana", columns="hora",
                                values="duracion_min", aggfunc="mean")
                   .rename(index=nombres_dias))

fig = px.imshow(matriz_duracion, color_continuous_scale="RdYlGn_r", aspect="auto",
                labels=dict(x="Hora de inicio", y="Día de la semana", color="Minutos"),
                title="Duración promedio del viaje según día de la semana y hora de inicio")
mostrar(fig, "eda_heatmap_hora_dia", alto=420)
""")

md(r"""
**Interpretación.** Los patrones temporales son nítidos y de alto valor operacional:

- La **demanda** tiene su mínimo a las 4:00 (16.123 viajes) y su máximo a las 18:00 (210.582
  viajes): una relación de 13 a 1 entre la hora más baja y la más alta.
- La **duración promedio no sigue la curva de la demanda**: su mínimo está a las 2:00 (12,1 min) y
  su máximo a las 16:00 (16,9 min). La diferencia es de **cerca de 40 %**, y no se explica por la
  distancia: en todo el horario diurno la distancia mediana se mantiene estable en torno a 1,6
  millas. Es congestión pura.
- Las **05:00 constituyen una excepción interesante**: pocos viajes pero duración alta (16,6 min)
  con una distancia mediana de 2,64 millas, muy superior al resto del día. Corresponde al patrón de
  traslados tempranos al aeropuerto: viajes largos por vías rápidas, no congestión.
- El mapa de calor muestra que la congestión es un fenómeno de **días hábiles en horario de tarde**;
  las madrugadas de sábado y domingo son los momentos más rápidos de la semana.

Este comportamiento es exactamente el que una regla de negocio basada en promedios no captura, y
constituye la principal justificación del proyecto: las variables `hora` y `dia_semana` deben formar
parte del modelo.

### 2.11 Matriz de correlación
""")

code(r"""
variables_correlacion = ["duracion_min", "trip_distance", "passenger_count", "hora",
                         "dia_semana", "fare_amount", "total_amount", "tip_amount"]
matriz_correlacion = df[variables_correlacion].corr(numeric_only=True)

fig = px.imshow(matriz_correlacion.round(3), text_auto=True, aspect="auto",
                color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                title="Matriz de correlación de Pearson (datos sin depurar)")
mostrar(fig, "eda_correlacion_sucia", alto=520)

print(f"Correlación distancia-duración SIN depurar: {df.trip_distance.corr(df.duracion_min):.4f}")
""")

md(r"""
**Interpretación — hallazgo central del EDA.** La correlación entre distancia y duración es de
**0,005**: prácticamente nula. Ese resultado es contraintuitivo, porque la distancia es el
determinante físico evidente de la duración de un viaje.

La explicación no es que la relación no exista, sino que **los valores extremos la ocultan**: unos
pocos miles de registros con distancias de cientos de miles de millas o duraciones de días dominan
por completo el cálculo del coeficiente de Pearson, que es sensible a valores atípicos. La misma
matriz muestra correlaciones bajas para todas las variables monetarias, cuando por construcción la
tarifa depende del tiempo y la distancia.

Este hallazgo demuestra por qué el análisis exploratorio debe preceder al modelamiento: **si se
hubiera hecho selección de variables con esta matriz, se habría descartado la variable más
predictiva del problema**. La correlación se vuelve a calcular tras la depuración en la sección 3.6.
""")

# ==========================================================================
md(r"""
## 3. Preparación de los datos  *(15 puntos)*

### 3.1 Tratamiento de valores extremos e inconsistencias

Se aplican filtros de calidad derivados directamente de los hallazgos del EDA. Cada criterio tiene
una justificación operacional, no estadística arbitraria:

| Filtro | Criterio | Justificación |
|---|---|---|
| Período | Inicio dentro de enero 2024 | El archivo corresponde a enero de 2024; hay registros de 2002 por error del taxímetro. |
| Duración | Entre 1 y 120 minutos | Bajo 1 minuto no hay servicio efectivo; sobre 2 horas se trata de viajes no urbanos o registros mal cerrados (percentil 99 = 60,5 min). |
| Distancia | Entre 0,1 y 100 millas | Excluye distancia cero (taxímetro sin registrar) y valores físicamente imposibles. |
| Velocidad implícita | Entre 1 y 80 mph | Filtro cruzado: detecta combinaciones inconsistentes entre distancia y tiempo que los filtros individuales no capturan. |
| Zona | Excluir 264 y 265 | Códigos que representan zona desconocida o fuera de la ciudad: no aportan información geográfica. |
| Tarifa | Excluir `RatecodeID = 99` | Código reservado a "tarifa desconocida", inconsistente con el resto. |
| Monto | `total_amount > 0` | Los montos negativos o nulos corresponden a anulaciones y reversos contables, no a viajes reales. |

El criterio general es **conservador**: se busca eliminar registros inválidos, no recortar la
variabilidad legítima del negocio.
""")

code(r"""
inicio = perf_counter()
registros_iniciales = len(df)
exclusiones = {}

def aplicar_filtro(datos, mascara_valida, nombre):
    '''Aplica un filtro, registra cuántos registros excluye y devuelve el dataset filtrado.'''
    excluidos = int((~mascara_valida).sum())
    exclusiones[nombre] = excluidos
    return datos.loc[mascara_valida].copy()

df["velocidad_mph"] = df.trip_distance / (df.duracion_min / 60)

df = aplicar_filtro(df, (df.tpep_pickup_datetime >= "2024-01-01") &
                        (df.tpep_pickup_datetime < "2024-02-01"), "Fecha fuera de enero 2024")
df = aplicar_filtro(df, df.duracion_min.between(1, 120), "Duración fuera de [1, 120] minutos")
df = aplicar_filtro(df, df.trip_distance.between(0.1, 100), "Distancia fuera de [0.1, 100] millas")
df = aplicar_filtro(df, df.velocidad_mph.between(1, 80), "Velocidad implícita fuera de [1, 80] mph")
df = aplicar_filtro(df, ~df.PULocationID.isin([264, 265]) & ~df.DOLocationID.isin([264, 265]),
                    "Zona de origen o destino desconocida")
df = aplicar_filtro(df, df.RatecodeID.isna() | (df.RatecodeID != 99), "RatecodeID = 99 (desconocido)")
df = aplicar_filtro(df, df.total_amount > 0, "Monto total menor o igual a cero")

reporte_exclusiones = pd.DataFrame({
    "registros_excluidos": pd.Series(exclusiones),
    "porcentaje_del_total": (pd.Series(exclusiones) / registros_iniciales * 100).round(3)
})
print(reporte_exclusiones)
print(f"\nRegistros iniciales : {registros_iniciales:,}")
print(f"Registros retenidos : {len(df):,} ({len(df) / registros_iniciales:.2%})")
print(f"Registros excluidos : {registros_iniciales - len(df):,} ({1 - len(df) / registros_iniciales:.2%})")
registrar_tiempo("Filtros de calidad", inicio)
""")

md(r"""
**Interpretación.** Se retiene el **94,6 %** de los registros: la depuración elimina anomalías sin
sacrificar volumen de información. El filtro más selectivo es el de distancia, seguido por el de
duración. La pérdida es marginal frente al beneficio de trabajar con datos internamente
consistentes, y el dataset resultante mantiene **más de 2,8 millones de viajes**, muy por encima del
mínimo exigido.

### 3.2 Tratamiento de valores nulos

Los nulos afectan a cinco variables secundarias y nunca al objetivo. En lugar de eliminar el 4,7 %
de las filas, se imputa con criterios explícitos:

| Variable | Criterio de imputación | Justificación |
|---|---|---|
| `passenger_count` | Moda (1 pasajero) y recorte al rango [1, 6] | Es el valor abrumadoramente mayoritario; 0 pasajeros es inválido y más de 6 excede la capacidad legal de un taxi. |
| `RatecodeID` | Tarifa estándar (1) | Es la tarifa aplicada en el 89,8 % de los viajes; asumir el caso general es la opción de mínimo riesgo. |
| `store_and_fwd_flag` | "N" (transmisión en línea) | La ausencia del indicador equivale a que no se activó el modo diferido. |
| `payment_type = 0` | Categoría explícita "Desconocido" | Se conserva como categoría propia: el código 0 aparece solo en los registros incompletos y esa condición es en sí misma informativa. |
| `congestion_surcharge`, `Airport_fee` | No se imputan | Son variables monetarias excluidas del modelo por fuga de información. |

Criterio metodológico: las imputaciones utilizan valores fijos de negocio (moda y categoría por
defecto), no estadísticos calculados sobre el conjunto completo, de modo que **no transfieren
información del conjunto de prueba al de entrenamiento**.
""")

code(r"""
df["passenger_count"] = df.passenger_count.fillna(1).clip(1, 6).astype(int)
df["RatecodeID"] = df.RatecodeID.fillna(1).astype(int)
df["store_and_fwd_flag"] = df.store_and_fwd_flag.fillna("N")
df["payment_type"] = df.payment_type.astype(int)

nulos_restantes = df.isna().sum()
print("Nulos restantes en las variables que se utilizarán:")
print(nulos_restantes[nulos_restantes > 0] if nulos_restantes.sum() else "Ninguno")
print("\nDistribución de pasajeros después de la imputación:")
print(df.passenger_count.value_counts().sort_index())
""")

md(r"""
### 3.3 Verificación de registros duplicados posterior a la depuración
""")

code(r"""
duplicados_finales = df.duplicated().sum()
print(f"Duplicados exactos tras la depuración : {duplicados_finales:,}")
if duplicados_finales:
    df = df.drop_duplicates()
    print(f"Registros después de eliminarlos      : {len(df):,}")
else:
    print("No se requiere eliminación: cada fila representa un viaje único.")
""")

md(r"""
### 3.4 Efecto de la depuración sobre la variable objetivo
""")

code(r"""
fig = go.Figure()
fig.add_trace(go.Box(y=df.duracion_min.sample(8_000, random_state=RANDOM_STATE),
                     name="Duración depurada", boxpoints=False, marker_color="#2a9d8f"))
fig.add_trace(go.Box(y=df.trip_distance.sample(8_000, random_state=RANDOM_STATE),
                     name="Distancia depurada", boxpoints=False, marker_color="#457b9d"))
fig.update_layout(title="Distribución de duración (minutos) y distancia (millas) tras la depuración",
                  yaxis_title="Valor")
mostrar(fig, "prep_boxplot")

print("Duración (minutos) tras la depuración:")
print(df.duracion_min.describe())
""")

md(r"""
### 3.5 Ingeniería de características

Se construyen variables con significado operacional a partir de las marcas de tiempo, de la tabla de
zonas TLC y de la relación entre origen y destino:

| Variable creada | Definición | Sentido de negocio |
|---|---|---|
| `hora` | Hora de inicio (0–23) | El EDA mostró variaciones de más de 50 % en la duración según la hora. |
| `dia_semana`, `es_fin_semana` | Día (0–6) e indicador de sábado/domingo | La congestión es un fenómeno de días hábiles. |
| `dia_mes` | Día del mes | Captura efectos de calendario (inicio de mes, feriados). |
| `es_hora_punta` | Inicio entre 7–9 h o 16–19 h | Sintetiza el efecto de congestión en una variable directamente accionable. |
| `franja_horaria` | Madrugada, mañana, punta AM, tarde, punta PM, noche | Versión categórica de la hora, útil para modelos no lineales y para reportería. |
| `pu_borough`, `do_borough` | Comuna de origen y destino (unión con zonas TLC) | Reduce 260 zonas a 7 categorías interpretables. |
| `pu_servicio`, `do_servicio` | Tipo de zona (Yellow Zone, Boro Zone, Aeropuertos, EWR) | Distingue el centro urbano de la periferia y de los aeropuertos. |
| `es_aeropuerto` | Origen o destino en zona de aeropuerto | Los viajes de aeropuerto son estructuralmente más largos. |
| `misma_zona`, `mismo_borough` | Origen y destino coinciden | Diferencia viajes internos de viajes entre comunas. |
| `log_distancia` | log(1 + distancia) | Corrige la asimetría de la distancia y ayuda a los modelos lineales. |

Todas las variables se calculan con información **conocida al momento de iniciar el viaje**, lo que
mantiene el modelo utilizable en producción.
""")

code(r"""
inicio = perf_counter()

mapa_servicio = zonas.set_index("zona_id").servicio.to_dict()

df["pu_borough"] = df.PULocationID.map(mapa_borough).fillna("Desconocido")
df["do_borough"] = df.DOLocationID.map(mapa_borough).fillna("Desconocido")
df["pu_servicio"] = df.PULocationID.map(mapa_servicio).fillna("Desconocido")
df["do_servicio"] = df.DOLocationID.map(mapa_servicio).fillna("Desconocido")

df["dia_mes"] = df.tpep_pickup_datetime.dt.day
df["es_fin_semana"] = (df.dia_semana >= 5).astype(int)
df["es_hora_punta"] = df.hora.isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
df["es_aeropuerto"] = ((df.pu_servicio == "Airports") | (df.do_servicio == "Airports")).astype(int)
df["misma_zona"] = (df.PULocationID == df.DOLocationID).astype(int)
df["mismo_borough"] = (df.pu_borough == df.do_borough).astype(int)
df["log_distancia"] = np.log1p(df.trip_distance)

# pd.cut corta una variable numérica en intervalos y asigna una etiqueta a cada uno.
df["franja_horaria"] = pd.cut(
    df.hora, bins=[-1, 5, 9, 12, 15, 19, 23],
    labels=["Madrugada", "Punta AM", "Media mañana", "Tarde", "Punta PM", "Noche"]
).astype(str)

registrar_tiempo("Ingeniería de características", inicio)
df[["duracion_min", "trip_distance", "log_distancia", "hora", "franja_horaria", "dia_semana",
    "es_fin_semana", "es_hora_punta", "pu_borough", "do_borough", "es_aeropuerto",
    "misma_zona", "mismo_borough"]].head(10)
""")

md(r"""
### 3.6 Análisis exploratorio posterior a la depuración

Se recalcula la matriz de correlación para verificar el efecto de la depuración sobre la relación
entre las variables y el objetivo.
""")

code(r"""
variables_modelo = ["duracion_min", "trip_distance", "log_distancia", "velocidad_mph",
                    "passenger_count", "hora", "dia_semana", "es_fin_semana",
                    "es_hora_punta", "es_aeropuerto", "misma_zona", "mismo_borough"]
matriz_limpia = df[variables_modelo].corr()

fig = px.imshow(matriz_limpia.round(2), text_auto=True, aspect="auto",
                color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                title="Matriz de correlación de Pearson (datos depurados)")
mostrar(fig, "prep_correlacion_limpia", alto=620)

correlaciones_objetivo = (matriz_limpia["duracion_min"].drop("duracion_min")
                          .sort_values(key=abs, ascending=False))
print("Correlación de cada variable con la duración del viaje:")
print(correlaciones_objetivo)
""")

code(r"""
muestra_grafico = df.sample(6_000, random_state=RANDOM_STATE)

fig = px.scatter(muestra_grafico, x="trip_distance", y="duracion_min",
                 color="es_hora_punta", opacity=0.45,
                 color_continuous_scale=["#457b9d", "#e63946"],
                 title="Relación entre distancia y duración del viaje (muestra de 6.000 viajes)",
                 labels={"trip_distance": "Distancia (millas)", "duracion_min": "Duración (minutos)",
                         "es_hora_punta": "Hora punta"})
mostrar(fig, "prep_dispersion_distancia")
""")

md(r"""
**Interpretación — el efecto de la preparación de datos.** Tras la depuración, la correlación entre
distancia y duración pasa de **0,005 a 0,810**. El mismo dato, con el mismo coeficiente, entrega
conclusiones opuestas según la calidad de los registros: es la evidencia más clara de que la
preparación de datos no es un trámite previo al modelamiento, sino parte del análisis.

Otras lecturas relevantes:

- `log_distancia` correlaciona **algo más** que la distancia lineal (0,843 frente a 0,810): la
  transformación logarítmica linealiza la relación, ya que el tiempo adicional por milla decrece en
  los viajes largos (vías más rápidas). Se conservan ambas variables.
- `mismo_borough` presenta la correlación negativa más fuerte (−0,64) y `es_aeropuerto` una
  correlación positiva alta (0,58): los viajes que cruzan comunas o involucran aeropuertos son
  estructuralmente más largos. Ambas variables fueron construidas en este proyecto, no venían en el
  archivo original.
- `hora` y `es_hora_punta` muestran correlaciones **cercanas a cero** (0,010 y 0,016) pese al patrón
  evidente del EDA. La razón es que la correlación de Pearson solo mide relación **lineal y
  marginal**: el efecto de la hora es no lineal (sube y baja durante el día) y opera por
  **interacción** con la distancia. Este punto es central y se confirma más adelante: la importancia
  por permutación situará a `hora` como la segunda variable más relevante del modelo.
- `velocidad_mph` correlaciona positivamente con la duración (0,34) porque los viajes largos usan
  vías más rápidas, pero **se excluye del modelo**: se calcula a partir de la duración y no está
  disponible antes de realizar el viaje. Incluirla sería fuga de información.
- El gráfico de dispersión muestra que, a igual distancia, los viajes en **hora punta** se ubican
  sistemáticamente por sobre la nube de puntos: la variable temporal aporta información que la
  distancia no contiene.

### 3.7 Selección de predictores y exclusión por fuga de información

Se descartan explícitamente:

- **Variables monetarias** (`fare_amount`, `extra`, `mta_tax`, `tip_amount`, `tolls_amount`,
  `improvement_surcharge`, `total_amount`, `congestion_surcharge`, `Airport_fee`): la tarifa del
  taxímetro se calcula en función del tiempo transcurrido, por lo que conocerla equivale a conocer
  parcialmente la respuesta. Solo existen una vez terminado el viaje.
- **`tpep_dropoff_datetime`**: define el objetivo.
- **`velocidad_mph`**: derivada de la duración.
""")

code(r"""
VARIABLES_NUMERICAS = [
    "trip_distance", "log_distancia", "hora", "dia_semana", "dia_mes", "passenger_count",
    "es_fin_semana", "es_hora_punta", "es_aeropuerto", "misma_zona", "mismo_borough",
]
VARIABLES_CATEGORICAS = [
    "pu_borough", "do_borough", "pu_servicio", "do_servicio", "franja_horaria",
    "VendorID", "RatecodeID", "payment_type", "store_and_fwd_flag",
]
VARIABLES_ALTA_CARDINALIDAD = ["PULocationID", "DOLocationID"]
OBJETIVO = "duracion_min"

PREDICTORES = VARIABLES_NUMERICAS + VARIABLES_CATEGORICAS + VARIABLES_ALTA_CARDINALIDAD

print(f"Predictores numéricos          : {len(VARIABLES_NUMERICAS)}")
print(f"Predictores categóricos        : {len(VARIABLES_CATEGORICAS)}")
print(f"Predictores de alta cardinalidad: {len(VARIABLES_ALTA_CARDINALIDAD)} "
      f"({df.PULocationID.nunique()} y {df.DOLocationID.nunique()} categorías)")
print(f"Total de predictores           : {len(PREDICTORES)}")
print(f"Variable objetivo              : {OBJETIVO}")
""")

md(r"""
### 3.8 Muestreo para el modelamiento

El dataset depurado supera los 2,8 millones de registros. Entrenar y validar múltiples algoritmos
—incluyendo búsqueda de hiperparámetros con validación cruzada— sobre ese volumen es
computacionalmente costoso en un entorno como Google Colab.

Se trabaja con una **muestra aleatoria simple de 400.000 viajes** (14 % del total depurado, cuatro
veces el mínimo exigido por la evaluación). Al ser aleatoria y de gran tamaño, conserva las
distribuciones de la población; a continuación se verifica empíricamente esa representatividad.
""")

code(r"""
TAMANO_MUESTRA = 400_000
muestra = df.sample(n=TAMANO_MUESTRA, random_state=RANDOM_STATE)

comparacion = pd.DataFrame({
    "poblacion_depurada": df[["duracion_min", "trip_distance", "hora", "passenger_count"]].mean(),
    "muestra": muestra[["duracion_min", "trip_distance", "hora", "passenger_count"]].mean(),
})
comparacion["diferencia_%"] = ((comparacion.muestra / comparacion.poblacion_depurada - 1) * 100).round(3)
print(f"Población depurada : {len(df):,} viajes")
print(f"Muestra utilizada  : {len(muestra):,} viajes ({len(muestra)/len(df):.1%})\n")
print("Comparación de medias (verificación de representatividad):")
print(comparacion)
print("\nDesviación estándar de la duración — población:",
      f"{df.duracion_min.std():.3f} | muestra: {muestra.duracion_min.std():.3f}")
""")

md(r"""
**Interpretación.** Las medias de la muestra difieren de las poblacionales en menos de 0,5 % y la
desviación estándar es prácticamente idéntica: la muestra es representativa y las conclusiones del
modelo son extrapolables al conjunto completo.

### 3.9 Codificación de variables categóricas y escalamiento

Se emplean tres tratamientos según la naturaleza de cada grupo de variables, integrados en un
`ColumnTransformer`:

| Grupo | Técnica | Justificación |
|---|---|---|
| Numéricas | `StandardScaler` | Necesario para la regresión lineal y **obligatorio para PCA**, que es sensible a la escala. Los árboles no lo requieren, pero al usar un único preprocesamiento se mantiene la comparabilidad entre modelos. |
| Categóricas de baja cardinalidad | `OneHotEncoder` | Las 9 variables suman pocas categorías; el *one-hot* no impone un orden inexistente. `handle_unknown="ignore"` evita fallas ante categorías no vistas en producción. |
| Zonas de origen/destino (más de 250 categorías cada una) | `TargetEncoder` | Un *one-hot* generaría más de 500 columnas dispersas. El codificador por objetivo reemplaza cada zona por la duración media asociada, usando **validación cruzada interna** para evitar fuga de información. |

El uso de un `Pipeline` garantiza que todas las transformaciones se **aprendan solo con los datos de
entrenamiento** y se apliquen igual en producción.
""")

code(r"""
# ============================================================
# Cómo funciona este bloque
# ============================================================
# ColumnTransformer aplica una transformación distinta a cada grupo de columnas y
# une los resultados en una sola matriz numérica:
#
#   StandardScaler : lleva cada variable numérica a media 0 y desviación estándar 1,
#                    tal como se trabajó antes de aplicar PCA en el Módulo 10.
#
#   OneHotEncoder  : convierte una columna de categorías en varias columnas de 0 y 1,
#                    una por categoría. Es necesario porque un modelo no opera sobre
#                    texto, y evita inventar un orden inexistente: si se codificara
#                    Manhattan = 1 y Queens = 2, el modelo interpretaría que 2 > 1.
#
#   TargetEncoder  : reemplaza cada zona por la duración promedio de los viajes de esa
#                    zona. Como ese promedio se calcula a partir de la variable que se
#                    quiere predecir, existe riesgo de fuga de información; para
#                    evitarlo, el codificador usa validación cruzada interna (calcula
#                    el promedio con una parte de los datos y lo aplica a otra), el
#                    mismo principio de la validación cruzada del Módulo 5.
preprocesador = ColumnTransformer([
    ("numericas", StandardScaler(), VARIABLES_NUMERICAS),
    ("categoricas", OneHotEncoder(handle_unknown="ignore", sparse_output=False, drop=None),
     VARIABLES_CATEGORICAS),
    ("zonas", TargetEncoder(random_state=RANDOM_STATE), VARIABLES_ALTA_CARDINALIDAD),
], verbose_feature_names_out=False)

print(preprocesador)
""")

md(r"""
### 3.10 División en conjuntos de entrenamiento y prueba

Se utiliza una división aleatoria **80 % entrenamiento / 20 % prueba** con semilla fija. Como cada
observación es un viaje independiente y no se está pronosticando una serie de tiempo, la división
aleatoria es adecuada; se verifica que ambos conjuntos tengan distribuciones equivalentes.
""")

code(r"""
X = muestra[PREDICTORES].copy()
for columna in VARIABLES_CATEGORICAS + VARIABLES_ALTA_CARDINALIDAD:
    X[columna] = X[columna].astype(str)     # los identificadores se tratan como categorías
y = muestra[OBJETIVO].to_numpy()

X_entrena, X_prueba, y_entrena, y_prueba = train_test_split(
    X, y, test_size=0.2, random_state=RANDOM_STATE
)

print(f"Entrenamiento : {X_entrena.shape[0]:,} viajes ({X_entrena.shape[1]} predictores)")
print(f"Prueba        : {X_prueba.shape[0]:,} viajes")
print(f"\nDuración promedio — entrenamiento: {y_entrena.mean():.3f} min | prueba: {y_prueba.mean():.3f} min")
print(f"Desviación estándar — entrenamiento: {y_entrena.std():.3f} | prueba: {y_prueba.std():.3f}")
""")

code(r"""
inicio = perf_counter()
X_entrena_procesado = preprocesador.fit_transform(X_entrena, y_entrena)
X_prueba_procesado = preprocesador.transform(X_prueba)
registrar_tiempo("Preprocesamiento (ajuste y transformación)", inicio)

nombres_caracteristicas = list(preprocesador.get_feature_names_out())
print(f"Matriz de entrenamiento : {X_entrena_procesado.shape}")
print(f"Matriz de prueba        : {X_prueba_procesado.shape}")
print(f"\nCaracterísticas generadas ({len(nombres_caracteristicas)}):")
print(nombres_caracteristicas)
""")

# ==========================================================================
md(r"""
## 4. Reducción de dimensionalidad  *(10 puntos)*

Se aplican y comparan **dos técnicas** estudiadas en el diplomado:

1. **PCA (Análisis de Componentes Principales):** proyecta las variables en un espacio de menor
   dimensión maximizando la varianza explicada. Criterio de selección del número de componentes:
   **conservar el 95 % de la varianza acumulada**, el mismo utilizado en el laboratorio de PCA.
2. **Selección de características por información mutua:** conserva las variables originales con
   mayor dependencia estadística respecto del objetivo. A diferencia de la correlación de Pearson,
   la información mutua detecta relaciones **no lineales**.

Ambas se evalúan por su efecto sobre el desempeño predictivo, que es el criterio que interesa al
negocio.

### 4.1 PCA: determinación del número de componentes
""")

code(r"""
inicio = perf_counter()
pca_completo = PCA(random_state=RANDOM_STATE).fit(X_entrena_procesado)
varianza_acumulada = np.cumsum(pca_completo.explained_variance_ratio_)
n_componentes_95 = int(np.argmax(varianza_acumulada >= 0.95) + 1)
registrar_tiempo("PCA (análisis completo)", inicio)

print(f"Características originales      : {X_entrena_procesado.shape[1]}")
print(f"Componentes para 95 % de varianza: {n_componentes_95}")
print(f"Varianza conservada             : {varianza_acumulada[n_componentes_95 - 1]:.2%}")
print(f"Reducción de dimensionalidad    : "
      f"{1 - n_componentes_95 / X_entrena_procesado.shape[1]:.1%}")
""")

code(r"""
fig = go.Figure()
fig.add_trace(go.Bar(x=np.arange(1, len(varianza_acumulada) + 1),
                     y=pca_completo.explained_variance_ratio_,
                     name="Varianza individual", marker_color="#a8dadc"))
fig.add_trace(go.Scatter(x=np.arange(1, len(varianza_acumulada) + 1), y=varianza_acumulada,
                         name="Varianza acumulada", mode="lines+markers",
                         line=dict(color="#1d3557", width=3)))
fig.add_hline(y=0.95, line_dash="dash", line_color="#e63946",
              annotation_text="95 % de varianza", annotation_position="bottom right")
fig.add_vline(x=n_componentes_95, line_dash="dot", line_color="#e63946",
              annotation_text=f"{n_componentes_95} componentes", annotation_position="top left")
fig.update_layout(title="Varianza explicada por componente principal (gráfico de sedimentación)",
                  xaxis_title="Número de componente principal",
                  yaxis_title="Proporción de varianza explicada",
                  legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"))
mostrar(fig, "pca_varianza")
""")

code(r"""
pca_95 = PCA(n_components=n_componentes_95, random_state=RANDOM_STATE)
X_entrena_pca = pca_95.fit_transform(X_entrena_procesado)
X_prueba_pca = pca_95.transform(X_prueba_procesado)

print(f"Matriz original : {X_entrena_procesado.shape}")
print(f"Matriz reducida : {X_entrena_pca.shape}")

# Proyección de los viajes en las dos primeras componentes, coloreada por duración.
indices_visual = np.random.RandomState(RANDOM_STATE).choice(len(X_entrena_pca), 5_000, replace=False)
proyeccion = pd.DataFrame(X_entrena_pca[indices_visual, :2], columns=["PC1", "PC2"])
proyeccion["duracion_min"] = y_entrena[indices_visual]

fig = px.scatter(proyeccion, x="PC1", y="PC2", color="duracion_min", opacity=0.6,
                 color_continuous_scale="Turbo",
                 title="Proyección de los viajes en las dos primeras componentes principales",
                 labels={"PC1": f"PC1 ({pca_95.explained_variance_ratio_[0]:.1%} de varianza)",
                         "PC2": f"PC2 ({pca_95.explained_variance_ratio_[1]:.1%} de varianza)",
                         "duracion_min": "Duración (min)"})
mostrar(fig, "pca_proyeccion")
""")

md(r"""
**Interpretación.** El 95 % de la varianza se concentra en muy pocas componentes: la matriz pasa de
**53 a 8 dimensiones**, una reducción cercana al 85 %. Esto ocurre porque muchas columnas del
*one-hot* son redundantes entre sí (por ejemplo, comuna de origen y tipo de zona de origen describen
parcialmente lo mismo) y porque las variables binarias, al tener varianza baja, aportan poco a la
varianza total.

La proyección en las dos primeras componentes muestra un gradiente de color: los viajes de mayor
duración se ordenan a lo largo de PC1, lo que confirma que la primera componente captura
esencialmente el "tamaño" del viaje (distancia y variables asociadas).

**Advertencia metodológica:** PCA maximiza varianza, no capacidad predictiva. La varianza de una
variable no garantiza que aporte información sobre el objetivo, por lo que el efecto real de la
reducción debe medirse comparando el desempeño del modelo (sección 4.3).

### 4.2 Selección de características por información mutua
""")

code(r"""
inicio = perf_counter()
# La información mutua mide cuánta información aporta una variable sobre el objetivo,
# incluso cuando la relación no es una línea recta (a diferencia de la correlación de
# Pearson, que solo detecta relaciones lineales).
# Limitación central, que este proyecto termina comprobando: la evalúa variable por
# variable, de modo que no puede detectar el aporte que surge de la interacción entre
# dos o más variables.
#
# El cálculo es costoso: se estima sobre una submuestra de 25.000 observaciones,
# suficiente para ordenar las variables de forma estable.
indices_mi = np.random.RandomState(RANDOM_STATE).choice(len(X_entrena_procesado), 25_000, replace=False)
informacion_mutua = mutual_info_regression(
    X_entrena_procesado[indices_mi], y_entrena[indices_mi], random_state=RANDOM_STATE
)
registrar_tiempo("Información mutua", inicio)

ranking_mi = (pd.Series(informacion_mutua, index=nombres_caracteristicas)
              .sort_values(ascending=False))
K_SELECCIONADAS = 15
caracteristicas_top = ranking_mi.head(K_SELECCIONADAS).index.tolist()

grafico_mi = (ranking_mi.head(20).iloc[::-1].rename_axis("caracteristica")
              .reset_index(name="informacion_mutua"))
fig = px.bar(grafico_mi, x="informacion_mutua", y="caracteristica", orientation="h",
             title="Información mutua con la duración del viaje (20 características principales)",
             labels={"informacion_mutua": "Información mutua estimada",
                     "caracteristica": "Característica"})
fig.update_layout(showlegend=False)
mostrar(fig, "seleccion_informacion_mutua", alto=620)

print(f"Características seleccionadas (K = {K_SELECCIONADAS}):")
for posicion, nombre in enumerate(caracteristicas_top, start=1):
    print(f"  {posicion:2d}. {nombre:35s} {ranking_mi[nombre]:.4f}")
""")

md(r"""
**Criterio de selección de K.** El *ranking* muestra una caída abrupta después de las dos variables
de distancia y una cola prácticamente plana. Se fija **K = 15**, punto en que se han incorporado
todas las características con información mutua apreciable antes de entrar en la zona plana, con una
reducción de dimensionalidad del 72 %.

Conviene anticipar una limitación de este criterio: la información mutua se calcula **variable por
variable frente al objetivo**, de modo que mide aporte *marginal* y es ciega a los efectos de
interacción. Las variables temporales (`hora`, `dia_semana`, `franja_horaria`) quedan fuera del
*top* 15 justamente porque su efecto no es marginal sino interactivo. La sección siguiente muestra
las consecuencias.

### 4.3 Impacto de la reducción de dimensionalidad sobre el desempeño

Se compara el mismo algoritmo (`HistGradientBoostingRegressor` con parámetros por defecto) sobre
tres representaciones de los datos: todas las características, componentes de PCA y subconjunto
seleccionado por información mutua.
""")

code(r"""
inicio = perf_counter()
indices_top = [nombres_caracteristicas.index(nombre) for nombre in caracteristicas_top]

representaciones = {
    f"Sin reducción ({X_entrena_procesado.shape[1]} características)":
        (X_entrena_procesado, X_prueba_procesado),
    f"PCA — {n_componentes_95} componentes (95 % var.)": (X_entrena_pca, X_prueba_pca),
    f"Información mutua — {K_SELECCIONADAS} características":
        (X_entrena_procesado[:, indices_top], X_prueba_procesado[:, indices_top]),
}

comparacion_reduccion = []
for nombre, (matriz_entrena, matriz_prueba) in representaciones.items():
    modelo = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    marca = perf_counter()
    modelo.fit(matriz_entrena, y_entrena)
    tiempo_ajuste = perf_counter() - marca
    resultado = metricas_regresion(y_prueba, modelo.predict(matriz_prueba))
    resultado.update({"Representación": nombre, "Dimensiones": matriz_entrena.shape[1],
                      "Tiempo de ajuste (s)": round(tiempo_ajuste, 2)})
    comparacion_reduccion.append(resultado)

tabla_reduccion = (pd.DataFrame(comparacion_reduccion)
                   [["Representación", "Dimensiones", "MAE", "RMSE", "R2", "Tiempo de ajuste (s)"]])
registrar_tiempo("Comparación de representaciones", inicio)
tabla_reduccion
""")

code(r"""
fig = px.bar(tabla_reduccion, x="Representación", y="R2", text_auto=".4f",
             color="Representación",
             title="Coeficiente de determinación (R²) según técnica de reducción de dimensionalidad",
             labels={"R2": "R² en el conjunto de prueba"})
fig.update_layout(showlegend=False, xaxis_title="")
fig.update_xaxes(tickangle=-15)
mostrar(fig, "reduccion_comparacion")
""")

md(r"""
**Interpretación — el impacto de la reducción de dimensionalidad.** Ninguna de las dos técnicas
mejoró el desempeño, y el orden del resultado es revelador:

- **Sin reducción** (53 características) el modelo alcanza el mejor R² (0,838) y el menor error
  (MAE 2,89 min).
- **PCA con 95 % de varianza** reduce la matriz un 85 %, pero el R² cae a 0,795 y el MAE sube a
  3,26 minutos. PCA construye combinaciones lineales de variables: destruye la estructura original
  que los modelos de árboles aprovechan mediante cortes sobre variables individuales, y asigna
  varianza a columnas del *one-hot* que poco dicen sobre la duración. **Maximizar varianza no es
  maximizar información sobre el objetivo.**
- **La selección por información mutua** (15 características) resulta incluso **peor** que PCA:
  R² 0,754 y MAE 3,54 minutos. El motivo es el anticipado en la sección anterior: al ordenar
  variables por su aporte *marginal*, el criterio descartó `hora`, `dia_semana` y `franja_horaria`,
  cuya correlación individual con la duración es casi nula pero que resultan decisivas **en
  interacción** con la distancia y la zona. La caída de casi nueve puntos de R² es la medida exacta
  de cuánto vale esa información temporal.

**Decisión fundamentada:** el modelo final se entrena **sin reducción de dimensionalidad**. Con 53
características el costo computacional es bajo (el ajuste toma segundos) y no existe un problema de
dimensionalidad que justifique sacrificar exactitud. PCA se descarta además porque las componentes no
son interpretables y el negocio requiere explicar sus estimaciones.

Este resultado es en sí mismo un aprendizaje doble: **reducir dimensionalidad no siempre mejora un
modelo** —su aporte depende de que exista redundancia real y del algoritmo empleado—, y **los filtros
univariados de selección de variables son peligrosos cuando el fenómeno es interactivo**, que es
justamente el caso de la movilidad urbana.
""")

# ==========================================================================
md(r"""
## 5. Construcción del modelo  *(20 puntos)*

### 5.1 Selección y justificación de los algoritmos

Se comparan cinco alternativas de complejidad creciente, todas de `scikit-learn`:

| Modelo | Rol | Justificación |
|---|---|---|
| `DummyRegressor` (media) | Línea base trivial | Representa la práctica actual de "usar el promedio histórico". Todo modelo debe superarla. |
| `LinearRegression` | Línea base interpretable | Modelo de referencia; permite cuantificar cuánta señal es lineal. |
| `DecisionTreeRegressor` | Modelo no lineal simple | Captura interacciones y umbrales (hora punta, aeropuerto) pero tiende a sobreajustar. |
| `RandomForestRegressor` | Ensamble por *bagging* | Promedia múltiples árboles y reduce la varianza; robusto pero costoso en datos masivos. |
| `HistGradientBoostingRegressor` | Ensamble por *boosting* | Implementación basada en histogramas, **diseñada para grandes volúmenes**; corrige errores de forma secuencial. Es el equivalente en scikit-learn de las librerías de *gradient boosting* vistas en clases. |

El problema tiene relaciones claramente no lineales (el efecto de la hora depende del día, el de la
distancia depende de la zona), por lo que se anticipa un mejor desempeño de los modelos de árboles.
""")

code(r"""
inicio = perf_counter()

# Dos de los estimadores merecen una nota:
#
#   DummyRegressor(strategy="mean") predice siempre el promedio del entrenamiento.
#   Es el mismo "Baseline" del laboratorio de Aprendizaje Supervisado, expresado con
#   una clase de scikit-learn en lugar de una regla escrita a mano.
#
#   HistGradientBoostingRegressor construye árboles de forma secuencial, donde cada
#   árbol corrige los errores del anterior: es el Gradient Boosting estudiado en la
#   clase de Aprendizaje Supervisado, en su implementación de scikit-learn (la
#   evaluación pide usar esta biblioteca). El prefijo "Hist" indica que agrupa los
#   valores de cada variable en histogramas antes de buscar los cortes, lo que reduce
#   el tiempo de entrenamiento y lo hace apropiado para volúmenes masivos de datos.
candidatos = {
    "Línea base (media)": DummyRegressor(strategy="mean"),
    "Regresión lineal": LinearRegression(),
    "Árbol de decisión": DecisionTreeRegressor(max_depth=12, min_samples_leaf=50,
                                               random_state=RANDOM_STATE),
    "Random Forest": RandomForestRegressor(n_estimators=100, min_samples_leaf=5,
                                          n_jobs=-1, random_state=RANDOM_STATE),
    "Gradient Boosting (Hist)": HistGradientBoostingRegressor(random_state=RANDOM_STATE),
}

resultados_candidatos = []
for nombre, modelo in candidatos.items():
    marca = perf_counter()
    modelo.fit(X_entrena_procesado, y_entrena)
    tiempo_ajuste = perf_counter() - marca
    metricas_prueba = metricas_regresion(y_prueba, modelo.predict(X_prueba_procesado))
    r2_entrenamiento = r2_score(y_entrena, modelo.predict(X_entrena_procesado))
    resultados_candidatos.append({
        "Modelo": nombre, **metricas_prueba,
        "R2_entrenamiento": r2_entrenamiento,
        "Brecha (train - test)": r2_entrenamiento - metricas_prueba["R2"],
        "Tiempo de ajuste (s)": round(tiempo_ajuste, 2),
    })
    print(f"{nombre:28s} MAE={metricas_prueba['MAE']:6.3f}  RMSE={metricas_prueba['RMSE']:6.3f}  "
          f"R²={metricas_prueba['R2']:.4f}  ({tiempo_ajuste:.1f} s)")

tabla_candidatos = pd.DataFrame(resultados_candidatos).sort_values("R2", ascending=False)
registrar_tiempo("Entrenamiento de los modelos candidatos", inicio)
tabla_candidatos
""")

code(r"""
fig = go.Figure()
fig.add_trace(go.Bar(x=tabla_candidatos.Modelo, y=tabla_candidatos.MAE,
                     name="MAE (minutos)", text=tabla_candidatos.MAE.round(3), textposition="outside",
                     marker_color="#457b9d"))
fig.add_trace(go.Bar(x=tabla_candidatos.Modelo, y=tabla_candidatos.RMSE,
                     name="RMSE (minutos)", text=tabla_candidatos.RMSE.round(3), textposition="outside",
                     marker_color="#e76f51"))
fig.update_layout(title="Error de predicción por modelo candidato (conjunto de prueba)",
                  xaxis_title="", yaxis_title="Error en minutos", barmode="group",
                  legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"))
mostrar(fig, "modelos_comparacion")
""")

md(r"""
**Interpretación.** La línea base de la media obtiene un R² de 0 y un error medio absoluto de
**7,84 minutos**: ese es el costo de estimar con promedios históricos, y es la referencia contra la
cual debe medirse todo lo demás. La regresión lineal explica el 76 % de la varianza —buena parte de
la señal es lineal por efecto de la distancia—, pero deja fuera las interacciones.

Los modelos de árboles superan claramente a los lineales. Entre ellos, **con parámetros por defecto
Random Forest obtiene un R² levemente superior** (0,844 frente a 0,838 del *gradient boosting*). Sin
embargo, se selecciona el *gradient boosting* por tres razones:

1. **Sobreajuste.** La columna *brecha (train − test)* muestra el diagnóstico del Módulo 5: Random
   Forest alcanza un R² de 0,920 en entrenamiento frente a 0,844 en prueba (brecha 0,076), es decir
   memoriza; el *boosting* tiene una brecha de apenas 0,008.
2. **Costo computacional.** 56 segundos frente a 4: catorce veces más rápido. Sobre el dataset
   completo la diferencia sería determinante, y también lo es para la búsqueda de hiperparámetros y
   el reentrenamiento periódico.
3. **Margen de mejora.** Los parámetros por defecto del *boosting* son conservadores; al ajustarlos
   (sección 5.3) supera a Random Forest, alcanzando un R² de 0,853 en prueba.

Esta decisión ilustra un criterio metodológico: **el mejor modelo no es el que obtiene la mejor
métrica en una única corrida sin ajustar**, sino el que ofrece el mejor equilibrio entre exactitud,
generalización y viabilidad operacional.

### 5.2 Validación cruzada

Una sola división entrenamiento/prueba puede entregar una estimación optimista o pesimista por azar.
Se aplica **K-Fold con 5 particiones** sobre el conjunto de entrenamiento para estimar la estabilidad
del desempeño, como en el laboratorio de Validación Cruzada.
""")

code(r"""
inicio = perf_counter()
particiones = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

modelos_validacion = {
    "Regresión lineal": LinearRegression(),
    "Árbol de decisión": DecisionTreeRegressor(max_depth=12, min_samples_leaf=50,
                                               random_state=RANDOM_STATE),
    "Gradient Boosting (Hist)": HistGradientBoostingRegressor(random_state=RANDOM_STATE),
}

resultados_validacion = []
for nombre, modelo in modelos_validacion.items():
    puntajes_r2 = cross_val_score(modelo, X_entrena_procesado, y_entrena,
                                  cv=particiones, scoring="r2", n_jobs=1)
    puntajes_mae = -cross_val_score(modelo, X_entrena_procesado, y_entrena,
                                    cv=particiones, scoring="neg_mean_absolute_error", n_jobs=1)
    resultados_validacion.append({
        "Modelo": nombre,
        "R² promedio": puntajes_r2.mean(), "R² desv. estándar": puntajes_r2.std(),
        "MAE promedio": puntajes_mae.mean(), "MAE desv. estándar": puntajes_mae.std(),
        "R² mínimo": puntajes_r2.min(), "R² máximo": puntajes_r2.max(),
    })
    print(f"{nombre:28s} R² = {puntajes_r2.mean():.4f} ± {puntajes_r2.std():.4f}   "
          f"MAE = {puntajes_mae.mean():.3f} ± {puntajes_mae.std():.3f} min")

tabla_validacion = pd.DataFrame(resultados_validacion)
registrar_tiempo("Validación cruzada (5 particiones)", inicio)
tabla_validacion
""")

md(r"""
**Interpretación.** La desviación estándar del R² entre particiones es de milésimas (0,0018 para el
*gradient boosting*, con un rango de 0,838 a 0,843 entre particiones), lo que indica que el desempeño
**no depende de la partición particular de los datos**: las estimaciones son estables y el volumen de
datos es suficiente. El ordenamiento de los modelos coincide con el obtenido en la división simple,
lo que confirma que la comparación no fue un artefacto del azar.

### 5.3 Ajuste de hiperparámetros

Se optimiza el modelo seleccionado con `GridSearchCV`, explorando los hiperparámetros que controlan
el equilibrio entre sesgo y varianza:

- `learning_rate`: cuánto corrige cada iteración (tasa de aprendizaje).
- `max_leaf_nodes`: complejidad máxima de cada árbol.
- `min_samples_leaf`: mínimo de observaciones por hoja (regularización).
- `max_iter`: número de iteraciones de *boosting*.

Se utilizan 3 particiones de validación cruzada para acotar el costo computacional, con `R²` como
métrica de selección.
""")

code(r"""
inicio = perf_counter()

grilla_parametros = {
    "learning_rate": [0.05, 0.1],
    "max_leaf_nodes": [31, 63],
    "min_samples_leaf": [20, 50],
    "max_iter": [300],
}

busqueda = GridSearchCV(
    HistGradientBoostingRegressor(random_state=RANDOM_STATE, early_stopping=False),
    param_grid=grilla_parametros, scoring="r2", cv=3, n_jobs=2, verbose=1, refit=True,
)
busqueda.fit(X_entrena_procesado, y_entrena)
registrar_tiempo("Ajuste de hiperparámetros (GridSearchCV)", inicio)

print("\nMejores hiperparámetros encontrados:")
for parametro, valor in busqueda.best_params_.items():
    print(f"  {parametro:20s} = {valor}")
print(f"\nMejor R² en validación cruzada: {busqueda.best_score_:.4f}")
""")

code(r"""
resultados_busqueda = (pd.DataFrame(busqueda.cv_results_)
                       [["param_learning_rate", "param_max_leaf_nodes", "param_min_samples_leaf",
                         "mean_test_score", "std_test_score", "mean_fit_time", "rank_test_score"]]
                       .sort_values("rank_test_score"))
resultados_busqueda.columns = ["learning_rate", "max_leaf_nodes", "min_samples_leaf",
                               "R² promedio", "R² desv. estándar", "Tiempo de ajuste (s)", "Ranking"]
resultados_busqueda
""")

md(r"""
### 5.4 Modelo final

El modelo definitivo se construye como un **`Pipeline` completo** que encapsula el preprocesamiento
y el estimador con sus hiperparámetros óptimos. Esta es la forma correcta de llevar un modelo a
producción: recibe los datos crudos de un viaje y devuelve la duración estimada, aplicando
internamente las mismas transformaciones aprendidas en el entrenamiento.
""")

code(r"""
inicio = perf_counter()

# El Pipeline encadena preprocesamiento y modelo en un único objeto: al llamar a fit
# aprende ambas cosas con los datos de entrenamiento, y al llamar a predict aplica
# exactamente las mismas transformaciones aprendidas. Es el flujo de entrenamiento y
# predicción visto en clases: en producción el modelo recibe los datos crudos del viaje
# y no es posible olvidar un paso ni aplicar un escalamiento distinto al del ajuste.
modelo_final = Pipeline([
    ("preprocesamiento", ColumnTransformer([
        ("numericas", StandardScaler(), VARIABLES_NUMERICAS),
        ("categoricas", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
         VARIABLES_CATEGORICAS),
        ("zonas", TargetEncoder(random_state=RANDOM_STATE), VARIABLES_ALTA_CARDINALIDAD),
    ], verbose_feature_names_out=False)),
    ("modelo", HistGradientBoostingRegressor(random_state=RANDOM_STATE,
                                             early_stopping=False,
                                             **busqueda.best_params_)),
])

modelo_final.fit(X_entrena, y_entrena)
registrar_tiempo("Entrenamiento del modelo final", inicio)

prediccion_entrena = modelo_final.predict(X_entrena)
prediccion_prueba = modelo_final.predict(X_prueba)
print("Modelo final entrenado sobre", f"{len(X_entrena):,}", "viajes.")
""")

md(r"""
### 5.5 Diagnóstico de sobreajuste

Siguiendo el criterio del Módulo 5, se compara el desempeño en entrenamiento y prueba: una brecha
amplia indicaría que el modelo memoriza en lugar de generalizar.
""")

code(r"""
metricas_entrena = metricas_regresion(y_entrena, prediccion_entrena)
metricas_prueba = metricas_regresion(y_prueba, prediccion_prueba)

diagnostico = pd.DataFrame({"Entrenamiento": metricas_entrena, "Prueba": metricas_prueba})
diagnostico["Diferencia"] = diagnostico.Entrenamiento - diagnostico.Prueba
print(diagnostico)

brecha = metricas_entrena["R2"] - metricas_prueba["R2"]
print(f"\nBrecha de R² (entrenamiento - prueba): {brecha:.4f}")
if brecha < 0.05:
    print("Diagnóstico: el modelo generaliza correctamente (brecha menor a 0,05).")
elif brecha < 0.15:
    print("Diagnóstico: sobreajuste leve, aceptable para uso operacional.")
else:
    print("Diagnóstico: sobreajuste relevante; conviene aumentar la regularización.")
""")

# ==========================================================================
md(r"""
## 6. Evaluación del modelo  *(15 puntos)*

Al tratarse de un problema de regresión, se utilizan las métricas exigidas: **MAE, MSE, RMSE y R²**.
A ellas se agregan indicadores expresados en lenguaje operacional, que son los que permiten decidir
si el modelo sirve para programar servicios.

### 6.1 Métricas de desempeño
""")

code(r"""
error_absoluto = np.abs(y_prueba - prediccion_prueba)
mape = mean_absolute_percentage_error(y_prueba, prediccion_prueba)

print("=" * 66)
print("DESEMPEÑO DEL MODELO FINAL — CONJUNTO DE PRUEBA")
print("=" * 66)
print(f"MAE  (error absoluto medio)        : {metricas_prueba['MAE']:8.3f} minutos")
print(f"MSE  (error cuadrático medio)      : {metricas_prueba['MSE']:8.3f} minutos²")
print(f"RMSE (raíz del error cuadrático)   : {metricas_prueba['RMSE']:8.3f} minutos")
print(f"R²   (coeficiente determinación)   : {metricas_prueba['R2']:8.4f}")
print("-" * 66)
print(f"MAPE (error porcentual absoluto)   : {mape:8.2%}")
print(f"Duración promedio observada        : {y_prueba.mean():8.3f} minutos")
print(f"Error relativo al promedio (MAE/ȳ) : {metricas_prueba['MAE'] / y_prueba.mean():8.2%}")
print(f"Predicciones con error ≤ 2 minutos : {(error_absoluto <= 2).mean():8.2%}")
print(f"Predicciones con error ≤ 3 minutos : {(error_absoluto <= 3).mean():8.2%}")
print(f"Predicciones con error ≤ 5 minutos : {(error_absoluto <= 5).mean():8.2%}")
print("=" * 66)

mejora_vs_base = 1 - metricas_prueba["MAE"] / tabla_candidatos.set_index("Modelo").loc["Línea base (media)", "MAE"]
print(f"\nReducción del error respecto de estimar con el promedio histórico: {mejora_vs_base:.1%}")
""")

md(r"""
### 6.2 Valores observados frente a valores predichos
""")

code(r"""
indices_evaluacion = np.random.RandomState(RANDOM_STATE).choice(len(y_prueba), 6_000, replace=False)
comparacion_predicciones = pd.DataFrame({
    "duracion_observada": y_prueba[indices_evaluacion],
    "duracion_predicha": prediccion_prueba[indices_evaluacion],
})

fig = px.scatter(comparacion_predicciones, x="duracion_observada", y="duracion_predicha",
                 opacity=0.35,
                 title="Duración observada frente a duración predicha (muestra de 6.000 viajes de prueba)",
                 labels={"duracion_observada": "Duración observada (minutos)",
                         "duracion_predicha": "Duración predicha (minutos)"})
limite = float(max(comparacion_predicciones.max()))
fig.add_trace(go.Scatter(x=[0, limite], y=[0, limite], mode="lines", name="Predicción perfecta",
                         line=dict(color="#e63946", dash="dash", width=2)))
mostrar(fig, "eval_observado_predicho", alto=520)
""")

md(r"""
### 6.3 Análisis de residuos
""")

code(r"""
residuos = y_prueba - prediccion_prueba

conteo, bordes = np.histogram(residuos, bins=120)
centros = (bordes[:-1] + bordes[1:]) / 2

fig = px.bar(x=centros, y=conteo,
             title="Distribución de los residuos del modelo (observado − predicho)")
fig.add_vline(x=0, line_dash="dash", line_color="#e63946")
fig.update_layout(showlegend=False, bargap=0.02, xaxis_title="Residuo (minutos)",
                  yaxis_title="Cantidad de viajes")
mostrar(fig, "eval_residuos_histograma")

print(f"Residuo promedio  : {residuos.mean():7.4f} minutos (un valor cercano a cero indica ausencia de sesgo)")
print(f"Desviación estándar: {residuos.std():7.4f} minutos")
print(f"Percentil 5       : {np.percentile(residuos, 5):7.3f} minutos")
print(f"Percentil 95      : {np.percentile(residuos, 95):7.3f} minutos")
print(f"Subestimaciones (residuo > 0): {(residuos > 0).mean():.2%}")
""")

code(r"""
residuos_grafico = pd.DataFrame({
    "duracion_predicha": prediccion_prueba[indices_evaluacion],
    "residuo": residuos[indices_evaluacion],
})

fig = px.scatter(residuos_grafico, x="duracion_predicha", y="residuo", opacity=0.35,
                 title="Residuos frente a valores predichos",
                 labels={"duracion_predicha": "Duración predicha (minutos)",
                         "residuo": "Residuo (minutos)"})
fig.add_hline(y=0, line_dash="dash", line_color="#e63946")
mostrar(fig, "eval_residuos_dispersion")
""")

md(r"""
### 6.4 Error por segmento operacional

El error promedio global puede ocultar comportamientos muy distintos entre segmentos. Se analiza el
MAE por franja horaria, por rango de distancia y por tipo de viaje, información necesaria para saber
**en qué condiciones el modelo es confiable**.
""")

code(r"""
detalle_prueba = X_prueba.copy()
detalle_prueba["duracion_observada"] = y_prueba
detalle_prueba["duracion_predicha"] = prediccion_prueba
detalle_prueba["error_absoluto"] = error_absoluto
detalle_prueba["rango_distancia"] = pd.cut(
    detalle_prueba.trip_distance, bins=[0, 1, 2, 5, 10, 100],
    labels=["≤ 1 mi", "1–2 mi", "2–5 mi", "5–10 mi", "> 10 mi"]
)

error_por_hora = (detalle_prueba.groupby("hora")
                  .agg(viajes=("error_absoluto", "size"),
                       mae=("error_absoluto", "mean"),
                       duracion_promedio=("duracion_observada", "mean"))
                  .reset_index())
error_por_hora["error_relativo_%"] = (error_por_hora.mae / error_por_hora.duracion_promedio * 100).round(2)

fig = px.bar(error_por_hora, x="hora", y="mae", text_auto=".2f",
             hover_data=["viajes", "error_relativo_%"],
             title="Error absoluto medio (MAE) según hora de inicio del viaje",
             labels={"hora": "Hora de inicio", "mae": "MAE (minutos)"})
mostrar(fig, "eval_error_hora")
error_por_hora
""")

code(r"""
error_por_distancia = (detalle_prueba.groupby("rango_distancia", observed=True)
                       .agg(viajes=("error_absoluto", "size"),
                            mae=("error_absoluto", "mean"),
                            duracion_promedio=("duracion_observada", "mean"))
                       .reset_index())
error_por_distancia["error_relativo_%"] = (
    error_por_distancia.mae / error_por_distancia.duracion_promedio * 100).round(2)

fig = px.bar(error_por_distancia, x="rango_distancia", y="mae", text_auto=".2f",
             hover_data=["viajes", "error_relativo_%"],
             title="Error absoluto medio (MAE) según rango de distancia recorrida",
             labels={"rango_distancia": "Rango de distancia", "mae": "MAE (minutos)"})
mostrar(fig, "eval_error_distancia")
error_por_distancia
""")

code(r"""
error_por_tipo = (detalle_prueba.assign(
        tipo_viaje=np.where(detalle_prueba.es_aeropuerto == 1, "Con aeropuerto", "Urbano"),
        momento=np.where(detalle_prueba.es_hora_punta == 1, "Hora punta", "Fuera de punta"))
    .groupby(["tipo_viaje", "momento"])
    .agg(viajes=("error_absoluto", "size"), mae=("error_absoluto", "mean"),
         duracion_promedio=("duracion_observada", "mean"))
    .reset_index())
error_por_tipo["error_relativo_%"] = (error_por_tipo.mae / error_por_tipo.duracion_promedio * 100).round(2)
error_por_tipo
""")

md(r"""
**Interpretación de la evaluación.**

- El modelo alcanza un **R² de 0,853**: explica el 85,3 % de la variabilidad de la duración de los
  viajes, con un **error medio de 2,74 minutos** sobre una duración promedio de 14,65 minutos
  (18,7 % en términos relativos, MAPE 22,2 %).
- Comparado con la práctica de estimar mediante el promedio histórico (MAE 7,84 min), **el error se
  reduce 65 %**. Ese es el aporte concreto del proyecto.
- El **69,3 % de las predicciones se equivoca en 3 minutos o menos** y el 85,6 % en 5 minutos o
  menos, precisión suficiente para programar servicios y comunicar tiempos estimados al cliente.
- El RMSE (4,20 min) es mayor que el MAE (2,74 min) porque penaliza los errores grandes: existe un
  grupo minoritario de viajes con desvíos importantes, coherente con la cola derecha de la
  distribución.
- Los **residuos se distribuyen en torno a cero** (media 0,06 min) y de forma aproximadamente
  simétrica —45,1 % de subestimaciones frente a 54,9 % de sobreestimaciones—, lo que indica ausencia
  de sesgo sistemático. El intervalo entre los percentiles 5 y 95 va de −5,5 a +6,8 minutos: nueve de
  cada diez predicciones caen dentro de esa banda.
- El gráfico de residuos frente a predicciones muestra un **abanico creciente**: la dispersión del
  error aumenta con la duración estimada (heterocedasticidad). En términos de negocio, los viajes
  largos son intrínsecamente menos predecibles, y así debe comunicarse el resultado.
- Por hora del día, el error es **mínimo de madrugada** (2,18 min a las 3:00) y **máximo a media
  mañana** (3,14 min a las 9:00): el modelo es más preciso cuando el tráfico es predecible.
- Por distancia, el error absoluto crece (de 1,57 min en viajes de menos de una milla a 5,58 min en
  los de más de diez) mientras el **error relativo disminuye** (de 26,1 % a 14,1 %): en viajes largos
  el modelo se equivoca en más minutos, pero en mucho menor proporción del tiempo total.
- Los viajes **con aeropuerto** concentran el mayor error absoluto (4,7 a 5,1 min) por ser los más
  largos, pero también el menor error relativo (cerca de 14 %). Para la operación esto es una buena
  noticia: los servicios de mayor valor son los que se estiman con mayor precisión proporcional.
""")

# ==========================================================================
md(r"""
## 7. Interpretación del modelo y conclusiones  *(10 puntos)*

### 7.1 Variables más importantes

Los modelos de *gradient boosting* basados en histogramas no exponen un atributo de importancia
directo, por lo que se utiliza **importancia por permutación**: se mide cuánto se degrada el
desempeño al permutar aleatoriamente cada variable. Es una medida de importancia **respecto del
modelo ya entrenado y medida sobre datos no vistos**, más confiable que las importancias internas.
""")

code(r"""
inicio = perf_counter()
# Importancia por permutación: se desordenan al azar los valores de una variable —con lo
# que se destruye su relación con el objetivo, sin alterar el resto de los datos— y se
# mide cuánto empeora el R². Si empeora mucho, esa variable era importante para el modelo.
# Se emplea esta técnica por dos razones: HistGradientBoostingRegressor no expone el
# atributo feature_importances_, y al medirse sobre datos no vistos resulta más confiable
# que las importancias internas del algoritmo.
#
# Se evalúa sobre una submuestra del conjunto de prueba para acotar el costo computacional.
indices_importancia = np.random.RandomState(RANDOM_STATE).choice(len(X_prueba), 25_000, replace=False)
X_importancia = X_prueba.iloc[indices_importancia]
y_importancia = y_prueba[indices_importancia]

importancia = permutation_importance(
    modelo_final, X_importancia, y_importancia,
    n_repeats=3, random_state=RANDOM_STATE, scoring="r2", n_jobs=1,
)
registrar_tiempo("Importancia por permutación", inicio)

tabla_importancia = (pd.DataFrame({
    "variable": X_prueba.columns,
    "caida_r2_promedio": importancia.importances_mean,
    "desv_estandar": importancia.importances_std,
}).sort_values("caida_r2_promedio", ascending=False).reset_index(drop=True))

fig = px.bar(tabla_importancia.head(15).iloc[::-1], x="caida_r2_promedio", y="variable",
             orientation="h", error_x="desv_estandar",
             title="Importancia de las variables por permutación (caída del R² al permutar)",
             labels={"caida_r2_promedio": "Caída del R²", "variable": "Variable"})
mostrar(fig, "interpretacion_importancia", alto=560)
tabla_importancia.head(15)
""")

md(r"""
**Interpretación.** La jerarquía obtenida es coherente con el conocimiento del negocio y corrige
varias intuiciones que la correlación de Pearson no permitía ver:

1. **Distancia** (`trip_distance`): es el determinante absolutamente dominante. Permutarla hace caer
   el R² en 2,05 puntos —es decir, el modelo pasa a ser mucho peor que predecir la media—, un orden
   de magnitud por encima de cualquier otra variable.
2. **Hora de inicio** (`hora`): segunda variable más importante (caída de R² de 0,127), pese a tener
   una correlación lineal con el objetivo de apenas 0,010. Es la confirmación cuantitativa de que su
   efecto es **no lineal e interactivo**, y la razón por la cual la selección por información mutua
   perjudicó el desempeño.
3. **Día de la semana** (`dia_semana`, 0,053) y **día del mes** (`dia_mes`, 0,025): completan la
   dimensión temporal, coherente con el mapa de calor del EDA.
4. **Zonas de origen y destino** (`PULocationID` y `DOLocationID` codificadas por objetivo: 0,036 y
   0,032): capturan la geografía real de la congestión —una zona céntrica no equivale a una
   periférica aunque la distancia sea la misma.
5. **Indicadores geográficos derivados** (`do_servicio`, `do_borough`, `mismo_borough`,
   `misma_zona`): aportan poco *adicional* (0,007 a 0,011) no porque sean irrelevantes —su
   correlación con la duración es alta— sino porque su información **ya está contenida** en la
   codificación de las zonas. Es un caso claro de redundancia: la importancia por permutación mide
   aporte marginal dado el resto del modelo, no importancia absoluta.

Las variables administrativas (`VendorID`, `store_and_fwd_flag`, `payment_type`) y `es_aeropuerto`
cierran el *ranking*. En el caso de las primeras el resultado era esperable: describen el registro
del viaje, no su naturaleza física. En el de `es_aeropuerto`, se trata otra vez de redundancia con las
zonas codificadas.

**Lectura de negocio:** después de la distancia, **lo que más determina el tiempo de un viaje es
cuándo se realiza**, no dónde. Esa es una conclusión directamente accionable para programar
servicios.

### 7.2 Fortalezas del modelo

- **Desempeño sólido y validado:** R² de 0,853 en prueba, con validación cruzada de 5 particiones y
  desviación estándar de 0,0018; el resultado no depende de la partición de los datos.
- **Sin fuga de información:** utiliza exclusivamente variables conocidas al iniciar el viaje, por lo
  que el desempeño medido es el que cabe esperar en producción.
- **Error interpretable y accionable:** se expresa en minutos y no en unidades abstractas, lo que
  permite negociar niveles de servicio con el cliente.
- **Eficiencia computacional:** entrena en segundos sobre cientos de miles de registros, condición
  necesaria para reentrenar de forma periódica.
- **Robustez operacional:** el `Pipeline` incorpora el preprocesamiento y maneja categorías no vistas
  (`handle_unknown="ignore"`), evitando fallas ante datos nuevos.
- **Escala:** el diseño se probó sobre casi tres millones de registros, con muestreo justificado y
  verificado.

### 7.3 Limitaciones del modelo

- **No incorpora variables de contexto** que son determinantes reales del tiempo de viaje: clima,
  accidentes, cortes de calles, eventos masivos o estado del tráfico en tiempo real.
- **Ventana temporal acotada:** los datos corresponden a un solo mes (enero de 2024), por lo que el
  modelo no captura estacionalidad anual ni el efecto de períodos como vacaciones.
- **Heterocedasticidad:** el error crece con la duración estimada; los viajes largos son
  sistemáticamente menos predecibles.
- **Granularidad geográfica limitada:** trabaja con 260 zonas administrativas, no con rutas ni
  coordenadas; dos viajes entre las mismas zonas pueden seguir trayectos muy distintos.
- **Dependencia de la calidad del registro:** fue necesario excluir 5,42 % de los datos por
  inconsistencias del taxímetro; una degradación de la captura afectaría al modelo.
- **Transferibilidad:** está entrenado con datos de Nueva York. Su aplicación a otra ciudad exige
  reentrenamiento con datos locales, aunque la metodología es directamente replicable.

### 7.4 Posibles mejoras

1. **Enriquecer con datos externos:** condiciones meteorológicas por hora, calendario de feriados y
   eventos, e indicadores de tráfico. Es la mejora con mayor potencial esperado.
2. **Ampliar la ventana temporal:** entrenar con doce meses permitiría capturar estacionalidad y
   evaluar la deriva del modelo en el tiempo.
3. **Modelos especializados por segmento:** entrenar modelos distintos para viajes urbanos y de
   aeropuerto, cuyos comportamientos son estructuralmente diferentes.
4. **Algoritmos alternativos:** evaluar XGBoost o LightGBM y ensambles apilados, además de
   optimización bayesiana de hiperparámetros en lugar de búsqueda en grilla.
5. **Predicción de intervalos:** utilizar regresión por cuantiles para entregar un rango
   (por ejemplo, "entre 12 y 18 minutos") en lugar de un valor puntual, lo que refleja mejor la
   incertidumbre real y es más útil para comprometer horarios.
6. **Prácticas de MLOps:** monitoreo de la deriva de datos, reentrenamiento programado y versionado
   del modelo, tal como se trabajó en el Módulo 5.

### 7.5 Aplicaciones prácticas en un contexto real

| Aplicación | Uso del modelo |
|---|---|
| **Estimación de tiempo de llegada (ETA)** | Informar al pasajero un tiempo estimado al momento de solicitar el servicio. |
| **Programación de turnos y flota** | Estimar la duración esperada de cada servicio para construir turnos factibles y dimensionar la flota por franja horaria. |
| **Cotización de servicios** | Convertir la duración estimada en costo esperado (horas conductor, combustible) para cotizar traslados con márgenes conocidos. |
| **Control de gestión** | Comparar duración real versus estimada para detectar desvíos operacionales y evaluar rutas. |
| **Simulación de escenarios** | Cuantificar el impacto de mover un servicio de las 18:00 a las 20:00, o de cambiar el punto de origen. |
| **Acuerdos de nivel de servicio** | Utilizar la distribución del error para comprometer rangos de cumplimiento realistas. |

### 7.6 Conclusiones finales
""")

code(r"""
resumen_final = pd.DataFrame([
    ("Registros del dataset original", f"{registros_iniciales:,}"),
    ("Registros tras la depuración", f"{len(df):,} ({len(df)/registros_iniciales:.1%})"),
    ("Muestra utilizada para modelar", f"{TAMANO_MUESTRA:,}"),
    ("Predictores construidos", f"{len(PREDICTORES)} variables → {len(nombres_caracteristicas)} características"),
    ("Reducción de dimensionalidad", f"PCA: {n_componentes_95} componentes (95 % varianza); "
                                     f"información mutua: {K_SELECCIONADAS} características"),
    ("Modelo seleccionado", "HistGradientBoostingRegressor (scikit-learn)"),
    ("Hiperparámetros óptimos", str(busqueda.best_params_)),
    ("MAE en prueba", f"{metricas_prueba['MAE']:.3f} minutos"),
    ("RMSE en prueba", f"{metricas_prueba['RMSE']:.3f} minutos"),
    ("R² en prueba", f"{metricas_prueba['R2']:.4f}"),
    ("Mejora respecto de la línea base", f"{mejora_vs_base:.1%} menos error absoluto medio"),
], columns=["Elemento", "Resultado"])
resumen_final
""")

md(r"""
**Conclusiones.**

1. **Es posible predecir la duración de un viaje urbano con precisión operacionalmente útil** usando
   solo información disponible antes de iniciarlo: el modelo explica el 85,3 % de la variabilidad,
   con un error medio de 2,74 minutos y casi el 70 % de las predicciones dentro de ±3 minutos.
2. **La preparación de datos determinó el resultado.** La correlación entre distancia y duración
   pasó de 0,005 a 0,810 tras depurar registros inconsistentes. Sin ese trabajo previo, el análisis
   habría descartado la variable más predictiva del problema.
3. **La reducción de dimensionalidad no mejoró el desempeño en este caso.** PCA comprimió 53
   características en 8 componentes conservando el 95,9 % de la varianza, pero el R² cayó de 0,838 a
   0,795: la varianza de las variables no equivale a información sobre el objetivo. La selección por
   información mutua fue aún menos favorable (R² 0,754) al descartar las variables temporales, cuyo
   aporte es interactivo y no marginal.
4. **El tiempo de viaje no depende solo de la distancia.** La hora de inicio es la segunda variable
   más importante del modelo pese a tener una correlación lineal casi nula con el objetivo: la
   duración promedio varía cerca de 40 % entre la hora más rápida y la más lenta del día con
   distancias equivalentes. Exactamente lo que una estimación por promedios no captura.
5. **La disciplina metodológica es lo que hace utilizable al modelo.** Excluir las variables
   monetarias —tentadoras por su alta correlación con el objetivo— fue indispensable para que el
   desempeño medido sea el desempeño real en producción.
6. **Aporte de negocio:** frente a la práctica de estimar con el promedio histórico, el error medio
   se reduce 65 % (de 7,84 a 2,74 minutos), lo que se traduce en programación de turnos más ajustada,
   mejores compromisos de tiempo con el cliente y menor holgura improductiva.
""")

# ==========================================================================
md(r"""
## 8. Persistencia del modelo (MLOps)

Se guarda el `Pipeline` completo con `joblib`, junto con un archivo de metadatos que documenta la
versión de las bibliotecas, las variables esperadas y las métricas obtenidas. Esta trazabilidad es
un requisito básico de MLOps: permite auditar qué modelo generó cada predicción y detectar
diferencias de entorno al desplegarlo.
""")

code(r"""
RUTA_MODELO = Path("Luna_Valeria_modelo_duracion_viaje.joblib")
joblib.dump(modelo_final, RUTA_MODELO, compress=3)

metadatos = {
    "nombre_modelo": "Predicción de duración de viajes urbanos",
    "estudiante": "Valeria Luna",
    "fecha_entrenamiento": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "dataset": "NYC TLC Yellow Taxi Trip Records — enero 2024",
    "enlace_dataset": "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
    "registros_originales": int(registros_iniciales),
    "registros_depurados": int(len(df)),
    "registros_entrenamiento": int(len(X_entrena)),
    "algoritmo": "HistGradientBoostingRegressor",
    "hiperparametros": {k: (int(v) if isinstance(v, (np.integer,)) else v)
                        for k, v in busqueda.best_params_.items()},
    "variables_esperadas": list(X_entrena.columns),
    "variable_objetivo": OBJETIVO,
    "metricas_prueba": {k: float(v) for k, v in metricas_prueba.items()},
    "version_sklearn": sklearn.__version__,
    "version_pandas": pd.__version__,
    "semilla": RANDOM_STATE,
}

RUTA_METADATOS = Path("Luna_Valeria_modelo_metadatos.json")
RUTA_METADATOS.write_text(json.dumps(metadatos, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Modelo guardado    : {RUTA_MODELO.name} ({RUTA_MODELO.stat().st_size / 1024**2:.2f} MB)")
print(f"Metadatos guardados: {RUTA_METADATOS.name}")
print(json.dumps(metadatos["metricas_prueba"], indent=2))
""")

md(r"""
### 8.1 Verificación de uso del modelo guardado

Se recarga el modelo desde el archivo y se predice sobre casos nuevos, simulando su uso en
producción. Este paso valida que el artefacto es autosuficiente.
""")

code(r"""
modelo_cargado = joblib.load(RUTA_MODELO)

casos_nuevos = pd.DataFrame([
    {"descripcion": "Viaje corto en Manhattan, martes 8:30 (hora punta)",
     "trip_distance": 1.8, "hora": 8, "dia_semana": 1, "dia_mes": 16, "passenger_count": 1,
     "es_fin_semana": 0, "es_hora_punta": 1, "es_aeropuerto": 0, "misma_zona": 0, "mismo_borough": 1,
     "pu_borough": "Manhattan", "do_borough": "Manhattan", "pu_servicio": "Yellow Zone",
     "do_servicio": "Yellow Zone", "franja_horaria": "Punta AM", "VendorID": "2", "RatecodeID": "1",
     "payment_type": "1", "store_and_fwd_flag": "N", "PULocationID": "236", "DOLocationID": "237"},
    {"descripcion": "Mismo viaje, domingo 3:00 de la madrugada",
     "trip_distance": 1.8, "hora": 3, "dia_semana": 6, "dia_mes": 21, "passenger_count": 1,
     "es_fin_semana": 1, "es_hora_punta": 0, "es_aeropuerto": 0, "misma_zona": 0, "mismo_borough": 1,
     "pu_borough": "Manhattan", "do_borough": "Manhattan", "pu_servicio": "Yellow Zone",
     "do_servicio": "Yellow Zone", "franja_horaria": "Madrugada", "VendorID": "2", "RatecodeID": "1",
     "payment_type": "1", "store_and_fwd_flag": "N", "PULocationID": "236", "DOLocationID": "237"},
    {"descripcion": "Traslado al aeropuerto JFK, viernes 17:00",
     "trip_distance": 17.5, "hora": 17, "dia_semana": 4, "dia_mes": 19, "passenger_count": 2,
     "es_fin_semana": 0, "es_hora_punta": 1, "es_aeropuerto": 1, "misma_zona": 0, "mismo_borough": 0,
     "pu_borough": "Manhattan", "do_borough": "Queens", "pu_servicio": "Yellow Zone",
     "do_servicio": "Airports", "franja_horaria": "Punta PM", "VendorID": "2", "RatecodeID": "2",
     "payment_type": "1", "store_and_fwd_flag": "N", "PULocationID": "138", "DOLocationID": "132"},
])

descripciones = casos_nuevos.pop("descripcion")
casos_nuevos["log_distancia"] = np.log1p(casos_nuevos.trip_distance)
predicciones_nuevas = modelo_cargado.predict(casos_nuevos[X_entrena.columns])

resultado_casos = pd.DataFrame({
    "Caso": descripciones,
    "Distancia (mi)": casos_nuevos.trip_distance.values,
    "Duración estimada (min)": predicciones_nuevas.round(1),
})
resultado_casos
""")

md(r"""
**Interpretación.** El modelo reproduce el comportamiento esperado por el negocio: el mismo trayecto
de 1,8 millas en Manhattan demora sensiblemente más en hora punta de un día hábil que en la
madrugada de un domingo, y el traslado al aeropuerto —mayor distancia y en horario de máxima
congestión— es el servicio más extenso. Es decir, el modelo aprendió relaciones **operacionalmente
correctas**, no solo correlaciones estadísticas.

### 8.2 Resumen de tiempos de ejecución
""")

code(r"""
tiempo_total = perf_counter() - inicio_cuaderno
resumen_tiempos = pd.DataFrame(registro_tiempos)
resumen_tiempos["Porcentaje (%)"] = (
    resumen_tiempos["Duración (s)"] / resumen_tiempos["Duración (s)"].sum() * 100).round(2)

print(f"Tiempo total de ejecución del cuaderno: {tiempo_total / 60:.2f} minutos")

fig = px.bar(resumen_tiempos.sort_values("Duración (s)"), x="Duración (s)", y="Proceso",
             orientation="h", text_auto=".1f",
             title="Tiempo de ejecución por etapa del proyecto",
             labels={"Duración (s)": "Duración (segundos)", "Proceso": ""})
mostrar(fig, "tiempos_ejecucion", alto=520)
resumen_tiempos
""")

# ==========================================================================
md(r"""
## Anexo · Entregables y referencias

### Entregables generados por este cuaderno

| Archivo | Contenido |
|---|---|
| `Luna_Valeria_EvaluacionFinal.ipynb` | Este cuaderno, ejecutado de principio a fin sin errores. |
| `Luna_Valeria_Informe.pdf` | Informe ejecutivo (máximo 10 páginas). |
| `Luna_Valeria_modelo_duracion_viaje.joblib` | Pipeline completo entrenado (preprocesamiento + modelo). |
| `Luna_Valeria_modelo_metadatos.json` | Trazabilidad: versiones, variables esperadas y métricas. |
| `figuras/` | Figuras exportadas en formato PNG. |

### Enlace oficial del dataset

- **Portal oficial:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- **Archivo de viajes utilizado:** https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet
- **Tabla de zonas:** https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
- **Diccionario de datos oficial:** https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf

### Referencias técnicas

- Pedregosa et al. (2011). *Scikit-learn: Machine Learning in Python*. JMLR 12, 2825–2830.
- Documentación de scikit-learn: `HistGradientBoostingRegressor`, `TargetEncoder`, `PCA`,
  `permutation_importance`, `GridSearchCV`.
- Micci-Barreca, D. (2001). *A preprocessing scheme for high-cardinality categorical attributes*.
  SIGKDD Explorations (fundamento del `TargetEncoder`).
- Material del Módulo 10 del Diplomado en Data Engineer, Universidad de Santiago de Chile.

### Declaración sobre el uso de Inteligencia Artificial

En el desarrollo de este proyecto se utilizaron herramientas de inteligencia artificial como apoyo
para la escritura y revisión del código, conforme lo autoriza la evaluación. Las decisiones
metodológicas —selección del dataset y del problema, definición de la variable objetivo, criterios
de depuración, exclusión de variables por fuga de información, elección de las técnicas de reducción
de dimensionalidad, selección del algoritmo e interpretación de los resultados— son propias y pueden
ser explicadas y justificadas íntegramente.
""")

# ==========================================================================
notebook = {
    "cells": celdas,
    "metadata": {
        "colab": {"provenance": [], "toc_visible": True},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

# nbformat exige source como lista de líneas o texto; se normaliza a texto con saltos de línea.
for celda in notebook["cells"]:
    celda["source"] = celda["source"] + "\n"
    if celda["cell_type"] == "code":
        celda["id"] = f"c{celdas.index(celda):03d}"
    else:
        celda["id"] = f"m{celdas.index(celda):03d}"

destino = Path(sys.argv[1])
destino.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Cuaderno generado: {destino}  ({len(celdas)} celdas, "
      f"{sum(1 for c in celdas if c['cell_type']=='code')} de código)")
