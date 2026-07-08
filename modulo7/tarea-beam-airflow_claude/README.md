# Tarea 1 — Módulo 7: Pipeline de Ventas LATAM (Apache Beam + Airflow)

Pipeline **ELT** que ingesta ventas desde tres sedes con tecnologías heterogéneas
(Santiago/CSV, Lima/Parquet, Buenos Aires/JSON Lines), las homogeneiza en una capa
**PSA (Persistent Staging Area)**, valida un **Contrato de Datos**, convierte los
montos a **USD** y publica el resultado en una capa **Gold** lista para BI. La
orquestación diaria la realiza un **DAG de Apache Airflow**.

## Arquitectura

```
                 ┌─────────────────────────────┐
   CSV  ─┐       │  JOB 1: Ingesta (E + L)     │      data/psa/proc_date=YYYY-MM-DD/
   Parquet ──────▶  Homogeneiza al esquema     ├────▶ (Parquet, monto como String)
   JSON ─┘       │  común. NO filtra ni valida │
                 └─────────────────────────────┘
                                                          │
                 ┌─────────────────────────────┐          ▼
                 │  JOB 2: Transformación (T)  │   ┌──────────────┐
                 │  - Data Contract            │──▶│ data/gold/   │  (Parquet, USD)
   tipo_cambio ─▶│  - DLQ (Tagged Outputs)     │   └──────────────┘
   (Side Input)  │  - Conversión a USD         │   ┌──────────────┐
                 │  - Deduplicación            │──▶│ data/errors/ │  (JSON Lines, DLQ)
                 └─────────────────────────────┘   └──────────────┘
```

## Estructura de archivos

```
tarea-beam-airflow/
├── dags/
│   └── dag_orden_ventas_latam.py   # DAG de Airflow (orquestación Job1 >> Job2)
├── beam_jobs/
│   ├── job1_ingest_to_psa.py       # Apache Beam — Ingesta a la capa PSA
│   └── job2_transform_gold.py      # Apache Beam — Transformación a la capa Gold
├── data/
│   └── inputs/                     # Fuentes de entrada de ejemplo
├── requirements.txt
└── README.md
```

## Requisitos e instalación

- Python 3.10 (recomendado; Apache Beam 2.60 soporta 3.9–3.12).

```bash
# 1) Crear entorno virtual
python -m venv .venv

# 2) Activarlo
#    Windows (PowerShell):
.venv\Scripts\Activate.ps1
#    Linux / macOS:
source .venv/bin/activate

# 3) Instalar dependencias
pip install -r requirements.txt
```

## Ejecución manual (sin Airflow, runner local DirectRunner)

Desde la raíz del proyecto (`tarea-beam-airflow/`):

```bash
# JOB 1 — Ingesta a la capa PSA
python beam_jobs/job1_ingest_to_psa.py \
    --proc_date 2026-06-10 \
    --input_dir data/inputs \
    --psa_dir data/psa

# JOB 2 — Transformación, validación y carga a Gold
python beam_jobs/job2_transform_gold.py \
    --proc_date 2026-06-10 \
    --psa_dir data/psa \
    --gold_dir data/gold \
    --errors_dir data/errors \
    --tipo_cambio data/inputs/tipo_cambio.csv
```

> En Windows usar `\` para continuar líneas no aplica; escribir cada comando en una
> sola línea o usar el backtick `` ` `` de PowerShell.

## Descripción de los scripts y sus parámetros

### `beam_jobs/job1_ingest_to_psa.py`
Fase **Extracción + Carga (E+L)**. Lee las tres fuentes **en paralelo** (tres ramas
de Beam unidas con `Flatten`), las homogeneiza al *Esquema Común de Transición*
mediante `DoFn` y escribe un único Parquet en la capa PSA, particionado por
`proc_date`. **No aplica reglas de negocio ni filtra filas** (principio PSA). El campo
`monto_original` se guarda **como String** para tolerar datos ruidosos (ej. `"NULO_ERROR"`).

Conectores I/O distribuidos usados: `ReadFromText` (CSV/JSON), `ReadFromParquet`
(Parquet) y `WriteToParquet` (salida).

| Parámetro | Req. | Default | Descripción |
|-----------|------|---------|-------------|
| `--proc_date` | Sí | — | Fecha de proceso `YYYY-MM-DD` (macro `{{ ds }}` de Airflow). |
| `--input_dir` | No | `data/inputs` | Carpeta con las fuentes de entrada. |
| `--psa_dir`   | No | `data/psa` | Carpeta destino de la capa PSA. |

**Esquema común de salida (todas las columnas String):** `id_transaccion`, `ciudad`,
`monto_original`, `moneda_origen` (CLP/PEN/ARS según origen), `fecha_transaccion`,
`ingestado_at` (timestamp de la ejecución).

### `beam_jobs/job2_transform_gold.py`
Fase **Transformación (T)**. Consume la capa PSA y:

1. **Data Contract** vía `DoFn` con **Tagged Outputs** (salidas etiquetadas):
   - `monto_original` debe ser numérico (`float`/`int`).
   - `monto_original > 0` **y** `ciudad ∈ {Santiago, Lima, Buenos Aires}`.
