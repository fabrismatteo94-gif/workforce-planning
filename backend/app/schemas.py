from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


# ---------- Azienda ----------

class AziendaCreate(BaseModel):
    nome: str
    settore: str = "Manifattura"
    regione: Optional[str] = None
    anno_fiscale: int
    dimensione: Optional[str] = None
    modello_organizzativo: Optional[str] = None
    turnover_annuale_pct: Optional[float] = 0.0


class AziendaOut(AziendaCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    data_creazione: datetime


# ---------- Parametri Org ----------

class ParametriOrgUpdate(BaseModel):
    turni: Optional[int] = None
    ore_per_turno: Optional[float] = None
    giorni_lavorativi_anno: Optional[int] = None
    margine_capacita_pct: Optional[float] = None
    budget_annuale: Optional[float] = None
    velocita_hiring_giorni: Optional[int] = None
    orizzonte_pianificazione_mesi: Optional[int] = None


class ParametriOrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    azienda_id: str
    turni: int
    ore_per_turno: float
    giorni_lavorativi_anno: int
    margine_capacita_pct: float
    budget_annuale: Optional[float]
    velocita_hiring_giorni: int
    orizzonte_pianificazione_mesi: int


# ---------- Funzione + Carico ----------

class CaricoLavoroIn(BaseModel):
    metrica_tipo: str = "Unita_Anno"
    metrica_valore: float = 0.0
    dettagli_metrica: dict[str, Any] = {}
    fonte_dato: str = "Input_Manuale"
    is_stimato: bool = False
    confidence: float = 0.85
    note: Optional[str] = None


class FunzioneCreate(BaseModel):
    nome: str
    categoria: str = "Diretto"
    formula_key: str = "produzione_generica"
    salary_medio_annuo: float = 35000.0
    carico: CaricoLavoroIn


class FunzioneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    azienda_id: str
    nome: str
    categoria: str
    ordine: int


class CaricoLavoroUpdate(BaseModel):
    metrica_valore: Optional[float] = None
    dettagli_metrica: Optional[dict[str, Any]] = None
    is_stimato: Optional[bool] = None
    confidence: Optional[float] = None
    note: Optional[str] = None


# ---------- Calcolo ----------

class RisultatoFunzioneOut(BaseModel):
    funzione_id: str
    nome: str
    fte_base: float
    fte_con_overhead: float
    fte_con_crescita: float
    fte_finale: float
    confidence: float
    formula_usata: str
    costo_annuo: float


class CalcoloOut(BaseModel):
    fte_totali: float
    costo_totale_annuo: float
    budget_utilizzo_pct: Optional[float]
    stato_budget: str
    per_funzione: list[RisultatoFunzioneOut]


class CalcoloRequest(BaseModel):
    scenario_tipo: str = "Base"  # Conservativo | Base | Aggressivo
    crescita_pct_override: Optional[float] = None  # se non passato, deriva dallo scenario_tipo
