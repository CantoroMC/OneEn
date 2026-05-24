"""
Download PUN MGP al quarto d'ora per un intervallo di date.

Dataset: ME_ZonalPrices | Segment: MGP | GranularityType: PT15
Disponibile dal 1° ottobre 2025.

Utilizzo da riga di comando:
    python pun_mgp_15min.py                                  -> interattivo
    python pun_mgp_15min.py --start 01/05/2026 --end 20/05/2026
    python pun_mgp_15min.py --start 01/05/2026 --duration 30g
    python pun_mgp_15min.py --end 20/05/2026 --duration 4s

Formato date: GG/MM/YYYY
Formato durata: Ng (N giorni) oppure Ns (N settimane)
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from gme import GmeApiError, GmeCache, GmeClient, GmeUi

_PLATFORM   = "PublicMarketResults"
_SEGMENT    = "MGP"
_DATA_NAME  = "ME_ZonalPrices"
_ATTRIBUTES = {"GranularityType": "PT15"}


def _get_pun(target_date: date) -> pd.DataFrame:
    cache = GmeCache()
    records = cache.get(_DATA_NAME, _SEGMENT, _ATTRIBUTES, target_date)

    if records is not None:
        print(f"[cache] {target_date:%d/%m/%Y} — {len(records)} record da disco")
    else:
        client = GmeClient()
        records = client.request_data(
            platform=_PLATFORM,
            segment=_SEGMENT,
            data_name=_DATA_NAME,
            interval_start=target_date,
            interval_end=target_date,
            attributes=_ATTRIBUTES,
        )
        cache.set(_DATA_NAME, _SEGMENT, _ATTRIBUTES, target_date, records)
        print(f"[api]   {target_date:%d/%m/%Y} — {len(records)} record scaricati e salvati in cache")

    df = pd.DataFrame(records)
    pun = df[df["Zone"] == "PUN"].copy()

    if pun.empty:
        raise GmeApiError(f"Nessun dato PUN trovato per il {target_date:%d/%m/%Y}")

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


def download_pun(start: date, end: date) -> pd.DataFrame:
    if end < start:
        raise ValueError(f"Data fine ({end:%d/%m/%Y}) precedente a data inizio ({start:%d/%m/%Y})")
    giorni = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    return pd.concat([_get_pun(d) for d in giorni], ignore_index=True)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Download PUN MGP al quarto d'ora. Date in formato GG/MM/YYYY, durata in Ng o Ns.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--start",    metavar="GG/MM/YYYY", help="Data inizio")
    p.add_argument("--end",      metavar="GG/MM/YYYY", help="Data fine")
    p.add_argument("--duration", metavar="Ng|Ns",      help="Durata (es. 30g, 4s)")
    return p


def _resolve_range(args: argparse.Namespace) -> tuple[date, date]:
    has_start = args.start is not None
    has_end   = args.end is not None
    has_dur   = args.duration is not None

    # Nessun flag passato: modalità interattiva tramite GmeUi
    if not any([has_start, has_end, has_dur]):
        return GmeUi.ask_date_range()

    def _d(s):
        v = GmeUi.parse_date(s)
        if v is None:
            print(f"Data non valida: '{s}'. Usa GG/MM/YYYY", file=sys.stderr)
            sys.exit(1)
        return v

    def _dur(s):
        v = GmeUi.parse_duration(s)
        if v is None:
            print(f"Durata non valida: '{s}'. Usa Ng o Ns (es. 30g, 4s)", file=sys.stderr)
            sys.exit(1)
        return v

    if has_start and has_end and not has_dur:
        return _d(args.start), _d(args.end)
    if has_start and has_dur and not has_end:
        s = _d(args.start)
        return s, s + _dur(args.duration) - timedelta(days=1)
    if has_end and has_dur and not has_start:
        e = _d(args.end)
        return e - _dur(args.duration) + timedelta(days=1), e

    print("Combinazione argomenti non valida.", file=sys.stderr)
    print("Usa: --start+--end  oppure  --start+--duration  oppure  --end+--duration", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    args = _build_parser().parse_args()
    try:
        start, end = _resolve_range(args)
        print(f"\nPeriodo: {start:%d/%m/%Y} -> {end:%d/%m/%Y} ({(end - start).days + 1} giorni)\n")

        df_pun = download_pun(start, end)
        print(f"\nQuarti d'ora PUN totali: {len(df_pun)}")
        print(df_pun.head(10).to_string(index=False))

        out_name = f"pun_mgp_15min_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        out_path = Path(__file__).parent / out_name
        df_pun.to_csv(out_path, index=False, sep=";", decimal=".")
        print(f"\nSalvato in: {out_path}")

    except (GmeApiError, ValueError) as e:
        print(f"Errore: {e}", file=sys.stderr)
        sys.exit(1)
