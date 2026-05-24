"""
Cache file-based per i dati GME.

Struttura su disco:
    cache/{DataName}_{Segment}_{attrs_tag}/{YYYYMMDD}.json

Ogni file contiene la lista grezza di record restituita dall'API (tutte le zone).
Il filtro per zona viene applicato al momento dell'uso, non qui.

Nota: i dati del giorno corrente non vengono mai cachati (potrebbero essere preliminari).
"""

import json
import tempfile
from datetime import date
from pathlib import Path


class GmeCache:
    def __init__(self, cache_dir: Path | None = None):
        self._root = cache_dir or Path(__file__).parent.parent / "cache"

    def get(
        self,
        data_name: str,
        segment: str,
        attributes: dict | None,
        target_date: date,
    ) -> list[dict] | None:
        """Ritorna i record dalla cache, o None se non presenti o file corrotto."""
        path = self._path(data_name, segment, attributes, target_date)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # File corrotto (scrittura interrotta): trattato come cache miss
            path.unlink(missing_ok=True)
            return None

    def set(
        self,
        data_name: str,
        segment: str,
        attributes: dict | None,
        target_date: date,
        records: list[dict],
    ) -> None:
        """Salva i record su disco in modo atomico."""
        path = self._path(data_name, segment, attributes, target_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Scrittura atomica: scrive su tmp poi rinomina
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump(records, tmp)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)

    def is_cacheable(self, target_date: date) -> bool:
        """Tutti i dati vengono cachati, inclusi oggi e domani.
        Per forzare un aggiornamento elimina il file corrispondente in cache/."""
        return True

    def _path(
        self,
        data_name: str,
        segment: str,
        attributes: dict | None,
        target_date: date,
    ) -> Path:
        attrs_tag = "_".join(str(v) for _, v in sorted((attributes or {}).items()))
        folder = "_".join(filter(None, [data_name, segment, attrs_tag]))
        return self._root / folder / f"{target_date:%Y%m%d}.json"
