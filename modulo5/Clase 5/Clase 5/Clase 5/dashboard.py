# dashboard.py - Tu mini-Kibana
import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(
    page_title='Mi observatorio ETL',
    layout='wide'
)

@st.cache_data
def cargar_logs(archivo):
    """Lee un archivo JSONL (un JSON por linea) y devuelve un DataFrame."""
    datos = []
    with open(archivo, 'r', encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                datos.append(json.loads(linea))
    df = pd.DataFrame(datos)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format="ISO8601" )
    return df


df = cargar_logs('logs_demo.jsonl')

st.title('Mi observatorio ETL')
st.caption(f'Total eventos cargados: {len(df)}')

st.sidebar.header('Filtros')
etapas = ['Todas'] + sorted(df['etapa'].dropna().unique().tolist())
etapa_sel = st.sidebar.selectbox('Etapa:', etapas)
 
statuses = ['Todos'] + sorted(df['status'].dropna().unique().tolist())
status_sel = st.sidebar.selectbox('Status:', statuses)

df_filt = df.copy()
if etapa_sel != 'Todas':
    df_filt = df_filt[df_filt['etapa'] == etapa_sel]
if status_sel != 'Todos':
    df_filt = df_filt[df_filt['status'] == status_sel]

st.sidebar.markdown(f'**Mostrando: {len(df_filt)} eventos**')


col1, col2, col3, col4 = st.columns(4)

with col1:
    n = len(df_filt)
    st.metric('Total eventos', f'{n}')

with col2:
    errores = (df_filt.get('status', pd.Series()) == 'ERROR').sum()
    pct = (errores / n * 100) if n > 0 else 0
    st.metric('Errores', f'{errores}', f'{pct:.1f}%', delta_color='inverse')

with col3:
    if 'duracion_ms' in df_filt.columns:
        prom = df_filt['duracion_ms'].mean()
        st.metric('Duracion promedio', f'{prom:.0f} ms')
    else:
        st.metric('Duracion promedio', 'N/A')

with col4:
    runs = df_filt['run_id'].nunique() if 'run_id' in df_filt.columns else 0
    st.metric('Corridas unicas', f'{runs}')

st.subheader('Duracion a traves del tiempo')

if 'duracion_ms' in df_filt.columns and len(df_filt) > 0:
    df_plot = df_filt.dropna(subset=['duracion_ms', 'timestamp']).copy()
    df_plot = df_plot.sort_values('timestamp')
    fig = px.line(
        df_plot,
        x='timestamp',
        y='duracion_ms',
        color='etapa' if 'etapa' in df_plot.columns else None,
        title='Duracion por etapa',
        labels={'duracion_ms': 'Duracion (ms)', 'timestamp': 'Tiempo'}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('No hay datos suficientes para graficar')


st.subheader('Ultimos 20 eventos')
 
if 'timestamp' in df_filt.columns:
    df_show = df_filt.sort_values('timestamp', ascending=False).head(20)
else:
    df_show = df_filt.head(20)
 
st.dataframe(df_show, use_container_width=True)
