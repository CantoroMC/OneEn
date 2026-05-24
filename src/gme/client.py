"""
Client HTTP per le API pubbliche del GME (Gestore Mercati Energetici).

Flusso:
    1. authenticate()  → ottiene JWT
    2. request_data()  → scarica dati (base64 → zip → json)
"""

import base64
import io
import json
import os
import requests
import zipfile
from datetime import date

from dotenv import load_dotenv

load_dotenv()

_BASE_URL     = "https://api.mercatoelettrico.org/request"
_GME_LOGIN    = os.environ["GME_LOGIN"]
_GME_PASSWORD = os.environ["GME_PASSWORD"]


class GmeApiError(Exception):
    pass

class GmeClient:
    def __init__(self, login: str = _GME_LOGIN, password: str = _GME_PASSWORD):
        self._login = login
        self._password = password
        self._token: str | None = None
        self._session = requests.Session()

    def authenticate(self) -> None:
        """POST /api/v1/Auth — recupera JWT e lo memorizza internamente."""
        url = f"{_BASE_URL}/api/v1/Auth"
        payload = {"Login": self._login, "Password": self._password}

        try:
            resp = self._session.post(url, json=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            raise GmeApiError(f"Errore di rete durante l'autenticazione: {e}") from e

        body = resp.json()
        if not body.get("success"):
            raise GmeApiError(
                f"Autenticazione fallita (HTTP {resp.status_code}): "
                f"{body.get('reason') or body.get('Reason')}"
            )

        self._token = body["token"]

    def request_data(
        self,
        platform: str,
        segment: str,
        data_name: str,
        interval_start: date,
        interval_end: date,
        attributes: dict | None = None,
    ) -> list[dict]:
        """
        POST /api/v1/RequestData — restituisce la lista di record JSON.

        La risposta è un base64 di un .zip contenente un file .json.
        """
        if self._token is None:
            self.authenticate()

        url = f"{_BASE_URL}/api/v1/RequestData"
        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {
            "Platform": platform,
            "Segment": segment,
            "DataName": data_name,
            "IntervalStart": interval_start.strftime("%Y%m%d"),
            "IntervalEnd": interval_end.strftime("%Y%m%d"),
            "Attributes": attributes or {},
        }

        try:
            resp = self._session.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise GmeApiError(f"Errore HTTP {resp.status_code} da RequestData: {e}") from e
        except requests.exceptions.RequestException as e:
            raise GmeApiError(f"Errore di rete durante RequestData: {e}") from e

        body = resp.json()
        result = body.get("resultRequest")
        if result and result != "OK":
            raise GmeApiError(f"Errore risposta GME: {result}")

        return self._decode_response(body["contentResponse"])

    def get_my_quotas(self) -> dict:
        """
        GET /api/v1/GetMyQuotas — restituisce usage e limiti dell'utente corrente.

        Campi principali nella risposta:
            activeConnections, connectionsPerMinute, connectionsPerHour,
            dataPerMinute, dataPerHour, lastModifiedTime,
            limits.maxConcurrentConnections, limits.maxConnectionsPerMinute,
            limits.maxConnectionsPerHour, limits.maxDataPerMinute, limits.maxDataPerHour
        """
        if self._token is None:
            self.authenticate()

        url = f"{_BASE_URL}/api/v1/GetMyQuotas"
        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            resp = self._session.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise GmeApiError(f"Errore HTTP {resp.status_code} da GetMyQuotas: {e}") from e
        except requests.exceptions.RequestException as e:
            raise GmeApiError(f"Errore di rete durante GetMyQuotas: {e}") from e

        return resp.json()

    @staticmethod
    def _decode_response(content_b64: str) -> list[dict]:
        """base64 → zip → json → lista di dict."""
        raw_zip = base64.b64decode(content_b64)
        with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
            json_name = next((n for n in zf.namelist() if n.endswith(".json")), None)
            if json_name is None:
                raise GmeApiError("Il file zip restituito dall'API non contiene nessun .json")
            with zf.open(json_name) as jf:
                return json.load(jf)