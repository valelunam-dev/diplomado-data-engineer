# -*- coding: utf-8 -*-
"""Genera el informe ejecutivo (Markdown + PDF) a partir de los resultados reales del cuaderno."""
import json, sys
from pathlib import Path

BASE = Path(__file__).parent
V = json.loads((BASE / "valores_informe.json").read_text(encoding="utf-8"))

FIGURAS = BASE / "figuras"

CSS = """
@page { size: a4 portrait; margin: 1.7cm 1.9cm 1.6cm 1.9cm;
        @frame footer { -pdf-frame-content: pie; bottom: 0.9cm; margin-left: 1.9cm;
                        margin-right: 1.9cm; height: 1cm; } }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.3pt; color: #1c1c1c;
       line-height: 1.42; text-align: justify; }
h1 { font-size: 17pt; color: #0b3c5d; margin: 0 0 2pt 0; line-height: 1.2; }
h2 { font-size: 11.4pt; color: #0b3c5d; margin: 13pt 0 4pt 0;
     border-bottom: 1.1pt solid #0b3c5d; padding-bottom: 2pt; }
h3 { font-size: 9.9pt; color: #16607f; margin: 9pt 0 3pt 0; }
p { margin: 0 0 5pt 0; }
ul { margin: 0 0 5pt 14pt; padding: 0; }
li { margin-bottom: 2pt; }
table { width: 100%; border-collapse: collapse; margin: 4pt 0 7pt 0; font-size: 8.3pt; }
th { background-color: #0b3c5d; color: #ffffff; padding: 3.5pt 4pt; text-align: left;
     font-weight: bold; }
td { padding: 3pt 4pt; border-bottom: 0.5pt solid #cfd8dc; vertical-align: top; }
tr.par td { background-color: #f2f6f8; }
.portada { text-align: center; margin-bottom: 8pt; }
.institucion { font-size: 8.6pt; color: #4a5a63; margin-bottom: 10pt; }
.subtitulo { font-size: 10.5pt; color: #33474f; margin: 2pt 0 8pt 0; }
.meta { font-size: 8.4pt; color: #4a5a63; }
.resumen { background-color: #eef4f7; border-left: 2.6pt solid #0b3c5d;
           padding: 6pt 8pt; margin: 6pt 0 9pt 0; font-size: 8.9pt; }
.destacado { background-color: #fff6e5; border-left: 2.6pt solid #d98324;
             padding: 5pt 8pt; margin: 5pt 0 7pt 0; font-size: 8.7pt; }
.kpi { width: 100%; border-collapse: collapse; margin: 5pt 0 8pt 0; }
.kpi td { text-align: center; border: 0.8pt solid #0b3c5d; padding: 5pt 3pt;
          background-color: #f7fafb; }
.kpi .valor { font-size: 14pt; color: #0b3c5d; font-weight: bold; }
.kpi .etiqueta { font-size: 7.4pt; color: #4a5a63; }
.figura { margin: 5pt 0 3pt 0; }
.pie-figura { font-size: 7.6pt; color: #4a5a63; text-align: center; margin: 0 0 7pt 0;
              font-style: italic; }
#pie { font-size: 7.2pt; color: #78909c; text-align: center; }
.nota { font-size: 7.8pt; color: #4a5a63; }
"""


def fila(celdas, par=False, cabecera=False):
    etiqueta = "th" if cabecera else "td"
    clase = ' class="par"' if par and not cabecera else ""
    return (f"<tr{clase}>" + "".join(f"<{etiqueta}>{c}</{etiqueta}>" for c in celdas) + "</tr>")


def tabla(cabeceras, filas, anchos=None):
    grupo = ""
    if anchos:
        grupo = "".join(f'<col width="{a}"/>' for a in anchos)
        grupo = f"<colgroup>{grupo}</colgroup>"
    cuerpo = "".join(fila(f, par=(i % 2 == 1)) for i, f in enumerate(filas))
    return f"<table>{grupo}{fila(cabeceras, cabecera=True)}{cuerpo}</table>"


ANCHO_UTIL = 487          # ancho útil de la página A4 con los márgenes definidos, en puntos

