"""
Mostra lo stato delle quote API GME per l'utente corrente.

Chiama GET /api/v1/GetMyQuotas e stampa un report con:
  - Usage corrente vs limiti (connessioni e dati)
  - Percentuale di consumo con barra visiva
  - Ultimo accesso registrato

Utilizzo:
  python show_quotas.py
"""

import sys
from gme import GmeApiError, GmeClient


def _bar(used: int | None, max_val: int | None, width: int = 20) -> str:
    """Barra di avanzamento ASCII."""
    if used is None or max_val is None or max_val == 0:
        return "[" + "-" * width + "]  n/d"
    ratio = min(used / max_val, 1.0)
    filled = int(ratio * width)
    pct = ratio * 100
    bar = "#" * filled + "." * (width - filled)
    return f"[{bar}] {pct:5.1f}%  ({used} / {max_val})"


def _val(data: dict, *keys):
    """Naviga un dizionario annidato in modo sicuro."""
    obj = data
    for k in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    return obj


def show_quotas() -> None:
    client = GmeClient()
    try:
        q = client.get_my_quotas()
    except GmeApiError as e:
        print(f"Errore: {e}", file=sys.stderr)
        sys.exit(1)

    limits = q.get("limits") or q.get("Limits") or {}

    # Normalizza chiavi (API restituisce camelCase o PascalCase)
    def get(key_camel: str, key_pascal: str, source: dict = q):
        return source.get(key_camel) or source.get(key_pascal)

    active_conn   = get("activeConnections",   "ActiveConnections")
    conn_min      = get("connectionsPerMinute", "ConnectionsPerMinute")
    conn_hour     = get("connectionsPerHour",   "ConnectionsPerHour")
    data_min      = get("dataPerMinute",        "DataPerMinute")
    data_hour     = get("dataPerHour",          "DataPerHour")
    last_access   = get("lastModifiedTime",     "LastModifiedTime")

    max_concurrent = get("maxConcurrentConnections",  "MaxConcurrentConnections",  limits)
    max_conn_min   = get("maxConnectionsPerMinute",   "MaxConnectionsPerMinute",   limits)
    max_conn_hour  = get("maxConnectionsPerHour",     "MaxConnectionsPerHour",     limits)
    max_data_min   = get("maxDataPerMinute",          "MaxDataPerMinute",          limits)
    max_data_hour  = get("maxDataPerHour",            "MaxDataPerHour",            limits)

    print("=" * 60)
    print("  QUOTE API GME — stato corrente")
    print("=" * 60)

    if last_access:
        print(f"  Ultimo accesso valido : {last_access}")
    print()

    print("  CONNESSIONI")
    print(f"  Attive ora            : {active_conn or 0} / {max_concurrent or 'n/d'}")
    print(f"  Nell'ultimo minuto    : {_bar(conn_min, max_conn_min)}")
    print(f"  Nell'ultima ora       : {_bar(conn_hour, max_conn_hour)}")
    print()

    print("  DATI SCARICATI  (unita = n_record x n_campi)")
    print(f"  Nell'ultimo minuto    : {_bar(data_min, max_data_min)}")
    print(f"  Nell'ultima ora       : {_bar(data_hour, max_data_hour)}")
    print()

    # Stima quota ora rimanente
    if data_hour is not None and max_data_hour and max_data_hour > 0:
        remaining = max_data_hour - data_hour
        print(f"  Quota dati rimanente (ora)  : {remaining:,} unita")
        # Un giorno PUN-MGP-PT15 = 2208 record x 6 campi = ~13'248 unita
        giorni_stimati = remaining // 13_248
        print(f"  Giorni PUN-MGP scaricabili  : ~{giorni_stimati} (stima su 2208 record x 6 campi)")

    print("=" * 60)


if __name__ == "__main__":
    show_quotas()
