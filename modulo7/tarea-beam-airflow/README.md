# Tarea Módulo 7 - Data Pipelines con Apache Beam y Airflow

## Autor

**Valeria Luna**

---

# Objetivo

Implementar un pipeline ETL utilizando Apache Beam y Apache Airflow que permita:

* Ingerir información de ventas desde múltiples formatos.
* Construir una Persistent Staging Area (PSA).
* Validar los registros mediante un Data Contract.
* Enviar registros inválidos a una Dead Letter Queue (DLQ).
* Transformar los datos válidos a una capa Gold con montos convertidos a USD.
* Orquestar el proceso completo mediante Apache Airflow.

---

# Estructura del proyecto

```text
tarea-beam-airflow/
│
├── beam_jobs/
│   ├── job1_ingest_to_psa.py
│   └── job2_transform_gold.py
│
├── dags/
│   └── dag_orden_ventas_latam.py
│
├── data/
│   ├── inputs/
│   ├── psa/
│   ├── gold/
│   └── errors/
│
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

---

# Tecnologías utilizadas

* Python 3.11
* Apache Beam 2.60.0
* Apache Airflow 2.10.5
* Docker
* Pandas
* PyArrow

---

# Job 1 - Ingesta hacia PSA

El primer proceso realiza la lectura de tres fuentes con distintos formatos:

* CSV (Santiago)
* Parquet (Lima)
* JSON (Buenos Aires)

Posteriormente homogeniza la estructura agregando los siguientes campos:

* id_transaccion
* ciudad
* monto_original
* moneda_origen
* fecha_transaccion
* ingestado_at
* proc_date

Finalmente genera una PSA particionada por fecha de procesamiento.

Ejemplo:

```text
data/psa/
└── proc_date=2026-06-29/
    └── ventas_unificadas.parquet
```

---

# Job 2 - Transformación a Gold

El segundo proceso realiza:

## Validaciones

* Ciudad válida:

  * Santiago
  * Lima
  * Buenos Aires

* Monto numérico.

* Monto mayor que cero.

Los registros inválidos son enviados a la Dead Letter Queue.

Los registros válidos son enriquecidos utilizando el archivo:

```text
tipo_cambio.csv
```

Posteriormente se calcula el monto en USD y se genera la capa Gold.

---

# Dead Letter Queue

Los registros rechazados son almacenados en:

```text
data/errors/proc_date=YYYY-MM-DD/
```

Incluyendo el registro original y el motivo del rechazo.

---

# Capa Gold

Los registros válidos son almacenados en:

```text
data/gold/proc_date=YYYY-MM-DD/
```

---

# Orquestación

Se implementó un DAG de Apache Airflow llamado:

```text
dag_orden_ventas_latam
```

con la siguiente secuencia:

```text
Job 1
   │
   ▼
Job 2
```

Configuración:

* Reintentos: 3
* Retry Delay: 5 minutos
* Ejecución diaria
* Parámetro proc_date enviado mediante:

```text
{{ ds }}
```

---

# Dependencias

Instalar:

```bash
pip install apache-beam==2.60.0 pandas pyarrow
```

Para Airflow se utilizó Docker.

---

# Evidencias obtenidas

Durante la ejecución del pipeline se verificó:

* Generación correcta de la PSA.
* Validación mediante Data Contract.
* Creación de la Dead Letter Queue.
* Generación de la capa Gold.
* Ejecución exitosa desde Apache Airflow.

---

# Prompts utilizados durante el desarrollo

Durante el desarrollo de esta actividad se utilizó ChatGPT como apoyo para resolver dudas técnicas y comprender mejor la implementación. Algunos de los prompts utilizados fueron:

1. "Ayúdame a implementar el Job 1 utilizando Apache Beam para leer archivos CSV, JSON y Parquet."

2. "¿Cuál es la mejor forma de construir una Persistent Staging Area (PSA) particionada por fecha de procesamiento?"

3. "Ayúdame a validar registros utilizando Apache Beam y Tagged Outputs para separar registros válidos e inválidos."

4. "¿Cómo generar una Dead Letter Queue (DLQ) utilizando Apache Beam?"

5. "Ayúdame a convertir los montos utilizando un archivo de tipo de cambio y generar la capa Gold."

6. "Ayúdame a crear un DAG de Apache Airflow que ejecute primero el Job 1 y luego el Job 2."

7. "¿Cómo ejecutar Apache Airflow utilizando Docker en Windows?"

8. "Ayúdame a corregir problemas de rutas relativas para que los scripts funcionen tanto localmente como dentro del contenedor Docker."

9. "Ayúdame a solucionar errores de dependencias de Apache Beam dentro de los contenedores de Airflow."

10. "Explícame las mejores prácticas para organizar un proyecto ETL con Apache Beam y Airflow."

---

# Conclusiones

Se implementó un pipeline ETL completo utilizando Apache Beam para la ingesta y transformación de datos y Apache Airflow para su orquestación.

La solución incorpora una PSA, validaciones mediante Data Contract, una Dead Letter Queue para registros inválidos y una capa Gold con datos transformados, permitiendo un flujo reproducible y escalable.
