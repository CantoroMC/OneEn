"""
Catalogo statico dei dataset disponibili tramite API GME (PublicMarketResults).

Uso:
    from gme import GmeCatalog

    GmeCatalog.datasets("ME")                        # lista DataName categoria ME
    GmeCatalog.segments("ME_ZonalPrices")            # segmenti validi
    GmeCatalog.attributes("ME_ZonalPrices", "MGP")   # attributi configurabili
    GmeCatalog.is_xml("Offers_PublicDomain")         # True se risposta XML

Fonte: Manuale tecnico API GME (ottobre 2025).
"""


class GmeCatalog:

    CATEGORIES: dict[str, str] = {
        "ME":  "Mercato Elettrico",
        "GAS": "Gas Naturale",
        "ENV": "Ambiente (GO, CV, TEE, ...)",
    }

    # Struttura di ogni entry:
    #   "DataName": {
    #       "description": str
    #       "category":    "ME" | "GAS" | "ENV"
    #       "segments":    list[str]
    #       "attributes":  {segment: {chiave: [valori_validi]}}   (opzionale)
    #       "xml_format":  bool                                    (opzionale)
    #   }
    _DATA: dict[str, dict] = {

        # -----------------------------------------------------------
        # MERCATO ELETTRICO
        # -----------------------------------------------------------

        "ME_AdditionalDemand": {
            "description": "Offerte integrative MGP",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_Cip6": {
            "description": "Informazioni preliminari CIP6",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_ConventionalPrices": {
            "description": "Prezzi convenzionali",
            "category": "ME",
            "segments": ["MGP", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7", "MA"],
        },
        "ME_Demand": {
            "description": "Fabbisogno",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_DemandAndSupply": {
            "description": "Domanda e offerta",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7"],
        },
        "ME_EuropeanExchanges": {
            "description": "Borse europee (statistiche)",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_ForecastDemand": {
            "description": "Stima del fabbisogno",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_GeneralisedConstraints": {
            "description": "Vincoli generalizzati",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3"],
        },
        "ME_HourlyPrice": {
            "description": "Prezzi orari XBID (60 e 15 minuti)",
            "category": "ME",
            "segments": ["XBID"],
        },
        "ME_Liquidity": {
            "description": "Liquidita MGP",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_MarketCoupling": {
            "description": "Market coupling",
            "category": "ME",
            "segments": ["MGP"],
        },
        "ME_MBResults": {
            "description": "Esiti Mercato del Bilanciamento (preliminari)",
            "category": "ME",
            "segments": ["MB"],
        },
        "ME_MLFResults": {
            "description": "Esiti MLF-Flex",
            "category": "ME",
            "segments": ["MGP", "MLT"],
        },
        "ME_MPEGResults": {
            "description": "Esiti MPEG",
            "category": "ME",
            "segments": ["MPEG"],
        },
        "ME_MSDExAnteResults": {
            "description": "Esiti MSD Ex-Ante",
            "category": "ME",
            "segments": ["MSD"],
        },
        "ME_MSDExPostResults": {
            "description": "Esiti MSD Ex-Post",
            "category": "ME",
            "segments": ["MSD"],
        },
        "ME_MTEResults": {
            "description": "Esiti MTE",
            "category": "ME",
            "segments": ["MTE"],
        },
        "ME_PABResults": {
            "description": "Esiti PAB",
            "category": "ME",
            "segments": ["PAB"],
        },
        "ME_PCEResults": {
            "description": "Esiti PCE",
            "category": "ME",
            "segments": ["PCE"],
        },
        "ME_PPANotices": {
            "description": "Annunci PPA in bacheca",
            "category": "ME",
            "segments": ["PPA"],
        },
        "ME_PPAContracts": {
            "description": "Contratti PPA registrati",
            "category": "ME",
            "segments": ["PPA"],
        },
        "ME_RampConstraints": {
            "description": "Vincoli di rampa",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3"],
        },
        "ME_Transits": {
            "description": "Transiti",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3"],
        },
        "ME_TransmissionLimits": {
            "description": "Limiti di transito",
            "category": "ME",
            "segments": ["MA1", "MGP", "MI-A1", "MI-A2", "MI-A3", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7", "MA"],
        },
        "ME_XBIDNominationPlatform": {
            "description": "Statistiche piattaforma di nomina XBID",
            "category": "ME",
            "segments": ["XBID"],
        },
        "ME_XBIDResults": {
            "description": "Esiti MI-XBID",
            "category": "ME",
            "segments": ["XBID"],
        },
        "ME_ZonalPrices": {
            "description": "Prezzi zonali (include PUN per MGP)",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7", "MA"],
            "attributes": {
                "MGP": {"GranularityType": ["PT15", "PT30", "PT60"]},
            },
        },
        "ME_ZonalVolumes": {
            "description": "Quantita zonali",
            "category": "ME",
            "segments": ["MGP", "MI-A1", "MI-A2", "MI-A3", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7", "MA"],
        },
        "Offers_PublicDomain": {
            "description": "Offerte pubbliche (file XML)",
            "category": "ME",
            "segments": [
                "MGP", "MI-A1", "MI-A2", "MI-A3", "MI1", "MI2", "MI3", "MI4", "MI5", "MI6", "MI7",
                "MA", "XBID", "MSD", "MB", "MTE", "MPEG", "AFRR", "AFRE", "MRR", "MRRTerna",
                "AGS", "MGAS", "MGS", "MTGAS", "PBGAS", "PBGAS-1", "CV", "TEE",
            ],
            "xml_format": True,
        },

        # -----------------------------------------------------------
        # GAS
        # -----------------------------------------------------------

        "GAS_ContinuousTrading": {
            "description": "Negoziazione continua gas",
            "category": "GAS",
            "segments": ["MGP-GAS", "MI-GAS", "MT-GAS"],
        },
        "GAS_DemandAndSupply": {
            "description": "Domanda e offerta gas",
            "category": "GAS",
            "segments": [
                "MGP-GAS", "MI-GAS", "MGS-Edison", "MGS-Stogit", "MGS-Adriatica",
                "PB-GAS", "PBZ-Edison stoccaggi", "PBZ-G+1", "PBZ-G+N", "PBZ-Import",
                "PBZ-Linepack", "PBZ-LNG", "PBZ-PSV", "PBZ-Reintegro Stogit",
                "PBZ-Risorse PSV", "PBZ-Stogit",
            ],
        },
        "GAS_IGIndex": {
            "description": "Indice IGI",
            "category": "GAS",
            "segments": ["IGI"],
        },
        "GAS_ImbalancePrice": {
            "description": "Prezzo di sbilanciamento gas",
            "category": "GAS",
            "segments": ["GAS"],
        },
        "GAS_MGASAuctionResults": {
            "description": "Esiti aste MGAS",
            "category": "GAS",
            "segments": ["MGP-GAS", "MI-GAS"],
        },
        "GAS_MGSAuctionResults": {
            "description": "Esiti aste MGS",
            "category": "GAS",
            "segments": ["MGS"],
        },
        "GAS_MPLAuctionResults": {
            "description": "Esiti aste MPL",
            "category": "GAS",
            "segments": ["MPL"],
        },
        "GAS_PBAuctionResults": {
            "description": "Esiti aste PB-GAS",
            "category": "GAS",
            "segments": ["PB-GAS"],
        },
        "GAS_PARResults": {
            "description": "Esiti PAR",
            "category": "GAS",
            "segments": ["PAR"],
        },
        "GAS_PGasResults": {
            "description": "Esiti P-GAS (import, aliquote, D.Lgs 13010)",
            "category": "GAS",
            "segments": ["IM", "RO", "SV"],
        },
        "GAS_PGRResults": {
            "description": "Esiti PGR (mercato non ancora attivo)",
            "category": "GAS",
            "segments": ["PGR"],
        },

        # -----------------------------------------------------------
        # AMBIENTE
        # -----------------------------------------------------------

        "ENV_AuctionResults": {
            "description": "Esiti aste GO",
            "category": "ENV",
            "segments": ["GO"],
        },
        "ENV_Bilaterals": {
            "description": "Bilaterali CV / GO / TEE",
            "category": "ENV",
            "segments": ["CV", "GO", "TEE"],
        },
        "ENV_BulletinBoard": {
            "description": "Bacheca GO",
            "category": "ENV",
            "segments": ["GO"],
        },
        "ENV_CVAuctionResults": {
            "description": "Esiti sessioni CV",
            "category": "ENV",
            "segments": ["CV"],
        },
        "ENV_HourlyPrice": {
            "description": "Prezzi orari GO / TEE",
            "category": "ENV",
            "segments": ["GO", "TEE"],
        },
        "ENV_MCICResults": {
            "description": "Esiti MCIC (biocarburanti)",
            "category": "ENV",
            "segments": ["MCIC"],
        },
        "ENV_PDCOilResults": {
            "description": "Rilevazione annuale PDC-OIL",
            "category": "ENV",
            "segments": ["PDC-OIL"],
        },
        "ENV_PLogistic": {
            "description": "Annunci P-Logistica oli minerali",
            "category": "ENV",
            "segments": ["P-Logistic"],
        },
        "ENV_Results": {
            "description": "Esiti mercato CV / GO / TEE",
            "category": "ENV",
            "segments": ["CV", "GO", "TEE"],
        },
        "ENV_TEEAvailableCertificates": {
            "description": "Titoli TEE disponibili",
            "category": "ENV",
            "segments": ["TEE"],
        },
        "ENV_TEEIssuedCertificates": {
            "description": "Titoli TEE emessi",
            "category": "ENV",
            "segments": ["TEE"],
        },
        "ENV_TEERelevantPrice": {
            "description": "Prezzo rilevante TEE",
            "category": "ENV",
            "segments": ["TEE"],
        },
        "ENV_TEETariffContribution": {
            "description": "Contributo tariffario TEE",
            "category": "ENV",
            "segments": ["TEE"],
        },
    }

    # ------------------------------------------------------------------
    # API pubblica
    # ------------------------------------------------------------------

    @classmethod
    def datasets(cls, category: str) -> list[str]:
        """DataName disponibili per categoria, ordinati alfabeticamente."""
        return sorted(k for k, v in cls._DATA.items() if v["category"] == category)

    @classmethod
    def segments(cls, data_name: str) -> list[str]:
        """Segment validi per un DataName."""
        return cls._DATA[data_name]["segments"]

    @classmethod
    def attributes(cls, data_name: str, segment: str) -> dict[str, list[str]]:
        """
        Attributi configurabili per la coppia DataName+Segment.
        Esempio: {"GranularityType": ["PT15", "PT30", "PT60"]}
        Dizionario vuoto se nessun attributo disponibile.
        """
        return cls._DATA[data_name].get("attributes", {}).get(segment, {})

    @classmethod
    def description(cls, data_name: str) -> str:
        """Descrizione leggibile del dataset."""
        return cls._DATA[data_name]["description"]

    @classmethod
    def is_xml(cls, data_name: str) -> bool:
        """True per dataset che restituiscono XML (es. Offers_PublicDomain)."""
        return cls._DATA[data_name].get("xml_format", False)
