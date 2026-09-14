import { useEffect, useState } from "react";
import { api } from "./api/client";
import type { Azienda } from "./api/client";
import { Dashboard } from "./components/Dashboard";

// Template di default per il settore Manifattura (sezione 2 / Step 2 del flusso
// utente) — Fase 1 MVP copre solo questo settore, come da roadmap.
const FUNZIONI_TEMPLATE_MANIFATTURA = [
  {
    nome: "Produzione",
    categoria: "Diretto",
    formula_key: "produzione_generica",
    salary_medio_annuo: 33000,
    carico: {
      metrica_tipo: "Unita_Anno",
      metrica_valore: 10000,
      dettagli_metrica: { tempo_ciclo: 0.02, overhead_pct: 0.3 },
    },
  },
  {
    nome: "QA / Controllo Qualità",
    categoria: "Diretto",
    formula_key: "qa",
    salary_medio_annuo: 33500,
    carico: { metrica_tipo: "Custom", metrica_valore: 0, dettagli_metrica: { rapporto: 2.5 } },
  },
  {
    nome: "Manutenzione",
    categoria: "Indiretto",
    formula_key: "manutenzione",
    salary_medio_annuo: 35000,
    carico: { metrica_tipo: "Custom", metrica_valore: 0, dettagli_metrica: {} },
  },
];

export default function App() {
  const [azienda, setAzienda] = useState<Azienda | null>(null);
  const [funzioni, setFunzioni] = useState<any[] | null>(null);
  const [nome, setNome] = useState("");
  const [regione, setRegione] = useState("");
  const [annoFiscale, setAnnoFiscale] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Se esiste già un'azienda salvata (sessione precedente), riprendi da lì
  useEffect(() => {
    api.listaAziende().then((lista) => {
      if (lista.length > 0) caricaAzienda(lista[0]);
    });
  }, []);

  async function caricaAzienda(a: Azienda) {
    setAzienda(a);
    const res = await fetch(`http://localhost:8000/aziende/${a.id}/funzioni`);
    const funzioniDb: { id: string; nome: string }[] = await res.json();

    // Arricchisce con formula_key e dettagli — per l'MVP li deduciamo dal
    // template originale per nome (in Fase 2 questi campi saranno esposti
    // direttamente dall'endpoint GET funzioni)
    const arricchite = funzioniDb.map((f) => {
      const t = FUNZIONI_TEMPLATE_MANIFATTURA.find((tt) => tt.nome === f.nome);
      return {
        id: f.id,
        nome: f.nome,
        formula_key: t?.formula_key ?? "produzione_generica",
        metrica_valore: t?.carico.metrica_valore ?? 0,
        dettagli_metrica: t?.carico.dettagli_metrica ?? {},
      };
    });
    setFunzioni(arricchite);
  }

  async function handleSetup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const nuovaAzienda = await api.creaAzienda({
        nome,
        settore: "Manifattura",
        anno_fiscale: annoFiscale,
        regione: regione || undefined,
      });

      const funzioniCreate = [];
      for (const template of FUNZIONI_TEMPLATE_MANIFATTURA) {
        const res = await fetch(`http://localhost:8000/aziende/${nuovaAzienda.id}/funzioni`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(template),
        });
        const creata = await res.json();
        funzioniCreate.push({
          id: creata.id,
          nome: template.nome,
          formula_key: template.formula_key,
          metrica_valore: template.carico.metrica_valore,
          dettagli_metrica: template.carico.dettagli_metrica,
        });
      }

      setAzienda(nuovaAzienda);
      setFunzioni(funzioniCreate);
    } catch (err: any) {
      setError(err.message ?? "Errore nella creazione dell'azienda");
    } finally {
      setLoading(false);
    }
  }

  if (azienda && funzioni) {
    return <Dashboard azienda={azienda} funzioniIniziali={funzioni} />;
  }

  return (
    <div>
      <div className="auxiell-header">
        <div className="auxiell-brand">
          <svg className="auxiell-logo-svg" viewBox="0 0 257.53 242.2" xmlns="http://www.w3.org/2000/svg">
            <path
              fill="#97a4ae"
              d="m196.24,150.26c-7.41-10.88-10.88-20.26-10.88-29.17,0-8.4,2.97-16.79,9.9-27.17L257.53,0h-55.85l-48.95,73.64c-4.94,7.41-8.4,15.82-10.87,24.23h-26.2c-1.97-8.41-5.93-16.82-10.87-24.23L55.36,0H0l62.29,93.92c6.91,10.38,9.88,18.78,9.88,27.17,0,8.91-3.46,18.29-10.88,29.17L0,242.2h55.36l49.43-73.17c5.44-8.4,9.38-17.29,11.85-26.69h24.23c2.47,9.4,6.43,18.29,11.85,26.69l49.43,73.17h55.36l-61.29-91.94Z"
            />
          </svg>
          <div className="auxiell-text">auxiell</div>
        </div>
      </div>

      <div className="setup-screen">
        <h2 className="sectionheader" style={{ marginBottom: 20 }}>
          Nuova pianificazione — Setup azienda
        </h2>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSetup}>
          <label className="fieldlabel">Nome azienda</label>
          <input value={nome} onChange={(e) => setNome(e.target.value)} required />

          <label className="fieldlabel">Regione</label>
          <input value={regione} onChange={(e) => setRegione(e.target.value)} placeholder="es. Lombardia" />

          <label className="fieldlabel">Anno fiscale</label>
          <input
            type="number"
            value={annoFiscale}
            onChange={(e) => setAnnoFiscale(Number(e.target.value))}
            required
          />

          <p style={{ fontSize: 12, color: "var(--auxiell-mid)", marginBottom: 16 }}>
            Fase 1 MVP: template Manifattura (Produzione, QA, Manutenzione) pre-caricato.
          </p>

          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? "Creazione…" : "Crea azienda e vai alla dashboard"}
          </button>
        </form>
      </div>
    </div>
  );
}
