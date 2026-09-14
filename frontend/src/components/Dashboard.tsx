import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Azienda, ParametriOrg, CalcoloOut, ScenarioTipo } from "../api/client";
import { Header } from "./Header";
import { ParametriOrgPanel } from "./ParametriOrgPanel";
import { FunzioneAccordion } from "./FunzioneAccordion";

interface FunzioneLocale {
  id: string;
  nome: string;
  formula_key: string;
  metrica_valore: number;
  dettagli_metrica: Record<string, any>;
}

interface Props {
  azienda: Azienda;
  funzioniIniziali: FunzioneLocale[];
}

type Tab = "funzioni" | "storico";

const DEBOUNCE_MS = 500;

export function Dashboard({ azienda, funzioniIniziali }: Props) {
  const [parametri, setParametri] = useState<ParametriOrg | null>(null);
  const [funzioni, setFunzioni] = useState<FunzioneLocale[]>(funzioniIniziali);
  const [calcolo, setCalcolo] = useState<CalcoloOut | null>(null);
  const [scenario, setScenario] = useState<ScenarioTipo>("Base");
  const [tab, setTab] = useState<Tab>("funzioni");
  const [storico, setStorico] = useState<any[]>([]);
  const [saveVisible, setSaveVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.ottieniParametriOrg(azienda.id).then(setParametri);
    ricalcola("Base");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [azienda.id]);

  function scheduleRecalc(scenarioAttivo: ScenarioTipo = scenario) {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => ricalcola(scenarioAttivo), DEBOUNCE_MS);
  }

  async function ricalcola(scenarioAttivo: ScenarioTipo) {
    try {
      const risultato = await api.calcola(azienda.id, scenarioAttivo);
      setCalcolo(risultato);
      setError(null);
      flashSaved();
    } catch (e: any) {
      setError(e.message ?? "Errore nel calcolo");
    }
  }

  function flashSaved() {
    setSaveVisible(true);
    setTimeout(() => setSaveVisible(false), 2000);
  }

  async function handleParametriChange(patch: Partial<ParametriOrg>) {
    if (!parametri) return;
    const aggiornato = { ...parametri, ...patch };
    setParametri(aggiornato);
    await api.aggiornaParametriOrg(azienda.id, patch);
    scheduleRecalc();
  }

  async function handleMetricaChange(funzioneId: string, valore: number) {
    setFunzioni((prev) => prev.map((f) => (f.id === funzioneId ? { ...f, metrica_valore: valore } : f)));
    await api.aggiornaCaricoFunzione(azienda.id, funzioneId, { metrica_valore: valore });
    scheduleRecalc();
  }

  async function handleDettagliChange(funzioneId: string, dettagli: Record<string, any>) {
    setFunzioni((prev) => prev.map((f) => (f.id === funzioneId ? { ...f, dettagli_metrica: dettagli } : f)));
    await api.aggiornaCaricoFunzione(azienda.id, funzioneId, { dettagli_metrica: dettagli });
    scheduleRecalc();
  }

  async function handleScenarioChange(s: ScenarioTipo) {
    setScenario(s);
    await ricalcola(s);
  }

  async function handleUndo() {
    try {
      await api.undo(azienda.id);
      // Ricarica parametri + funzioni potenzialmente cambiati dall'undo, poi ricalcola
      const p = await api.ottieniParametriOrg(azienda.id);
      setParametri(p);
      await ricalcola(scenario);
      if (tab === "storico") caricaStorico();
    } catch (e: any) {
      setError(e.message ?? "Niente da annullare");
    }
  }

  async function caricaStorico() {
    const s = await api.storico(azienda.id);
    setStorico(s);
  }

  function apriTab(t: Tab) {
    setTab(t);
    if (t === "storico") caricaStorico();
  }

  if (!parametri) return <div style={{ padding: 40 }}>Caricamento…</div>;

  return (
    <>
      <Header
        scenario={scenario}
        onScenarioChange={handleScenarioChange}
        onUndo={handleUndo}
        undoDisabled={storico.length > 0 && storico[0]?.is_undone}
        budgetPct={calcolo?.budget_utilizzo_pct ?? null}
        statoBudget={calcolo?.stato_budget ?? "n/a"}
      />

      <div className="auxiell-main">
        <div className="tabbar">
          <button className={`tabbtn ${tab === "funzioni" ? "active" : ""}`} onClick={() => apriTab("funzioni")}>
            Per funzione
          </button>
          <button className={`tabbtn ${tab === "storico" ? "active" : ""}`} onClick={() => apriTab("storico")}>
            Storico
          </button>
          <a
            className="tabbtn"
            href={api.exportExcelUrl(azienda.id)}
            style={{ textDecoration: "none", marginLeft: "auto" }}
          >
            ⬇ Export Excel
          </a>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {tab === "funzioni" && (
          <>
            <ParametriOrgPanel parametri={parametri} onChange={handleParametriChange} />

            <div style={{ marginBottom: 24 }}>
              <h2 className="sectionheader">Funzioni e carico di lavoro</h2>
              {funzioni.map((f) => (
                <FunzioneAccordion
                  key={f.id}
                  nome={f.nome}
                  formulaKey={f.formula_key}
                  dettagliMetrica={f.dettagli_metrica}
                  metricaValore={f.metrica_valore}
                  risultato={calcolo?.per_funzione.find((r) => r.funzione_id === f.id)}
                  onChangeMetrica={(v) => handleMetricaChange(f.id, v)}
                  onChangeDettagli={(d) => handleDettagliChange(f.id, d)}
                />
              ))}
            </div>

            {calcolo && (
              <div className="summary">
                <div className="summarycard">
                  <div className="summarylabel">FTE totali</div>
                  <div className="summaryvalue">{calcolo.fte_totali}</div>
                </div>
                <div className="summarycard">
                  <div className="summarylabel">Costo annuo</div>
                  <div className="summaryvalue">€{Math.round(calcolo.costo_totale_annuo / 1000)}k</div>
                </div>
                <div className="summarycard">
                  <div className="summarylabel">Funzioni</div>
                  <div className="summaryvalue">{funzioni.length}</div>
                </div>
                <div className="summarycard">
                  <div className="summarylabel">Budget utiliz.</div>
                  <div className="summaryvalue">
                    {calcolo.budget_utilizzo_pct !== null ? `${calcolo.budget_utilizzo_pct}%` : "n/d"}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {tab === "storico" && (
          <div>
            <h2 className="sectionheader">Storico modifiche</h2>
            {storico.length === 0 && <p style={{ color: "var(--auxiell-mid)", fontSize: 13 }}>Nessuna modifica registrata.</p>}
            {storico.map((m) => (
              <div className="timelineitem" key={m.id}>
                <div className="timelinetime">{new Date(m.timestamp).toLocaleString("it-IT")}</div>
                <div>
                  <div className="timelinelabel">
                    {m.tipo_modifica} — {m.campo_modificato}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--auxiell-mid)" }}>
                    {JSON.stringify(m.valore_precedente)} → {JSON.stringify(m.valore_nuovo)}
                    {m.is_undone ? " (annullata)" : ""}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className={`savefeedback ${saveVisible ? "show" : ""}`}>✓ Salvato</div>
    </>
  );
}
