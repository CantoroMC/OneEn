"""
Dashboard PUN MGP — prezzi al quarto d'ora.

Avvio:
    streamlit run dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

from data import fetch_pun, daily_stats
from gme import GmeApiError

# ---------------------------------------------------------------------------
# Configurazione pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PUN Dashboard",
    layout="wide",
)

st.title("PUN MGP — Prezzi al quarto d'ora")
st.caption("Dati: Gestore Mercati Energetici — ME_ZonalPrices / MGP / PT15")

# ---------------------------------------------------------------------------
# Sidebar — selezione periodo
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Periodo")

    today         = date.today()
    default_start = today - timedelta(days=29)

    start = st.date_input("Data inizio", value=default_start, max_value=today)
    end   = st.date_input("Data fine",   value=today,         max_value=today)

    if end < start:
        st.error("La data fine deve essere successiva alla data inizio.")
        st.stop()

    n_giorni = (end - start).days + 1
    st.caption(f"Periodo: {n_giorni} giorn{'o' if n_giorni == 1 else 'i'}")

    st.divider()
    st.caption(
        "I dati vengono cachati per 1 ora. "
        "Per forzare il refresh usa il menu in alto a destra."
    )

# ---------------------------------------------------------------------------
# Fetch dati
# ---------------------------------------------------------------------------
try:
    df = fetch_pun(start, end)
except GmeApiError as e:
    st.error(f"Errore API GME: {e}")
    st.stop()

if df.empty:
    st.warning("Nessun dato disponibile per il periodo selezionato.")
    st.stop()

# ---------------------------------------------------------------------------
# Metriche riepilogative
# ---------------------------------------------------------------------------
pun = df["PUN_EUR_MWh"]

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Media",          f"{pun.mean():.2f} €/MWh")
col2.metric("Minimo",         f"{pun.min():.2f} €/MWh")
col3.metric("Massimo",        f"{pun.max():.2f} €/MWh")
col4.metric("Dev. standard",  f"{pun.std():.2f} €/MWh")
col5.metric("Quart. d'ora",   f"{len(df):,}")

st.divider()

# ---------------------------------------------------------------------------
# Grafico 15 minuti
# ---------------------------------------------------------------------------
fig_15 = go.Figure()
fig_15.add_trace(go.Scatter(
    x=df["Timestamp"],
    y=df["PUN_EUR_MWh"],
    mode="lines",
    name="PUN 15min",
    line=dict(color="#1f77b4", width=1),
    hovertemplate="%{x|%d/%m/%Y %H:%M}<br><b>%{y:.2f} €/MWh</b><extra></extra>",
))
fig_15.update_layout(
    title="Prezzo PUN — granularita 15 minuti",
    yaxis_title="EUR/MWh",
    xaxis_title=None,
    hovermode="x unified",
    height=420,
    margin=dict(t=50, b=10, l=60, r=20),
)
fig_15.update_xaxes(
    rangeselector=dict(
        buttons=[
            dict(count=1,  label="1g",  step="day",   stepmode="backward"),
            dict(count=7,  label="7g",  step="day",   stepmode="backward"),
            dict(count=1,  label="1m",  step="month", stepmode="backward"),
            dict(step="all", label="Tutto"),
        ]
    ),
    rangeslider=dict(visible=True, thickness=0.06),
)
st.plotly_chart(fig_15, use_container_width=True)

# ---------------------------------------------------------------------------
# Media giornaliera
# ---------------------------------------------------------------------------
df_daily = daily_stats(df)

fig_daily = go.Figure()
fig_daily.add_trace(go.Bar(
    x=df_daily["Data"],
    y=df_daily["Media"],
    name="Media",
    marker_color="#1f77b4",
    hovertemplate="%{x|%d/%m/%Y}<br>Media: <b>%{y:.2f} €/MWh</b><extra></extra>",
))
fig_daily.add_trace(go.Scatter(
    x=df_daily["Data"],
    y=df_daily["Massimo"],
    mode="lines",
    name="Massimo",
    line=dict(color="#d62728", width=1, dash="dot"),
    hovertemplate="%{x|%d/%m/%Y}<br>Max: %{y:.2f} €/MWh<extra></extra>",
))
fig_daily.add_trace(go.Scatter(
    x=df_daily["Data"],
    y=df_daily["Minimo"],
    mode="lines",
    name="Minimo",
    line=dict(color="#2ca02c", width=1, dash="dot"),
    hovertemplate="%{x|%d/%m/%Y}<br>Min: %{y:.2f} €/MWh<extra></extra>",
))
fig_daily.update_layout(
    title="Media giornaliera PUN (con range min/max)",
    yaxis_title="EUR/MWh",
    xaxis_title=None,
    height=320,
    margin=dict(t=50, b=10, l=60, r=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_daily, use_container_width=True)

# ---------------------------------------------------------------------------
# Distribuzione (sezione espandibile)
# ---------------------------------------------------------------------------
with st.expander("Distribuzione prezzi"):
    col_a, col_b = st.columns([2, 1])

    with col_a:
        fig_hist = px.histogram(
            df, x="PUN_EUR_MWh",
            nbins=60,
            title="Distribuzione PUN (EUR/MWh)",
            labels={"PUN_EUR_MWh": "EUR/MWh"},
            color_discrete_sequence=["#1f77b4"],
        )
        fig_hist.update_layout(
            height=300,
            margin=dict(t=50, b=10),
            yaxis_title="Conteggio quarti d'ora",
            showlegend=False,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        percentili = pun.quantile([0.05, 0.25, 0.50, 0.75, 0.95]).rename("EUR/MWh").to_frame()
        percentili.index = ["P5", "P25", "P50", "P75", "P95"]
        percentili["EUR/MWh"] = percentili["EUR/MWh"].map("{:.2f}".format)
        st.markdown("**Percentili**")
        st.dataframe(percentili, use_container_width=True)
