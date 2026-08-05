# -*- coding: utf-8 -*-
"""Renumera las secciones del cuaderno para que coincidan con los apartados del informe.

Solo toca celdas markdown (encabezados y referencias cruzadas): las salidas no se alteran.
"""
import json, re, sys
from pathlib import Path

# Reemplazos explícitos, del más específico al más general para evitar colisiones.
REEMPLAZOS = [
    # --- Sección 1 -> 0 : Configuración del entorno
    ("## 1. Configuración del entorno", "## 0. Configuración del entorno"),
    ("### 1.1 Funciones auxiliares", "### 0.1 Funciones auxiliares"),

    # --- Sección 2 -> 1 : Comprensión del problema
    ("## 2. Comprensión del problema", "## 1. Comprensión del problema"),
    ("### 2.1 Problema de negocio", "### 1.1 Problema de negocio"),
    ("### 2.2 Objetivo del proyecto", "### 1.2 Objetivo del proyecto"),
    ("### 2.3 Variable objetivo", "### 1.3 Variable objetivo"),
    ("### 2.4 Tipo de problema de Machine Learning", "### 1.4 Tipo de problema de Machine Learning"),
    ("### 2.5 Beneficio esperado para la organización", "### 1.5 Beneficio esperado para la organización"),
    ("### 2.6 Restricción metodológica clave", "### 1.6 Restricción metodológica clave"),

    # --- Secciones 3 y 4 -> 2 : Dataset y análisis exploratorio
    ("## 3. Carga de los datos",
     "## 2. Dataset y análisis exploratorio (EDA)  *(20 puntos)*\n\n### 2.1 Carga de los datos"),
    ("## 4. Análisis Exploratorio de Datos (EDA)  *(20 puntos)*\n\n", ""),
    ("### 4.1 Dimensiones, tipos de datos y consumo de memoria", "### 2.2 Dimensiones, tipos de datos y consumo de memoria"),
    ("### 4.2 Valores nulos", "### 2.3 Valores nulos"),
    ("### 4.3 Registros duplicados", "### 2.4 Registros duplicados"),
    ("### 4.4 Construcción de la variable objetivo", "### 2.5 Construcción de la variable objetivo"),
    ("### 4.5 Estadísticas descriptivas", "### 2.6 Estadísticas descriptivas"),
    ("### 4.6 Distribución de la variable objetivo", "### 2.7 Distribución de la variable objetivo"),
    ("### 4.7 Distribución de las variables numéricas", "### 2.8 Distribución de las variables numéricas"),
    ("### 4.8 Análisis de las variables categóricas", "### 2.9 Análisis de las variables categóricas"),
    ("### 4.9 Patrones temporales de la operación", "### 2.10 Patrones temporales de la operación"),
    ("### 4.10 Matriz de correlación", "### 2.11 Matriz de correlación"),

    # --- Sección 5 -> 3 : Preparación de los datos
    ("## 5. Preparación de los datos", "## 3. Preparación de los datos"),
    ("### 5.10 División en conjuntos de entrenamiento y prueba", "### 3.10 División en conjuntos de entrenamiento y prueba"),
    ("### 5.1 Tratamiento de valores extremos", "### 3.1 Tratamiento de valores extremos"),
    ("### 5.2 Tratamiento de valores nulos", "### 3.2 Tratamiento de valores nulos"),
    ("### 5.3 Verificación de registros duplicados", "### 3.3 Verificación de registros duplicados"),
    ("### 5.4 Efecto de la depuración", "### 3.4 Efecto de la depuración"),
    ("### 5.5 Ingeniería de características", "### 3.5 Ingeniería de características"),
    ("### 5.6 Análisis exploratorio posterior", "### 3.6 Análisis exploratorio posterior"),
    ("### 5.7 Selección de predictores", "### 3.7 Selección de predictores"),
    ("### 5.8 Muestreo para el modelamiento", "### 3.8 Muestreo para el modelamiento"),
    ("### 5.9 Codificación de variables categóricas", "### 3.9 Codificación de variables categóricas"),

    # --- Sección 6 -> 4 : Reducción de dimensionalidad
    ("## 6. Reducción de dimensionalidad", "## 4. Reducción de dimensionalidad"),
    ("### 6.1 PCA: determinación", "### 4.1 PCA: determinación"),
    ("### 6.2 Selección de características por información mutua", "### 4.2 Selección de características por información mutua"),
    ("### 6.3 Impacto de la reducción", "### 4.3 Impacto de la reducción"),

    # --- Sección 7 -> 5 : Construcción del modelo
    ("## 7. Construcción del modelo", "## 5. Construcción del modelo"),
    ("### 7.1 Selección y justificación de los algoritmos", "### 5.1 Selección y justificación de los algoritmos"),
    ("### 7.2 Validación cruzada", "### 5.2 Validación cruzada"),
    ("### 7.3 Ajuste de hiperparámetros", "### 5.3 Ajuste de hiperparámetros"),
    ("### 7.4 Modelo final", "### 5.4 Modelo final"),
    ("### 7.5 Diagnóstico de sobreajuste", "### 5.5 Diagnóstico de sobreajuste"),

    # --- Sección 8 -> 6 : Evaluación del modelo
    ("## 8. Evaluación del modelo", "## 6. Evaluación del modelo"),
    ("### 8.1 Métricas de desempeño", "### 6.1 Métricas de desempeño"),
    ("### 8.2 Valores observados frente a valores predichos", "### 6.2 Valores observados frente a valores predichos"),
    ("### 8.3 Análisis de residuos", "### 6.3 Análisis de residuos"),
    ("### 8.4 Error por segmento operacional", "### 6.4 Error por segmento operacional"),

    # --- Sección 9 -> 7 : Interpretación y conclusiones
    ("## 9. Interpretación del modelo y conclusiones", "## 7. Interpretación del modelo y conclusiones"),
    ("### 9.1 Variables más importantes", "### 7.1 Variables más importantes"),
    ("### 9.2 Fortalezas del modelo", "### 7.2 Fortalezas del modelo"),
    ("### 9.3 Limitaciones del modelo", "### 7.3 Limitaciones del modelo"),
    ("### 9.4 Posibles mejoras", "### 7.4 Posibles mejoras"),
    ("### 9.5 Aplicaciones prácticas", "### 7.5 Aplicaciones prácticas"),
    ("### 9.6 Conclusiones finales", "### 7.6 Conclusiones finales"),

    # --- Sección 10 -> 8 : Persistencia del modelo
    ("## 10. Persistencia del modelo (MLOps)", "## 8. Persistencia del modelo (MLOps)"),
    ("### 10.1 Verificación de uso del modelo guardado", "### 8.1 Verificación de uso del modelo guardado"),
    ("### 10.2 Resumen de tiempos de ejecución", "### 8.2 Resumen de tiempos de ejecución"),

    # --- Sección 11 -> Anexo : Entregables y referencias
    ("## 11. Entregables y referencias", "## Anexo · Entregables y referencias"),

    # --- Referencias cruzadas dentro del texto (de específico a general)
    ("sección 5.1", "sección 3.1"),
    ("sección 5.2", "sección 3.2"),
    ("sección 5.6", "sección 3.6"),
    ("sección 6.3", "sección 4.3"),
    ("sección 7.3", "sección 5.3"),
    ("sección 5", "sección 3"),
]


def renumerar_texto(texto):
    for antes, despues in REEMPLAZOS:
        texto = texto.replace(antes, despues)
    return texto


def renumerar_cuaderno(ruta):
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    tocadas = 0
    for celda in datos["cells"]:
        if celda["cell_type"] != "markdown":
            continue
        fuente = celda["source"]
        original = fuente if isinstance(fuente, str) else "".join(fuente)
        nuevo = renumerar_texto(original)
        if nuevo != original:
            celda["source"] = nuevo
            tocadas += 1
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{ruta}: {tocadas} celdas markdown actualizadas")


def renumerar_generador(ruta):
    texto = Path(ruta).read_text(encoding="utf-8")
    Path(ruta).write_text(renumerar_texto(texto), encoding="utf-8")
    print(f"{ruta}: generador actualizado")


if __name__ == "__main__":
    renumerar_cuaderno(sys.argv[1])
    if len(sys.argv) > 2:
        renumerar_generador(sys.argv[2])
