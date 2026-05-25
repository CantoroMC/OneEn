"""
Download interattivo di qualsiasi dataset GME.

Unico entry point per il download dei dati di mercato. Guida l'utente
attraverso categoria, dataset, segment, attributi e intervallo di date
tramite menu questionary con fuzzy search. Nessun argparse.

Utilizzo:
    gme-download          (se installato con pip install -e .)
    python -m gme.download
"""

import sys
import pandas as pd
from pathlib import Path

from gme import GmeApiError, GmeClient, GmeCatalog, GmeUi


def main() -> None:
    print("\n  Download dati GME\n")

    category   = GmeUi.ask_category()
    data_name  = GmeUi.ask_dataset(category)
    segment    = GmeUi.ask_segment(data_name)
    attributes = GmeUi.ask_attributes(data_name, segment)

    if GmeCatalog.is_xml(data_name):
        print(
            "\n  Attenzione: questo dataset restituisce file XML, non JSON.\n"
            "  Il download non e' supportato in formato CSV da questo script.",
            file=sys.stderr,
        )
        sys.exit(1)

    start, end = GmeUi.ask_date_range()
    print(f"\n  Periodo: {start:%d/%m/%Y} -> {end:%d/%m/%Y}\n")

    client = GmeClient()
    try:
        all_records = client.request_data(
            platform="PublicMarketResults",
            segment=segment,
            data_name=data_name,
            interval_start=start,
            interval_end=end,
            attributes=attributes,
        )
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
    out_path = Path.cwd() / out_name
    df.to_csv(out_path, index=False, sep=";", decimal=".")
    print(f"\n  Salvato in: {out_path}")


if __name__ == "__main__":
    main()
