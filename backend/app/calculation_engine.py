"""
Motore di calcolo FTE.

Implementa la sezione 3 dell'architettura:
- Formula base universale (3.1)
- Knowledge base regole per settore Manifattura (3.2) — Fase 1 MVP copre solo
  questo settore, come da roadmap (sezione 9, Fase 1)
- Algoritmo di calcolo (3.3)
- Soglie budget alert in tempo reale (17.5)

Principio di design: trasparenza > sofisticazione. Ogni FTE calcolato porta
con sé i passaggi intermedi (fte_base, fte_con_overhead, fte_con_crescita,
fte_finale) così l'utente può sempre capire "perché" il numero è quello.
"""
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Knowledge base settoriale — Manifattura (sezione 3.2)
# In Fase 2 questo dizionario diventa dati in tabella REGOLA_CALCOLO
# popolabili/editabili da UI; per l'MVP resta codice così è facile da
# leggere, testare e correggere.
# ---------------------------------------------------------------------------

REGOLE_MANIFATTURA = {
    "produzione_generica": {
        "tipo": "formula",
        "overhead_default": 0.30,
        "overhead_range": (0.15, 0.50),
    },
    "supervisione": {
        "tipo": "rapporto",
        "rapporto_default": 6,  # 1 supervisore ogni 6 operatori
        "rapporto_range": (3, 10),
        "riferimento_funzione": "produzione_generica",
    },
    "qa": {
        "tipo": "rapporto",
        "rapporto_default": 2.5,
        "rapporto_range": (1.5, 5),
        "riferimento_funzione": "produzione_generica",
    },
    "manutenzione": {
        "tipo": "formula_derivata",
        "base_fte": 0.5,
        "scalare_per_fte_produzione": 0.1,
        "riferimento_funzione": "produzione_generica",
    },
    "logistica_interna": {
        "tipo": "rapporto",
        "rapporto_default": 3,
        "rapporto_range": (2, 6),
        "riferimento_funzione": "produzione_generica",
    },
}


@dataclass
class RisultatoFunzione:
    funzione_id: str
    nome: str
    fte_base: float
    fte_con_overhead: float
    fte_con_crescita: float
    fte_finale: float
    confidence: float
    formula_usata: str
    note: Optional[str] = None


@dataclass
class RisultatoCalcolo:
    fte_totali: float
    costo_totale_annuo: float
    per_funzione: dict = field(default_factory=dict)  # funzione_id -> RisultatoFunzione
    budget_utilizzo_pct: Optional[float] = None


def ore_annue_disponibili(turni: int, ore_per_turno: float, giorni_anno: int) -> float:
    """Sezione 3.1 — Ore_Annue = turni × ore/shift × giorni/anno."""
    return turni * ore_per_turno * giorni_anno


def _calcola_produzione(carico_valore: float, dettagli: dict, ore_annue: float,
                         crescita_pct: float, margine_capacita_pct: float) -> RisultatoFunzione:
    tempo_ciclo = dettagli.get("tempo_ciclo", 0.02)
    overhead_pct = dettagli.get("overhead_pct", REGOLE_MANIFATTURA["produzione_generica"]["overhead_default"])

    fte_base = (carico_valore * tempo_ciclo) / ore_annue if ore_annue > 0 else 0.0
    fte_con_overhead = fte_base * (1 + overhead_pct)
    fte_con_crescita = fte_con_overhead * (1 + crescita_pct)
    fte_finale = fte_con_crescita * (1 + margine_capacita_pct)

    return RisultatoFunzione(
        funzione_id="", nome="",
        fte_base=round(fte_base, 2),
        fte_con_overhead=round(fte_con_overhead, 2),
        fte_con_crescita=round(fte_con_crescita, 2),
        fte_finale=round(fte_finale, 2),
        confidence=dettagli.get("confidence", 0.85),
        formula_usata="produzione_generica",
    )


def _calcola_rapporto(fte_riferimento: float, dettagli: dict, regola_key: str,
                       crescita_pct: float, margine_capacita_pct: float) -> RisultatoFunzione:
    regola = REGOLE_MANIFATTURA[regola_key]
    rapporto = dettagli.get("rapporto", regola["rapporto_default"])

    fte_base = fte_riferimento / rapporto if rapporto > 0 else 0.0
    fte_con_overhead = fte_base  # nessun overhead aggiuntivo per funzioni a rapporto
    fte_con_crescita = fte_con_overhead * (1 + crescita_pct)
    fte_finale = fte_con_crescita * (1 + margine_capacita_pct)

    return RisultatoFunzione(
        funzione_id="", nome="",
        fte_base=round(fte_base, 2),
        fte_con_overhead=round(fte_con_overhead, 2),
        fte_con_crescita=round(fte_con_crescita, 2),
        fte_finale=round(fte_finale, 2),
        confidence=dettagli.get("confidence", 0.85),
        formula_usata=regola_key,
    )