2. Los registros que fallan se desvían a la **Dead-Letter Queue** (`data/errors/...`)
   en **JSON Lines** con `raw_record` + `motivo_rechazo`, **sin botar el pipeline**.
3. Cruce con `tipo_cambio.csv` mediante **Side Input** (`AsDict`) para convertir a USD.
4. **Deduplicación** por `id_transaccion` (`GroupByKey`) y escritura en la capa Gold
   (`data/gold/...`) en Parquet.

| Parámetro | Req. | Default | Descripción |
|-----------|------|---------|-------------|
| `--proc_date`   | Sí | — | Fecha de proceso `YYYY-MM-DD`. |
| `--psa_dir`     | No | `data/psa` | Carpeta de la capa PSA (entrada). |
| `--gold_dir`    | No | `data/gold` | Carpeta destino Gold. |
| `--errors_dir`  | No | `data/errors` | Carpeta destino de la DLQ. |
| `--tipo_cambio` | No | `data/inputs/tipo_cambio.csv` | Maestro de tipos de cambio. |

**Esquema Gold:** `id_transaccion`, `ciudad`, `monto_usd` (float), `fecha_compras`.

### `dags/dag_orden_ventas_latam.py`
DAG de Airflow que orquesta `job1_ingesta_psa >> job2_transform_gold`.

- **Secuencialidad:** dependencia explícita; el Job 2 no inicia si el Job 1 falla.
- **Idempotencia:** las rutas se parametrizan con el macro nativo `{{ ds }}`. Re-ejecutar
  el mismo día de datos no duplica resultados (misma partición `proc_date` + dedup).
- **Resiliencia:** `retries=3` con `retry_delay=5 min` ante caídas de infraestructura.
- **Schedule:** diario a las 06:00 (`0 6 * * *`). Para *backfill* histórico, poner
  `catchup=True`.

Variables de entorno opcionales para el despliegue:
`PROYECTO_BEAM_DIR` (raíz del proyecto) y `PYTHON_BIN` (intérprete a usar).

## Decisiones de diseño y análisis FinOps

- **Parquet en PSA y Gold (FinOps):** formato columnar comprimido que reduce el espacio
  de almacenamiento y, sobre todo, el **costo de escaneo** en consultas de BI (solo se
  leen las columnas necesarias) frente a CSV/JSON.
- **Side Input distribuido** para el tipo de cambio: evita cargar colecciones completas
  en memoria de cada worker; Beam distribuye el diccionario de tasas eficientemente.
- **PSA inmutable y sin reglas de negocio:** garantiza auditabilidad y permite
  reprocesar la capa Gold sin volver a tocar las fuentes originales.
- **DLQ en lugar de descartar filas:** no se pierde información; los registros corruptos
  quedan disponibles para auditoría con su motivo de rechazo.
- **`raw_record` en la DLQ** corresponde al registro tal como quedó en la capa PSA
  (esquema homogeneizado), coherente con que el Job 2 solo consume la PSA.

## Notas de ejecución en Windows

- El conector glob del filesystem local de Beam tiene una limitación en Windows con
  patrones `*`. Por eso el Job 2 resuelve los archivos PSA con `glob` de Python y lee
  cada *shard*. En un runner distribuido (Dataflow/Flink) se pasaría el patrón directo.
- Beam puede dejar una carpeta temporal `beam-temp-*` tras escribir en Windows; es
  inofensiva y no ocurre en Linux. Puede borrarse manualmente.

---

## Anexo — Uso de Inteligencia Artificial

Para el desarrollo de esta tarea se utilizó un asistente de IA. Prompt principal:

> "Necesito ayuda para hacer una tarea de Data Engineer (Módulo 7). Debo construir un
> pipeline ELT con **Apache Beam (Python SDK)** compuesto por dos jobs orquestados con
> **Apache Airflow**:
> **Job 1** lee en paralelo tres fuentes heterogéneas (CSV de Santiago, Parquet de Lima
> y JSON Lines de Buenos Aires), las homogeneiza a un esquema común
> (`id_transaccion, ciudad, monto_original [String], moneda_origen, fecha_transaccion,
> ingestado_at`) inyectando el código de moneda (CLP/PEN/ARS), y escribe la capa PSA en
> Parquet particionada por `proc_date`, sin aplicar reglas de negocio.
> **Job 2** consume la PSA, valida un Data Contract (monto numérico y > 0; ciudad en
> {Santiago, Lima, Buenos Aires}), desvía los registros inválidos a una Dead-Letter
> Queue en JSON usando Tagged Outputs, cruza con `tipo_cambio.csv` mediante Side Input
> para convertir a USD, deduplica y escribe la capa Gold en Parquet.
> El **DAG de Airflow** debe encadenar Job1 >> Job2, ser idempotente con el macro
> `{{ ds }}` y tener 3 reintentos cada 5 minutos.
> Genera los tres scripts y un README, y verifica que las salidas coincidan con las
> esperadas del enunciado."

El código generado fue revisado, ejecutado y validado localmente con el `DirectRunner`,
confirmando que las salidas (capa Gold y DLQ) coinciden con las esperadas en el enunciado.
