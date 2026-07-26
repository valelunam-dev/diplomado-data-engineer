# Orange Canvas — Punto 3: Reglas de Asociación

**Grupo 6 · Escenario 6: Datos Duplicados · Pipeline P1006**
**Archivo de datos:** `orange_escenario6_categorico.csv` (150 filas, 9 columnas categóricas)

> Se eligió **reglas de asociación** (opción 3a). NO clasificador: `Estado` es
> constante = OK en el escenario 6, no hay dos clases para clasificar.

---

## Flujo (workflow) en Orange
```
[File] --> [Association Rules]
       \-> [Data Table]   (para revisar los datos)
```
1. Instalar el add-on **"Associate"** (Options → Add-ons → Associate) si no está.
2. **File**: cargar `orange_escenario6_categorico.csv`. Verificar que todas las
   columnas queden como **categorical** (discretas), no numéricas.
3. Conectar **Association Rules**.
4. Configurar parámetros (ver abajo) y en el buscador filtrar por
   `Nivel_Duplicados=Alto` para ver causas, o poner `Nivel_Duplicados=Alto`
   como antecedente para ver efectos.

## Parámetros recomendados (para el informe)
- **Soporte mínimo:** 5 % (0,05)
- **Confianza mínima:** 50 % (0,50)

> Con 150 filas, umbrales más altos dejan sin reglas. Reportar EXACTAMENTE estos
> valores en el informe (el PDF lo exige).

---

## Reglas esperadas — CAUSAS (antecedente → Nivel_Duplicados=Alto)
Soporte base P(Nivel=Alto) = 0,36. Lift > 1 = asociación relevante.

| Regla | Soporte | Confianza | Lift |
|---|---|---|---|
| Region=Norte & Dia=Lunes → Alto | 0,05 | 0,75 | 2,08 |
| Tipo=Batch & Dia=Lunes → Alto | 0,07 | 0,73 | 2,02 |
| Prioridad=Media & Dia=Lunes → Alto | 0,06 | 0,67 | 1,85 |
| Sistema=CRM & Region=Sur → Alto | 0,06 | 0,56 | 1,54 |
| Sistema=CRM & Prioridad=Alta → Alto | 0,07 | 0,55 | 1,52 |
| Sistema=CRM & Region=Centro → Alto | 0,10 | 0,53 | 1,48 |

**Regla de 1 ítem más fuerte:** `Dia=Lunes → Alto` (confianza 0,67, lift 1,85).
→ El **lunes** es el mayor detonante de duplicación alta.

## Reglas esperadas — EFECTOS (Nivel_Duplicados=Alto → consecuencia)
| Regla | Soporte | Confianza | Lift |
|---|---|---|---|
| Nivel=Alto → Rechazos_Alto | 0,18 | 0,50 | 1,50 |
| Nivel=Alto → Reglas_Muchas | 0,17 | 0,46 | 1,39 |

→ La duplicación alta **aumenta 50 % la probabilidad** de muchos registros
rechazados y de incumplir muchas reglas de calidad.

---

## Interpretación para el informe (hilo conductor)
- **Causa temporal dominante:** los lunes concentran la duplicación alta
  (posible reproceso de fin de semana / cargas acumuladas).
- **Causa por fuente:** CRM combinado con ciertas regiones/prioridad.
- **Efecto:** más duplicados → más rechazos y más reglas de calidad incumplidas.
- Esto confirma y profundiza la historia de Flourish (heatmap CRM, race, mapa)
  y el dashboard de Tableau (efectos y pico del lunes).

## Cómo se discretizaron las variables (documentar)
- `Nivel_Duplicados`: Duplicados % → Bajo(0-1) / Medio(2-3) / Alto(4-5)
- `Rechazos`: terciles de Registros_Rechazados → Bajo/Medio/Alto
- `Reglas_Calidad`: 0-2=Pocas / 3=Medias / >=4=Muchas
- `Reintentos`: 0/1/2
- Estructurales sin cambio: Sistema_Origen, Tipo_Pipeline, Prioridad, Region, Dia_Semana
