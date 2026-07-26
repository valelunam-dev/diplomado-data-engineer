# Conclusiones técnicas — Escenario 6: Datos Duplicados (Grupo 6)

**Método:** Reglas de asociación en Orange (Soporte mín. 5%, Confianza mín. 50%).
**Objetivo del análisis:** identificar causas y efectos de la duplicación en el pipeline P1006.

---

## Reglas más fuertes → Nivel_Duplicados = Alto (CAUSAS)

| Regla | Sup | Conf | Lift |
|---|---|---|---|
| Lunes + Muchas reglas de calidad → Alto | 0,053 | **0,889** | **2,47** |
| Región Sur + Rechazos altos → Alto | 0,067 | 0,833 | 2,32 |
| Batch + Lunes → Alto | 0,053 | 0,727 | 2,02 |
| Streaming + Prioridad Alta + Rechazos altos → Alto | 0,053 | 0,727 | 2,02 |
| Prioridad Alta + Rechazos altos → Alto | 0,080 | 0,667 | 1,85 |
| **Lunes → Alto** (regla de 1 solo ítem) | 0,080 | 0,667 | 1,85 |
| CRM + Región Centro → Alto | 0,053 | 0,533 | 1,48 |

## Reglas de efecto (duplicación ↔ consecuencias)
| Regla | Sup | Conf | Lift |
|---|---|---|---|
| Rechazos altos → Nivel Alto | 0,180 | 0,540 | 1,50 |
| Muchas reglas de calidad → Nivel Alto | 0,167 | 0,500 | 1,39 |

## Perfil "limpio" → Nivel_Duplicados = Bajo (contraste)
| Regla | Sup | Conf | Lift |
|---|---|---|---|
| Pocos rechazos + Pocas reglas incumplidas + 1 reintento → Bajo | 0,053 | 0,889 | 2,84 |
| Batch + Sur + Pocos rechazos + Pocas reglas → Bajo | 0,053 | 0,800 | 2,55 |

---

## CONCLUSIONES (para el informe, punto 5)

1. **El día lunes es el principal detonante de la duplicación alta.** Es la regla
   de un solo antecedente más fuerte (conf. 0,67; lift 1,85) y, combinada con
   "muchas reglas de calidad incumplidas", alcanza **88,9% de confianza (lift 2,47)**.
   Como el lunes aparece tanto en pipelines Batch como Streaming, apunta a una
   **causa operacional** (probable reproceso/acumulación del fin de semana), no a
   un tipo de pipeline específico.

2. **Cadena causa–efecto confirmada en ambos sentidos:** la duplicación alta va
   asociada a **más registros rechazados** y a **más reglas de calidad incumplidas**
   (lift 1,50 y 1,39). Es decir, los duplicados **degradan la calidad y aumentan
   el rechazo** de datos, el efecto central del escenario.

3. **Perfiles de riesgo por fuente y zona:** CRM combinado con la Región Centro,
   y las cargas de Prioridad Alta con rechazos altos, concentran duplicación alta.
   Coincide con el heatmap de Flourish (CRM/Web como fuentes más duplicadas).

4. **Perfil limpio bien definido:** pocos rechazos + pocas reglas incumplidas
   predicen duplicación baja con 88,9% de confianza (lift 2,84). Sirve como
   "estado objetivo" para la plataforma.

5. **Recomendación técnica:** reforzar la deduplicación en las cargas de los
   **lunes** y en la fuente **CRM**, y monitorear las reglas de calidad como
   indicador temprano: cuando se disparan, la duplicación alta es casi segura.

> Estas conclusiones integran los tres artefactos: la **historia Flourish**
> (dónde y cuándo), el **dashboard Tableau** (efectos y pico del lunes) y las
> **reglas de asociación Orange** (relaciones causa–efecto cuantificadas).
