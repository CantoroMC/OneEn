"""
Fetch e trasformazione dati PUN MGP 15min dall'API GME.

Espone fetch_pun() con cache Streamlit (TTL 1h) per evitare
chiamate ripetute all'API durante l'esplorazione interattiva.
"""

import pandas as pd
import streamlit as st
from datetime import date

from gme import GmeClient, GmeApiError

_PLATFORM   = "PublicMarketResults"
_SEGMENT    = "MGP"
_DATA_NAME  = "ME_ZonalPrices"
_ATTRIBUTES = {"GranularityType": "PT15"}


@st.cache_data(ttl=3600, show_spinner="Scaricamento dati GME...")
def fetch_pun(start: date, end: date) -> pd.DataFrame:
    """
    Scarica prezzi PUN MGP al quarto d'ora per l'intervallo indicato.

    Ritorna DataFrame con:
        Timestamp    datetime64  inizio del quarto d'ora
        PUN_EUR_MWh  float64     prezzo in EUR/MWh
    """
    client = GmeClient()
    records = client.request_data(
        platform=_PLATFORM,
        segment=_SEGMENT,
        data_name=_DATA_NAME,
        interval_start=start,
        interval_end=end,
        attributes=_ATTRIBUTES,
    )

    df = pd.DataFrame(records)
    pun = df[df["Zone"] == "PUN"].copy()

    if pun.empty:
        raise GmeApiError(f"Nessun dato PUN per {start:%d/%m/%Y}–{end:%d/%m/%Y}")

    pun["FlowDate"]  = pd.to_datetime(pun["FlowDate"].astype(str), format="%Y%m%d")
    pun["Price"]     = pun["Price"].astype(float)
    pun["Timestamp"] = pun["FlowDate"] + pd.to_timedelta(
        (pun["Period"].astype(int) - 1) * 15, unit="min"
    )
    return (
        pun[["Timestamp", "Price"]]
        .sort_values("Timestamp")
        .reset_index(drop=True)
        .rename(columns={"Price": "PUN_EUR_MWh"})
    )


def daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Media, minimo e massimo giornaliero del PUN."""
    return (
        df.set_index("Timestamp")["PUN_EUR_MWh"]
        .resample("D")
        .agg(Media="mean", Minimo="min", Massimo="max")
        .reset_index()
        .rename(columns={"Timestamp": "Data"})
    )
