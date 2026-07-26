# Story de Flourish — Grupo 6 (Datos Duplicados)

Objetivo: unir las 3 visualizaciones en UNA sola historia con navegación, para
obtener **un único link público** (el del pie de página del informe).

## Visualizaciones a incluir (ya publicadas)
1. Heatmap (estática): https://public.flourish.studio/visualisation/29661215/
2. Bar chart race (dinámica): https://public.flourish.studio/visualisation/29661242/
3. Mapa de puntos: https://public.flourish.studio/visualisation/29661334/

---

## Cómo crear la Story (paso a paso)
1. Entra a flourish.studio → en tu panel, botón **"New story"** (arriba, junto a
   "New visualisation").
2. Se abre el editor de Story. A la izquierda verás la lista de **slides**.
3. En cada slide, clic en **"Choose visualisation"** y selecciona una de tus 3
   visualizaciones publicadas.
4. Para cada slide, en el panel derecho escribe el **título** y el **texto**
   (usa los de abajo).
5. Agrega slides con el botón **"+ Add slide"** hasta tener las 5.
6. Ordena los slides arrastrándolos (intro → heatmap → race → mapa → cierre).
7. Arriba a la derecha: **Preview** para revisar la navegación (flechas).
8. **Publish** → copia el enlace público. **Verifica que NO termine en "edit".**
9. Ese link va en el pie de página del informe (página 4 del esqueleto).

> Nota: si un slide muestra la misma visualización que otro pero con un filtro o
> zoom distinto, puedes fijar ese "estado" con el botón de cámara/estado del slide.
> Para este trabajo basta con un slide por visualización.

---

## Texto de cada slide (copiar y pegar)

### Slide 1 — Portada / Contexto
**Título:** Datos duplicados en JLMLSys Solutions — Pipeline P1006
**Texto:**
> Diagnóstico del escenario de datos duplicados sobre 150 ejecuciones
> (enero–junio 2025). Recorrido: qué dispara la duplicación (causas) y qué
> consecuencias genera (efectos).
> Grupo 6 · Valeria Luna Meza · Pedro Barraza Rivera.
*(Puedes usar el heatmap de fondo o dejar solo texto.)*

### Slide 2 — Heatmap (¿en qué fuente?)
**Visualización:** Heatmap (29661215)
**Título:** La duplicación no es pareja entre fuentes
**Texto:**
> CRM concentra la mayor cantidad de casos de duplicación **Alta**, seguido de Web.
> IoT muestra el perfil más limpio. La fuente de origen es la primera pista.

### Slide 3 — Bar chart race (¿cómo evoluciona?)
**Visualización:** Bar chart race (29661242)
**Título:** El volumen duplicado se acumula mes a mes
**Texto:**
> Entre enero y junio, los registros duplicados crecen de forma sostenida.
> **Web y CRM** lideran el volumen acumulado, confirmando el patrón del heatmap.

### Slide 4 — Mapa (¿dónde?)
**Visualización:** Mapa de puntos (29661334)
**Título:** La Zona Norte concentra la mayor tasa de duplicación
**Texto:**
> Geolocalizando las 150 ejecuciones, la **Zona Norte** presenta la tasa promedio
> más alta (2,71%). El tamaño del punto = volumen duplicado; el color = tasa.

### Slide 5 — Cierre (causas → efectos)
**Visualización:** puede repetir el mapa o el heatmap de fondo
**Título:** Causas y efectos: el lunes y CRM disparan; la calidad lo paga
**Texto:**
> Los duplicados se disparan los **lunes** y en la fuente **CRM**, y su efecto es
> claro: más **registros rechazados** y más **reglas de calidad incumplidas**.
> (Detalle cuantitativo en el dashboard Tableau y las reglas de asociación Orange.)

---

## Después de publicar
- [ ] Copiar el link de la Story (termina en un número, NO en "edit")
- [ ] Pegarlo en `ENLACES_INFORME.md` y en el pie de página del informe
- [ ] Tomar screenshot de cada slide si quieres insertarlos en el PDF