def _calcola_manutenzione(fte_produzione: float, dettagli: dict,
                           crescita_pct: float, margine_capacita_pct: float) -> RisultatoFunzione:
    regola = REGOLE_MANIFATTURA["manutenzione"]
    fte_base = regola["base_fte"] + regola["scalare_per_fte_produzione"] * fte_produzione
    fte_con_overhead = fte_base
    fte_con_crescita = fte_con_overhead * (1 + crescita_pct)
    fte_finale = fte_con_crescita * (1 + margine_capacita_pct)

    return RisultatoFunzione(
        funzione_id="", nome="",
        fte_base=round(fte_base, 2),
        fte_con_overhead=round(fte_con_overhead, 2),
        fte_con_crescita=round(fte_con_crescita, 2),
        fte_finale=round(fte_finale, 2),
        confidence=dettagli.get("confidence", 0.80),
        formula_usata="manutenzione",
    )


def calcola_scenario(
    funzioni: list,           # list di dict: {id, nome, formula_key, carico_valore, dettagli_metrica, salary_medio_annuo}
    turni: int,
    ore_per_turno: float,
    giorni_lavorativi_anno: int,
    margine_capacita_pct: float,
    crescita_pct: float = 0.0,
    budget_annuale: Optional[float] = None,
) -> RisultatoCalcolo:
    """
    Implementa l'algoritmo di sezione 3.3.
    Ordine di calcolo: prima le funzioni 'formula' (es. produzione, che è la
    base), poi quelle 'rapporto'/'formula_derivata' che dipendono dal FTE
    di produzione già calcolato — replica la logica "riferimento_funzione".
    """
    ore_annue = ore_annue_disponibili(turni, ore_per_turno, giorni_lavorativi_anno)

    risultati: dict[str, RisultatoFunzione] = {}
    fte_per_formula_key: dict[str, float] = {}  # per risolvere le dipendenze (es. supervisione -> produzione)

    # Passo 1: funzioni indipendenti (formula diretta, es. produzione)
    indipendenti = [f for f in funzioni if REGOLE_MANIFATTURA.get(f["formula_key"], {}).get("tipo") == "formula"]
    dipendenti = [f for f in funzioni if f not in indipendenti]

    for f in indipendenti:
        r = _calcola_produzione(f["carico_valore"], f.get("dettagli_metrica") or {}, ore_annue,
                                 crescita_pct, margine_capacita_pct)
        r.funzione_id, r.nome = f["id"], f["nome"]
        risultati[f["id"]] = r
        fte_per_formula_key[f["formula_key"]] = r.fte_finale

    # Passo 2: funzioni dipendenti (rapporto o formula_derivata)
    for f in dipendenti:
        regola_key = f["formula_key"]
        regola = REGOLE_MANIFATTURA.get(regola_key, REGOLE_MANIFATTURA["produzione_generica"])
        rif_key = regola.get("riferimento_funzione", "produzione_generica")
        fte_riferimento = fte_per_formula_key.get(rif_key, 0.0)

        if regola["tipo"] == "rapporto":
            r = _calcola_rapporto(fte_riferimento, f.get("dettagli_metrica") or {}, regola_key,
                                   crescita_pct, margine_capacita_pct)
        elif regola["tipo"] == "formula_derivata":
            r = _calcola_manutenzione(fte_riferimento, f.get("dettagli_metrica") or {},
                                       crescita_pct, margine_capacita_pct)
        else:
            # fallback: tratta come produzione generica sul proprio carico
            r = _calcola_produzione(f["carico_valore"], f.get("dettagli_metrica") or {}, ore_annue,
                                     crescita_pct, margine_capacita_pct)

        r.funzione_id, r.nome = f["id"], f["nome"]
        risultati[f["id"]] = r
        fte_per_formula_key[regola_key] = r.fte_finale

    # Totali e costi
    fte_totali = sum(r.fte_finale for r in risultati.values())
    costo_totale = 0.0
    for f in funzioni:
        salary = f.get("salary_medio_annuo", 35000.0)
        costo_totale += risultati[f["id"]].fte_finale * salary

    budget_pct = None
    if budget_annuale and budget_annuale > 0:
        budget_pct = round((costo_totale / budget_annuale) * 100, 1)

    return RisultatoCalcolo(
        fte_totali=round(fte_totali, 2),
        costo_totale_annuo=round(costo_totale, 2),
        per_funzione={k: v for k, v in risultati.items()},
        budget_utilizzo_pct=budget_pct,
    )


# Soglie budget alert — sezione 17.5
BUDGET_WARNING_PCT = 90
BUDGET_CRITICAL_PCT = 100


def stato_budget(budget_utilizzo_pct: Optional[float]) -> str:
    if budget_utilizzo_pct is None:
        return "n/a"
    if budget_utilizzo_pct >= BUDGET_CRITICAL_PCT:
        return "critical"
    if budget_utilizzo_pct >= BUDGET_WARNING_PCT:
        return "warning"
    return "ok"
