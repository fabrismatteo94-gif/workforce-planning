from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/aziende", tags=["aziende"])


@router.post("", response_model=schemas.AziendaOut)
def crea_azienda(payload: schemas.AziendaCreate, db: Session = Depends(get_db)):
    azienda = models.Azienda(**payload.model_dump())
    db.add(azienda)
    db.flush()

    # Crea parametri org di default (sezione 4 del flusso utente)
    parametri = models.ParametriOrg(azienda_id=azienda.id)
    db.add(parametri)

    db.commit()
    db.refresh(azienda)
    return azienda


@router.get("", response_model=list[schemas.AziendaOut])
def lista_aziende(db: Session = Depends(get_db)):
    return db.query(models.Azienda).all()


@router.get("/{azienda_id}", response_model=schemas.AziendaOut)
def ottieni_azienda(azienda_id: str, db: Session = Depends(get_db)):
    azienda = db.query(models.Azienda).filter(models.Azienda.id == azienda_id).first()
    if not azienda:
        raise HTTPException(status_code=404, detail="Azienda non trovata")
    return azienda


@router.get("/{azienda_id}/parametri-org", response_model=schemas.ParametriOrgOut)
def ottieni_parametri_org(azienda_id: str, db: Session = Depends(get_db)):
    parametri = db.query(models.ParametriOrg).filter(models.ParametriOrg.azienda_id == azienda_id).first()
    if not parametri:
        raise HTTPException(status_code=404, detail="Parametri org non trovati")
    return parametri


@router.patch("/{azienda_id}/parametri-org", response_model=schemas.ParametriOrgOut)
def aggiorna_parametri_org(azienda_id: str, payload: schemas.ParametriOrgUpdate, db: Session = Depends(get_db)):
    """
    Ricalcolo cascata (sezione 17.2): questo endpoint NON ricalcola da solo —
    il frontend, dopo l'update riuscito, chiama POST /calcolo/{azienda_id}
    così tutte le funzioni vengono ricalcolate in un'unica passata coerente.
    Qui ci limitiamo a salvare il parametro e loggare la Modifica.
    """
    parametri = db.query(models.ParametriOrg).filter(models.ParametriOrg.azienda_id == azienda_id).first()
    if not parametri:
        raise HTTPException(status_code=404, detail="Parametri org non trovati")

    dati_nuovi = payload.model_dump(exclude_unset=True)
    for campo, valore_nuovo in dati_nuovi.items():
        valore_precedente = getattr(parametri, campo)
        if valore_precedente != valore_nuovo:
            db.add(models.Modifica(
                azienda_id=azienda_id,
                tipo_modifica="Parametro_Org",
                campo_modificato=campo,
                valore_precedente=valore_precedente,
                valore_nuovo=valore_nuovo,
            ))
        setattr(parametri, campo, valore_nuovo)

    db.commit()
    db.refresh(parametri)
    return parametri
