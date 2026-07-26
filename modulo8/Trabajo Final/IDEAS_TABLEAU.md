# Ideas Dashboard Tableau — Punto 2 (para Pedro)

**Grupo 6 · Escenario 6: Datos Duplicados · Pipeline P1006**
**Fuente de datos:** `Grupo6_Escenario6_Duplicados_limpio.csv` (150 filas)

> Regla del PDF: mínimo 2 visualizaciones que **complementen** la historia de Flourish
> (no repetir). Flourish ya mostró: heatmap por fuente, evolución mensual y mapa.
> Tableau debe enfocarse en los **EFECTOS** de los duplicados y el **patrón semanal**.

---

## Tema del dashboard
**"Los efectos de la duplicación: más rechazos y más reglas de calidad incumplidas"**

## Fila de KPIs (BANs / números grandes) — arriba del dashboard
- **Registros duplicados estimados (total):** 1.017.658
- **% duplicados promedio:** 2,57 %
- **Fuente más crítica:** CRM
- **Día más crítico:** Lunes (3,50 %)

Campo: usa `Registros_Duplicados_est` (SUM), `Duplicados` (AVG). Formato como texto grande.

---

## Visualización 1 — EFECTO sobre registros rechazados
- **Tipo:** barras por `Nivel_Duplicados` (Bajo/Medio/Alto) con AVG(`Registros_Rechazados`).
- **Qué muestra:** rechazos suben 1.107 → 1.751 → 2.222 al subir el nivel de duplicación.
- **Correlación de respaldo:** Duplicados vs Registros_Rechazados = +0,35.
- Ordena el eje: Bajo → Medio → Alto (no alfabético).

## Visualización 2 — EFECTO sobre reglas de calidad
- **Tipo:** barras o dual-axis, AVG(`Reglas_Calidad`) por `Nivel_Duplicados`.
- **Qué muestra:** 2,0 → 3,0 → 3,4 reglas incumplidas. Correlación +0,39.
- Alternativa: scatter `Duplicados` (x) vs `Reglas_Calidad` (y) con línea de tendencia.

## Visualización 3 — Patrón SEMANAL (complementa el race mensual de Flourish)
- **Tipo:** barras AVG(`Duplicados`) por `Dia_Semana`, ordenadas Lunes→Domingo.
- **Qué muestra:** el pico del **lunes (3,50 %)** vs ~2,4 % el resto → posible causa operacional.
- Resalta el lunes con color distinto.

## Visualización 4 (opcional) — Batch vs Streaming
- **Tipo:** barras comparando AVG(`Duplicados`) y SUM(`Registros_Duplicados_est`)
  entre `Tipo_Pipeline`.
- **Qué muestra:** Streaming duplica algo más (2,70 %) que Batch (2,43 %).

---

## Layout sugerido
```
[ KPI 1 ][ KPI 2 ][ KPI 3 ][ KPI 4 ]     <- fila de números grandes
[  Viz 1: rechazos por nivel   ][ Viz 3: patrón semanal ]
[  Viz 2: reglas de calidad     ][ Viz 4: batch vs stream ]
```
- Añadir **filtros** interactivos: `Sistema_Origen`, `Region`, `Tipo_Pipeline`.
- Título del dashboard y una frase de conclusión abajo.

## Notas
- NO repetir el heatmap ni el mapa (ya están en Flourish).
- Campos derivados ya vienen en el CSV: `Nivel_Duplicados`, `Registros_Duplicados_est`,
  `Dia_Semana`, `Mes`, `Tiempo_min`.
- Exportar screenshots de buena calidad para el informe PDF.
