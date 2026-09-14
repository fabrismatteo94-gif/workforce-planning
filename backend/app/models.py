"""
Modelli ORM — Fase 1 MVP.
Copre: Azienda, Funzione, CaricoLavoro, ParametriOrg, RegolaCalcolo, CalcoloSnapshot.
Le entità di Fase 2+ (Organigramma, ProfiloPersona, Scenario multipli salvati,
StoricoDato, CurvaStagionale, BusinessUnit) sono nello schema YAML di
architettura.md e verranno aggiunte quando si sviluppano quegli step.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Azienda(Base):
    __tablename__ = "aziende"

    id = Column(String, primary_key=True, default=gen_uuid)
    nome = Column(String, nullable=False)
    settore = Column(String, nullable=False, default="Manifattura")
    regione = Column(String, nullable=True)
    anno_fiscale = Column(Integer, nullable=False)
    dimensione = Column(String, nullable=True)  # micro/pmi/mid/large
    modello_organizzativo = Column(String, nullable=True)
    turnover_annuale_pct = Column(Float, nullable=True, default=0.0)
    data_creazione = Column(DateTime, default=now_utc)

    funzioni = relationship("Funzione", back_populates="azienda", cascade="all, delete-orphan")
    parametri_org = relationship("ParametriOrg", back_populates="azienda", uselist=False, cascade="all, delete-orphan")
    snapshots = relationship("CalcoloSnapshot", back_populates="azienda", cascade="all, delete-orphan")
    modifiche = relationship("Modifica", back_populates="azienda", cascade="all, delete-orphan")


class ParametriOrg(Base):
    """Un record per azienda — i parametri organizzativi globali (sezione 4 del flusso utente)."""
    __tablename__ = "parametri_org"

    id = Column(String, primary_key=True, default=gen_uuid)
    azienda_id = Column(String, ForeignKey("aziende.id"), nullable=False, unique=True)

    turni = Column(Integer, nullable=False, default=2)
    ore_per_turno = Column(Float, nullable=False, default=8.0)
    giorni_lavorativi_anno = Column(Integer, nullable=False, default=240)
    margine_capacita_pct = Column(Float, nullable=False, default=0.20)
    budget_annuale = Column(Float, nullable=True)
    velocita_hiring_giorni = Column(Integer, nullable=False, default=45)
    orizzonte_pianificazione_mesi = Column(Integer, nullable=False, default=12)

    azienda = relationship("Azienda", back_populates="parametri_org")


class Funzione(Base):
    __tablename__ = "funzioni"

    id = Column(String, primary_key=True, default=gen_uuid)
    azienda_id = Column(String, ForeignKey("aziende.id"), nullable=False)
    nome = Column(String, nullable=False)
    categoria = Column(String, nullable=False, default="Diretto")  # Diretto/Indiretto/Leadership/Strategico
    tipo_calcolo = Column(String, nullable=False, default="formula")  # formula | rapporto
    ordine = Column(Integer, default=0)

    azienda = relationship("Azienda", back_populates="funzioni")
    carico = relationship("CaricoLavoro", back_populates="funzione", uselist=False, cascade="all, delete-orphan")
    regola = relationship("RegolaCalcolo", back_populates="funzione", uselist=False, cascade="all, delete-orphan")


class CaricoLavoro(Base):
    __tablename__ = "carico_lavoro"

    id = Column(String, primary_key=True, default=gen_uuid)
    funzione_id = Column(String, ForeignKey("funzioni.id"), nullable=False, unique=True)

    metrica_tipo = Column(String, nullable=False, default="Unita_Anno")
    metrica_valore = Column(Float, nullable=False, default=0.0)
    dettagli_metrica = Column(JSON, nullable=True, default=dict)  # es: {tempo_ciclo, overhead_pct, rapporto}
    fonte_dato = Column(String, nullable=False, default="Input_Manuale")
    is_stimato = Column(Boolean, default=False)
    confidence = Column(Float, default=0.85)
    note = Column(Text, nullable=True)
    ultima_modifica = Column(DateTime, default=now_utc, onupdate=now_utc)

    funzione = relationship("Funzione", back_populates="carico")


class RegolaCalcolo(Base):
    __tablename__ = "regole_calcolo"

    id = Column(String, primary_key=True, default=gen_uuid)
    funzione_id = Column(String, ForeignKey("funzioni.id"), nullable=False, unique=True)

    tipo_regola = Column(String, nullable=False, default="Default")  # Default | Override_Custom | Storico
    formula_key = Column(String, nullable=False, default="produzione_generica")
    parametri = Column(JSON, nullable=True, default=dict)
    versione = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    funzione = relationship("Funzione", back_populates="regola")


class CalcoloSnapshot(Base):
    """Ultimo risultato calcolato per l'azienda (sezione 3.3 + 17.1 dell'architettura)."""
    __tablename__ = "calcolo_snapshot"

    id = Column(String, primary_key=True, default=gen_uuid)
    azienda_id = Column(String, ForeignKey("aziende.id"), nullable=False)
    scenario_tipo = Column(String, nullable=False, default="Base")  # Conservativo/Base/Aggressivo
    data_calcolo = Column(DateTime, default=now_utc)

    fte_totali = Column(Float, default=0.0)
    costo_totale_annuo = Column(Float, default=0.0)
    budget_utilizzo_pct = Column(Float, nullable=True)
    risultati_per_funzione = Column(JSON, default=dict)  # {funzione_id: {fte, costo, confidence, ...}}

    azienda = relationship("Azienda", back_populates="snapshots")


class Modifica(Base):
    """Change log — sezione 17.1. Alimenta Undo + tab Storico."""
    __tablename__ = "modifiche"

    id = Column(String, primary_key=True, default=gen_uuid)
    azienda_id = Column(String, ForeignKey("aziende.id"), nullable=False)
    timestamp = Column(DateTime, default=now_utc)

    tipo_modifica = Column(String, nullable=False)  # Parametro_Org | Carico_Funzione | Budget_Override | Undo
    campo_modificato = Column(String, nullable=False)
    valore_precedente = Column(JSON, nullable=True)
    valore_nuovo = Column(JSON, nullable=True)
    risultato_calcolo_snapshot = Column(JSON, nullable=True)
    note = Column(Text, nullable=True)
    is_undone = Column(Boolean, default=False)
    undo_parent_id = Column(String, ForeignKey("modifiche.id"), nullable=True)

    azienda = relationship("Azienda", back_populates="modifiche")
