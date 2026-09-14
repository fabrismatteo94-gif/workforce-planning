import { useState } from "react";
import type { RisultatoFunzione } from "../api/client";

interface Props {
  nome: string;
  formulaKey: string;
  dettagliMetrica: Record<string, any>;
  metricaValore: number;
  risultato: RisultatoFunzione | undefined;
  onChangeMetrica: (valore: number) => void;
  onChangeDettagli: (dettagli: Record<string, any>) => void;
}

function confidenceClass(c: number): string {
  if (c >= 0.85) return "";
  if (c >= 0.6) return "medium";
  return "low";
}

export function FunzioneAccordion({
  nome,
  formulaKey,
  dettagliMetrica,
  metricaValore,
  risultato,
  onChangeMetrica,
  onChangeDettagli,
}: Props) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="accordion">
      <div className="accordionheader" onClick={() => setExpanded(!expanded)}>
        <span>
          {expanded ? "▼" : "▶"} {nome.toUpperCase()}
        </span>
        <span style={{ fontSize: 11, color: "var(--auxiell-mid)" }}>
          FTE: <strong>{risultato?.fte_finale ?? "—"}</strong>
        </span>
      </div>

      {expanded && (
        <div className="accordionbody">
          {formulaKey === "produzione_generica" && (
            <>
              <div className="fieldrow">
                <div>
                  <div className="fieldlabel">Carico (unità/anno)</div>
                  <input
                    type="number"
                    className="fieldinput"
                    value={metricaValore}
                    onChange={(e) => onChangeMetrica(Number(e.target.value))}
                  />
                </div>
                <div>
                  <div className="fieldlabel">Tempo ciclo (ore/unità)</div>
                  <input
                    type="number"
                    step="0.01"
                    className="fieldinput"
                    value={dettagliMetrica.tempo_ciclo ?? 0.02}
                    onChange={(e) =>
                      onChangeDettagli({ ...dettagliMetrica, tempo_ciclo: Number(e.target.value) })
                    }
                  />
                </div>
              </div>
              <div className="fieldrow full">
                <div>
                  <div className="fieldlabel">Overhead %</div>
                  <input
                    type="number"
                    className="fieldinput"
                    value={Math.round((dettagliMetrica.overhead_pct ?? 0.3) * 100)}
                    onChange={(e) =>
                      onChangeDettagli({ ...dettagliMetrica, overhead_pct: Number(e.target.value) / 100 })
                    }
                  />
                </div>
              </div>
            </>
          )}

          {(formulaKey === "qa" || formulaKey === "supervisione" || formulaKey === "logistica_interna") && (
            <div className="fieldrow full">
              <div>
                <div className="fieldlabel">Rapporto (1 ogni X operatori produzione)</div>
                <input
                  type="number"
                  step="0.1"
                  className="fieldinput"
                  value={dettagliMetrica.rapporto ?? 2.5}
                  onChange={(e) => onChangeDettagli({ ...dettagliMetrica, rapporto: Number(e.target.value) })}
                />
              </div>
            </div>
          )}

          {formulaKey === "manutenzione" && (
            <div className="fieldrow full">
              <div>
                <div className="fieldlabel">Formula</div>
                <input
                  type="text"
                  className="fieldinput"
                  value="0.5 + 0.1 × FTE Produzione"
                  disabled
                  style={{ color: "var(--auxiell-mid)" }}
                />
              </div>
            </div>
          )}

          {risultato && (
            <div className="outputrow">
              <div>
                <div className="outputlabel">FTE calcolato</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
                  <span className="outputvalue">{risultato.fte_finale}</span>
                  <span className={`confidence ${confidenceClass(risultato.confidence)}`}>
                    {Math.round(risultato.confidence * 100)}%
                  </span>
                </div>
              </div>
              <div style={{ textAlign: "right", marginLeft: "auto" }}>
                <div className="outputlabel">Costo annuo</div>
                <div className="outputvalue" style={{ fontSize: 18 }}>
                  €{Math.round(risultato.costo_annuo / 1000)}k
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
