# Sprint Review — GME API Client
**Data**: 2026-05-21
**Scope**: `src/gme_client.py`, `src/cache.py`, `src/examples/pun_mgp_15min.py`
**Test eseguiti**: Sì — esecuzione funzionale di `pun_mgp_15min.py` (nessun test formale disponibile)

---

## 🐛 Bug e problemi

> Problemi che causano o possono causare errori a runtime. Ordinati per severità.

### [MEDIO] Errori di rete in `authenticate()` non sono wrappati in `GmeApiError`

- **File**: `gme_client.py:42`
- **Problema**: `self._session.post()` può sollevare `requests.exceptions.ConnectionError`, `Timeout`, `SSLError` ecc. Queste eccezioni non vengono catturate e propagano come eccezioni `requests` grezze, mentre tutto il resto del client usa `GmeApiError`. L'utente riceve un traceback inaspettato invece di un messaggio chiaro.
- **Fix**: wrappare la chiamata in un `try/except requests.exceptions.RequestException` e rilanciare come `GmeApiError`.

---

### [MEDIO] HTTP error in `request_data()` non wrappato in `GmeApiError`

- **File**: `gme_client.py:81`
- **Problema**: `resp.raise_for_status()` solleva `requests.exceptions.HTTPError` (es. 401 per token scaduto, 429 per rate limit). Inconsistente con `authenticate()` che usa `GmeApiError`. Se il token scade durante una sessione lunga, l'utente riceve un `HTTPError` non gestito.
- **Fix**: catturare `HTTPError` e rilanciare come `GmeApiError` con messaggio leggibile.

---

### [MEDIO] `os.environ["GME_LOGIN"]` a livello di modulo blocca qualsiasi import

- **File**: `gme_client.py:22-23`
- **Problema**: le variabili `_GME_LOGIN` e `_GME_PASSWORD` vengono lette da `os.environ` all'import, prima che `GmeClient()` venga mai istanziato. Se qualcuno importa solo `GmeApiError` da `gme_client` (per gestire eccezioni) senza avere `.env` configurato, ottiene `KeyError` anche se non usa il client.
- **Fix**: spostare la lettura delle variabili dentro `GmeClient.__init__()`, o usare `os.environ.get("GME_LOGIN") or ""` con un check esplicito in `authenticate()`.

---

### [MEDIO] `_get_pun()` non gestisce il caso di zona PUN assente

- **File**: `examples/pun_mgp_15min.py:61`
- **Problema**: se GME non restituisce dati con `Zone == "PUN"` (dataset vuoto, cambio nome zona, errore API silente), `pun` è un DataFrame vuoto. Le operazioni successive (`.astype(int)`, `.sort_values()`) non falliscono ma restituiscono un DataFrame vuoto senza alcun avviso. Lo script termina scrivendo un CSV vuoto senza che l'utente se ne accorga.
- **Fix**: aggiungere un check `if pun.empty: raise GmeApiError("Nessun dato PUN trovato per la data richiesta")`.

---

### [BASSO] `_decode_response()` solleva `StopIteration` senza messaggio

- **File**: `gme_client.py:95`
- **Problema**: `next(n for n in zf.namelist() if n.endswith(".json"))` solleva `StopIteration` se il file zip non contiene alcun `.json`. Eccezione non documentata e non wrappata in `GmeApiError`.
- **Fix**: usare `next(..., None)` con un check esplicito e un messaggio d'errore chiaro.

---

### [BASSO] `cache.get()` non gestisce file corrotti

- **File**: `cache.py:37`
- **Problema**: `json.loads(path.read_text(...))` solleva `json.JSONDecodeError` se il file in cache è corrotto (scrittura interrotta da crash, disco pieno, ecc.). La cache diventerebbe inutilizzabile senza un messaggio chiaro.
- **Fix**: wrappare in `try/except json.JSONDecodeError`, loggare un warning e ritornare `None` (trattare come cache miss).

---

### [BASSO] `cache.set()` non è atomico — rischio file corrotto

