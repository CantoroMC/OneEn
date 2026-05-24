"""
Interfaccia utente interattiva per i dati GME.

Fornisce prompt questionary riusabili da qualsiasi script del progetto,
eliminando la necessità di argparse quando si lavora in modalità interattiva.

Logica data di default:
    Il MGP (Mercato del Giorno Prima) pubblica i risultati per D+1 intorno alle 12:55.
    Dopo le 14:00 il dato di domani è disponibile → default = domani.
    Prima delle 14:00 il dato di oggi è l'ultimo disponibile → default = oggi.
"""

import sys
from datetime import date, datetime, timedelta

import questionary
from questionary import Style

from .catalog import GmeCatalog

_STYLE = Style([
    ("qmark",       "fg:#00aa00 bold"),
    ("question",    "bold"),
    ("answer",      "fg:#00aaaa bold"),
    ("pointer",     "fg:#00aa00 bold"),
    ("highlighted", "fg:#00aa00 bold"),
    ("selected",    "fg:#00aaaa"),
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
            - dopo le 14:00 → domani (D+1, risultati pubblicati ~12:55)
            - prima delle 14:00 → oggi (D)
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
        Guida l'utente nella scelta dell'intervallo con tre modalità.
        Il default è la data singola calcolata da smart_default_date().
        """
        default_date = GmeUi.smart_default_date()
        default_label = f"Data singola  (default: {default_date:%d/%m/%Y})"

        mode = questionary.select(
            "Intervallo di date:",
            choices=[
                default_label,
                "Data inizio + data fine",
                "Data inizio + durata",
                "Data fine   + durata",
            ],
            default=default_label,
            style=_STYLE,
        ).ask()
        if mode is None:
            sys.exit(0)

        if mode == default_label:
            return default_date, default_date

        if mode == "Data inizio + data fine":
            s = GmeUi._ask_date("Data inizio")
            e = GmeUi._ask_date("Data fine  ")
            return s, e

        if mode == "Data inizio + durata":
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
