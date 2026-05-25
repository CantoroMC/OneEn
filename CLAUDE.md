# apy-gme — Contesto progetto

## Scopo

Wrapper Python per le API pubbliche del GME (Gestore Mercati Energetici).
Permette di scaricare qualsiasi dataset di mercato (prezzi, domanda, aste GO/CV/TEE)
tramite un'interfaccia interattiva questionary e di salvarlo in CSV.

## Struttura

```
src/gme/               # Pacchetto installabile
│   ├── client.py      # Client HTTP + autenticazione JWT
│   ├── catalog.py     # Catalogo statico dei dataset (67 dataset, aggiornato ott. 2025)
│   ├── ui.py          # Prompt questionary riusabili (selezione parametri + date)
│   ├── download.py    # Entry point: download interattivo
│   ├── show_quotas.py # Entry point: usage e limiti API
│   └── __init__.py    # Esporta GmeClient, GmeApiError, GmeCatalog, GmeUi
man/                   # Manuali PDF API GME (utente + tecnico, ott. 2025)
pyproject.toml         # Configurazione pacchetto e entry point
```

## Utilizzo

Dopo `pip install -e .` i comandi sono disponibili ovunque nel terminale:

```bash
gme-download      # download interattivo (preset + selezione manuale)
gme-quotas        # stato quote API

# Alternativamente senza installazione:
python -m gme.download
python -m gme.show_quotas
```

I CSV vengono salvati nella **directory corrente** da cui si lancia il comando.

## Setup

```bash
pip install -e .
```

Creare un file `.env` nella root con le credenziali GME:

```
GME_LOGIN=tuo_login
GME_PASSWORD=tua_password
```

Il file è in `.gitignore` — non committarlo mai.

## Convenzioni

- **Date nell'UI**: formato `GG/MM/YYYY` (questionary)
- **Date nei nomi file output**: formato `YYYYMMDD`
- **Durate**: `Ng` = N giorni, `Ns` = N settimane
- **Output CSV**: separatore `;`, decimale `.`
- I CSV prodotti finiscono in `src/` (stessa cartella degli script)

## Decisioni architetturali

- **No cache su disco**: l'API GME supporta nativamente range multi-giorno con una
  singola chiamata. La cache giornaliera era ridondante e aggiungeva stato.
- **No argparse**: tutta l'interazione avviene via questionary. Un solo script (`download.py`)
  copre tutti i casi d'uso.
- **No loop giornaliero**: `request_data()` accetta `interval_start`/`interval_end` direttamente.
- **Trasformazione PUN non inclusa**: il dataset `ME_ZonalPrices` viene scaricato raw.
  Il filtraggio `Zone==PUN` e la costruzione della colonna `Timestamp` da `Period` si
  fanno a valle in Power BI / Excel.

## Problemi noti / TODO

Nessuno al momento. Tutti i bug del SPRINT_REVIEW.md sono stati risolti.