- **File**: `cache.py:49-50`
- **Problema**: scrive direttamente sul file di destinazione. Se il processo viene interrotto (Ctrl+C, crash, disco pieno) durante la scrittura, il file rimane parzialmente scritto e il successivo `get()` fallirà con `json.JSONDecodeError`.
- **Fix**: scrivere su un file temporaneo nella stessa cartella, poi rinominarlo (`path.rename()`) — l'operazione di rename è atomica sui filesystem comuni.

---

### [BASSO] Colonna `PUN_EUR_MWh` potrebbe rimanere stringa

- **File**: `examples/pun_mgp_15min.py:72`
- **Problema**: i valori `Price` arrivano dall'API come stringhe (`"167.920000"`). Pandas li converte in float durante la creazione del DataFrame, ma questo comportamento è implicito e non garantito se il formato cambia.
- **Fix**: cast esplicito `pun["Price"] = pun["Price"].astype(float)` prima del rename.

---

## 💡 Spunti di miglioramento

### Test formali assenti

- **File**: nessuno — manca la cartella `tests/`
- **Contesto**: l'unico modo di verificare il funzionamento è eseguire lo script, che chiama l'API reale (o la cache). Non c'è modo di testare `GmeCache._path()`, `is_cacheable()`, la logica di decodifica base64, o la gestione degli errori senza una connessione attiva.
- **Suggerimento**: creare `src/tests/test_cache.py` con test unitari per `GmeCache` (usando cartelle temporanee con `tmp_path` di pytest) e `src/tests/test_client.py` con mock di `requests.Session` per testare `authenticate()` e `request_data()` senza toccare l'API reale.

---

### Struttura pacchetto: `sys.path.insert` è un workaround fragile

- **File**: `examples/pun_mgp_15min.py:22`
- **Contesto**: il `sys.path.insert(0, ...)` funziona solo se lo script viene eseguito direttamente. Se importato da un altro modulo, o eseguito da una directory diversa, l'import fallisce. Peggio: inquina `sys.path` globale.
- **Suggerimento**: aggiungere un `pyproject.toml` minimale e installare il pacchetto con `pip install -e .`. Gli import diventano `from gme_api.cache import GmeCache` ovunque, senza trucchi.

---

### Nessuna retry logic per errori transitori di rete

- **File**: `gme_client.py`
- **Contesto**: le API GME hanno rate limiting e la rete può avere picchi di latenza. Attualmente un timeout o un 429 fa fallire tutto. Per un'esecuzione notturna automatizzata questo è un problema reale.
- **Suggerimento**: aggiungere retry con backoff esponenziale. Con `tenacity` basta un decoratore:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential
  @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
  def request_data(...):
  ```

---

### `print()` invece di `logging`

- **File**: `examples/pun_mgp_15min.py:43,56,58`
- **Contesto**: va bene per uno script standalone, ma se `_get_pun()` viene importata come libreria i print sono inaspettati e non silenziabili. In un'esecuzione schedulata (cron, task scheduler) non c'è modo di controllare il livello di verbosità.
- **Suggerimento**: sostituire i `print()` con `logging.getLogger(__name__).info(...)`. Chi usa la funzione come libreria può configurare il livello di log; chi la usa come script può aggiungere `logging.basicConfig(level=logging.INFO)`.

---

### Token JWT mai aggiornato — sessioni lunghe possono rompersi

- **File**: `gme_client.py:66-67`
- **Contesto**: il token viene ottenuto una volta e riutilizzato per tutta la vita dell'oggetto `GmeClient`. I JWT tipicamente scadono (ore o giorni). In uno script breve non è un problema, ma in un'applicazione che usa lo stesso client per ore sì.
- **Suggerimento**: intercettare il 401 in `request_data()`, chiamare `authenticate()` per rinnovare il token, e riprovare la richiesta una volta.

---

## Riepilogo

| | Conteggio |
|---|---|
| Bug critici | 0 |
| Bug medi | 4 |
| Bug bassi | 3 |
| Spunti di miglioramento | 5 |
