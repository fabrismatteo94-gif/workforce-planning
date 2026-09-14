from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/aziende/{azienda_id}/funzioni", tags=["funzioni"])


@router.post("", response_model=schemas.FunzioneOut)
def crea_funzione(azienda_id: str, payload: schemas.FunzioneCreate, db: Session = Depends(get_db)):
    azienda = db.query(models.Azienda).filter(models.Azienda.id == azienda_id).first()
    if not azienda:
        raise HTTPException(status_code=404, detail="Azienda non trovata")

    funzione = models.Funzione(
        azienda_id=azienda_id,
        nome=payload.nome,
        categoria=payload.categoria,
    )
    db.add(funzione)
    db.flush()

    carico = models.CaricoLavoro(
        funzione_id=funzione.id,
        **payload.carico.model_dump(),
    )
    db.add(carico)

    regola = models.RegolaCalcolo(
        funzione_id=funzione.id,
        formula_key=payload.formula_key,
        parametri={"salary_medio_annuo": payload.salary_medio_annuo},
    )
    db.add(regola)

    db.commit()
    db.refresh(funzione)
    return funzione


@router.get("", response_model=list[schemas.FunzioneOut])
def lista_funzioni(azienda_id: str, db: Session = Depends(get_db)):
    return db.query(models.Funzione).filter(models.Funzione.azienda_id == azienda_id).order_by(models.Funzione.ordine).all()


@router.patch("/{funzione_id}/carico")
def aggiorna_carico(azienda_id: str, funzione_id: str, payload: schemas.CaricoLavoroUpdate, db: Session = Depends(get_db)):
    carico = db.query(models.CaricoLavoro).filter(models.CaricoLavoro.funzione_id == funzione_id).first()
    if not carico:
        raise HTTPException(status_code=404, detail="Carico di lavoro non trovato")

    dati_nuovi = payload.model_dump(exclude_unset=True)
    for campo, valore_nuovo in dati_nuovi.items():
        valore_precedente = getattr(carico, campo)
        if valore_precedente != valore_nuovo:
            db.add(models.Modifica(
                azienda_id=azienda_id,
                tipo_modifica="Carico_Funzione",
                campo_modificato=f"{funzione_id}.{campo}",
                valore_precedente=valore_precedente,
                valore_nuovo=valore_nuovo,
            ))
        setattr(carico, campo, valore_nuovo)

    db.commit()
    return {"status": "ok"}


@router.delete("/{funzione_id}")
def elimina_funzione(azienda_id: str, funzione_id: str, db: Session = Depends(get_db)):
    funzione = db.query(models.Funzione).filter(models.Funzione.id == funzione_id).first()
    if not funzione:
        raise HTTPException(status_code=404, detail="Funzione non trovata")
    db.delete(funzione)
    db.commit()
    return {"status": "ok"}
