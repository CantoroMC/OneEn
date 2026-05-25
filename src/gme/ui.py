"""
Interfaccia utente interattiva per i dati GME.

Fornisce prompt questionary riusabili da qualsiasi script del progetto,
eliminando la necessità di argparse quando si lavora in modalità interattiva.

Logica data di default:
    Il MGP (Mercato del Giorno Prima) pubblica i risultati per D+1 intorno alle 12:55.
    Dopo le 13:00 il dato di domani è disponibile → default = domani.
    Prima delle 13:00 il dato di oggi è l'ultimo disponibile → default = oggi.
"""

import sys
import questionary
from questionary import Style
from datetime import date, datetime, timedelta

from .catalog import GmeCatalog

_STYLE = Style([
    ("qmark",       "fg:#07962A bold"),
    ("question",    "bold"),
    ("answer",      "fg:#458588 italic"),
    ("pointer",     "fg:#07962A bold"),
    ("highlighted", "fg:#00aa00 bold"),
    ("selected",    "fg:#003E8A"),
])

_MGP_PUBLISH_HOUR = 13  # dopo quest'ora i risultati D+1 sono disponibili


class GmeUi:

    # ------------------------------------------------------------------
    # Data di default
    # ------------------------------------------------------------------

    @staticmethod
    def smart_default_date() -> date:
        """
        Restituisce la data più recente disponibile per il MGP:
            - dopo le 13:00 → domani (D+1, risultati pubblicati ~12:55)
            - prima delle 13:00 → oggi (D)
        """
        if datetime.now().hour >= _MGP_PUBLISH_HOUR:
            return date.today() + timedelta(days=1)
        return date.today()

    # ------------------------------------------------------------------
    # Selezione parametri dataset
    # ------------------------------------------------------------------

    @staticmethod
    def ask_category(default: str = "ME") -> str:
        """Selezione categoria con frecce. Default: ME."""
        choices = [f"{k}  —  {v}" for k, v in GmeCatalog.CATEGORIES.items()]
        default_choice = next((c for c in choices if c.startswith(default)), choices[0])
        scelta = questionary.select(
            "Categoria:",
            choices=choices,
            default=default_choice,
            style=_STYLE,
        ).ask()
        if scelta is None:
            sys.exit(0)
        return scelta.split()[0]

    @staticmethod
    def ask_dataset(category: str, default: str = "ME_ZonalPrices") -> str:
        """Selezione DataName con fuzzy search. Default: ME_ZonalPrices."""
        nomi = GmeCatalog.datasets(category)
        choices = [f"{n}  —  {GmeCatalog.description(n)}" for n in nomi]
        default_choice = next((c for c in choices if c.startswith(default)), choices[0])
        scelta = questionary.autocomplete(
            "Dataset (DataName):",
            choices=choices,
            default=default_choice,
            style=_STYLE,
            match_middle=True,
        ).ask()
        if scelta is None:
            sys.exit(0)
        return scelta.split()[0]

    @staticmethod
    def ask_segment(data_name: str, default: str = "MGP") -> str:
        """Selezione Segment con fuzzy search. Default: MGP se disponibile."""
        segs = GmeCatalog.segments(data_name)
        if len(segs) == 1:
            print(f"  Segment: {segs[0]}  (unica opzione disponibile)")
            return segs[0]
        default_seg = default if default in segs else segs[0]
        scelta = questionary.autocomplete(
            "Segment:",
            choices=segs,
            default=default_seg,
            style=_STYLE,
            match_middle=True,
        ).ask()
        if scelta is None:
            sys.exit(0)
        return scelta.strip()

    @staticmethod
    def ask_attributes(data_name: str, segment: str) -> dict:
        """Selezione attributi opzionali (es. GranularityType). Vuoto se non applicabili."""
        attrs = GmeCatalog.attributes(data_name, segment)
        result = {}
        for key, values in attrs.items():
            scelta = questionary.select(
                f"Attributo {key}:",
                choices=values,
                default=values[0],
                style=_STYLE,
            ).ask()
            if scelta is None:
                sys.exit(0)
            result[key] = scelta
        return result

    # ------------------------------------------------------------------
    # Selezione intervallo di date
    # ------------------------------------------------------------------

    @staticmethod
    def ask_date_range() -> tuple[date, date]:
        """
        Guida l'utente nella scelta dell'intervallo.
        Offre preset rapidi (oggi/ieri/settimana/mese) o selezione manuale.
        """
        default_date  = GmeUi.smart_default_date()
        _PRESET       = "Preset rapido       (oggi / ieri / ultima settimana ...)"
        _SINGOLA      = f"Data singola        (default: {default_date:%d/%m/%Y})"
        _INIZIO_FINE  = "Data inizio + data fine"
        _INIZIO_DUR   = "Data inizio + durata"
        _FINE_DUR     = "Data fine   + durata"

        mode = questionary.select(
            "Intervallo di date:",
            choices=[_PRESET, _SINGOLA, _INIZIO_FINE, _INIZIO_DUR, _FINE_DUR],
            default=_PRESET,
            style=_STYLE,
        ).ask()
        if mode is None:
            sys.exit(0)

        if mode == _PRESET:
            today = date.today()
            presets = {
                f"Oggi               ({today:%d/%m/%Y})":
                    (today, today),
                f"Ieri               ({today - timedelta(days=1):%d/%m/%Y})":
                    (today - timedelta(days=1), today - timedelta(days=1)),
                f"Ultima settimana   ({today - timedelta(days=6):%d/%m/%Y} -> {today:%d/%m/%Y})":
                    (today - timedelta(days=6), today),
                f"Ultimo mese        ({today - timedelta(days=29):%d/%m/%Y} -> {today:%d/%m/%Y})":
                    (today - timedelta(days=29), today),
                f"Ultimi 3 mesi      ({today - timedelta(days=89):%d/%m/%Y} -> {today:%d/%m/%Y})":
                    (today - timedelta(days=89), today),
            }
            scelta = questionary.select(
                "Preset:",
                choices=list(presets.keys()),
                style=_STYLE,
            ).ask()
            if scelta is None:
                sys.exit(0)
            return presets[scelta]

        if mode == _SINGOLA:
            return default_date, default_date

        if mode == _INIZIO_FINE:
            s = GmeUi._ask_date("Data inizio")
            e = GmeUi._ask_date("Data fine  ")
            return s, e

        if mode == _INIZIO_DUR:
            s   = GmeUi._ask_date("Data inizio")
            dur = GmeUi._ask_duration()
            return s, s + dur - timedelta(days=1)

        # Data fine + durata
        e   = GmeUi._ask_date("Data fine  ")
        dur = GmeUi._ask_duration()
        return e - dur + timedelta(days=1), e

    # ------------------------------------------------------------------
    # Parsing e validazione (usabili anche senza prompt interattivi)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_date(s: str) -> date | None:
        """GG/MM/YYYY → date. None se formato non valido."""
        try:
            d, m, y = s.strip().split("/")
            return date(int(y), int(m), int(d))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def parse_duration(s: str) -> timedelta | None:
        """Ng (giorni) o Ns (settimane) → timedelta. None se formato non valido."""
        s = s.strip().lower()
        try:
            if s.endswith("g"):
                return timedelta(days=int(s[:-1]))
            if s.endswith("s"):
                return timedelta(weeks=int(s[:-1]))
        except ValueError:
            pass
        return None

    # ------------------------------------------------------------------
    # Interni
    # ------------------------------------------------------------------

    @staticmethod
    def _ask_date(label: str) -> date:
        s = questionary.text(
            f"{label} (GG/MM/YYYY):",
            validate=lambda v: GmeUi.parse_date(v) is not None or "Usa GG/MM/YYYY (es. 01/05/2026)",
            style=_STYLE,
        ).ask()
        if s is None:
            sys.exit(0)
        return GmeUi.parse_date(s)

    @staticmethod
    def _ask_duration() -> timedelta:
        s = questionary.text(
            "Durata (es. 30g, 4s):",
            validate=lambda v: GmeUi.parse_duration(v) is not None or "Usa Ng o Ns (es. 30g, 4s)",
            style=_STYLE,
        ).ask()
        if s is None:
            sys.exit(0)
        return GmeUi.parse_duration(s)
