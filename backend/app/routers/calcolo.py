from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..calculation_engine import calcola_scenario, stato_budget

router = APIRouter(prefix="/aziende/{azienda_id}", tags=["calcolo"])

# Sezione 3.3 / scenari dinamici (slider Conservativo/Base/Aggressivo)
CRESCITA_PER_SCENARIO = {
    "Conservativo": -0.10,
    "Base": 0.0,
    "Aggressivo": 0.25,
}


@router.post("/calcolo", response_model=schemas.CalcoloOut)
def esegui_calcolo(azienda_id: str, payload: schemas.CalcoloRequest, db: Session = Depends(get_db)):
    """
    Ricalcolo cascata (sezione 17.2): ricalcola TUTTE le funzioni dell'azienda
    in un'unica passata coerente, poi valuta la soglia budget (17.5) e salva
    lo snapshot. Il frontend chiama questo endpoint dopo ogni modifica
    (parametro org o carico di una funzione) con debounce 500ms.
    """
    azienda = db.query(models.Azienda).filter(models.Azienda.id == azienda_id).first()
    if not azienda:
        raise HTTPException(status_code=404, detail="Azienda non trovata")

    parametri = db.query(models.ParametriOrg).filter(models.ParametriOrg.azienda_id == azienda_id).first()
    if not parametri:
        raise HTTPException(status_code=404, detail="Parametri org non trovati")

    funzioni_db = db.query(models.Funzione).filter(models.Funzione.azienda_id == azienda_id).all()
    if not funzioni_db:
        raise HTTPException(status_code=400, detail="Nessuna funzione definita per questa azienda")

    funzioni_input = []
    for f in funzioni_db:
        carico = f.carico
        regola = f.regola
        salary = (regola.parametri or {}).get("salary_medio_annuo", 35000.0) if regola else 35000.0
        funzioni_input.append({
            "id": f.id,
            "nome": f.nome,
            "formula_key": regola.formula_key if regola else "produzione_generica",
            "carico_valore": carico.metrica_valore if carico else 0.0,
            "dettagli_metrica": {
                **(carico.dettagli_metrica or {}),
                "confidence": carico.confidence if carico else 0.85,
            },
            "salary_medio_annuo": salary,
        })

    crescita_pct = payload.crescita_pct_override
    if crescita_pct is None:
        crescita_pct = CRESCITA_PER_SCENARIO.get(payload.scenario_tipo, 0.0)

    risultato = calcola_scenario(
        funzioni=funzioni_input,
        turni=parametri.turni,
        ore_per_turno=parametri.ore_per_turno,
        giorni_lavorativi_anno=parametri.giorni_lavorativi_anno,
        margine_capacita_pct=parametri.margine_capacita_pct,
        crescita_pct=crescita_pct,
        budget_annuale=parametri.budget_annuale,
    )

    stato = stato_budget(risultato.budget_utilizzo_pct)

    # Salva snapshot (sezione 3.3 output + CALCOLO_SNAPSHOT)
    snapshot = models.CalcoloSnapshot(
        azienda_id=azienda_id,
        scenario_tipo=payload.scenario_tipo,
        fte_totali=risultato.fte_totali,
        costo_totale_annuo=risultato.costo_totale_annuo,
        budget_utilizzo_pct=risultato.budget_utilizzo_pct,
        risultati_per_funzione={
            fid: {
                "nome": r.nome,
                "fte_finale": r.fte_finale,
                "confidence": r.confidence,
                "formula_usata": r.formula_usata,
            }
            for fid, r in risultato.per_funzione.items()
        },
    )
    db.add(snapshot)
    db.commit()

    per_funzione_out = []
    for fid, r in risultato.per_funzione.items():
        f = next(f for f in funzioni_db if f.id == fid)
        salary = (f.regola.parametri or {}).get("salary_medio_annuo", 35000.0) if f.regola else 35000.0
        per_funzione_out.append(schemas.RisultatoFunzioneOut(
            funzione_id=r.funzione_id,
            nome=r.nome,
            fte_base=r.fte_base,
            fte_con_overhead=r.fte_con_overhead,
            fte_con_crescita=r.fte_con_crescita,
            fte_finale=r.fte_finale,
            confidence=r.confidence,
            formula_usata=r.formula_usata,
            costo_annuo=round(r.fte_finale * salary, 2),
        ))

    return schemas.CalcoloOut(
        fte_totali=risultato.fte_totali,
        costo_totale_annuo=risultato.costo_totale_annuo,
        budget_utilizzo_pct=risultato.budget_utilizzo_pct,
        stato_budget=stato,
        per_funzione=per_funzione_out,
    )


@router.get("/storico", response_model=list[dict])
def storico_modifiche(azienda_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """Sezione 17.4 — timeline modifiche per la tab Storico."""
    modifiche = (
        db.query(models.Modifica)
        .filter(models.Modifica.azienda_id == azienda_id)
        .order_by(models.Modifica.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "timestamp": m.timestamp.isoformat(),
            "tipo_modifica": m.tipo_modifica,
            "campo_modificato": m.campo_modificato,
            "valore_precedente": m.valore_precedente,
            "valore_nuovo": m.valore_nuovo,
            "is_undone": m.is_undone,
        }
        for m in modifiche
    ]


@router.post("/undo")
def undo_ultima_modifica(azienda_id: str, db: Session = Depends(get_db)):
    """
    Sezione 17.3 — Undo. Ripristina l'ultima modifica non ancora annullata.
    NB: qui ripristiniamo il valore sul modello corretto in base al
    tipo_modifica; il frontend dovrà poi richiamare /calcolo per il
    ricalcolo cascata, mantenendo coerente il principio "un solo punto
    di ricalcolo" invece di duplicare la logica qui.
    """
    ultima = (
        db.query(models.Modifica)
        .filter(models.Modifica.azienda_id == azienda_id, models.Modifica.is_undone == False)  # noqa: E712
        .order_by(models.Modifica.timestamp.desc())
        .first()
    )
    if not ultima:
        raise HTTPException(status_code=404, detail="Nessuna modifica da annullare")

    if ultima.tipo_modifica == "Parametro_Org":
        parametri = db.query(models.ParametriOrg).filter(models.ParametriOrg.azienda_id == azienda_id).first()
        setattr(parametri, ultima.campo_modificato, ultima.valore_precedente)
    elif ultima.tipo_modifica == "Carico_Funzione":
        funzione_id, campo = ultima.campo_modificato.split(".", 1)
        carico = db.query(models.CaricoLavoro).filter(models.CaricoLavoro.funzione_id == funzione_id).first()
        if carico:
            setattr(carico, campo, ultima.valore_precedente)

    ultima.is_undone = True
    db.add(models.Modifica(
        azienda_id=azienda_id,
        tipo_modifica="Undo",
        campo_modificato=ultima.campo_modificato,
        valore_precedente=ultima.valore_nuovo,
        valore_nuovo=ultima.valore_precedente,
        undo_parent_id=ultima.id,
    ))
    db.commit()
    return {"status": "ok", "campo_ripristinato": ultima.campo_modificato}
