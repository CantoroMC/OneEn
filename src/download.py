"""
Download interattivo di qualsiasi dataset GME.

Guida l'utente attraverso la selezione di categoria, dataset, segment,
attributi e intervallo di date tramite menu questionary con fuzzy search.

Utilizzo:
    python download.py
"""

import sys
from pathlib import Path

import pandas as pd

from gme import GmeApiError, GmeCache, GmeClient, GmeCatalog, GmeUi


def _download_day(
    client: GmeClient,
    cache: GmeCache,
    data_name: str,
    segment: str,
    attributes: dict,
    target_date,
) -> list[dict]:
    records = cache.get(data_name, segment, attributes, target_date)
    if records is not None:
        print(f"  [cache] {target_date:%d/%m/%Y} — {len(records)} record")
        return records

    records = client.request_data(
        platform="PublicMarketResults",
        segment=segment,
        data_name=data_name,
        interval_start=target_date,
        interval_end=target_date,
        attributes=attributes,
    )
    cache.set(data_name, segment, attributes, target_date, records)
    print(f"  [api]   {target_date:%d/%m/%Y} — {len(records)} record (salvati in cache)")
    return records


def main() -> None:
    from datetime import timedelta

    print("\n  Download dati GME\n")

    category   = GmeUi.ask_category()
    data_name  = GmeUi.ask_dataset(category)
    segment    = GmeUi.ask_segment(data_name)
    attributes = GmeUi.ask_attributes(data_name, segment)
    start, end = GmeUi.ask_date_range()

    if GmeCatalog.is_xml(data_name):
        print(
            "\n  Attenzione: questo dataset restituisce file XML, non JSON.\n"
            "  Il download non e' supportato in formato CSV da questo script.",
            file=sys.stderr,
        )
        sys.exit(1)

    giorni = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    print(f"\n  Periodo: {start:%d/%m/%Y} -> {end:%d/%m/%Y} ({len(giorni)} giorni)\n")

    client = GmeClient()
    cache  = GmeCache()

    try:
        all_records = []
        for d in giorni:
            all_records.extend(_download_day(client, cache, data_name, segment, attributes, d))
    except GmeApiError as e:
        print(f"\n  Errore: {e}", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(all_records)
    print(f"\n  Record totali: {len(df)}")
    print(df.head(5).to_string(index=False))

    attrs_tag = "_".join(f"{k}{v}" for k, v in sorted(attributes.items()))
    out_name  = "_".join(filter(None, [
        data_name, segment, attrs_tag,
        f"{start:%Y%m%d}", f"{end:%Y%m%d}",
    ])) + ".csv"
    out_path = Path(__file__).parent / out_name
    df.to_csv(out_path, index=False, sep=";", decimal=".")
    print(f"\n  Salvato in: {out_path}")


if __name__ == "__main__":
    main()
