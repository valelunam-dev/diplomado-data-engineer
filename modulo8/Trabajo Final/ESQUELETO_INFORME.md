# Esqueleto del Informe Técnico — Módulo 8
**Grupo 6:** Valeria Luna Meza · Pedro Barraza Rivera
**Escenario 6:** Datos Duplicados (identificar causas y efectos) · Plataforma JLMLSys Solutions · Pipeline P1006

> Formato: 1 PDF, máx. 8 páginas. Debe contener los 5 resultados (cada uno con su
> visualización + explicación) y una conclusión técnica. La URL de la historia
> Flourish va como **pie de página** (no puede terminar en "edit").
> Entrega: aula virtual, domingo 12 de julio 23:59.

---

## PÁGINA 1 — Portada + Introducción

**Portada (mitad superior):**
- Universidad de Santiago — Facultad de Administración y Economía
- Diplomado en Data Engineer · Módulo 8: Fundamentos de Visualización de Datos
- Título: *"Diagnóstico de Datos Duplicados en la plataforma JLMLSys Solutions"*
- Integrantes: Valeria Luna Meza, Pedro Barraza Rivera
- Profesor: José Luis Martí Lara · Fecha: julio 2025

**Introducción (mitad inferior) — texto base:**
> La empresa JLMLSys Solutions opera una plataforma de datos que integra múltiples
> sistemas de origen (ERP, CRM, POS, IoT, Web). Este informe diagnostica el
> comportamiento del pipeline **P1006** con foco en el escenario de **datos
> duplicados**, buscando identificar sus **causas** y **efectos**. Se trabajó con
> 150 ejecuciones registradas entre enero y junio de 2025. Tras una limpieza y
> preparación de datos (tipado de fechas/horas, verificación de nulos y duplicados
> exactos —sin registros descartados, se mantienen los 150— y creación de variables
> derivadas como `Nivel_Duplicados`), se aplicaron herramientas de visualización
> (Flourish, Tableau) y de minería de datos (Orange) siguiendo un hilo conductor
> único: **qué dispara la duplicación y qué consecuencias genera**.

---

## PÁGINA 2 — Resultado 1: Visualización ESTÁTICA (Heatmap) [Flourish]

- **Captura:** heatmap Sistema_Origen × Nivel_Duplicados (foto ya en la carpeta).
- **Texto base:**
> El mapa de calor muestra la distribución de ejecuciones según fuente de origen y
> nivel de duplicación (Bajo/Medio/Alto). **CRM concentra la mayor cantidad de casos
> de duplicación Alta**, seguido de Web, mientras que **IoT presenta el perfil más
> limpio**. Esto entrega una primera hipótesis: la fuente de origen incide en la
> duplicación.

---

## PÁGINA 3 — Resultado 2: Visualización DINÁMICA (Bar chart race) [Flourish]

- **Captura:** bar chart race (o secuencia de 2-3 frames: mes 1, mes 3, mes 6).
- **Texto base:**
> La carrera de barras muestra la **acumulación de registros duplicados por fuente**
> entre enero y junio de 2025. Se observa un crecimiento sostenido, con **Web y CRM
> liderando el volumen acumulado** al cierre del período, confirmando el patrón del
> heatmap y agregando la dimensión temporal del problema.

---

## PÁGINA 4 — Resultado 3: MAPA / GRAFO [Flourish]

*(El enunciado pide un grafo O un mapa; incluimos el mapa; el grafo de reglas
queda como refuerzo opcional del punto 5.)*
- **Captura:** mapa de puntos (150 ejecuciones por lat/lon).
- **Texto base:**
> El mapa geolocaliza las ejecuciones en tres zonas (Norte, Centro, Sur). La **Zona
> Norte presenta la mayor tasa promedio de duplicación (2,71%)**. El tamaño de cada
> punto representa el volumen duplicado y el color, la tasa, revelando focos
> geográficos que conviene priorizar.

**➜ PIE DE PÁGINA (aquí):** *Historia interactiva Flourish:*
`https://public.flourish.studio/visualisation/29661334/`
*(Reemplazar por el link de la STORY si se agrupan las 3 piezas en una sola.)*

---

## PÁGINA 5 — Resultado 4: DASHBOARD [Tableau] (Pedro)

- **Captura:** dashboard con ≥2 visualizaciones (efectos + patrón semanal).
- **Texto base:**
> El dashboard complementa la historia enfocándose en los **efectos** de la
> duplicación. Se observa que al aumentar el `Nivel_Duplicados`, crecen los
> **registros rechazados** (1.107 → 1.751 → 2.222 en promedio) y las **reglas de
> calidad incumplidas**. Además, el patrón semanal evidencia un **pico los lunes**
> (3,50% vs ~2,4% el resto), sugiriendo una causa operacional.

---

## PÁGINA 6 — Resultado 5: REGLAS DE ASOCIACIÓN [Orange]

- **Capturas:** (1) panel de configuración (Soporte 5%, Confianza 50%) y
  (2) tabla de reglas legibles filtradas a `Nivel_Duplicados=Alto`.
- **Texto base:**
> Con Orange se generaron reglas de asociación (**soporte mínimo 5%, confianza
> mínima 50%**). Las reglas de mayor fuerza confirman las causas y efectos:
> - `Lunes + Muchas reglas de calidad → Nivel Alto` (conf. 0,889; lift 2,47)
> - `Región Sur + Rechazos altos → Nivel Alto` (conf. 0,833; lift 2,32)
> - `Rechazos altos → Nivel Alto` y `Muchas reglas incumplidas → Nivel Alto`
>   (lift 1,50 y 1,39), evidenciando la relación bidireccional entre duplicación,
>   rechazo y calidad.

---

## PÁGINA 7 — Conclusiones técnicas

Usar las 5 conclusiones de `CONCLUSIONES.md`:
1. El **lunes** es el principal detonante de duplicación alta (causa operacional).
2. Cadena **causa–efecto confirmada**: duplicados → más rechazos y más reglas
   de calidad incumplidas.
3. Perfiles de riesgo: **CRM + Centro**, **Prioridad Alta + rechazos altos**.
4. Perfil limpio bien definido (pocos rechazos + pocas reglas → Nivel Bajo).
5. **Recomendación:** reforzar deduplicación en cargas de lunes y en CRM;
   usar las reglas de calidad como alerta temprana.

---

## PÁGINA 8 — (Reserva) Anexos / Coherencia metodológica

- Nota de coherencia: las 3 herramientas apuntan al mismo hallazgo (lunes + CRM
  como causa; rechazos + calidad como efecto).
- Opcional: grafo de reglas (network graph) como evidencia visual de las relaciones.
- Diccionario de datos resumido / fuente del dataset.

> Si el contenido cabe en 7 páginas, mejor: el límite es "no más de 8".

---

## Checklist de entrega
- [ ] 5 resultados, cada uno con visualización + explicación
- [ ] URL Flourish en pie de página (NO termina en "edit")
- [ ] Máx. 8 páginas · un solo PDF
- [ ] Capturas de buena calidad (Orange con reglas legibles, no cortadas)
- [ ] Conclusión técnica al final
- [ ] Hilo conductor claro: causas (lunes/CRM) → efectos (rechazos/calidad)

## Enlaces
- Heatmap (estática): https://public.flourish.studio/visualisation/29661215/
- Bar chart race (dinámica): https://public.flourish.studio/visualisation/29661242/
- Mapa de puntos (mapa): https://public.flourish.studio/visualisation/29661334/