def figura(nombre, pie, ancho=1.0):
    ruta = (FIGURAS / f"{nombre}.png").as_posix()
    puntos = int(ANCHO_UTIL * ancho)
    return (f'<div class="figura"><img src="{ruta}" style="width: {puntos}pt"/></div>'
            f'<p class="pie-figura">{pie}</p>')


HTML = f"""
<div id="pie"><p id="pie">Evaluación Final — Diplomado en Data Engineer · USACH · Valeria Luna
· Predicción de la duración de viajes urbanos · página <pdf:pagenumber> de <pdf:pagecount></p></div>

<div class="portada">
  <p class="institucion"><b>UNIVERSIDAD DE SANTIAGO DE CHILE</b><br/>
  Facultad de Administración y Economía · Diplomado en Data Engineer<br/>
  Módulo 10 — Machine Learning para la escala masiva de datos</p>
  <h1>Predicción de la duración de viajes urbanos mediante Machine Learning</h1>
  <p class="subtitulo">Informe ejecutivo — Evaluación Final</p>
  <p class="meta"><b>Estudiante:</b> Valeria Luna &nbsp;·&nbsp; <b>Fecha:</b> agosto de 2026
  &nbsp;·&nbsp; <b>Tipo de problema:</b> Regresión supervisada<br/>
  <b>Dataset:</b> NYC TLC — <i>Yellow Taxi Trip Records</i>, enero 2024
  ({V['registros_originales']} viajes)</p>
</div>

<div class="resumen">
<b>Resumen ejecutivo.</b> Las empresas de transporte de pasajeros programan su operación en función
del tiempo que demora cada servicio y, en la práctica, lo estiman con promedios históricos. Este
proyecto construye un modelo de Machine Learning que predice la duración de un viaje urbano
utilizando <b>solo información disponible al momento de iniciarlo</b>. Sobre {V['registros_originales']}
viajes reales de la ciudad de Nueva York, el modelo seleccionado
(<i>HistGradientBoostingRegressor</i> de scikit-learn) alcanza un <b>R² de {V['r2']}</b> y un error
medio absoluto de <b>{V['mae']} minutos</b> frente a una duración promedio de {V['duracion_promedio']}
minutos, lo que representa una <b>reducción de {V['mejora_base']} del error</b> respecto de estimar
con el promedio histórico. El trabajo deja dos hallazgos metodológicos relevantes: la depuración de
datos elevó la correlación entre distancia y duración de <b>{V['corr_sucia']} a {V['corr_limpia']}</b>,
y la reducción de dimensionalidad mediante PCA <b>no mejoró</b> el desempeño predictivo.
</div>

<h2>1. Comprensión del problema</h2>

<p><b>Problema de negocio.</b> Cuando la duración de un servicio se estima mal se producen efectos
en cadena: conductores sin holgura entre servicios, incumplimiento de horarios comprometidos,
sobredotación o subdotación de flota y tiempos muertos que se pagan igual. La estimación por
promedios ignora que la duración depende fuertemente de la hora del día, del día de la semana, del
origen-destino y de si el viaje involucra un aeropuerto.</p>

<p><b>Objetivo.</b> Construir un modelo capaz de predecir la duración de un viaje urbano, en minutos,
utilizando únicamente información conocida al iniciar el servicio, de modo que sea utilizable en
producción.</p>

<p><b>Variable objetivo.</b> <span class="nota"><b>duracion_min</b> = (hora de término − hora de
inicio) en minutos.</span> Variable numérica continua y positiva, construida a partir de las marcas
de tiempo del viaje. Corresponde a un problema de <b>aprendizaje supervisado de regresión</b>.</p>

<p><b>Beneficio esperado.</b></p>
{tabla(["Ámbito", "Beneficio"],
       [["Programación de servicios y turnos",
         "Estimar la duración antes de asignar el servicio permite construir turnos factibles y reducir la holgura improductiva."],
        ["Compromiso con el cliente",
         "Informar un tiempo estimado de llegada (ETA) confiable mejora la experiencia y reduce reclamos."],
        ["Dimensionamiento de flota",
         "Conocer la duración esperada por franja horaria y zona permite anticipar los vehículos requeridos."],
        ["Control de gestión y costos",
         "El tiempo es el principal componente del costo variable; comparar duración real versus estimada entrega una línea base objetiva."]],
       anchos=["30%", "70%"])}

<h2>2. Dataset y análisis exploratorio</h2>

<p>Se utilizaron los registros públicos de viajes de taxis amarillos de la ciudad de Nueva York
(NYC Taxi &amp; Limousine Commission), correspondientes a enero de 2024:
<b>{V['registros_originales']} viajes y 19 variables</b> en formato Parquet. El conjunto no fue
utilizado en las clases del diplomado y supera con holgura el mínimo de 100.000 registros. La unidad
de análisis es un viaje individual.</p>

<table class="kpi">
<tr>
  <td><span class="valor">{V['registros_originales']}</span><br/><span class="etiqueta">viajes analizados</span></td>
  <td><span class="valor">{V['nulos_pct']}</span><br/><span class="etiqueta">registros con nulos</span></td>
  <td><span class="valor">0</span><br/><span class="etiqueta">registros duplicados</span></td>
  <td><span class="valor">{V['duracion_mediana']}</span><br/><span class="etiqueta">mediana de duración (min)</span></td>
</tr>
</table>

<p><b>Calidad de los datos.</b> El análisis detectó problemas que condicionan todo el modelamiento:
{V['duracion_negativa']} viajes con duración negativa (término anterior al inicio), una duración
máxima de {V['duracion_maxima']} minutos, una distancia máxima de {V['distancia_maxima']} millas
—físicamente imposible—, {V['distancia_cero']} viajes con distancia cero, montos negativos de hasta
−900 USD y {V['pasajeros_cero']} viajes con cero pasajeros. Los nulos afectan exactamente a
{V['nulos_registros']} registros ({V['nulos_pct']}) y siempre al mismo bloque de cinco variables, lo
que revela registros incompletos de un flujo de captura distinto y no ausencias aleatorias.</p>

{figura("eda_hora", "Figura 1. La demanda alcanza su máximo a las 18:00 (210.582 viajes) y su mínimo a las 4:00 (16.123), pero la duración promedio sigue una curva propia: varía cerca de 40 % entre las 2:00 (12,1 min) y las 16:00 (16,9 min) con distancias medianas equivalentes.")}

{figura("eda_heatmap_hora_dia", "Figura 2. La congestión es un fenómeno de días hábiles en horario de tarde; las madrugadas de fin de semana son los momentos más rápidos de la semana.")}

<div class="destacado">
<b>Hallazgo central del análisis exploratorio.</b> En los datos sin depurar, la correlación entre
distancia y duración es de <b>{V['corr_sucia']}</b>: prácticamente nula, un resultado contraintuitivo
tratándose del determinante físico evidente del tiempo de viaje. La relación no está ausente: unos
pocos miles de registros con valores extremos dominan el coeficiente de Pearson y la ocultan. Si la
selección de variables se hubiera hecho con esa matriz de correlación, <b>se habría descartado la
variable más predictiva del problema</b>.
</div>

<h2>3. Preparación de los datos</h2>

<p><b>Filtros de calidad.</b> Cada criterio responde a una justificación operacional y no a un
recorte estadístico arbitrario. Se retuvo el <b>{V['retenidos_pct']}</b> de los registros
({V['registros_depurados']} viajes), eliminando anomalías sin sacrificar volumen de información.</p>

{tabla(["Filtro aplicado", "Criterio", "Justificación"],
       [["Período", "Inicio dentro de enero 2024", "El archivo corresponde a enero de 2024; existen registros fechados en 2002 por error del taxímetro."],
        ["Duración", "Entre 1 y 120 minutos", f"Bajo 1 minuto no hay servicio efectivo; sobre 2 horas se trata de registros mal cerrados (percentil 99 = {V['percentil99']} min)."],
        ["Distancia", "Entre 0,1 y 100 millas", "Excluye taxímetros sin registrar y valores físicamente imposibles."],
        ["Velocidad implícita", "Entre 1 y 80 mph", "Filtro cruzado: detecta inconsistencias entre distancia y tiempo que los filtros individuales no capturan."],
        ["Zona y tarifa", "Excluir zonas 264/265 y RatecodeID 99", "Códigos reservados a 'desconocido': no aportan información."],
        ["Monto", "total_amount &gt; 0", "Los montos negativos corresponden a anulaciones y reversos contables."]],
       anchos=["17%", "25%", "58%"])}

<p><b>Valores nulos.</b> En lugar de eliminar el {V['nulos_pct']} de las filas, se imputó con
criterios de negocio explícitos: <i>passenger_count</i> con la moda (1 pasajero, recortada al rango
1–6), <i>RatecodeID</i> con la tarifa estándar (aplicada al {V['tarifa_estandar_pct']} de los viajes),
<i>store_and_fwd_flag</i> con "N", y <i>payment_type = 0</i> se conservó como categoría
"Desconocido" por ser informativa en sí misma. Las imputaciones usan valores fijos y no estadísticos
del conjunto completo, de modo que no transfieren información del conjunto de prueba. No se
detectaron registros duplicados, ni por todas las columnas ni por la llave de negocio.</p>

<p><b>Ingeniería de características.</b> Se construyeron {V['n_predictores']} predictores a partir de
las marcas de tiempo, de la tabla oficial de zonas TLC y de la relación origen-destino: hora, día de
la semana, día del mes, indicadores de fin de semana y hora punta, franja horaria, comuna
(<i>borough</i>) y tipo de zona de origen y destino, indicador de aeropuerto, coincidencia de zona y
de comuna, y el logaritmo de la distancia. Todas se calculan con información disponible antes de
iniciar el viaje.</p>

<div class="destacado">
<b>Exclusión deliberada por fuga de información (<i>data leakage</i>).</b> Las variables monetarias
(<i>fare_amount</i>, <i>total_amount</i>, <i>tip_amount</i>, <i>tolls_amount</i> y recargos) se
excluyeron del modelo: la tarifa de un taxi se calcula <b>en función del tiempo y la distancia
recorridos</b>, por lo que conocerla equivale a conocer parcialmente la respuesta, y solo existe una
vez terminado el viaje. Incluirlas habría producido métricas excelentes en el cuaderno y un modelo
inútil en producción. Por la misma razón se excluyó la velocidad implícita, derivada de la duración.
</div>

<p><b>Codificación, escalamiento y división.</b> Se integró todo en un <i>Pipeline</i> de
scikit-learn con tres tratamientos diferenciados: <i>StandardScaler</i> para las variables numéricas
(indispensable para PCA y para la regresión lineal), <i>OneHotEncoder</i> para las categóricas de
baja cardinalidad —con <i>handle_unknown="ignore"</i> para tolerar categorías nuevas en producción— y
<i>TargetEncoder</i> con validación cruzada interna para las zonas de origen y destino
({V['n_zonas_pu']} y {V['n_zonas_do']} categorías), que con codificación <i>one-hot</i> habrían
generado más de 500 columnas dispersas. El resultado son {V['n_caracteristicas']} características.
El modelamiento se realizó sobre una <b>muestra aleatoria de {V['muestra']} viajes</b>
({V['muestra_pct']} del total depurado), cuya representatividad se verificó comparando medias y
desviaciones estándar con la población (diferencias inferiores a 0,5 %), con división
<b>80 % entrenamiento / 20 % prueba</b> y semilla fija.</p>

<h2>4. Reducción de dimensionalidad</h2>

<p>Se aplicaron y compararon dos técnicas estudiadas en el diplomado. <b>PCA</b>, con el criterio de
conservar el 95 % de la varianza acumulada, comprimió las {V['n_caracteristicas']} características en
<b>{V['n_componentes']} componentes</b> (reducción del {V['reduccion_pca_pct']}). La <b>selección por
información mutua</b> —que a diferencia de la correlación de Pearson detecta relaciones no
lineales— retuvo las {V['k_seleccionadas']} características con mayor dependencia respecto del
objetivo, fijando K en el punto donde el <i>ranking</i> entra en su zona plana.</p>

{tabla(["Representación de los datos", "Dimensiones", "MAE (min)", "RMSE (min)", "R²"],
       V["tabla_reduccion"], anchos=["46%", "14%", "13%", "13%", "14%"])}

{figura("pca_varianza", "Figura 3. Gráfico de sedimentación: el 95 % de la varianza se concentra en muy pocas componentes, producto de la redundancia entre columnas del one-hot.", ancho=0.88)}

<div class="destacado">
<b>Impacto de la reducción de dimensionalidad.</b> <b>Ninguna de las dos técnicas mejoró el
desempeño.</b> PCA redujo la matriz un {V['reduccion_pca_pct']} pero el R² cayó de
{V['r2_sin_reduccion']} a {V['r2_pca']} y el MAE aumentó de {V['mae_sin_reduccion']} a
{V['mae_pca']} minutos: PCA maximiza varianza, no capacidad predictiva, y sus combinaciones lineales
destruyen la estructura original que los modelos de árboles aprovechan mediante cortes sobre
variables individuales. La selección por información mutua resultó <b>aún menos favorable</b>
(R² = {V['r2_mi']}, MAE {V['mae_mi']} min) por una razón instructiva: al ordenar las variables por su
aporte <i>marginal</i>, descartó <i>hora</i>, <i>día de la semana</i> y <i>franja horaria</i>, cuya
correlación individual con la duración es casi nula ({V['corr_hora']}) pero que resultan decisivas
<b>en interacción</b> con la distancia y la zona —como confirma después la importancia por
permutación, donde <i>hora</i> aparece en segundo lugar—. <b>Decisión:</b> el modelo final se entrena
sin reducción de dimensionalidad; con {V['n_caracteristicas']} características el costo computacional
es bajo y el negocio requiere explicar sus estimaciones, algo imposible con componentes principales.
</div>

<h2>5. Construcción del modelo</h2>

<p>Se compararon cinco alternativas de complejidad creciente, todas de scikit-learn, sobre el mismo
preprocesamiento: la media histórica como línea base (representa la práctica actual), regresión
lineal, árbol de decisión, <i>Random Forest</i> y <i>gradient boosting</i> por histogramas. El
problema presenta relaciones claramente no lineales —el efecto de la hora depende del día y el de la
distancia depende de la zona—, por lo que se anticipaba un mejor desempeño de los modelos de
árboles.</p>

{tabla(["Modelo", "MAE (min)", "RMSE (min)", "R² prueba", "R² entren.", "Brecha", "Ajuste (s)"],
       V["tabla_modelos"], anchos=["30%", "12%", "12%", "12%", "12%", "10%", "12%"])}

<p>La línea base de la media obtiene un error medio de {V['mae_base']} minutos: ese es el costo de
estimar con promedios. La regresión lineal explica cerca del {V['r2_lineal_pct']} de la varianza
—buena parte de la señal es lineal por efecto de la distancia—, pero no captura las interacciones.</p>

<p>Con parámetros por defecto, <i>Random Forest</i> obtiene un R² levemente superior
({V['r2_rf']} frente a {V['r2_sin_reduccion']}). Se seleccionó igualmente el <i>gradient
boosting</i> por tres razones: <b>sobreajuste</b> —Random Forest alcanza 0,920 en entrenamiento
contra {V['r2_rf']} en prueba, una brecha de {V['brecha_rf']}, mientras el <i>boosting</i> mantiene
0,0079—; <b>costo computacional</b> —{V['veces_mas_rapido']} veces más rápido, lo que resulta
determinante para la búsqueda de hiperparámetros y el reentrenamiento periódico—; y <b>margen de
mejora</b>, ya que al ajustar sus hiperparámetros supera a Random Forest y alcanza un R² de
{V['r2']} en prueba. El criterio aplicado es que el mejor modelo no es el que obtiene la mejor
métrica en una única corrida sin ajustar, sino el que equilibra exactitud, generalización y
viabilidad operacional.</p>

<p><b>Validación cruzada e hiperparámetros.</b> Con <i>K-Fold</i> de 5 particiones sobre el conjunto
de entrenamiento, el modelo seleccionado obtuvo <b>R² = {V['cv_r2']} ± {V['cv_sd']}</b>: una
desviación estándar de milésimas indica que el desempeño no depende de la partición particular de los
datos. El ajuste con <i>GridSearchCV</i> (validación cruzada de 3 particiones, 24 entrenamientos
sobre una grilla de tasa de aprendizaje, complejidad del árbol y regularización) elevó el R² de
validación a {V['cv_r2_ajustado']} y seleccionó <b>{V['hiperparametros']}</b>. El modelo definitivo se
encapsuló en un <i>Pipeline</i> completo —preprocesamiento más estimador— de modo que recibe los
datos crudos de un viaje y devuelve la duración estimada. El cuaderno completo se ejecuta en
{V['tiempo_total']} minutos.</p>

<h2>6. Evaluación del modelo</h2>

<table class="kpi">
<tr>
  <td><span class="valor">{V['mae']}</span><br/><span class="etiqueta">MAE (minutos)</span></td>
  <td><span class="valor">{V['rmse']}</span><br/><span class="etiqueta">RMSE (minutos)</span></td>
  <td><span class="valor">{V['r2']}</span><br/><span class="etiqueta">R² en prueba</span></td>
  <td><span class="valor">{V['mse']}</span><br/><span class="etiqueta">MSE (min²)</span></td>
  <td><span class="valor">{V['dentro_3min']}</span><br/><span class="etiqueta">error ≤ 3 minutos</span></td>
</tr>
</table>

<p>El modelo explica el <b>{V['r2_pct']} de la variabilidad</b> de la duración de los viajes, con un
error medio de <b>{V['mae']} minutos</b> sobre una duración promedio de {V['duracion_promedio']}
minutos ({V['error_relativo']} en términos relativos) y un MAPE de {V['mape']}. Frente a la práctica
de estimar con el promedio histórico, <b>el error se reduce en {V['mejora_base']}</b>. Alrededor de
{V['dentro_3min']} de las predicciones se equivoca en 3 minutos o menos y {V['dentro_5min']} en 5
minutos o menos, precisión suficiente para programar servicios y comunicar tiempos al cliente. El
RMSE ({V['rmse']} min) supera al MAE ({V['mae']} min) porque penaliza los errores grandes: existe un
grupo minoritario de viajes con desvíos importantes. La brecha de R² entre entrenamiento y prueba es
de {V['brecha']}, lo que confirma que el modelo <b>generaliza correctamente</b>.</p>

{figura("eval_observado_predicho", "Figura 4. Duración observada frente a predicha en el conjunto de prueba: los puntos se agrupan en torno a la recta de predicción perfecta, con dispersión creciente en los viajes largos.", ancho=0.82)}

{figura("eval_residuos_histograma", "Figura 5. Los residuos se distribuyen en torno a cero de forma aproximadamente simétrica (residuo promedio " + str(V['residuo_promedio']) + " min): el modelo no tiende a subestimar ni a sobreestimar sistemáticamente.", ancho=0.82)}

<p><b>Análisis por segmento.</b> El error global puede ocultar comportamientos distintos entre
segmentos, información necesaria para saber en qué condiciones el modelo es confiable. El error es
menor de madrugada y mayor en las horas de máxima congestión; crece con la distancia en términos
absolutos, pero el <b>error relativo disminuye</b>: en viajes largos el modelo se equivoca en más
minutos, aunque en menor proporción del tiempo total. El gráfico de residuos frente a predicciones
muestra un abanico creciente (heterocedasticidad): los viajes largos son intrínsecamente menos
predecibles y así debe comunicarse el resultado.</p>

{tabla(["Rango de distancia", "Viajes", "MAE (min)", "Duración promedio (min)", "Error relativo"],
       V["tabla_segmentos"], anchos=["22%", "18%", "18%", "24%", "18%"])}

<h2>7. Interpretación del modelo y conclusiones</h2>

<p><b>Variables más importantes.</b> Se utilizó importancia por permutación —medida sobre datos no
vistos y respecto del modelo ya entrenado— por ser más confiable que las importancias internas del
algoritmo. La <b>distancia</b> es el determinante absolutamente dominante: permutarla hace caer el R²
en {V['importancia_distancia']} puntos, un orden de magnitud por sobre cualquier otra variable. Le
sigue, en segundo lugar, la <b>hora de inicio</b> ({V['importancia_hora']}), pese a que su
correlación lineal con la duración es de apenas {V['corr_hora']}: es la confirmación cuantitativa de
que su efecto es no lineal e interactivo, y explica por qué la selección univariada de variables
perjudicó el desempeño. Completan el <i>ranking</i> el <b>día de la semana</b>
({V['importancia_dia']}) y las <b>zonas de origen y destino</b> ({V['importancia_zonas']}), que
capturan la geografía real de la congestión.</p>

<p>Los indicadores geográficos derivados (tipo de zona, comuna, coincidencia de comuna, paso por
aeropuerto) y las variables administrativas cierran la lista. En el primer caso no por irrelevancia
—su correlación con la duración es alta— sino por <b>redundancia</b>: su información ya está contenida
en la codificación de las zonas, y la importancia por permutación mide aporte marginal dado el resto
del modelo. En el segundo, el resultado era esperable: describen el registro del viaje, no su
naturaleza física. <b>Lectura de negocio:</b> después de la distancia, lo que más determina el tiempo
de un viaje es <i>cuándo</i> se realiza, no dónde.</p>

{figura("interpretacion_importancia", "Figura 6. Importancia por permutación: caída del R² al permutar aleatoriamente cada variable en el conjunto de prueba.", ancho=0.88)}

<h3>Fortalezas</h3>
<ul>
<li><b>Desempeño validado:</b> R² de {V['r2']} con validación cruzada de 5 particiones y desviación
estándar de milésimas; el resultado no depende de la partición de los datos.</li>
<li><b>Sin fuga de información:</b> usa solo variables conocidas al iniciar el viaje, por lo que el
desempeño medido es el esperable en producción.</li>
<li><b>Error interpretable:</b> se expresa en minutos, lo que permite negociar niveles de servicio.</li>
<li><b>Eficiencia y escala:</b> entrena en segundos sobre cientos de miles de registros; el diseño se
probó sobre casi tres millones de viajes con muestreo justificado y verificado.</li>
<li><b>Robustez operacional:</b> el <i>Pipeline</i> incorpora el preprocesamiento y tolera categorías
no vistas, evitando fallas ante datos nuevos.</li>
</ul>

<h3>Limitaciones</h3>
<ul>
<li><b>Sin variables de contexto:</b> no incorpora clima, accidentes, cortes de calles, eventos
masivos ni estado del tráfico en tiempo real, que son determinantes reales del tiempo de viaje.</li>
<li><b>Ventana temporal acotada:</b> un solo mes (enero de 2024), por lo que no captura
estacionalidad anual.</li>
<li><b>Heterocedasticidad:</b> el error crece con la duración estimada; los viajes largos son menos
predecibles.</li>
<li><b>Granularidad geográfica:</b> trabaja con zonas administrativas, no con rutas ni coordenadas;
dos viajes entre las mismas zonas pueden seguir trayectos distintos.</li>
<li><b>Transferibilidad:</b> está entrenado con datos de Nueva York; aplicarlo a otra ciudad exige
reentrenamiento con datos locales, aunque la metodología es directamente replicable.</li>
</ul>

<h3>Posibles mejoras</h3>
<ul>
<li>Enriquecer con <b>datos externos</b>: clima por hora, calendario de feriados y eventos, e
indicadores de tráfico. Es la mejora con mayor potencial esperado.</li>
<li>Ampliar la ventana a <b>doce meses</b> para capturar estacionalidad y evaluar la deriva del
modelo.</li>
<li><b>Modelos especializados por segmento</b> (viajes urbanos versus aeropuerto), cuyos
comportamientos son estructuralmente distintos.</li>
<li>Evaluar <b>XGBoost o LightGBM</b> y optimización bayesiana de hiperparámetros.</li>
<li><b>Predicción por intervalos</b> mediante regresión por cuantiles, para entregar un rango
("entre 12 y 18 minutos") que refleje la incertidumbre real.</li>
<li>Prácticas de <b>MLOps</b>: monitoreo de deriva, reentrenamiento programado y versionado del
modelo.</li>
</ul>

<h3>Aplicaciones prácticas</h3>
<ul>
<li><b>Estimación de tiempo de llegada (ETA)</b> informada al pasajero al solicitar el servicio.</li>
<li><b>Programación de turnos y dimensionamiento de flota</b> por franja horaria y zona.</li>
<li><b>Cotización de traslados</b>, convirtiendo duración estimada en costo esperado.</li>
<li><b>Control de gestión</b>: comparar duración real versus estimada para detectar desvíos.</li>
<li><b>Simulación de escenarios</b>: cuantificar el impacto de mover un servicio de las 18:00 a las
20:00.</li>
<li><b>Acuerdos de nivel de servicio</b> basados en la distribución real del error.</li>
</ul>

<h3>Conclusiones</h3>
<ul>
<li><b>Es posible predecir la duración de un viaje urbano con precisión operacionalmente útil</b>
usando solo información previa al servicio: R² de {V['r2']} y error medio de {V['mae']} minutos.</li>
<li><b>La preparación de datos determinó el resultado:</b> la correlación entre distancia y duración
pasó de {V['corr_sucia']} a {V['corr_limpia']} tras depurar registros inconsistentes. Sin ese trabajo
previo, el análisis habría descartado la variable más predictiva.</li>
<li><b>Reducir dimensionalidad no siempre mejora un modelo:</b> PCA comprimió
{V['n_caracteristicas']} características en {V['n_componentes']} componentes conservando el
{V['varianza_pca']} de la varianza, pero el R² cayó a {V['r2_pca']}, porque la varianza no equivale a
información sobre el objetivo. La selección univariada por información mutua fue peor
({V['r2_mi']}): los filtros marginales son riesgosos cuando el fenómeno es interactivo, como ocurre
en movilidad urbana.</li>
<li><b>El tiempo de viaje no depende solo de la distancia:</b> la hora de inicio es la segunda
variable más importante del modelo aun teniendo correlación lineal casi nula con el objetivo. La
duración promedio varía cerca de 40 % entre la hora más rápida y la más lenta del día con distancias
equivalentes: exactamente lo que una estimación por promedios no captura.</li>
<li><b>La disciplina metodológica es lo que hace utilizable al modelo:</b> excluir las variables
monetarias —tentadoras por su alta correlación con el objetivo— fue indispensable para que el
desempeño medido sea el desempeño real.</li>
<li><b>Aporte de negocio:</b> el error se reduce {V['mejora_base']} respecto del promedio histórico,
lo que se traduce en programación más ajustada, mejores compromisos de tiempo y menor holgura
improductiva.</li>
</ul>

<h2>Anexo · Fuentes y entregables</h2>

<p class="nota"><b>Enlace oficial del dataset:</b>
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page<br/>
<b>Archivo utilizado:</b>
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet<br/>
<b>Tabla de zonas:</b> https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv<br/>
<b>Diccionario oficial:</b>
https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf<br/>
<b>Entregables:</b> <i>Luna_Valeria_EvaluacionFinal.ipynb</i> (cuaderno ejecutado),
<i>Luna_Valeria_Informe.pdf</i> (este informe),
<i>Luna_Valeria_modelo_duracion_viaje.joblib</i> (Pipeline entrenado) y
<i>Luna_Valeria_modelo_metadatos.json</i> (trazabilidad de versiones, variables y métricas).<br/>
<b>Entorno:</b> Python, scikit-learn {V['version_sklearn']}, pandas {V['version_pandas']};
semilla fija 42 en todos los procesos aleatorios.<br/>
<b>Uso de Inteligencia Artificial:</b> se utilizaron herramientas de IA como apoyo para la escritura
y revisión del código, conforme lo autoriza la evaluación. Las decisiones metodológicas —selección
del problema y del dataset, criterios de depuración, exclusión de variables por fuga de información,
técnicas de reducción de dimensionalidad, elección del algoritmo e interpretación de resultados— son
propias y pueden ser explicadas y justificadas íntegramente.</p>
"""

documento = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{HTML}</body></html>"
ruta_html = BASE / "Luna_Valeria_Informe.html"
ruta_html.write_text(documento, encoding="utf-8")
print("HTML generado:", ruta_html)

from xhtml2pdf import pisa
ruta_pdf = BASE / "Luna_Valeria_Informe.pdf"
with open(ruta_pdf, "wb") as salida:
    estado = pisa.CreatePDF(documento, dest=salida, encoding="utf-8", path=str(BASE / "x.html"))
print("PDF generado:", ruta_pdf, "| errores:", estado.err)
