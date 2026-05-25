"""
Genera data/pun.json con dati PUN MGP 15min per un periodo scelto via UI.

Utilizzo:
    python dashboard/build_pun.py

Output: dashboard/data/pun.json  (sovrascritto ad ogni esecuzione)

Struttura del JSON:
    meta        → periodo, data di generazione
    timeseries  → serie 15min  [{t, v}, ...]
    stats       → statistiche globali del periodo
    daily       → aggregazioni giornaliere [{date, mean, min, max, spread}, ...]
"""

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from gme import GmeApiError, GmeClient, GmeUi

# ---------------------------------------------------------------------------
# Costanti dataset
# ---------------------------------------------------------------------------
_PLATFORM   = "PublicMarketResults"
_SEGMENT    = "MGP"
_DATA_NAME  = "ME_ZonalPrices"
_ATTRIBUTES = {"GranularityType": "PT15"}

OUTPUT = Path(__file__).parent.parent / "docs" / "data" / "pun.json"


# ---------------------------------------------------------------------------
# Fetch e trasformazione
# ---------------------------------------------------------------------------
def fetch_pun(start: date, end: date) -> pd.DataFrame:
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


def build_json(df: pd.DataFrame, start: date, end: date) -> dict:
    pun = df["PUN_EUR_MWh"]

    # Serie 15min — formato [timestamp_iso, valore]
    timeseries = [
        [row["Timestamp"].isoformat(), round(row["PUN_EUR_MWh"], 4)]
        for _, row in df.iterrows()
    ]

    # Statistiche globali
    stats = {
        "mean": round(pun.mean(), 4),
        "min":  round(pun.min(),  4),
        "max":  round(pun.max(),  4),
        "std":  round(pun.std(),  4),
        "p25":  round(pun.quantile(0.25), 4),
        "p50":  round(pun.quantile(0.50), 4),
        "p75":  round(pun.quantile(0.75), 4),
    }

    # Aggregazioni giornaliere
    daily_df = (
        df.set_index("Timestamp")["PUN_EUR_MWh"]
        .resample("D")
        .agg(mean="mean", min="min", max="max")
        .dropna()
        .reset_index()
    )
    daily_df["spread"] = (daily_df["max"] - daily_df["min"]).round(4)

    daily = [
        {
            "date":   row["Timestamp"].strftime("%Y-%m-%d"),
            "mean":   round(row["mean"],   4),
            "min":    round(row["min"],    4),
            "max":    round(row["max"],    4),
            "spread": row["spread"],
        }
        for _, row in daily_df.iterrows()
    ]

    return {
        "meta": {
            "start":        start.isoformat(),
            "end":          end.isoformat(),
            "n_points":     len(df),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "timeseries": timeseries,
        "stats":      stats,
        "daily":      daily,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("\n  Build PUN JSON\n")
    start, end = GmeUi.ask_date_range()
    print(f"\n  Periodo: {start:%d/%m/%Y} → {end:%d/%m/%Y}")
    print("  Download in corso...\n")

    try:
        df = fetch_pun(start, end)
    except GmeApiError as e:
        print(f"  Errore: {e}")
        return

    data = build_json(df, start, end)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  Punti 15min : {data['meta']['n_points']}")
    print(f"  Media PUN   : {data['stats']['mean']:.2f} EUR/MWh")
    print(f"  Giorni       : {len(data['daily'])}")
    print(f"\n  Salvato in  : {OUTPUT}")
    print("\n  Avvia il server con:")
    print("    python -m http.server 8000 --directory docs")
    print("  poi apri  http://localhost:8000\n")


if __name__ == "__main__":
    main()
