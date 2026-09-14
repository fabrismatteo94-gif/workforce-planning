const API_BASE = "http://localhost:8000";

export interface Azienda {
  id: string;
  nome: string;
  settore: string;
  regione: string | null;
  anno_fiscale: number;
}

export interface ParametriOrg {
  id: string;
  azienda_id: string;
  turni: number;
  ore_per_turno: number;
  giorni_lavorativi_anno: number;
  margine_capacita_pct: number;
  budget_annuale: number | null;
  velocita_hiring_giorni: number;
  orizzonte_pianificazione_mesi: number;
}

export interface RisultatoFunzione {
  funzione_id: string;
  nome: string;
  fte_base: number;
  fte_con_overhead: number;
  fte_con_crescita: number;
  fte_finale: number;
  confidence: number;
  formula_usata: string;
  costo_annuo: number;
}

export interface CalcoloOut {
  fte_totali: number;
  costo_totale_annuo: number;
  budget_utilizzo_pct: number | null;
  stato_budget: "ok" | "warning" | "critical" | "n/a";
  per_funzione: RisultatoFunzione[];
}

export type ScenarioTipo = "Conservativo" | "Base" | "Aggressivo";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  listaAziende: () => req<Azienda[]>("/aziende"),

  creaAzienda: (payload: { nome: string; settore: string; anno_fiscale: number; regione?: string }) =>
    req<Azienda>("/aziende", { method: "POST", body: JSON.stringify(payload) }),

  ottieniParametriOrg: (aziendaId: string) =>
    req<ParametriOrg>(`/aziende/${aziendaId}/parametri-org`),

  aggiornaParametriOrg: (aziendaId: string, payload: Partial<ParametriOrg>) =>
    req<ParametriOrg>(`/aziende/${aziendaId}/parametri-org`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  aggiornaCaricoFunzione: (
    aziendaId: string,
    funzioneId: string,
    payload: { metrica_valore?: number; dettagli_metrica?: Record<string, unknown> }
  ) =>
    req(`/aziende/${aziendaId}/funzioni/${funzioneId}/carico`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  calcola: (aziendaId: string, scenarioTipo: ScenarioTipo) =>
    req<CalcoloOut>(`/aziende/${aziendaId}/calcolo`, {
      method: "POST",
      body: JSON.stringify({ scenario_tipo: scenarioTipo }),
    }),

  undo: (aziendaId: string) => req(`/aziende/${aziendaId}/undo`, { method: "POST" }),

  storico: (aziendaId: string) => req<any[]>(`/aziende/${aziendaId}/storico`),

  exportExcelUrl: (aziendaId: string) => `${API_BASE}/aziende/${aziendaId}/export/excel`,
};
